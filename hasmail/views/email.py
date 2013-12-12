#! -*- coding: utf-8 -*-

from flask import flash
from baseframe.forms import render_redirect, render_form,

from .. import app, lastuser
from ..models import db, Account, Campaign
from ..forms import AccountForm, CampaignForm, SendEmailForm


@app.route('/account', methods=["POST", "GET"])
@lastuser.requires_login
def account_view():
    form = AccountForm()
    if form.validate_on_submit():
        account = Account()
        form.populate_obj(account)
        db.session.add(account)
        db.session.commit()
        flash(u"Account details saved", "success")
        return render_redirect(url_for('index'), code=303)
    return render_form(form=form, title="Change account details", submit=u"Edit",
        cancel_url=url_for('index'), ajax=False)


@app.route('/campaign/new', methods=["POST", "GET"])
@lastuser.requires_login
def campaign_new(campaign):
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign()
        form.populate_obj(campaign)
        db.session.add(campaign)
        db.session.commit()
        flash(u"Campaign created", "success")
        return render_redirect(url_for('campaign_view', id=campaign.id), code=303)
    return render_form(form=form, title="New campaign", submit=u"Create",
        cancel_url=url_for('index'), ajax=False)


@app.route('/campaign/<id>')
@lastuser.requires_login
@load_model(campaign, {'id': 'id'}, 'campaign')
def campaign_view(campaign):
    pass


@app.route('/campaign/<id>/<md5sum>', methods=["GET", "POST"])
@lastuser.requires_login
@load_models(
    (Campaign, {'id': 'id'}, 'campaign'),
    (Email, {'campaign': 'campaign', 'md5sum': 'md5sum'}, 'email'))
def send_email(campaign, id, email):
    form = SendEmailForm()
    if form.validate_on_submit():
        account = Account()
        form.populate_obj(account)
        db.session.add(account)
        db.session.commit()
        flash(u"Account details saved", "success")
        return render_redirect(url_for('campaign_view', id=id), code=303)
    return render_form(form=form, title="Send Email", submit=u"Send",
        cancel_url=url_for('campaign_view', id=id), ajax=False)

