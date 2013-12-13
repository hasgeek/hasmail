# -*- coding: utf-8 -*-

import wtforms
from baseframe.forms import Form, MarkdownField
from .. import __

__all__ = ['CampaignSettingsForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(__(u"Title"), description=__(u"For your own reference"),
        validators=[wtforms.validators.Required(__(u"This is required"))])

    importfile = wtforms.FileField(__(u"Import recipients"), description=__(u"CSV file containing names and email addresses"))


class TemplateForm(Form):
    template = MarkdownField(__(u"Template"))
