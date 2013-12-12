# -*- coding: utf-8

import wtforms
from baseframe import __
from baseframe.forms import Form, MarkdownField


class AccountForm(Form):
    email = wtforms.TextField(__("Email"), validators=[wtforms.validators.Required()])
    password = wtforms.PasswordField(__("Password"), validators=[wtforms.validators.Required()])


class CampaignForm(Form):
    title = wtforms.TextField(__("Title"), description="Name of the Campaign", validators=[wtforms.validators.Required(), wtforms.validators.NoneOf(values=["new"]), wtforms.validators.length(max=250)])
    template = MarkdownField(__("Template"), validators=[wtforms.validators.Required()])


class SendEmailForm(Form):
    sender = wtforms.TextField(__("Sender"), validators=[wtforms.validators.Required()])
    recipient = wtforms.TextField(__("Recipient"), validators=[wtforms.validators.Required()])
    body = MarkdownField(__("Body"), validators=[wtforms.validators.Required()])

