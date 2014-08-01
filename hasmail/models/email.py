# -*- coding: utf-8 -*-

import re
from flask import url_for, Markup, request
from sqlalchemy.orm import defer, deferred
import pystache
import short_url
from premailer import transform as email_transform
from coaster.utils import buid, md5sum, newsecret, LabeledEnum
from coaster.gfm import markdown, GFM_TAGS
from . import db, TimestampMixin, BaseMixin, BaseNameMixin, BaseScopedIdMixin, JsonDict
from .user import User
from .. import __

__all__ = ['CAMPAIGN_STATUS', 'EmailCampaign', 'EmailDraft', 'EmailRecipient', 'EmailLink', 'EmailLinkRecipient']

NAMESPLIT_RE = re.compile(r'[\W\.]+')
EMAIL_RE = re.compile(r'^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$', re.I)

EMAIL_TAGS = dict(GFM_TAGS)
for key in EMAIL_TAGS:
    EMAIL_TAGS[key].append('class')
    EMAIL_TAGS[key].append('style')
del key


def render_preview(campaign, text):
    return email_transform(
        Markup((u'<style type="text/css">%s</style>\n' % campaign.stylesheet) if campaign.stylesheet else u'')
            + markdown(text, html=True, valid_tags=EMAIL_TAGS),
        base_url=request.url_root)


class CAMPAIGN_STATUS(LabeledEnum):
    DRAFT = (0, __(u"Draft"))
    QUEUED = (1, __(u"Queued"))
    SENDING = (2, __(u"Sending"))
    SENT = (3, __(u"Sent"))


class EmailCampaign(BaseNameMixin, db.Model):
    __tablename__ = 'email_campaign'

    user_id = db.Column(None, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship(User, backref=db.backref('campaigns', order_by=db.desc('email_campaign.updated_at')))
    status = db.Column(db.Integer, nullable=False, default=CAMPAIGN_STATUS.DRAFT)
    _fields = db.Column('fields', db.UnicodeText, nullable=False, default=u'')
    trackopens = db.Column(db.Boolean, nullable=False, default=False)
    trackclicks = db.Column(db.Boolean, nullable=False, default=False)
    stylesheet = db.Column(db.UnicodeText, nullable=False, default=u'')
    _cc = db.Column('cc', db.UnicodeText, nullable=True)
    _bcc = db.Column('bcc', db.UnicodeText, nullable=True)

    def __repr__(self):
        return '<EmailCampaign "%s" (%s)>' % (self.title, CAMPAIGN_STATUS.get(self.status))

    @property
    def fields(self):
        flist = self._fields.split(u' ')
        while u'' in flist:
            flist.remove(u'')
        return flist

    @fields.setter
    def fields(self, value):
        self._fields = u' '.join(sorted(set(value)))

    fields = db.synonym('_fields', descriptor=fields)

    @property
    def cc(self):
        return self._cc

    @cc.setter
    def cc(self, value):
        if isinstance(value, basestring):
            value = [l.strip() for l in value.replace(u'\r\n', u'\n').replace(u'\r', u'\n').split(u'\n') if l]
        self._cc = u'\n'.join(sorted(set(value)))

    cc = db.synonym('_cc', descriptor=cc)

    @property
    def bcc(self):
        return self._bcc

    @bcc.setter
    def bcc(self, value):
        if isinstance(value, basestring):
            value = [l.strip() for l in value.replace(u'\r\n', u'\n').replace(u'\r', u'\n').split(u'\n') if l]
        self._bcc = u'\n'.join(sorted(set(value)))

    bcc = db.synonym('_bcc', descriptor=bcc)

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
                'report',
                ])
        return perms

    def url_for(self, action='view'):
        if action == 'view' or action == 'edit':
            return url_for('campaign_view', campaign=self.name)
        elif action == 'recipients':
            return url_for('campaign_recipients', campaign=self.name)
        elif action == 'template':
            return url_for('campaign_template', campaign=self.name)
        elif action == 'send':
            return url_for('campaign_send', campaign=self.name)
        elif action == 'report':
            return url_for('campaign_report', campaign=self.name)

    def draft(self):
        if self.drafts:
            return self.drafts[-1]


