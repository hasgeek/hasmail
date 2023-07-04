"""Link tracking

Revision ID: 32de3aa6b4f4
Revises: 441fa655c385
Create Date: 2014-07-08 02:19:50.325405

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '32de3aa6b4f4'
down_revision = '441fa655c385'


def upgrade() -> None:
    op.create_table(
        'email_link',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.Unicode(length=10), nullable=True),
        sa.Column('url', sa.Unicode(length=2083), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index('ix_email_link_url', 'email_link', ['url'])
    op.create_table(
        'email_link_recipient',
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('link_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['link_id'], ['email_link.id']),
        sa.ForeignKeyConstraint(['recipient_id'], ['email_recipient.id']),
        sa.PrimaryKeyConstraint('link_id', 'recipient_id'),
    )


def downgrade() -> None:
    op.drop_table('email_link_recipient')
    op.drop_index('ix_email_link_url')
    op.drop_table('email_link')
