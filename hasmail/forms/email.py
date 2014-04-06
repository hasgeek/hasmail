# -*- coding: utf-8 -*-

import wtforms
from baseframe.forms import Form
from .. import __

__all__ = ['CampaignSettingsForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(__(u"What’s this email about?"),
        validators=[wtforms.validators.Required(__(u"This is required"))])

    importfile = wtforms.FileField(__(u"Who do you want to send this to?"),
        description=__(u"A CSV file containing names and email addresses would be most excellent"))


class TemplateForm(Form):
    revision_id = wtforms.HiddenField(__(u"Revision id"))
    subject = wtforms.TextField(__(u"Subject"))
    # Don't use MarkdownField since the only thing it does is adding the
    # 'markdown' class for automatic linking with codemirror, while we
    # want to do that manually with additional options
    template = wtforms.TextAreaField(__(u"Template"))

    def validate_revision_id(self, field):
        if field.data.isdigit():
            field.data = int(field.data)
