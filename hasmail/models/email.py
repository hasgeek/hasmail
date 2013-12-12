# -*- coding: utf-8 -*-

from coaster.utils import md5sum
from . import db, BaseMixin, BaseScopedIdMixin, MarkdownColumn

__all__ = ['EmailCampaign', 'EmailRecipient']


class EmailCampaign(BaseMixin, db.Model):
    __tablename__ = 'email_campaign'


class EmailDraft(BaseScopedIdMixin, db.Model):
    __tablename__ = 'email_draft'

    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)
    campaign = db.relationship(EmailCampaign, backref=db.backref('drafts',
        cascade='all, delete-orphan', order_by='EmailDraft.url_id'))
    parent = db.synonym('campaign')

    template = MarkdownColumn('template', nullable=False, default=u"")

    __table_args__ = (db.UniqueConstraint('campaign_id', 'url_id'),)


class EmailRecipient(BaseMixin, db.Model):
    __tablename__ = 'email_recipient'

    # Campaign this recipient is a part of
    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)
    campaign = db.relationship(EmailCampaign, backref=db.backref('recipients', cascade='all, delete-orphan'))

    _fullname = db.Column('fullname', db.Unicode(80), nullable=True)
    _firstname = db.Column('firstname', db.Unicode(80), nullable=True)
    _lastname = db.Column('lastname', db.Unicode(80), nullable=True)

    _email = db.Column('email', db.Unicode(80), nullable=False)
    md5sum = db.Column(db.String(32), nullable=False)

    # Customised template for this recipient
    # TODO: Discover template for linked groups (only one recipient will have a custom template that is used for all)
    template = MarkdownColumn('template', nullable=True)

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
