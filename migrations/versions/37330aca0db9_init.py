"""Init

Revision ID: 37330aca0db9
Revises: None
Create Date: 2014-04-05 20:42:13.939218

"""

# revision identifiers, used by Alembic.
revision = '37330aca0db9'
down_revision = None

from alembic import op
import sqlalchemy as sa

from coaster.sqlalchemy import JsonDict


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('username', sa.Unicode(length=80), nullable=True),
        sa.Column('lastuser_token_scope', sa.Unicode(length=250), nullable=True),
        sa.Column('lastuser_token_type', sa.Unicode(length=250), nullable=True),
        sa.Column('userid', sa.String(length=22), nullable=False),
        sa.Column('lastuser_token', sa.String(length=22), nullable=True),
        sa.Column('fullname', sa.Unicode(length=80), nullable=False),
        sa.Column('email', sa.Unicode(length=80), nullable=True),
        sa.Column('userinfo', JsonDict(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('lastuser_token'),
        sa.UniqueConstraint('userid'),
        sa.UniqueConstraint('username'),
    )
    op.create_table(
        'email_campaign',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('_headers', sa.UnicodeText(), nullable=False),
        sa.Column('trackopens', sa.Boolean(), nullable=False),
        sa.Column('trackclicks', sa.Boolean(), nullable=False),
        sa.Column('name', sa.Unicode(length=250), nullable=False),
        sa.Column('title', sa.Unicode(length=250), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table(
        'email_draft',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('subject', sa.Unicode(length=250), nullable=False),
        sa.Column('template_text', sa.UnicodeText(), nullable=False),
        sa.Column('template_html', sa.UnicodeText(), nullable=False),
        sa.Column('url_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaign.id'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'url_id'),
    )
    op.create_table(
        'email_recipient',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('fullname', sa.Unicode(length=80), nullable=True),
        sa.Column('firstname', sa.Unicode(length=80), nullable=True),
        sa.Column('lastname', sa.Unicode(length=80), nullable=True),
        sa.Column('email', sa.Unicode(length=80), nullable=False),
        sa.Column('md5sum', sa.String(length=32), nullable=False),
        sa.Column('data', JsonDict(), nullable=True),
        sa.Column('opentoken', sa.Unicode(length=44), nullable=False),
        sa.Column('opened', sa.Boolean(), nullable=False),
        sa.Column('rsvptoken', sa.Unicode(length=44), nullable=False),
        sa.Column('rsvp', sa.Unicode(length=1), nullable=True),
        sa.Column('subject', sa.Unicode(length=250), nullable=True),
        sa.Column('template_text', sa.UnicodeText(), nullable=True),
        sa.Column('template_html', sa.UnicodeText(), nullable=True),
        sa.Column('rendered_text', sa.UnicodeText(), nullable=True),
        sa.Column('rendered_html', sa.UnicodeText(), nullable=True),
        sa.Column('draft_id', sa.Integer(), nullable=True),
        sa.Column('linkgroup', sa.Integer(), nullable=True),
        sa.Column('url_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['email_campaign.id'],),
        sa.ForeignKeyConstraint(['draft_id'], ['email_draft.id'],),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('campaign_id', 'url_id'),
        sa.UniqueConstraint('opentoken'),
        sa.UniqueConstraint('rsvptoken'),
    )


def downgrade():
    op.drop_table('email_recipient')
    op.drop_table('email_draft')
    op.drop_table('email_campaign')
    op.drop_table('user')
