"""Don't pre-render drafts

Revision ID: 1d4ce659308a
Revises: 124505044ba4
Create Date: 2014-07-11 01:12:56.818872

"""

# revision identifiers, used by Alembic.
revision = '1d4ce659308a'
down_revision = '124505044ba4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('email_draft', 'template_html')
    op.alter_column('email_draft', 'template_text', new_column_name='template')


def downgrade():
    op.alter_column('email_draft', 'template', new_column_name='template_text')
    op.add_column('email_draft', sa.Column('template_html', sa.TEXT(), nullable=False))
