# -*- coding: utf-8 -*-

from datetime import datetime
from flask import request, redirect
from coaster.views import load_model, load_models
from .. import app
from ..models import db, EmailRecipient, EmailLink, EmailLinkRecipient

gif1x1 = 'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw=='.decode('base64')


def track_open_inner(recipient, isopen=True):
    recipient.opened = True
    now = datetime.utcnow()
    if not recipient.opened_ipaddr:
        recipient.opened_ipaddr = request.remote_addr
    if not recipient.opened_first_at:
        recipient.opened_first_at = now
    if isopen:
        recipient.opened_last_at = now
        recipient.opened_count = EmailRecipient.opened_count + 1
    else:
        if not recipient.opened_last_at:
            recipient.opened_last_at = now


@app.route('/open/<opentoken>.gif')
@load_model(EmailRecipient, {'opentoken': 'opentoken'}, 'recipient')
def track_open_gif(recipient):
    track_open_inner(recipient, isopen=True)
    db.session.commit()

    return gif1x1, 200, {'Content-Type': 'image/gif'}


@app.route('/go/<name>/<opentoken>')
@load_models(
    (EmailLink, {'name': 'name'}, 'link'),
    (EmailRecipient, {'opentoken': 'opentoken'}, 'recipient'))
def track_open_link(link, recipient):
    track_open_inner(recipient, isopen=False)
    link_recipient = EmailLinkRecipient.query.get((link.id, recipient.id))
    if not link_recipient:
        link_recipient = EmailLinkRecipient(link=link, recipient=recipient)
        db.session.add(link_recipient)
    db.session.commit()
    return redirect(link.url)
