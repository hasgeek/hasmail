"""Use UserBase2

Revision ID: 405e179cec7d
Revises: 28cbf4bd7fb6
Create Date: 2016-04-12 18:39:55.871861

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '405e179cec7d'
down_revision = '28cbf4bd7fb6'


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column('status', sa.Integer(), nullable=False, server_default=sa.text('0')),
    )
    op.alter_column('user', 'status', server_default=None)


def downgrade() -> None:
    op.drop_column('user', 'status')
