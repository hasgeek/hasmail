"""Login support."""

from typing import Dict, Optional

from flask import Markup, escape, flash, redirect
from flask.typing import ResponseReturnValue

from baseframe.forms import render_message
from coaster.views import get_next_url

from .. import _, app, lastuser
from ..models import User, db


@app.route('/login')
@lastuser.login_handler
def login() -> Dict[str, str]:
    return {'scope': 'id email phone organizations'}


@app.route('/logout')
@lastuser.logout_handler
def logout() -> str:
    flash(_("You are now logged out"), category='success')
    return get_next_url()


@app.route('/login/redirect')
@lastuser.auth_handler
def lastuserauth() -> ResponseReturnValue:
    return redirect(get_next_url())


@app.route('/login/notify', methods=['POST'])
@lastuser.notification_handler
def lastusernotify(user: User):
    # Perform operations here if required.
    # Warning: this *could* be a spoof call, so ignore all request data.
    # Only trust the 'user' parameter to this function.
    db.session.commit()


@lastuser.auth_error_handler
def lastuser_error(
    error: str, error_description: Optional[str] = None, error_uri: Optional[str] = None
) -> ResponseReturnValue:
    if error == 'access_denied':
        flash(_("You denied the request to login"), category='error')
        return redirect(get_next_url())
    return render_message(
        title=_("Error: {error}").format(error=error),
        message=Markup(
            f"<p>{escape(error_description or '')}</p>"
            f"<p>URI: {escape(error_uri or _('NA'))}</p>"
        ),
    )
