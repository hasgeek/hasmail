# -*- coding: utf-8 -*-

from cssselect.parser import parse as parse_css, SelectorError
import wtforms
from baseframe.forms import Form, StylesheetField
from .. import _, __

__all__ = ['CampaignSettingsForm', 'CampaignSendForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(__(u"What’s this email about?"),
        validators=[wtforms.validators.Required(__(u"This is required"))])

    importfile = wtforms.FileField(__(u"Who do you want to send this to?"),
        description=__(u"A CSV file containing names and email addresses would be most excellent"))

    stylesheet = StylesheetField(__(u"CSS Stylesheet"),
        description=__(u"These styles will be applied to your email before it is sent"))

    trackopens = wtforms.BooleanField(__(u"Track opens"), default=False,
        description=__(u"This will include a tiny, invisible image in your email. "
            u"Your recipient's email client may ask them if they want to view images. "
            u"Best used if your email also includes images"))

    # trackclicks = wtforms.BooleanField(__(u"Track clicks"), default=False,
    #     description=__(u"All links in your email will be wrapped and clicks will be tracked "
    #         u"so you know which recipient opened which links"))

    def validate_stylesheet(self, field):
        try:
            parse_css(field.data)
        except SelectorError:
            raise wtforms.validators.StopValidation(_("This stylesheet has syntax errors"))


class CampaignSendForm(Form):
    email = wtforms.RadioField(__(u"Send from"),
        description=__(u"What email address would you like to send this from?"))


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
