"""Index views."""

from flask import redirect, render_template, url_for
from flask.typing import ResponseReturnValue

from baseframe import forms
from coaster.auth import current_auth

from .. import _, app, lastuser
from ..models import Mailer, MailerState, db


@app.route('/')
def index() -> ResponseReturnValue:
    if current_auth:
        return redirect(url_for('dashboard'), code=303)
    return render_template('index.html.jinja2')


@app.route('/mail', methods=('GET', 'POST'))
@lastuser.requires_login
# To prevent public service from being abused
# @lastuser.requires_permission('emailuser')
def dashboard() -> ResponseReturnValue:
    form = forms.Form()
    if form.validate_on_submit():
        mailer = Mailer(title=_("Untitled Email"), user=current_auth.user)
        db.session.add(mailer)
        db.session.commit()
        return redirect(mailer.url_for(), 303)
    return render_template(
        'dashboard.html.jinja2',
        mailers=current_auth.user.mailers,
        form=form,
        wstep=1,
        STATUS=MailerState,
    )
