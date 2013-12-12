# -*- coding: utf-8 -*-

from flask import render_template
from .. import app


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wip')
def wip():
    return render_template('wip.html')
