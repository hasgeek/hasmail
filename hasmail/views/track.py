from base64 import b64decode
from datetime import datetime

from flask import redirect, render_template, request

from coaster.views import load_models

from .. import app
from ..models import EmailLink, EmailLinkRecipient, EmailRecipient, db

gif1x1 = b64decode(b'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw==')


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
def track_open_gif(opentoken):
    recipient = EmailRecipient.query.filter_by(opentoken=opentoken).first()
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
    else:
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


@app.route('/go/<name>/<opentoken>')
@load_models(
    (EmailLink, {'name': 'name'}, 'link'),
    (EmailRecipient, {'opentoken': 'opentoken'}, 'recipient'),
)
def track_open_link(link, recipient):
    track_open_inner(recipient, isopen=False)
    link_recipient = EmailLinkRecipient.query.get((link.id, recipient.id))
    if not link_recipient:
        link_recipient = EmailLinkRecipient(link=link, recipient=recipient)
        db.session.add(link_recipient)
    db.session.commit()
    return redirect(link.url)


@app.route('/rsvp/<rsvptoken>/<status>')
def rsvp(rsvptoken, status):
    recipient = EmailRecipient.query.filter_by(rsvptoken=rsvptoken).first_or_404()
    status = status.upper()
    if status in ('Y', 'N', 'M'):
        recipient.rsvp = status
        db.session.commit()
    return render_template('rsvp.html.jinja2', recipient=recipient, status=status)
