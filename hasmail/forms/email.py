import wtforms

from baseframe.forms import Form, StylesheetField

from .. import __

__all__ = ['CampaignSettingsForm', 'CampaignSendForm', 'TemplateForm']


class CampaignSettingsForm(Form):
    title = wtforms.TextField(
        __("What’s this email about?"),
        validators=[wtforms.validators.Required(__("This is required"))],
    )

    importfile = wtforms.FileField(
        __("Who do you want to send this to?"),
        description=__(
            "A CSV file containing names and email addresses would be most excellent"
        ),
    )

    stylesheet = StylesheetField(
        __("CSS Stylesheet"),
        description=__("These styles will be applied to your email before it is sent"),
        validators=[wtforms.validators.Optional()],
    )

    # TODO: Validate addresses
    cc = wtforms.TextAreaField(
        __("CC"), description=__("CCed recipients, one per line")
    )

    # TODO: Validate addresses
    bcc = wtforms.TextAreaField(
        __("BCC"), description=__("BCCed recipients, one per line")
    )

    trackopens = wtforms.BooleanField(
        __("Track opens"),
        default=False,
        description=__(
            "This will include a tiny, invisible image in your email. "
            "Your recipient's email client may ask them if they want to view images. "
            "Best used if your email also includes images"
        ),
    )

    # trackclicks = wtforms.BooleanField(__(u"Track clicks"), default=False,
    #     description=__(u"All links in your email will be wrapped and clicks will be tracked "
    #         u"so you know which recipient opened which links"))


class CampaignSendForm(Form):
    email = wtforms.RadioField(
        __("Send from"),
        description=__("What email address would you like to send this from?"),
    )


class TemplateForm(Form):
    revision_id = wtforms.HiddenField(__("Revision id"))
    subject = wtforms.TextField(__("Subject"))
    # Don't use MarkdownField since the only thing it does is adding the
    # 'markdown' class for automatic linking with codemirror, while we
    # want to do that manually with additional options
    template = wtforms.TextAreaField(__("Template"))

    def validate_revision_id(self, field):
        if field.data.isdigit():
            field.data = int(field.data)
