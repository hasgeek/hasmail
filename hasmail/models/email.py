"""Mailer models."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Collection, Dict, Iterator, List, Optional, Set, Union

import pystache
from flask import Markup, escape, request, url_for
from premailer import transform as email_transform
from sqlalchemy.orm import defer

from coaster.utils import (
    MARKDOWN_HTML_TAGS,
    LabeledEnum,
    buid,
    markdown,
    md5sum,
    newsecret,
)
from flask_lastuser.sqlalchemy import UserBase2

from .. import __
from . import (
    BaseNameMixin,
    BaseScopedIdMixin,
    DynamicMapped,
    JsonDict,
    Mapped,
    Model,
    db,
    relationship,
    sa,
)

__all__ = [
    'CAMPAIGN_STATUS',
    'User',
    'EmailCampaign',
    'EmailDraft',
    'EmailRecipient',
]

NAMESPLIT_RE = re.compile(r'[\W\.]+')
EMAIL_RE = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$', re.I)

EMAIL_TAGS = dict(MARKDOWN_HTML_TAGS)
for _key in EMAIL_TAGS:
    EMAIL_TAGS[_key].append('class')
    EMAIL_TAGS[_key].append('style')


class CAMPAIGN_STATUS(LabeledEnum):  # noqa: N801
    DRAFT = (0, __("Draft"))
    QUEUED = (1, __("Queued"))
    SENDING = (2, __("Sending"))
    SENT = (3, __("Sent"))


class User(UserBase2, Model):
    __tablename__ = 'user'

    campaigns: Mapped[List[EmailCampaign]] = relationship(
        back_populates='user', order_by='EmailCampaign.updated_at.desc()'
    )


class EmailCampaign(BaseNameMixin, Model):
    __tablename__ = 'email_campaign'

    user_id: Mapped[int] = sa.orm.mapped_column(
        sa.ForeignKey('user.id'), nullable=False
    )
    user: Mapped[User] = relationship(
        User,
        back_populates='campaigns',
    )
    status: Mapped[int] = sa.orm.mapped_column(
        sa.Integer, nullable=False, default=CAMPAIGN_STATUS.DRAFT
    )
    _fields: Mapped[str] = sa.orm.mapped_column(
        'fields', sa.UnicodeText, nullable=False, default=''
    )
    trackopens: Mapped[bool] = sa.orm.mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    trackclicks: Mapped[bool] = sa.orm.mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    stylesheet: Mapped[str] = sa.orm.mapped_column(
        sa.UnicodeText, nullable=False, default=''
    )
    _cc: Mapped[str] = sa.orm.mapped_column('cc', sa.UnicodeText, nullable=True)
    _bcc: Mapped[str] = sa.orm.mapped_column('bcc', sa.UnicodeText, nullable=True)

    recipients: DynamicMapped[EmailRecipient] = relationship(
        lazy='dynamic',
        back_populates='campaign',
        cascade='all, delete-orphan',
        order_by='(EmailRecipient.draft_id, EmailRecipient._fullname,'
        ' EmailRecipient._firstname, EmailRecipient._lastname)',
    )
    drafts: Mapped[List[EmailDraft]] = relationship(
        back_populates='campaign',
        cascade='all, delete-orphan',
        order_by='EmailDraft.url_id',
    )

    def __repr__(self) -> str:
        return f'<EmailCampaign "{self.title}" ({CAMPAIGN_STATUS.get(self.status)})>'

    @property
    def fields(self) -> Collection[str]:
        flist = self._fields.split(' ')
        while '' in flist:
            flist.remove('')
        return tuple(flist)

    @fields.setter
    def fields(self, value: Collection[str]):
        self._fields = ' '.join(sorted(set(value)))

    @property
    def cc(self) -> str:
        return self._cc

    @cc.setter
    def cc(self, value: Union[str, Collection[str]]):
        if isinstance(value, str):
            value = [
                _l.strip()
                for _l in value.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                if _l
            ]
        self._cc = '\n'.join(sorted(set(value)))

    @property
    def bcc(self) -> str:
        return self._bcc

    @bcc.setter
    def bcc(self, value: Union[str, Collection[str]]) -> None:
        if isinstance(value, str):
            value = [
                _l.strip()
                for _l in value.replace('\r\n', '\n').replace('\r', '\n').split('\n')
                if _l
            ]
        self._bcc = '\n'.join(sorted(set(value)))

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if 'name' not in kwargs:  # Use random name unless one was provided
            self.name = buid()

    def recipients_iter(self) -> Iterator[EmailRecipient]:
        ids = [
            i.id
            for i in db.session.query(EmailRecipient.id)
            .filter(EmailRecipient.campaign_id == self.id)
            .order_by(EmailRecipient.id)
            .all()
        ]
        for rid in ids:
            recipient = EmailRecipient.query.get(rid)
            if recipient:
                yield recipient

    def permissions(
        self, user: Optional[User], inherited: Optional[Set[str]] = None
    ) -> Set[str]:
        perms = super().permissions(user, inherited)
        if user is not None and user == self.user:
            perms.update(['edit', 'delete', 'send', 'new-recipient', 'report'])
        return perms

    def url_for(self, action: str = 'view', **kwargs: Any) -> str:
        if action in {'view', 'edit'}:
            return url_for('campaign_view', campaign=self.name, **kwargs)
        if action == 'recipients':
            return url_for('campaign_recipients', campaign=self.name, **kwargs)
        if action == 'template':
            return url_for('campaign_template', campaign=self.name, **kwargs)
        if action == 'send':
            return url_for('campaign_send', campaign=self.name, **kwargs)
        if action == 'report':
            return url_for('campaign_report', campaign=self.name, **kwargs)
        raise ValueError(f"Unknown action {action}")

    def draft(self) -> Optional[EmailDraft]:
        if self.drafts:
            return self.drafts[-1]
        return None

    def render_preview(self, text: str) -> str:
        if self.stylesheet is not None and self.stylesheet.strip():
            stylesheet = f'<style type="text/css">{escape(self.stylesheet)}</style>\n'
        else:
            stylesheet = ''
        rendered_text = Markup(stylesheet) + markdown(
            text, html=True, valid_tags=EMAIL_TAGS
        )
        # email_transform uses LXML, which does not like empty strings
        if rendered_text:
            return email_transform(rendered_text, base_url=request.url_root)
        return ''


class EmailDraft(BaseScopedIdMixin, Model):
    __tablename__ = 'email_draft'

    campaign_id: Mapped[int] = sa.orm.mapped_column(
        sa.ForeignKey('email_campaign.id'), nullable=False
    )
    campaign: Mapped[EmailCampaign] = relationship(
        EmailCampaign, back_populates='drafts'
    )
    parent: Mapped[EmailCampaign] = sa.orm.synonym('campaign')
    revision_id: Mapped[int] = sa.orm.synonym('url_id')

    subject: Mapped[str] = sa.orm.mapped_column(
        sa.Unicode(250), nullable=False, default="", deferred=True
    )

    template: Mapped[str] = sa.orm.mapped_column(
        sa.UnicodeText, nullable=False, default="", deferred=True
    )

    __table_args__ = (sa.UniqueConstraint('campaign_id', 'url_id'),)

    def __repr__(self) -> str:
        return f'<EmailDraft {self.revision_id} of {self.campaign!r}>'

    def get_preview(self) -> str:
        return self.campaign.render_preview(self.template)


class EmailRecipient(BaseScopedIdMixin, Model):
    __tablename__ = 'email_recipient'

    # Campaign this recipient is a part of
    campaign_id: Mapped[int] = sa.orm.mapped_column(
        sa.ForeignKey('email_campaign.id'), nullable=False
    )

    _fullname: Mapped[Optional[str]] = sa.orm.mapped_column(
        'fullname', sa.Unicode(80), nullable=True
    )
    _firstname: Mapped[Optional[str]] = sa.orm.mapped_column(
        'firstname', sa.Unicode(80), nullable=True
    )
    _lastname: Mapped[Optional[str]] = sa.orm.mapped_column(
        'lastname', sa.Unicode(80), nullable=True
    )
    _nickname: Mapped[Optional[str]] = sa.orm.mapped_column(
        'nickname', sa.Unicode(80), nullable=True
    )

    _email: Mapped[str] = sa.orm.mapped_column(
        'email', sa.Unicode(80), nullable=False, index=True
    )
    md5sum: Mapped[str] = sa.orm.mapped_column(
        sa.String(32), nullable=False, index=True
    )

    data: Mapped[Optional[dict]] = sa.orm.mapped_column(JsonDict)

    # Support email open tracking
    opentoken: Mapped[str] = sa.orm.mapped_column(
        sa.Unicode(44), nullable=False, default=newsecret, unique=True
    )
    opened: Mapped[bool] = sa.orm.mapped_column(
        sa.Boolean, nullable=False, default=False
    )
    opened_ipaddr: Mapped[Optional[str]] = sa.orm.mapped_column(
        sa.Unicode(45), nullable=True
    )
    opened_first_at: Mapped[Optional[datetime]] = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    opened_last_at: Mapped[Optional[datetime]] = sa.orm.mapped_column(
        sa.TIMESTAMP(timezone=True), nullable=True
    )
    opened_count: Mapped[int] = sa.orm.mapped_column(
        sa.Integer, nullable=False, default=0
    )

    # Support RSVP if the email requires it
    rsvptoken: Mapped[str] = sa.orm.mapped_column(
        sa.Unicode(44), nullable=False, default=newsecret, unique=True
    )
    # Y/N/M response
    rsvp: Mapped[Optional[str]] = sa.orm.mapped_column(sa.Unicode(1), nullable=True)

    # Customised template for this recipient
    # TODO: Discover template for linked groups (only one recipient will have a custom
    # template that is used for all)
    subject: Mapped[Optional[str]] = sa.orm.mapped_column(
        sa.Unicode(250), nullable=True
    )
    template: Mapped[Optional[str]] = sa.orm.mapped_column(
        sa.UnicodeText, nullable=True, deferred=True
    )

    # Rendered version of user's template, for archival
    rendered_text: Mapped[Optional[str]] = sa.orm.mapped_column(
        sa.UnicodeText, nullable=True, deferred=True
    )
    rendered_html: Mapped[Optional[str]] = sa.orm.mapped_column(
        sa.UnicodeText, nullable=True, deferred=True
    )

    # Draft of the campaign template that the custom template is linked to (for updating
    # before finalising)
    draft_id: Mapped[Optional[int]] = sa.orm.mapped_column(
        None, sa.ForeignKey('email_draft.id'), nullable=True
    )
    draft: Mapped[EmailDraft] = relationship(EmailDraft)

    # Recipients may be emailed as a group with all emails in the To field. Unique
    # number to identify them
    linkgroup: Mapped[Optional[int]] = sa.orm.mapped_column(sa.Integer, nullable=True)

    campaign: Mapped[EmailCampaign] = relationship(
        EmailCampaign,
        back_populates='recipients',
    )
    parent: Mapped[EmailCampaign] = sa.orm.synonym('campaign')

    __table_args__ = (sa.UniqueConstraint('campaign_id', 'url_id'),)

    def __repr__(self) -> str:
        return f'<EmailRecipient {self.fullname} {self.email} of {self.campaign!r}>'

    @property
    def fullname(self) -> Optional[str]:
        """Recipient's fullname, constructed from first and last names if required."""
        if self._fullname:
            return self._fullname
        if self._firstname:
            if self._lastname:
                # FIXME: Cultural assumption of <first> <space> <last> name.
                return f"{self._firstname} {self._lastname}"
            return self._firstname
        if self._lastname:
            return self._lastname
        return None

    @fullname.setter
    def fullname(self, value: Optional[str]) -> None:
        self._fullname = value

    @property
    def firstname(self) -> Optional[str]:
        if self._firstname:
            return self._firstname
        if self._fullname:
            return NAMESPLIT_RE.split(self._fullname)[0]
        return None

    @firstname.setter
    def firstname(self, value: Optional[str]) -> None:
        self._firstname = value

    @property
    def lastname(self) -> Optional[str]:
        if self._lastname:
            return self._lastname
        if self._fullname:
            return NAMESPLIT_RE.split(self._fullname)[-1]
        return None

    @lastname.setter
    def lastname(self, value: Optional[str]) -> None:
        self._lastname = value

    @property
    def nickname(self) -> Optional[str]:
        return self._nickname or self.firstname

    @nickname.setter
    def nickname(self, value: Optional[str]) -> None:
        self._nickname = value

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = value.lower()
        self.md5sum = md5sum(value)

    def is_email_valid(self) -> bool:
        return EMAIL_RE.match(self.email) is not None

    @property
    def revision_id(self) -> Optional[int]:
        return self.draft.revision_id if self.draft else None

    def is_latest_draft(self) -> bool:
        if not self.draft:
            return True
        return self.draft == self.campaign.drafts[-1]

    def make_linkgroup(self) -> None:
        if self.linkgroup is None and self.campaign is not None:
            self.linkgroup = (
                db.session.query(EmailRecipient.linkgroup)
                .filter(EmailRecipient.campaign == self.campaign)
                .scalar()
                or 0
            ) + 1

    def template_data(self) -> Dict[str, Any]:
        tdata = {
            'fullname': self.fullname,
            'email': self.email,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'nickname': self.nickname,
            'RSVP_Y': self.url_for('rsvp', status='Y', _external=True),
            'RSVP_N': self.url_for('rsvp', status='N', _external=True),
            'RSVP_M': self.url_for('rsvp', status='M', _external=True),
        }
        if self.data:
            tdata.update(self.data)
        return tdata

    def get_rendered(self, draft: EmailDraft) -> str:
        # FIXME: Why does this ignore the parameter?
        if self.draft:
            return pystache.render(self.template or '', self.template_data())
        return pystache.render(draft.template or '', self.template_data())

    def get_preview(self, draft: EmailDraft) -> str:
        return self.campaign.render_preview(self.get_rendered(draft))

    def url_for(self, action='view', _external=False, **kwargs) -> str:
        if action in {'view', 'template'}:
            return url_for(
                'recipient_view',
                campaign=self.campaign.name,
                recipient=self.url_id,
                _external=_external,
                **kwargs,
            )
        if action == 'edit':
            return url_for(
                'recipient_edit',
                campaign=self.campaign.name,
                recipient=self.url_id,
                _external=_external,
                **kwargs,
            )
        if action == 'delete':
            return url_for(
                'recipient_delete',
                campaign=self.campaign.name,
                recipient=self.url_id,
                _external=_external,
                **kwargs,
            )
        if action == 'trackopen':
            return url_for(
                'track_open_gif', opentoken=self.opentoken, _external=True, **kwargs
            )
        if action == 'report':
            return url_for(
                'recipient_report',
                campaign=self.campaign.name,
                recipient=self.url_id,
                _external=_external,
                **kwargs,
            )
        if action == 'rsvp':
            return url_for('rsvp', rsvptoken=self.rsvptoken, _external=True, **kwargs)
        raise ValueError(f"Unknown action {action}")

    def openmarkup(self) -> Markup:
        if self.campaign.trackopens:
            return Markup(
                f'\n<img src="{self.url_for("trackopen")}" width="1" height="1" alt=""'
                f' border="0" style="height:1px !important;width:1px !important;'
                f'border-width:0 !important;margin-top:0 !important;'
                f'margin-bottom:0 !important;margin-right:0 !important;'
                f'margin-left:0 !important;padding-top:0 !important;'
                f'padding-bottom:0 !important;padding-right:0 !important;'
                f'padding-left:0 !important;"/>'
            )
        return Markup('')

    @classmethod
    def custom_draft_in(cls, campaign: EmailCampaign) -> List[EmailRecipient]:
        return (
            cls.query.filter(
                cls.campaign == campaign,
                cls.draft.isnot(None),
                cls.__table__.c.template_text.isnot(None),
            )
            .options(
                defer(cls.created_at),
                defer(cls.updated_at),
                defer(cls._email),
                defer(cls.md5sum),
                defer(cls._fullname),
                defer(cls._firstname),
                defer(cls._lastname),
                defer(cls.data),
                defer(cls.opentoken),
                defer(cls.opened),
                defer(cls.rsvptoken),
                defer(cls.rsvp),
                defer(cls.linkgroup),
                defer(cls._nickname),
            )
            .all()
        )