class EmailDraft(BaseScopedIdMixin, db.Model):
    __tablename__ = 'email_draft'

    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)
    campaign = db.relationship(EmailCampaign, backref=db.backref('drafts',
        cascade='all, delete-orphan', order_by='EmailDraft.url_id'))
    parent = db.synonym('campaign')
    revision_id = db.synonym('url_id')

    subject = deferred(db.Column(db.Unicode(250), nullable=False, default=u""))
    template = deferred(db.Column(db.UnicodeText, nullable=False, default=u""))

    __table_args__ = (db.UniqueConstraint('campaign_id', 'url_id'),)

    def __repr__(self):
        return '<EmailDraft %d of %s>' % (self.revision_id, repr(self.campaign)[1:-1])

    def get_preview(self):
        return render_preview(self.campaign, self.template)


class EmailRecipient(BaseScopedIdMixin, db.Model):
    __tablename__ = 'email_recipient'

    # Campaign this recipient is a part of
    campaign_id = db.Column(None, db.ForeignKey('email_campaign.id'), nullable=False)

    _fullname = db.Column('fullname', db.Unicode(80), nullable=True)
    _firstname = db.Column('firstname', db.Unicode(80), nullable=True)
    _lastname = db.Column('lastname', db.Unicode(80), nullable=True)
    _nickname = db.Column('nickname', db.Unicode(80), nullable=True)

    _email = db.Column('email', db.Unicode(80), nullable=False, index=True)
    md5sum = db.Column(db.String(32), nullable=False, index=True)

    data = db.Column(JsonDict)

    # Support email open tracking
    opentoken = db.Column(db.Unicode(44), nullable=False, default=newsecret, unique=True)
    opened = db.Column(db.Boolean, nullable=False, default=False)
    opened_ipaddr = db.Column(db.Unicode(45), nullable=True)
    opened_first_at = db.Column(db.DateTime, nullable=True)
    opened_last_at = db.Column(db.DateTime, nullable=True)
    opened_count = db.Column(db.Integer, nullable=False, default=0)

    # Support RSVP if the email requires it
    rsvptoken = db.Column(db.Unicode(44), nullable=False, default=newsecret, unique=True)
    rsvp = db.Column(db.Unicode(1), nullable=True)  # Y/N/M response

    # Customised template for this recipient
    # TODO: Discover template for linked groups (only one recipient will have a custom template that is used for all)
    subject = db.Column(db.Unicode(250), nullable=True)
    template = deferred(db.Column(db.UnicodeText, nullable=True))

    # Rendered version of user's template, for archival
    rendered_text = deferred(db.Column(db.UnicodeText, nullable=True))
    rendered_html = deferred(db.Column(db.UnicodeText, nullable=True))

    # Draft of the campaign template that the custom template is linked to (for updating before finalising)
    draft_id = db.Column(None, db.ForeignKey('email_draft.id'), nullable=True)
    draft = db.relationship(EmailDraft)

    # Recipients may be emailed as a group with all emails in the To field. Unique number to identify them
    linkgroup = db.Column(db.Integer, nullable=True)

    campaign = db.relationship(EmailCampaign, backref=db.backref('recipients',
        cascade='all, delete-orphan', order_by=(draft_id, _fullname, _firstname, _lastname)))
    parent = db.synonym('campaign')

    __table_args__ = (db.UniqueConstraint('campaign_id', 'url_id'),)

    def __repr__(self):
        return '<EmailRecipient %s %s of %s>' % (self.fullname, self.email, repr(self.campaign)[1:-1])

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
                return self._firstname
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
            return NAMESPLIT_RE.split(self._fullname)[0]
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
            return NAMESPLIT_RE.split(self._fullname)[-1]
        else:
            return None

    @lastname.setter
    def lastname(self, value):
        self._lastname = value

    @property
    def nickname(self):
        return self._nickname or self.firstname

    @nickname.setter
    def nickname(self, value):
        self._nickname = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        self._email = value.lower()
        self.md5sum = md5sum(value)

    fullname = db.synonym('_fullname', descriptor=fullname)
    firstname = db.synonym('_firstname', descriptor=firstname)
    lastname = db.synonym('_lastname', descriptor=lastname)
    nickname = db.synonym('_nickname', descriptor=nickname)
    email = db.synonym('_email', descriptor=email)

    def is_email_valid(self):
        return EMAIL_RE.match(self.email) is not None

    @property
    def revision_id(self):
        return self.draft.revision_id if self.draft else None

    def is_latest_draft(self):
        if not self.draft:
            return True
        return self.draft == self.campaign.drafts[-1]

    def make_linkgroup(self):
        if self.linkgroup is None and self.campaign is not None:
            self.linkgroup = (db.session.query(EmailRecipient.linkgroup).filter(
                EmailRecipient.campaign == self.campaign).first() or 0) + 1

    def template_data(self):
        return dict([
            ('fullname', self.fullname),
            ('email', self.email),
            ('firstname', self.firstname),
            ('lastname', self.lastname),
            ('nickname', self.nickname),
            ('RSVP_Y', self.url_for('rsvp', status='Y')),
            ('RSVP_N', self.url_for('rsvp', status='N')),
            ('RSVP_M', self.url_for('rsvp', status='M')),
            ] + (self.data.items() if self.data else []))

    def get_rendered(self, draft):
        if self.draft:
            return pystache.render(self.template, self.template_data())
        else:
            return pystache.render(draft.template, self.template_data())

    def get_preview(self, draft):
        return render_preview(self.campaign, self.get_rendered(draft))

    def url_for(self, action='view', _external=False, **kwargs):
        if action == 'view' or action == 'template':
            return url_for('recipient_view', campaign=self.campaign.name, recipient=self.url_id, _external=_external, **kwargs)
        elif action == 'edit':
            return url_for('recipient_edit', campaign=self.campaign.name, recipient=self.url_id, _external=_external, **kwargs)
        elif action == 'delete':
            return url_for('recipient_delete', campaign=self.campaign.name, recipient=self.url_id, _external=_external, **kwargs)
        elif action == 'trackopen':
            return url_for('track_open_gif', opentoken=self.opentoken, _external=True, **kwargs)
        elif action == 'report':
            return url_for('recipient_report', campaign=self.campaign.name, recipient=self.url_id, _external=_external, **kwargs)
        elif action == 'rsvp':
            return url_for('rsvp', rsvptoken=self.rsvptoken, _external=True, **kwargs)

    def openmarkup(self):
        if self.campaign.trackopens:
            return Markup(
                u'\n<img src="{url}" width="1" height="1" alt="" border="0" style="height:1px !important;'
                u'width:1px !important;border-width:0 !important;margin-top:0 !important;'
                u'margin-bottom:0 !important;margin-right:0 !important;margin-left:0 !important;'
                u'padding-top:0 !important;padding-bottom:0 !important;padding-right:0 !important;'
                u'padding-left:0 !important;"/>'.format(url=self.url_for('trackopen')))
        else:
            return Markup(u'')

    @classmethod
    def custom_draft_in(cls, campaign):
        return cls.query.filter(cls.campaign == campaign,
            cls.draft != None,
            cls.__table__.c.template_text != None).options(
                defer('created_at'), defer('updated_at'), defer('email'), defer('md5sum'),
                defer('fullname'), defer('firstname'), defer('lastname'), defer('data'),
                defer('opentoken'), defer('opened'), defer('rsvptoken'), defer('rsvp'),
                defer('linkgroup'), defer('nickname')
            ).all()


class EmailLink(BaseMixin, db.Model):
    __tablename__ = 'email_link'

    name = db.Column(db.String(10), nullable=True, unique=True)
    url = db.Column(db.String(2083), nullable=False, index=True)

    @classmethod
    def shorten(cls, url):
        link = cls.query.filter_by(url=url).first()
        if link:
            return link
        link = cls(url=url)
        db.session.add(link)
        db.session.flush()
        link.name = short_url.encode_url(link.id)
        return link

    @classmethod
    def get(cls, name):
        return cls.query.filter_by(name=name).one_or_none()


class EmailLinkRecipient(TimestampMixin, db.Model):
    __tablename__ = 'email_link_recipient'

    link_id = db.Column(None, db.ForeignKey('email_link.id'), primary_key=True)
    link = db.relationship(EmailLink, backref=db.backref('link_recipients', cascade='all, delete-orphan'))
    recipient_id = db.Column(None, db.ForeignKey('email_recipient.id'), primary_key=True)
    recipient = db.relationship(EmailRecipient, backref=db.backref('recipient_links', cascade='all, delete-orphan'))
