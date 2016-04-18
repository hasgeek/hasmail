"""Phone field

Revision ID: 295069eec83c
Revises: 405e179cec7d
Create Date: 2016-04-13 23:16:36.474136

"""

# revision identifiers, used by Alembic.
revision = '295069eec83c'
down_revision = '405e179cec7d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('email_campaign', sa.Column('default_country', sa.Unicode(length=2), nullable=False,
        server_default='IN'))
    op.alter_column('email_campaign', 'default_country', server_default=None)
    op.add_column('email_campaign', sa.Column('type', sa.SmallInteger(), nullable=False, server_default=sa.text('0')))
    op.alter_column('email_campaign', 'type', server_default=None)
    op.add_column('email_recipient', sa.Column('phone', sa.Unicode(length=16), nullable=True))
    op.add_column('email_recipient', sa.Column('phone_valid', sa.Boolean(), nullable=True))
    op.alter_column('email_recipient', 'email',
        type_=sa.VARCHAR(length=254),
        existing_type=sa.VARCHAR(length=80),
        nullable=True)
    op.alter_column('email_recipient', 'md5sum',
        existing_type=sa.VARCHAR(length=32),
        nullable=True)
    op.create_index(op.f('ix_email_recipient_phone'), 'email_recipient', ['phone'], unique=False)
    op.create_unique_constraint('email_recipient_campaign_id_phone_key', 'email_recipient', ['campaign_id', 'phone'])
    op.create_unique_constraint('email_recipient_campaign_id_email_key', 'email_recipient', ['campaign_id', 'email'])


def downgrade():
    op.drop_constraint('email_recipient_campaign_id_email_key', 'email_recipient', type_='unique')
    op.drop_constraint('email_recipient_campaign_id_phone_key', 'email_recipient', type_='unique')
    op.drop_index(op.f('ix_email_recipient_phone'), table_name='email_recipient')
    op.alter_column('email_recipient', 'md5sum',
        existing_type=sa.VARCHAR(length=32),
        nullable=False)
    op.alter_column('email_recipient', 'email',
        type_=sa.VARCHAR(length=80),
        existing_type=sa.VARCHAR(length=254),
        nullable=False)
    op.drop_column('email_recipient', 'phone_valid')
    op.drop_column('email_recipient', 'phone')
    op.drop_column('email_campaign', 'type')
    op.drop_column('email_campaign', 'default_country')
