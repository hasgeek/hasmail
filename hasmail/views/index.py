"""Index views."""

from flask import g, redirect, render_template, url_for

from baseframe import forms

from .. import _, app, lastuser
from ..models import CAMPAIGN_STATUS, EmailCampaign, db


@app.route('/')
def index():
    if g.user:
        return redirect(url_for('dashboard'), code=303)
    return render_template('index.html.jinja2')


@app.route('/mail', methods=('GET', 'POST'))
@lastuser.requires_login
# To prevent public service from being abused
# @lastuser.requires_permission('emailuser')
def dashboard():
    form = forms.Form()
    if form.validate_on_submit():
        campaign = EmailCampaign(title=_("Untitled Email"), user=g.user)
        db.session.add(campaign)
        db.session.commit()
        return redirect(campaign.url_for(), 303)
    return render_template(
        'dashboard.html.jinja2',
        campaigns=g.user.campaigns,
        form=form,
        wstep=1,
        STATUS=CAMPAIGN_STATUS,
    )
