# -*- coding: utf-8 -*-

import unicodecsv
from flask import render_template, request
from coaster.utils import make_name
from coaster.views import load_model, load_models
from baseframe.forms import render_redirect

from .. import app, lastuser
from ..models import db, EmailCampaign, EmailRecipient
from ..forms import CampaignSettingsForm


def import_from_csv(campaign, reader):
    existing = set([r.email.lower() for r in
        db.session.query(EmailRecipient.email).filter(EmailRecipient.campaign == campaign).all()])

    headers = set(campaign.headers)

    for row in reader:
        row = dict([(make_name(key), value) for key, value in row.items()])

        fullname = firstname = lastname = email = None

        # The first column in each of the following is significant as that is the field name
        # in the EmailRecipient model and is the name passed to the email template

        # Now look for email (mandatory), first name, last name and full name
        for field in ['email', 'e-mail', 'email-address', 'e-mail-address']:
            if field in row and row[field]:
                email = row[field]
                del row[field]
                break

        if not email:
            continue

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

        if email.lower() not in existing:
            recipient = EmailRecipient(campaign=campaign, email=email, fullname=fullname, firstname=firstname, lastname=lastname)
            recipient.data = {}
            for key in row:
                recipient.data[key] = row[key]
                headers.add(key)
            db.session.add(recipient)
            existing.add(recipient.email)

    campaign.headers = headers


@app.route('/mail/<campaign>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_view(campaign):
    form = CampaignSettingsForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        if 'importfile' in request.files:
            reader = unicodecsv.DictReader(request.files['importfile'])
            import_from_csv(campaign, reader)
        db.session.commit()
        return render_redirect(campaign.url_for('recipients'), code=303)
    return render_template('campaign.html', campaign=campaign, form=form, wstep=2)


@app.route('/mail/<campaign>/recipients')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_recipients(campaign):
    return render_template('recipients.html', campaign=campaign, wstep=3)


@app.route('/mail/<campaign>/write', defaults={'version': None})
@app.route('/mail/<campaign>/write/<version>')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit', kwargs=True)
def campaign_template(campaign, kwargs=None):
    return render_template('template.html', campaign=campaign, wstep=4)


@app.route('/mail/<campaign>/<recipient>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='edit')
def recipient_view(campaign, recipient):
    return render_template('recipient.html', campaign=campaign, recipient=recipient, wstep=4)

@app.route('/mail/<campaign>/<recipient>/edit', methods=('POST',))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='edit')
def recipient_edit(campaign, recipient):

    if 'pk' in request.form and int(request.form['pk']) == recipient.url_id:
        if 'name' not in request.form:
            return "Field not specified", 400
        if 'value' not in request.form:
            return "Value not specified", 400
        field = request.form['name']
        value = request.form['value']
        if field == 'email':
            recipient.email = value
        elif field == 'fullname':
            recipient.fullname = value
        elif field == 'firstname':
            recipient.firstname = value
        elif field == 'lastname':
            recipient.lastname = value
        else:
            recipient.data[field] = value
        db.session.commit()
        return "Saved", 200
    else:
        return "Primary key missing, please contact the site administrator", 400
