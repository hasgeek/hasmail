"""Background job to patch email recipient drafts."""

from diff_match_patch import diff_match_patch

from .. import rq
from ..models import Mailer, MailerRecipient, db


@rq.job('hasmail')
def patch_drafts(mailer_id: int) -> None:
    mailer = Mailer.query.get(mailer_id)
    if mailer is None:
        return
    patcher = diff_match_patch()
    draft = mailer.draft()
    if draft is None:  # This shouldn't happen
        return
    patches = {}  # (old draft, new draft): patches

    for recipient in MailerRecipient.custom_draft_in(mailer):
        if recipient.draft and recipient.draft.revision_id < draft.revision_id:
            key = (recipient.draft.revision_id, draft.revision_id)
            if key not in patches:
                patches[key] = patcher.patch_make(
                    recipient.draft.template, draft.template
                )
            patched, _results = patcher.patch_apply(patches[key], recipient.template)
            recipient.template = patched
            recipient.draft = draft
    db.session.commit()


def update_recipient(recipient: MailerRecipient) -> None:
    mailer = recipient.mailer
    draft = mailer.draft()
    if draft is None:
        return
    if (
        recipient.template is not None
        and recipient.draft is not None
        and recipient.draft != draft
    ):
        patcher = diff_match_patch()
        patch = patcher.patch_make(recipient.draft.template, draft.template)
        patched, _results = patcher.patch_apply(patch, recipient.template)
        recipient.template = patched
        recipient.draft = draft
        db.session.commit()
