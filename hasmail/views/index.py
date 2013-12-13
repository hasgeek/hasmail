# -*- coding: utf-8 -*-

from flask import g, render_template, redirect
from .. import _, app, lastuser
from ..models import db, EmailCampaign
from ..forms import BlankForm

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mail', methods=('GET', 'POST'))
@lastuser.requires_login
# @lastuser.requires_permission('emailuser')  # To prevent public service from being abused
def dashboard():
    form = BlankForm()
    if form.validate_on_submit():
        campaign = EmailCampaign(title=_(u"Untitled Email"), user=g.user)
        db.session.add(campaign)
        db.session.commit()
        return redirect(campaign.url_for(), 303)
    return render_template('dashboard.html', campaigns=g.user.campaigns, form=form, wstep=1)


@app.route('/wip')
def wip():
    return render_template('wip.html')
