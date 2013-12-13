# -*- coding: utf-8 -*-

from flask import flash, url_for, render_template
from coaster.views import load_model, load_models
from baseframe.forms import render_redirect, render_form

from .. import _, app, lastuser
from ..models import db, EmailCampaign, EmailRecipient
from ..forms import CampaignSettingsForm


@app.route('/mail/<campaign>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_view(campaign):
    form = CampaignSettingsForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        db.session.commit()
        return render_redirect(campaign.url_for(), code=303)
    return render_template('campaign.html', campaign=campaign, form=form)


@app.route('/mail/<campaign>/draft', defaults={'version': None})
@app.route('/mail/<campaign>/draft/<version>')
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit', kwargs=True)
def campaign_template(campaign, kwargs=None):
    return render_template('template.html', campaign=campaign)


@app.route('/mail/<campaign>/<recipient>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'md5sum': 'recipient'}, 'recipient'),
    permission='edit')
def recipient_view(campaign, recipient):
    return render_template('recipient.html', campaign=campaign, recipient=recipient)
