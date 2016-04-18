# -*- coding: utf-8 -*-

from StringIO import StringIO
import unicodecsv
import phonenumbers
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
    existing_email = set([r.email.lower() for r in
        db.session.query(EmailRecipient.email).filter(EmailRecipient.campaign == campaign).all()])
    existing_phone = set([r.phone for r in
        db.session.query(EmailRecipient.phone).filter(EmailRecipient.campaign == campaign).all()])

    existing_email.remove(None)
    existing_phone.remove(None)

    fields = set(campaign.fields)

    for row in reader:
        row = dict([(make_name(key), value.strip()) for key, value in row.items()])

        fullname = firstname = lastname = email = nickname = phone = None

        # The first column in each of the following is significant as that is the field name
        # in the EmailRecipient model and is the name passed to the email template

        # Now look for email or phone (mandatory), first name, last name and full name
        for field in ['email', 'e-mail', 'email-id', 'e-mail-id', 'email-address', 'e-mail-address']:
            if field in row and row[field]:
                email = row[field].lower()
                del row[field]
                break

        for field in ['phone', 'phone-no', 'phone-number', 'mobile', 'mobile-no', 'mobile-number', 'telephone']:
            if field in row and row[field]:
                phone = row[field]
                try:
                    phone_parsed = phonenumbers.parse(phone, campaign.default_country)
                    phone = phonenumbers.format_number(phone_parsed, phonenumbers.PhoneNumberFormat.E164)
                except phonenumbers.NumberParseException:
                    pass
                del row[field]
                break

        if not (email or phone):
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

        if email not in existing_email and phone not in existing_phone:
            recipient = EmailRecipient(campaign=campaign)
            db.session.add(recipient)
        elif email:
            recipient = EmailRecipient.get(campaign=campaign, email=email)
        elif phone:
            recipient = EmailRecipient.get(campaign=campaign, phone=phone)
        else:
            raise Exception("This should not happen")

        if recipient:
            recipient.email = email
            recipient.phone = phone
            recipient.fullname = fullname
            recipient.firstname = firstname
            recipient.lastname = lastname
            recipient.nickname = nickname
            if not recipient.data:
                recipient.data = {}
            for key in row:
                recipient.data[key] = row[key].strip()
                fields.add(key)
            if recipient.email:
                existing_email.add(recipient.email)
            if recipient.phone:
                existing_phone.add(recipient.phone)

    campaign.fields = fields


@app.route('/mail/<campaign>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_view(campaign):
    form = CampaignSettingsForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        if 'importfile' in request.files:
            fileob = request.files['importfile']
            if hasattr(fileob, 'getvalue'):
                data = fileob.getvalue()
            else:
                data = fileob.read()
            data = StringIO(data.replace('\r\n', '\n').replace('\r', '\n'))
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


@app.route('/mail/<campaign>/recipients', defaults={'page': 1})
@app.route('/mail/<campaign>/recipients/<int:page>')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit', kwargs=True)
def campaign_recipients(campaign, kwargs):
    page = kwargs.get('page', 1)
    return render_template('recipients.html', campaign=campaign, page=page, wstep=3)


@app.route('/mail/<campaign>/send', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='send')
def campaign_send(campaign):
    form = CampaignSendForm()
    form.email.choices = [(e, e) for e in lastuser.user_emails(g.user)]
    if form.validate_on_submit():
        campaign.status = CAMPAIGN_STATUS.QUEUED
        db.session.commit()

        campaign_send_do.delay(campaign.id, g.user.id, form.email.data, timeout=86400)
        flash(_(u"Your email has been queued for delivery"), 'success')
        return redirect(campaign.url_for('report'), code=303)
    return render_template('send.html', campaign=campaign, form=form, wstep=5)


@app.route('/mail/<campaign>/report')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='report')
def campaign_report(campaign):
    count = campaign.recipients.count()
    if count > 1000:
        recipients = campaign.recipients
    else:
        recipients = campaign.recipients.all()
        recipients.sort(key=lambda r:
            ((r.rsvp == u'Y' and 1) or (r.rsvp == u'M' and 2) or (r.rsvp == u'N' and 3) or (r.opened and 4) or 5, r.fullname))
    return render_template('report.html', campaign=campaign, recipients=recipients, recipient=None, count=count, wstep=6)


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
    for recipient in campaign.recipients_iter():
        if not recipient.rendered_text:
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
                recipients=[u'"{fullname}" <{email}>'.format(fullname=(recipient.fullname or '').replace('"', "'"), email=recipient.email)],
                body=recipient.rendered_text,
                html=Markup(recipient.rendered_html) + recipient.openmarkup(),
                cc=campaign.cc.split('\n'),
                bcc=campaign.bcc.split('\n')
                )
            mail.send(msg)
            # print msg.recipients
            # 6. Commit after each recipient
            db.session.commit()

    # Done!
    campaign.status = CAMPAIGN_STATUS.SENT
    db.session.commit()

    if ctx:
        ctx.pop()
