"""Mailer writer views."""

from typing import Union

from flask import jsonify, render_template, request
from flask.typing import ResponseReturnValue

from baseframe.forms import render_delete_sqla
from coaster.views import load_model, load_models

from .. import _, app, lastuser
from ..forms import TemplateForm
from ..models import EmailCampaign, EmailDraft, EmailRecipient, db
from .diffpatch import update_recipient


@app.route('/mail/<campaign>/write', methods=('GET', 'POST'))
@lastuser.requires_login
@load_model(EmailCampaign, {'name': 'campaign'}, 'campaign', permission='edit')
def campaign_template(campaign: EmailCampaign) -> ResponseReturnValue:
    draft = campaign.draft()
    form = TemplateForm(obj=draft)
    if form.validate_on_submit():
        # Make a new draft if we're editing an existing draft or there is no existing
        # draft. But don't make new drafts on page reload with no content change
        if not draft or (
            draft.revision_id == form.revision_id.data
            and (
                draft.subject != form.subject.data
                or draft.template != form.template.data
            )
        ):
            draft = EmailDraft(campaign=campaign)
            db.session.add(draft)
        draft.subject = form.subject.data
        draft.template = form.template.data
        db.session.commit()

        # The background job approach isn't reliable. We don't know if it's because it's
        # a background process, or because it's simply multi-threading with race
        # conditions. Foreground processing for now:

        # patch_drafts.queue(campaign.id)
        # patch_drafts(campaign.id)

        # Update: we now patch on loading the recipient's draft

        return jsonify(
            {
                'template': draft.template,
                'preview': draft.get_preview(),
                'subject': draft.subject,
                'revision_id': draft.revision_id,
                'form_nonce': form.form_nonce.default(),
            }
        )
    return render_template(
        'template.html.jinja2', campaign=campaign, wstep=4, form=form
    )


@app.route('/mail/<campaign>/<int:recipient>', methods=('GET', 'POST'))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='edit',
)
def recipient_view(
    campaign: EmailCampaign, recipient: EmailRecipient
) -> ResponseReturnValue:
    draft = campaign.draft()
    already_sent = bool(recipient.rendered_text)

    if recipient.custom_draft:
        # This user has a custom template, use it
        if not already_sent:
            update_recipient(recipient)
        form = TemplateForm(obj=recipient)
        if request.method == 'GET':
            if not recipient.subject:
                form.subject.data = draft.subject if draft else ''
            if not recipient.template:
                form.template.data = draft.template if draft else ''
    else:
        # Use the standard template
        form = TemplateForm(obj=draft)
    if form.validate_on_submit():
        if not draft:
            # Make a blank draft for reference
            draft = EmailDraft(campaign=campaign)
            db.session.add(draft)
            db.session.flush()  # Ensure campaign.draft() == draft

        # Discard updates if email was already sent to this recipient
        if already_sent:
            ob: Union[EmailRecipient, EmailDraft] = (
                recipient if recipient.custom_draft else draft
            )
            return jsonify(
                {
                    'template': ob.template,
                    'preview': recipient.get_preview(),
                    'subject': ob.subject,
                    'revision_id': ob.revision_id,
                }
            )

        # Check if the subject or template differs from the draft. If so,
        # customise it for this recipient.
        if form.subject.data != draft.subject:
            recipient.subject = form.subject.data
        else:
            recipient.subject = None

        if form.template.data != draft.template:
            recipient.template = form.template.data
        else:
            recipient.template = None

        if recipient.subject or recipient.template:
            recipient.draft = draft
        else:
            recipient.draft = None

        db.session.commit()

        ob = recipient if recipient.custom_draft else draft
        return jsonify(
            {
                'template': ob.template,
                'preview': recipient.get_preview(),
                'subject': recipient.subject
                if recipient.subject is not None
                else draft.subject,
                'revision_id': ob.revision_id,
            }
        )
    return render_template(
        'recipient.html.jinja2',
        campaign=campaign,
        recipient=recipient,
        wstep=4,
        form=form,
        already_sent=already_sent,
    )


@app.route('/mail/<campaign>/<recipient>/edit', methods=('POST',))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='edit',
)
def recipient_edit(
    campaign: EmailCampaign, recipient: EmailRecipient
) -> ResponseReturnValue:
    if (
        request.form.get('pk', '').isdigit()
        and int(request.form['pk']) == recipient.url_id
    ):
        if 'name' not in request.form:
            return _("Field not specified"), 400
        if 'value' not in request.form:
            return _("Value not specified"), 400
        field = request.form['name']
        value = request.form['value']
        if field == 'email':
            recipient.email = value
        elif field == 'fullname':
            recipient.fullname = value or None
        elif field == 'firstname':
            recipient.firstname = value or None
        elif field == 'lastname':
            recipient.lastname = value or None
        elif field == 'nickname':
            recipient.nickname = value or None
        else:
            if recipient.data is None:
                recipient.data = {}
            recipient.data[field] = value or None
        db.session.commit()
        return _("Saved"), 200
    return _("Primary key missing, please contact the site administrator"), 400


@app.route('/mail/<campaign>/<recipient>/delete', methods=('GET', 'POST'))
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='delete',
)
def recipient_delete(
    campaign: EmailCampaign, recipient: EmailRecipient
) -> ResponseReturnValue:
    return render_delete_sqla(
        recipient,
        db,
        title=_("Confirm delete"),
        message=_("Remove recipient ‘{fullname}’? ").format(
            fullname=recipient.fullname
        ),
        success=_("You have removed recipient ‘{fullname}’").format(
            fullname=recipient.fullname
        ),
        next=campaign.url_for('recipients'),
    )


@app.route('/mail/<campaign>/<recipient>/report')
@lastuser.requires_login
@load_models(
    (EmailCampaign, {'name': 'campaign'}, 'campaign'),
    (EmailRecipient, {'campaign': 'campaign', 'url_id': 'recipient'}, 'recipient'),
    permission='report',
)
def recipient_report(
    campaign: EmailCampaign, recipient: EmailRecipient
) -> ResponseReturnValue:
    return render_template(
        'report.html.jinja2', campaign=campaign, recipient=recipient, wstep=6
    )
