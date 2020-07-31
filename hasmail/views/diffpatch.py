from diff_match_patch import diff_match_patch

from .. import rq
from ..models import EmailCampaign, EmailRecipient, db


@rq.job('hasmail')
def patch_drafts(campaign_id):
    campaign = EmailCampaign.query.get(campaign_id)
    if not campaign:
        return
    patcher = diff_match_patch()
    draft = campaign.draft()
    patches = {}  # (old draft, new draft): patches

    for recipient in EmailRecipient.custom_draft_in(campaign):
        if recipient.draft.revision_id < draft.revision_id:
            key = (recipient.draft.revision_id, draft.revision_id)
            if key not in patches:
                patches[key] = patcher.patch_make(
                    recipient.draft.template, draft.template
                )
            patched, results = patcher.patch_apply(patches[key], recipient.template)
            recipient.template = patched
            recipient.draft = draft
    db.session.commit()


def update_recipient(recipient):
    campaign = recipient.campaign
    draft = campaign.draft()
    if recipient.template is not None and recipient.draft != draft:
        patcher = diff_match_patch()
        patch = patcher.patch_make(recipient.draft.template, draft.template)
        patched, results = patcher.patch_apply(patch, recipient.template)
        recipient.template = patched
        recipient.draft = draft
        db.session.commit()
