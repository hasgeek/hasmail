# -*- coding: utf-8 -*-

from flask import url_for
from coaster.utils import buid, md5sum, newsecret, LabeledEnum
from . import db, BaseMixin, BaseNameMixin, BaseScopedIdMixin, MarkdownColumn
from .user import User
from .. import __

__all__ = ['CAMPAIGN_STATUS', 'EmailCampaign', 'EmailDraft', 'EmailRecipient']


class CAMPAIGN_STATUS(LabeledEnum):
    DRAFT = (0, __(u"Draft"))
    QUEUED = (1, __(u"Queued"))
    SENDING = (2, __(u"Sending"))
    SENT = (3, __(u"Sent"))


class EmailCampaign(BaseNameMixin, db.Model):
    __tablename__ = 'email_campaign'

    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, backref='campaigns')
    status = db.Column(db.Integer, nullable=False, default=CAMPAIGN_STATUS.DRAFT)
    _headers = db.Column(db.UnicodeText, nullable=False, default=u'')
    trackopens = db.Column(db.Boolean, nullable=False, default=False)
    trackclicks = db.Column(db.Boolean, nullable=False, default=False)

    @property
    def headers(self):
        return self._headers.split(u' ')

    @headers.setter
    def headers(self, value):
        self._headers = u' '.join(sorted(set(value)))

    headers = db.synonym('_headers', descriptor=headers)

    def __init__(self, **kwargs):
        super(EmailCampaign, self).__init__(**kwargs)
        if 'name' not in kwargs:  # Use random name unless one was provided
            self.name = buid()

    def permissions(self, user, inherited=None):
        perms = super(EmailCampaign, self).permissions(user, inherited)
        if user is not None and user == self.user:
            perms.update([
                'edit',
                'delete',
                'send',
                'new-recipient',
                ])
        return perms

    def url_for(self, action='view'):
        if action == 'view' or action == 'edit':
            return url_for('campaign_view', campaign=self.name)
        elif action == 'recipients':
            return url_for('campaign_recipients', campaign=self.name)
        elif action == 'template':
            return url_for('campaign_template', campaign=self.name)


class EmailDraft(BaseScopedIdMixin, db.Model):
    __tablename__ = 'email_draft'

    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)
    campaign = db.relationship(EmailCampaign, backref=db.backref('drafts',
        cascade='all, delete-orphan', order_by='EmailDraft.url_id'))
    parent = db.synonym('campaign')

    subject = db.Column(db.Unicode(250), nullable=False, default=u"")
    template = MarkdownColumn('template', nullable=False, default=u"")

    __table_args__ = (db.UniqueConstraint('campaign_id', 'url_id'),)


class EmailRecipient(BaseMixin, db.Model):
    __tablename__ = 'email_recipient'

    # Campaign this recipient is a part of
    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)

    _fullname = db.Column('fullname', db.Unicode(80), nullable=True)
    _firstname = db.Column('firstname', db.Unicode(80), nullable=True)
    _lastname = db.Column('lastname', db.Unicode(80), nullable=True)

    campaign = db.relationship(EmailCampaign, backref=db.backref('recipients',
        cascade='all, delete-orphan', order_by=(_fullname, _firstname, _lastname)))

    _email = db.Column('email', db.Unicode(80), nullable=False)
    md5sum = db.Column(db.String(32), nullable=False)

    opentoken = db.Column(db.Unicode(44), nullable=False, default=newsecret, unique=True)
    opened = db.Column(db.Boolean, nullable=False, default=False)

    # Customised template for this recipient
    # TODO: Discover template for linked groups (only one recipient will have a custom template that is used for all)
    subject = db.Column(db.Unicode(250), nullable=True)
    template = MarkdownColumn('template', nullable=True)

    # Rendered version of user's template
    rendered = MarkdownColumn('rendered', nullable=True)

    # Draft of the campaign template that the custom template is linked to (for updating before finalising)
    draft_id = db.Column(None, db.ForeignKey('email_draft.id'), nullable=True)
    draft = db.relationship(EmailDraft)

    # Recipients may be emailed as a group with all emails in the To field. Unique number to identify them
    linkgroup = db.Column(db.Integer, nullable=True)

    __table_args__ = (db.UniqueConstraint(campaign_id, md5sum),)

    @property
    def fullname(self):
        """
        Recipient's fullname, constructed from first and last names if required.
        """
        if self._fullname:
            return self._fullname
        elif self._firstname:
            if self._lastname:
                # FIXME: Cultural assumption of <first> <space> <last> name.
                return u"{first} {last}".format(first=self._firstname, last=self._lastname)
            else:
                return self._lastname
        elif self._lastname:
            return self._lastname
        else:
            return None

    @fullname.setter
    def fullname(self, value):
        self._fullname = value

    @property
    def firstname(self):
        if self._firstname:
            return self._firstname
        elif self._fullname:
            return self._fullname.split(u' ')[0]
        else:
            return None

    @firstname.setter
    def firstname(self, value):
        self._firstname = value

    @property
    def lastname(self):
        if self._lastname:
            return self._lastname
        elif self._fullname:
            return self._fullname.split(u' ')[-1]
        else:
            return None

    @lastname.setter
    def lastname(self, value):
        self._lastname = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value
        self.md5sum = md5sum(value)

    fullname = db.synonym('_fullname', descriptor=fullname)
    firstname = db.synonym('_firstname', descriptor=firstname)
    lastname = db.synonym('_lastname', descriptor=lastname)
    email = db.synonym('_email', descriptor=email)

    def is_latest_draft(self):
        if not self.draft:
            return True
        return self.draft == self.campaign.drafts[-1]

    def make_linkgroup(self):
        if self.linkgroup is None and self.campaign is not None:
            self.linkgroup = (db.session.query(EmailRecipient.linkgroup).filter(
                EmailRecipient.campaign == self.campaign).first() or 0) + 1
