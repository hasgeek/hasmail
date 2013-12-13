# -*- coding: utf-8 -*-

import wtforms
from baseframe.forms import Form, MarkdownField
from .. import __

__all__ = ['CampaignSettingsForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(__(u"What’s this email about?"),
        validators=[wtforms.validators.Required(__(u"This is required"))])

    importfile = wtforms.FileField(__(u"Who do you want to send this to?"),
        description=__(u"A CSV file containing names and email addresses would be most excellent"))


class TemplateForm(Form):
    template = MarkdownField(__(u"Template"))
