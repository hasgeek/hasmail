# -*- coding: utf-8 -*-

from diff_match_patch import diff_match_patch
from flask.ext.rq import job
from ..models import db, EmailCampaign, EmailRecipient


@job('hasmail')
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
                patches[key] = patcher.patch_make(recipient.draft.template.text, draft.template.text)
            patched, results = patcher.patch_apply(patches[key], recipient.template.text)
            recipient.template.text = patched
            recipient.draft = draft
    db.session.commit()
