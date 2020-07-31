"""Open tracking

Revision ID: 441fa655c385
Revises: 37330aca0db9
Create Date: 2014-07-08 00:52:25.473714

"""

# revision identifiers, used by Alembic.
revision = '441fa655c385'
down_revision = '37330aca0db9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'email_recipient',
        sa.Column('opened_ipaddr', sa.Unicode(length=45), nullable=True),
    )
    op.add_column(
        'email_recipient', sa.Column('opened_first_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'email_recipient', sa.Column('opened_last_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_column('email_recipient', 'opened_last_at')
    op.drop_column('email_recipient', 'opened_first_at')
    op.drop_column('email_recipient', 'opened_ipaddr')
