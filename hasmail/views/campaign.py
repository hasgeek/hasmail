# -*- coding: utf-8 -*-

from StringIO import StringIO
import unicodecsv
from flask import g, url_for, request, render_template, flash, redirect, Markup
from flask.ext.mail import Message
from flask.ext.rq import job
from coaster.utils import make_name
from coaster.views import load_model
from baseframe.forms import render_redirect, render_delete_sqla

from .. import app, mail, lastuser, _
from ..models import db, User, EmailCampaign, EmailRecipient, CAMPAIGN_STATUS
from ..forms import CampaignSettingsForm, CampaignSendForm
from .diffpatch import update_recipient


def import_from_csv(campaign, reader):
    existing = set([r.email.lower() for r in
        db.session.query(EmailRecipient.email).filter(EmailRecipient.campaign == campaign).all()])

    fields = set(campaign.fields)

    for row in reader:
        row = dict([(make_name(key), value.strip()) for key, value in row.items()])

        fullname = firstname = lastname = email = nickname = None

        # The first column in each of the following is significant as that is the field name
        # in the EmailRecipient model and is the name passed to the email template

        # Now look for email (mandatory), first name, last name and full name
        for field in ['email', 'e-mail', 'email-id', 'e-mail-id', 'email-address', 'e-mail-address']:
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
            recipient = EmailRecipient(campaign=campaign, email=email.lower(),
                fullname=fullname, firstname=firstname, lastname=lastname, nickname=nickname)
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
def campaign_view(campaign):
    form = CampaignSettingsForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        if 'importfile' in request.files:
            data = StringIO(request.files['importfile'].getvalue().replace('\r\n', '\n').replace('\r', '\n'))
            reader = unicodecsv.DictReader(data)
            import_from_csv(campaign, reader)
        db.session.commit()
        return render_redirect(campaign.url_for('recipients'), code=303)
    return render_template('campaign.html', campaign=campaign, form=form, wstep=2)


@app.route('/mail/<campaign>/delete', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='delete')
def campaign_delete(campaign):
    return render_delete_sqla(campaign, db, title=_(u"Confirm delete"),
        message=_(u"Remove campaign ‘{title}’? This will delete ALL data related to the campaign. There is no undo.").format(title=campaign.title),
        success=_(u"You have deleted the ‘{title}’ campaign and ALL related data").format(title=campaign.title),
        next=url_for('index'))


@app.route('/mail/<campaign>/recipients')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_recipients(campaign):
    return render_template('recipients.html', campaign=campaign, wstep=3)


@app.route('/mail/<campaign>/send', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='send')
def campaign_send(campaign):
    form = CampaignSendForm()
    form.email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
    if form.validate_on_submit():
        campaign.status = CAMPAIGN_STATUS.QUEUED
        db.session.commit()
        campaign_send_do.delay(campaign.id, g.user.id, form.email.data)
        flash(_(u"Your email has been queued for delivery"), 'success')
        return redirect(campaign.url_for('report'), code=303)
    return render_template('send.html', campaign=campaign, form=form, wstep=5)


@app.route('/mail/<campaign>/report')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='report')
def campaign_report(campaign):
    recipients = campaign.recipients
    recipients.sort(key=lambda r:
        ((r.rsvp == u'Y' and 1) or (r.rsvp == u'M' and 2) or (r.rsvp == u'N' and 3) or (r.opened and 4) or 5, r.fullname))
    return render_template('report.html', campaign=campaign, recipients=recipients, recipient=None, wstep=6)


@job('hasmail')
def campaign_send_do(campaign_id, user_id, email):
    ctx = None
    if not request:
        ctx = app.test_request_context()
        ctx.push()
    campaign = EmailCampaign.query.get(campaign_id)
    campaign.status = CAMPAIGN_STATUS.SENDING
    draft = campaign.draft()
    user = User.query.get(user_id)

    # User wants to send. Perform all necessary activities:
    # 1. Wrap links if click tracking is enabled, in the master template
    # TODO
    # 2. Update all drafts
    send_to = [recipient for recipient in campaign.recipients if not recipient.rendered_text]
    for recipient in send_to:
        update_recipient(recipient)
        # 3. Wrap links in custom templates
        # TODO
        # 4. Generate rendering per recipient and mark recipient as sent
        recipient.rendered_text = recipient.get_rendered(draft)
        recipient.rendered_html = recipient.get_preview(draft)
        # 5. Send message
        msg = Message(
            subject=(recipient.subject if recipient.subject is not None else draft.subject) if recipient.draft else draft.subject,
            sender=(user.fullname, email),
            recipients=['"{fullname}" <{email}>'.format(fullname=recipient.fullname.replace('"', "'"), email=recipient.email)],
            body=recipient.rendered_text,
            html=Markup(recipient.rendered_html) + recipient.openmarkup(),
            cc=campaign.cc.split('\n'),
            bcc=campaign.bcc.split('\n')
            )
        mail.send(msg)
        # 6. Commit after each recipient
        db.session.commit()

    # Done!
    campaign.status = CAMPAIGN_STATUS.SENT
    db.session.commit()

    if ctx:
        ctx.pop()
