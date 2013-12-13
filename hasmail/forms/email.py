# -*- coding: utf-8 -*-

import wtforms
from baseframe.forms import Form, MarkdownField
from .. import __

__all__ = ['CampaignSettingsForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(__(u"Title"), description=__(u"On what this email is for, for your own reference"),
        validators=[wtforms.validators.Required(__(u"This is required"))])


class TemplateForm(Form):
    template = MarkdownField(__(u"Template"))
