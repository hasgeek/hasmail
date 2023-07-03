"""Hasgeek Mailer."""

# The imports in this file are order-sensitive

from flask import Flask
from flask_mail import Mail
from flask_migrate import Migrate
from flask_rq2 import RQ

import coaster.app
from baseframe import Version, _, __, assets, baseframe  # NOQA
from flask_lastuser import Lastuser
from flask_lastuser.sqlalchemy import UserManager

from ._version import __version__

version = Version(__version__)

# First, make an app

app = Flask(__name__, instance_relative_config=True)
mail = Mail()
lastuser = Lastuser()
rq = RQ()

# Second, import the models and views

from . import models, views  # noqa: F401 # isort:skip
from .models import db  # isort:skip

# Third, setup baseframe and assets

assets['hasmail.js'][version] = 'js/app.js'
assets['hasmail.css'][version] = 'css/app.css'


# Configure the app
coaster.app.init_app(app, config=['py', 'env'], env_prefix=['FLASK', 'APP_HASMAIL'])
db.init_app(app)
migrate = Migrate(app, db)
rq.init_app(app)  # Pick up RQ configuration from the app
baseframe.init_app(
    app,
    requires=['hasmail'],
    ext_requires=[
        'bootstrap3-editable',
        'codemirror-markdown',
        'codemirror-css',
        'fontawesome',
        'baseframe-bs3',
    ],
)
mail.init_app(app)
lastuser.init_app(app)
lastuser.init_usermanager(UserManager(db, models.User))
