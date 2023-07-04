"""Mailer forms."""

from baseframe import __, forms

__all__ = ['CampaignSettingsForm', 'CampaignSendForm', 'TemplateForm']


class CampaignSettingsForm(forms.Form):
    title = forms.StringField(
        __("What’s this email about?"),
        description=__("A private description for your own reference"),
        validators=[forms.validators.DataRequired(__("This is required"))],
    )

    importfile = forms.FileField(
        __("Who do you want to send this to?"),
        description=__(
            "A CSV file containing names and email addresses would be most excellent"
        ),
    )

    stylesheet = forms.StylesheetField(
        __("CSS Stylesheet"),
        description=__("These styles will be applied to your email before it is sent"),
        validators=[forms.validators.Optional()],
    )

    # TODO: Validate addresses
    cc = forms.TextAreaField(__("CC"), description=__("CCed recipients, one per line"))

    # TODO: Validate addresses
    bcc = forms.TextAreaField(
        __("BCC"), description=__("BCCed recipients, one per line")
    )

    trackopens = forms.BooleanField(
        __("Track opens"),
        default=False,
        description=__(
            "This will include a tiny, invisible image in your email. "
            "Your recipient's email client may ask them if they want to view images. "
            "Best used if your email also includes images"
        ),
    )


class CampaignSendForm(forms.Form):
    email = forms.RadioField(
        __("Send from"),
        description=__("What email address would you like to send this from?"),
    )


class TemplateForm(forms.Form):
    revision_id = forms.HiddenField(__("Revision id"))
    subject = forms.StringField(__("Subject"))
    # Don't use MarkdownField since the only thing it does is adding the
    # 'markdown' class for automatic linking with codemirror, while we
    # want to do that manually with additional options
    template = forms.TextAreaField(__("Template"))

    def validate_revision_id(self, field):
        if field.data.isdigit():
            field.data = int(field.data)
