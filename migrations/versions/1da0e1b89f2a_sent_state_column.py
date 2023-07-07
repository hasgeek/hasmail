"""Sent state column

Revision ID: 1da0e1b89f2a
Revises: b9ffb7fde6f7
Create Date: 2023-07-06 22:08:36.541604

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1da0e1b89f2a'
down_revision = 'b9ffb7fde6f7'


email_recipient = sa.table(
    'email_recipient',
    sa.column('rendered_text', sa.Unicode()),
    sa.column('is_sent', sa.Boolean()),
)


def upgrade() -> None:
    op.add_column(
        'email_recipient',
        sa.Column('is_sent', sa.Boolean(), server_default=sa.false(), nullable=True),
    )
    op.execute(
        email_recipient.update()
        .values(is_sent=True)
        .where(email_recipient.c.rendered_text.isnot(None))
    )
    op.alter_column('email_recipient', 'is_sent', nullable=False, server_default=None)


def downgrade() -> None:
    op.drop_column('email_recipient', 'is_sent')
