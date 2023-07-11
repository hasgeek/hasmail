"""Rename campaign_id to mailer_id

Revision ID: 60b9647f38c2
Revises: 1da0e1b89f2a
Create Date: 2023-07-07 11:56:09.339548

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '60b9647f38c2'
down_revision = '1da0e1b89f2a'


def upgrade() -> None:
    with op.batch_alter_table('email_draft', schema=None) as batch_op:
        batch_op.alter_column('campaign_id', new_column_name='mailer_id')
        batch_op.drop_constraint('email_draft_campaign_id_url_id_key', type_='unique')
        batch_op.drop_constraint('email_draft_campaign_id_fkey', type_='foreignkey')
        batch_op.create_unique_constraint(
            'email_draft_mailer_id_url_id_key', ['mailer_id', 'url_id']
        )
        batch_op.create_foreign_key(
            'email_draft_mailer_id_fkey', 'email_campaign', ['mailer_id'], ['id']
        )

    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.alter_column('campaign_id', new_column_name='mailer_id')
        batch_op.drop_constraint(
            'email_recipient_campaign_id_url_id_key', type_='unique'
        )
        batch_op.drop_constraint('email_recipient_campaign_id_fkey', type_='foreignkey')
        batch_op.create_unique_constraint(
            'email_recipient_mailer_id_url_id_key', ['mailer_id', 'url_id']
        )
        batch_op.create_foreign_key(
            'email_recipient_mailer_id_fkey', 'email_campaign', ['mailer_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.alter_column('mailer_id', new_column_name='campaign_id')
        batch_op.drop_constraint('email_recipient_mailer_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'email_recipient_campaign_id_fkey',
            'email_campaign',
            ['campaign_id'],
            ['id'],
        )
        batch_op.drop_constraint('email_recipient_mailer_id_url_id_key', type_='unique')
        batch_op.create_unique_constraint(
            'email_recipient_campaign_id_url_id_key', ['campaign_id', 'url_id']
        )

    with op.batch_alter_table('email_draft', schema=None) as batch_op:
        batch_op.alter_column('mailer_id', new_column_name='campaign_id')
        batch_op.drop_constraint('email_draft_mailer_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'email_draft_campaign_id_fkey', 'email_campaign', ['campaign_id'], ['id']
        )
        batch_op.drop_constraint('email_draft_mailer_id_url_id_key', type_='unique')
        batch_op.create_unique_constraint(
            'email_draft_campaign_id_url_id_key', ['campaign_id', 'url_id']
        )
