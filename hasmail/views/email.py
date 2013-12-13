# -*- coding: utf-8 -*-

import unicodecsv
from flask import render_template, request
from coaster.utils import make_name, md5sum
from coaster.views import load_model, load_models
from baseframe.forms import render_redirect

from .. import _, app, lastuser
from ..models import db, EmailCampaign, EmailRecipient
from ..forms import CampaignSettingsForm


def import_from_csv(campaign, reader):
    existing = set([r.md5sum for r in
        db.session.query(EmailRecipient.md5sum).filter(EmailRecipient.campaign == campaign).all()])

    for row in reader:
        row = dict([(make_name(key), value) for key, value in row.items()])

        # Now look for email (mandatory), first name, last name and full name
        email = row.get('email') or row.get('e-mail') or row.get('email-address') or row.get('e-mail-address')
        if not email:
            continue

        fullname = row.get('name') or row.get('fullname') or row.get('full-name')
        firstname = row.get('first-name') or row.get('firstname') or row.get('given-name') or row.get('fname')
        lastname = row.get('last-name') or row.get('lastname') or row.get('surname') or row.get('lname')

        if md5sum(email) not in existing:
            recipient = EmailRecipient(campaign=campaign, email=email, fullname=fullname, firstname=firstname, lastname=lastname)
            recipient.data = {}
            for key in row:
                recipient.data[key] = row[key]
            db.session.add(recipient)
            existing.add(recipient.md5sum)


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


@app.route('/mail/<campaign>/recipients', defaults={'version': None})
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
    (EmailRecipient, {'campaign': 'campaign', 'md5sum': 'recipient'}, 'recipient'),
    permission='edit')
def recipient_view(campaign, recipient):
    return render_template('recipient.html', campaign=campaign, recipient=recipient, wstep=4)
