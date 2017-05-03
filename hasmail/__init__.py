# -*- coding: utf-8 -*-

# The imports in this file are order-sensitive

from __future__ import absolute_import
from flask import Flask
from flask_mail import Mail
from flask_rq import RQ
from flask_lastuser import Lastuser
from flask_lastuser.sqlalchemy import UserManager
from baseframe import baseframe, assets, Version, _, __
import coaster.app
from ._version import __version__

version = Version(__version__)

# First, make an app

app = Flask(__name__, instance_relative_config=True)
mail = Mail()
lastuser = Lastuser()

# Second, import the models and views

from . import models, views
from .models import db

# Third, setup baseframe and assets

assets['hasmail.js'][version] = 'js/app.js'
assets['hasmail.css'][version] = 'css/app.css'


# Configure the app
def init_for(env):
    coaster.app.init_app(app, env)
    db.init_app(app)
    db.app = app
    RQ(app)  # Pick up RQ configuration from the app
    baseframe.init_app(app, requires=['hasmail'],
        ext_requires=['bootstrap3-editable', 'codemirror-markdown', 'codemirror-css', 'fontawesome', 'baseframe-bs3'])
    mail.init_app(app)
    lastuser.init_app(app)
    lastuser.init_usermanager(UserManager(db, models.User))
