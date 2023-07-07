"""Rename models

Revision ID: 761d820f2eaa
Revises: 2ff3aaf78532
Create Date: 2023-07-07 13:58:27.187831

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = '761d820f2eaa'
down_revision = '2ff3aaf78532'

renames = [
    ('table', 'email_campaign', 'mailer'),
    ('sequence', 'email_campaign_id_seq', 'mailer_id_seq'),
    ('constraint', 'mailer', 'email_campaign_pkey', 'mailer_pkey'),
    ('constraint', 'mailer', 'email_campaign_name_key', 'mailer_name_key'),
    ('constraint', 'mailer', 'email_campaign_user_uuid_fkey', 'mailer_user_uuid_fkey'),
    ('table', 'email_recipient', 'mailer_recipient'),
    ('sequence', 'email_recipient_id_seq', 'mailer_recipient_id_seq'),
    ('constraint', 'mailer_recipient', 'email_recipient_pkey', 'mailer_recipient_pkey'),
    (
        'constraint',
        'mailer_recipient',
        'email_recipient_mailer_id_url_id_key',
        'mailer_recipient_mailer_id_url_id_key',
    ),
    (
        'constraint',
        'mailer_recipient',
        'email_recipient_opentoken_key',
        'mailer_recipient_opentoken_key',
    ),
    (
        'constraint',
        'mailer_recipient',
        'email_recipient_rsvptoken_key',
        'mailer_recipient_rsvptoken_key',
    ),
    (
        'index',
        'ix_email_recipient_email',
        'ix_mailer_recipient_email',
    ),
    (
        'index',
        'ix_email_recipient_md5sum',
        'ix_mailer_recipient_md5sum',
    ),
    ('table', 'email_draft', 'mailer_draft'),
    ('sequence', 'email_draft_id_seq', 'mailer_draft_id_seq'),
    ('constraint', 'mailer_draft', 'email_draft_pkey', 'mailer_draft_pkey'),
    (
        'constraint',
        'mailer_draft',
        'email_draft_mailer_id_url_id_key',
        'mailer_draft_mailer_id_url_id_key',
    ),
    (
        'constraint',
        'mailer_draft',
        'email_draft_mailer_id_fkey',
        'mailer_draft_mailer_id_fkey',
    ),
]


def upgrade() -> None:
    for row in renames:
        if row[0] == 'table':
            old_name, new_name = row[1:]
            op.rename_table(old_name, new_name)
        elif row[0] == 'sequence':
            old_name, new_name = row[1:]
            op.execute(f'ALTER SEQUENCE {old_name} RENAME TO {new_name}')
        elif row[0] == 'constraint':
            table_name, old_name, new_name = row[1:]
            op.execute(
                f'ALTER TABLE {table_name} RENAME CONSTRAINT'
                f' {old_name} TO {new_name}'
            )
        elif row[0] == 'index':
            old_name, new_name = row[1:]
            op.execute(f'ALTER INDEX {old_name} RENAME TO {new_name}')


def downgrade() -> None:
    for row in renames[::-1]:
        if row[0] == 'table':
            old_name, new_name = row[1:]
            op.rename_table(new_name, old_name)
        elif row[0] == 'sequence':
            old_name, new_name = row[1:]
            op.execute(f'ALTER SEQUENCE {new_name} RENAME TO {old_name}')
        elif row[0] == 'constraint':
            table_name, old_name, new_name = row[1:]
            op.execute(
                f'ALTER TABLE {table_name} RENAME CONSTRAINT'
                f' {new_name} TO {old_name}'
            )
        elif row[0] == 'index':
            old_name, new_name = row[1:]
            op.execute(f'ALTER INDEX {new_name} RENAME TO {old_name}')
