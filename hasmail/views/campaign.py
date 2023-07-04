"""Email campaign views."""

import csv
from email.utils import formataddr
from io import StringIO
from typing import Any, Dict, List, Union

from flask import Markup, flash, g, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_mail import Message

from baseframe.forms import render_delete_sqla, render_redirect
from coaster.utils import make_name
from coaster.views import load_model

from .. import _, app, lastuser, mail, rq
from ..forms import CampaignSendForm, CampaignSettingsForm
from ..models import (
    AppenderQuery,
    EmailCampaign,
    EmailCampaignState,
    EmailRecipient,
    User,
    db,
)
from .diffpatch import update_recipient


def import_from_csv(campaign: EmailCampaign, reader: csv.DictReader) -> None:
    existing = {
        # pylint: disable=protected-access
        r.email.lower()
        for r in db.session.query(EmailRecipient._email)
        .filter(EmailRecipient.campaign == campaign)
        .all()
    }

    fields = set(campaign.fields)

    for row in reader:
        row = {make_name(key): value.strip() for key, value in row.items()}

        fullname = firstname = lastname = email = nickname = None

        # The first column in each of the following is significant as that is the field
        # name in the EmailRecipient model and is the name passed to the email template

        # Now look for email (mandatory), first name, last name and full name
        for field in [
            'email',
            'e-mail',
            'email-id',
            'e-mail-id',
            'email-address',
            'e-mail-address',
        ]:
            if field in row and row[field]:
                email = row[field]
                del row[field]
                break

        if not email:
            continue

        # XXX: Cheating! Don't hardcode for Funnel's columns
        for field in ['fullname', 'name', 'full-name', 'speaker', 'proposer']:
            if field in row and row[field]:
                fullname = row[field]
                del row[field]
                break

        for field in ['firstname', 'first-name', 'given-name', 'fname']:
            if field in row and row[field]:
                firstname = row[field]
                del row[field]
                break

        for field in ['lastname', 'last-name', 'surname', 'lname']:
            if field in row and row[field]:
                lastname = row[field]
                del row[field]
                break

        for field in ['nickname', 'nick', 'nick-name']:
            if field in row and row[field]:
                nickname = row[field]
                del row[field]
                break

        if email.lower() not in existing:
            recipient = EmailRecipient(
                campaign=campaign,
                email=email.lower(),
                fullname=fullname,
                firstname=firstname,
                lastname=lastname,
                nickname=nickname,
            )
            recipient.data = {}
            for key in row:
                recipient.data[key] = row[key].strip()
                fields.add(key)
            db.session.add(recipient)
            existing.add(recipient.email.lower())

    campaign.fields = fields


@app.route('/mail/<campaign>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_view(campaign: EmailCampaign) -> ResponseReturnValue:
    form = CampaignSettingsForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        if 'importfile' in request.files:
            fileob = request.files['importfile']
            if fileob.filename != '':
                data = StringIO(fileob.read().decode())
                reader = csv.DictReader(data)
                import_from_csv(campaign, reader)
        db.session.commit()
        return render_redirect(campaign.url_for('recipients'), code=303)
    return render_template(
        'campaign.html.jinja2', campaign=campaign, form=form, wstep=2
    )


@app.route('/mail/<campaign>/delete', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='delete')
def campaign_delete(campaign: EmailCampaign) -> ResponseReturnValue:
    return render_delete_sqla(
        campaign,
        db,
        title=_("Confirm delete"),
        message=_(
            "Remove campaign ‘{title}’? This will delete ALL data related to the"
            " campaign. There is no undo."
        ).format(title=campaign.title),
        success=_(
            "You have deleted the ‘{title}’ campaign and ALL related data"
        ).format(title=campaign.title),
        next=url_for('index'),
    )


@app.route('/mail/<campaign>/recipients', defaults={'page': 1})
@app.route('/mail/<campaign>/recipients/<int:page>')
@lastuser.requires_login
@load_model(
    EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit', kwargs=True
)
def campaign_recipients(
    campaign: EmailCampaign, kwargs: Dict[str, Any]
) -> ResponseReturnValue:
    page = kwargs.get('page', 1)
    return render_template(
        'recipients.html.jinja2', campaign=campaign, page=page, wstep=3
    )


@app.route('/mail/<campaign>/send', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='send')
def campaign_send(campaign: EmailCampaign) -> ResponseReturnValue:
    form = CampaignSendForm()
    form.email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
    if form.validate_on_submit():
        campaign.status = EmailCampaignState.QUEUED
        db.session.commit()

        campaign_send_do.queue(campaign.id, g.user.id, form.email.data, timeout=86400)
        flash(_("Your email has been queued for delivery"), 'success')
        return redirect(campaign.url_for('report'), code=303)
    return render_template('send.html.jinja2', campaign=campaign, form=form, wstep=5)


@app.route('/mail/<campaign>/report')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='report')
def campaign_report(campaign: EmailCampaign) -> ResponseReturnValue:
    recipients: Union[List[EmailRecipient], AppenderQuery[EmailRecipient]]
    count = campaign.recipients.count()
    if count > 1000:
        recipients = campaign.recipients
    else:
        recipients = campaign.recipients.all()
        recipients.sort(
            key=lambda r: (
                (r.rsvp == 'Y' and 1)
                or (r.rsvp == 'M' and 2)
                or (r.rsvp == 'N' and 3)
                or (r.opened and 4)
                or 5,
                r.fullname or '',
            )
        )
    return render_template(
        'report.html.jinja2',
        campaign=campaign,
        recipients=recipients,
        recipient=None,
        count=count,
        wstep=6,
    )


@rq.job('hasmail')
def campaign_send_do(campaign_id: int, user_id: int, email: str) -> None:
    ctx = None
    if not request:
        ctx = app.test_request_context()
        ctx.push()
    campaign = EmailCampaign.query.get(campaign_id)
    if campaign is None:
        return
    campaign.status = EmailCampaignState.SENDING
    draft = campaign.draft()
    if draft is None:
        return
    user = User.query.get(user_id)
    if user is None:
        return

    # User wants to send. Perform all necessary activities:
    # 1. Update all drafts
    for recipient in campaign.recipients_iter():
        if not recipient.rendered_text:
            update_recipient(recipient)
            # 2. Generate rendering per recipient and mark recipient as sent
            recipient.rendered_text = recipient.get_rendered()
            recipient.rendered_html = recipient.get_preview()
            # 3. Send message
            msg = Message(
                subject=(
                    recipient.subject
                    if recipient.subject is not None
                    else draft.subject
                )
                if recipient.custom_draft
                else draft.subject,
                sender=formataddr((user.fullname, email)),
                recipients=[formataddr((recipient.fullname or '', recipient.email))],
                body=recipient.rendered_text,
                html=Markup(recipient.rendered_html) + recipient.openmarkup(),
                cc=campaign.cc.split('\n'),
                bcc=campaign.bcc.split('\n'),
            )
            mail.send(msg)
            # 4. Commit after each recipient
            db.session.commit()

    # 5. Done!
    campaign.status = EmailCampaignState.SENT
    db.session.commit()

    if ctx:
        ctx.pop()
