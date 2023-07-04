"""Email view tracker."""

from base64 import b64decode
from datetime import datetime

from flask import render_template, request
from flask.typing import ResponseReturnValue

from .. import app
from ..models import MailerRecipient, db

gif1x1 = b64decode(b'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw==')


def track_open_inner(recipient: MailerRecipient, isopen: bool = True) -> None:
    recipient.opened = True
    now = datetime.utcnow()
    if not recipient.opened_ipaddr:
        recipient.opened_ipaddr = request.remote_addr
    if not recipient.opened_first_at:
        recipient.opened_first_at = now
    if isopen:
        recipient.opened_last_at = now
        recipient.opened_count = MailerRecipient.opened_count + 1
    else:
        if not recipient.opened_last_at:
            recipient.opened_last_at = now


@app.route('/open/<opentoken>.gif')
def track_open_gif(opentoken) -> ResponseReturnValue:
    recipient = MailerRecipient.query.filter_by(opentoken=opentoken).first()
    if recipient is not None:
        track_open_inner(recipient, isopen=True)
        db.session.commit()
        return (
            gif1x1,
            200,
            {
                'Content-Type': 'image/gif',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
            },
        )
    return (
        gif1x1,
        404,
        {
            'Content-Type': 'image/gif',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
        },
    )


@app.route('/rsvp/<rsvptoken>/<status>')
def rsvp(rsvptoken, status) -> ResponseReturnValue:
    recipient = MailerRecipient.query.filter_by(rsvptoken=rsvptoken).first_or_404()
    status = status.upper()
    if status in ('Y', 'N', 'M'):
        recipient.rsvp = status
        db.session.commit()
    return render_template('rsvp.html.jinja2', recipient=recipient, status=status)
