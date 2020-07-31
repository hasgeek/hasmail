"""EmailRecipient template has no rendered version

Revision ID: 29d480776419
Revises: 32de3aa6b4f4
Create Date: 2014-07-10 23:24:41.829859

"""

# revision identifiers, used by Alembic.
revision = '29d480776419'
down_revision = '32de3aa6b4f4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('email_recipient', 'template_html')
    op.alter_column('email_recipient', 'template_text', new_column_name='template')


def downgrade():
    op.alter_column('email_recipient', 'template', new_column_name='template_text')
    op.add_column(
        'email_recipient', sa.Column('template_html', sa.TEXT(), nullable=True)
    )
