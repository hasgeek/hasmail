"""CC and BCC

Revision ID: 28cbf4bd7fb6
Revises: 29a2220f73e3
Create Date: 2014-08-01 10:58:31.224368

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '28cbf4bd7fb6'
down_revision = '29a2220f73e3'


def upgrade() -> None:
    op.add_column('email_campaign', sa.Column('bcc', sa.UnicodeText(), nullable=True))
    op.add_column('email_campaign', sa.Column('cc', sa.UnicodeText(), nullable=True))
    op.alter_column('email_campaign', '_headers', new_column_name='fields')


def downgrade() -> None:
    op.alter_column('email_campaign', 'fields', new_column_name='_headers')
    op.drop_column('email_campaign', 'cc')
    op.drop_column('email_campaign', 'bcc')
