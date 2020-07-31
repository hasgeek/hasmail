#!/usr/bin/env python

from hasmail import app
from hasmail.models import db
import hasmail
import hasmail.forms as forms
import hasmail.models as models
import hasmail.views as views

from coaster.manage import init_manager

if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(
        app, db, hasmail=hasmail, models=models, forms=forms, views=views
    )
    manager.run()
