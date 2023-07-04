"""Add nickname

Revision ID: 29a2220f73e3
Revises: a8549653a69
Create Date: 2014-07-17 01:54:49.589928

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '29a2220f73e3'
down_revision = 'a8549653a69'


def upgrade() -> None:
    op.add_column(
        'email_recipient', sa.Column('nickname', sa.Unicode(length=80), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('email_recipient', 'nickname')
