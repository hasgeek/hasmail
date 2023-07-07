"""Drop linkgroup

Revision ID: 1ba0d0459d7f
Revises: 60b9647f38c2
Create Date: 2023-07-07 12:26:00.690352

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1ba0d0459d7f'
down_revision = '60b9647f38c2'


def upgrade() -> None:
    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.drop_column('linkgroup')


def downgrade() -> None:
    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('linkgroup', sa.INTEGER(), autoincrement=False, nullable=True)
        )
