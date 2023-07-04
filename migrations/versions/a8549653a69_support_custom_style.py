"""Support custom stylesheets

Revision ID: a8549653a69
Revises: 1d4ce659308a
Create Date: 2014-07-16 15:05:14.116405

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a8549653a69'
down_revision = '1d4ce659308a'


def upgrade() -> None:
    op.add_column(
        'email_campaign',
        sa.Column(
            'stylesheet', sa.UnicodeText(), nullable=False, server_default=sa.text("''")
        ),
    )
    op.alter_column('email_campaign', 'stylesheet', server_default=None)


def downgrade() -> None:
    op.drop_column('email_campaign', 'stylesheet')
