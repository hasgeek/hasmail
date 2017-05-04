#!/usr/bin/env python

from coaster.manage import init_manager

import hasmail
import hasmail.models as models
import hasmail.forms as forms
import hasmail.views as views
from hasmail.models import db
from hasmail import app


if __name__ == '__main__':
    db.init_app(app)
    manager = init_manager(app, db, hasmail=hasmail, models=models, forms=forms, views=views)
    manager.run()
