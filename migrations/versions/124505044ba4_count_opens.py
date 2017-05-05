"""Count opens

Revision ID: 124505044ba4
Revises: 29d480776419
Create Date: 2014-07-11 00:18:51.584987

"""

# revision identifiers, used by Alembic.
revision = '124505044ba4'
down_revision = '29d480776419'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('email_recipient', sa.Column('opened_count', sa.Integer(), nullable=False, server_default=sa.text('0')))
    op.alter_column('email_recipient', 'opened_count', server_default=None)


def downgrade():
    op.drop_column('email_recipient', 'opened_count')
