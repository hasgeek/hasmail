"""Drop unused trackclicks flag

Revision ID: 2ff3aaf78532
Revises: c781ab2adda3
Create Date: 2023-07-07 13:49:21.176325

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '2ff3aaf78532'
down_revision = 'c781ab2adda3'


def upgrade() -> None:
    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.drop_column('trackclicks')


def downgrade() -> None:
    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'trackclicks', sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch_op.alter_column('trackclicks', server_default=None)
