# -*- coding: utf-8 -*-

from coaster.views import load_model

from .. import app
from ..models import db, EmailRecipient

gif1x1 = 'R0lGODlhAQABAJAAAP8AAAAAACH5BAUQAAAALAAAAAABAAEAAAICBAEAOw=='.decode('base64')


@app.route('/open/<opentoken>.gif', methods=('GET', 'POST'))
@load_model(EmailRecipient, {'opentoken': 'opentoken'}, 'recipient')
def track_open_gif(recipient):
    recipient.opened = True
    db.session.commit()

    return gif1x1, 200, {'Content-Type': 'image/gif'}
