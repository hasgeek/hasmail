"""Drop unused models, fix timestamps.

Revision ID: b9ffb7fde6f7
Revises: 405e179cec7d
Create Date: 2023-07-03 23:35:23.256882

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b9ffb7fde6f7'
down_revision = '405e179cec7d'


def upgrade() -> None:
    op.drop_table('email_link_recipient')
    with op.batch_alter_table('email_link', schema=None) as batch_op:
        batch_op.drop_index('ix_email_link_url')

    op.drop_table('email_link')
    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )

    with op.batch_alter_table('email_draft', schema=None) as batch_op:
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )

    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.alter_column(
            'data',
            existing_type=sa.TEXT(),
            type_=postgresql.JSONB(),
            existing_nullable=True,
            postgresql_using='data::jsonb',
        )
        batch_op.alter_column(
            'opened_first_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )
        batch_op.alter_column(
            'opened_last_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column(
            'userinfo',
            existing_type=sa.TEXT(),
            type_=postgresql.JSONB(),
            existing_nullable=True,
            postgresql_using='userinfo::jsonb',
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.DateTime(),
            type_=sa.TIMESTAMP(timezone=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'userinfo',
            existing_type=postgresql.JSONB(),
            type_=sa.TEXT(),
            existing_nullable=True,
        )

    with op.batch_alter_table('email_recipient', schema=None) as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'opened_last_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            'opened_first_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            'data',
            existing_type=postgresql.JSONB(),
            type_=sa.TEXT(),
            nullable=True,
        )

    with op.batch_alter_table('email_draft', schema=None) as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )

    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.alter_column(
            'updated_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            'created_at',
            existing_type=sa.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=False,
        )

    op.create_table(
        'email_link',
        sa.Column(
            'id',
            sa.INTEGER(),
            server_default=sa.text("nextval('email_link_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=False),
        sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=False),
        sa.Column('name', sa.VARCHAR(length=10), autoincrement=False, nullable=True),
        sa.Column('url', sa.VARCHAR(length=2083), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name='email_link_pkey'),
        sa.UniqueConstraint('name', name='email_link_name_key'),
        postgresql_ignore_search_path=False,
    )
    with op.batch_alter_table('email_link', schema=None) as batch_op:
        batch_op.create_index('ix_email_link_url', ['url'], unique=False)

    op.create_table(
        'email_link_recipient',
        sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=False),
        sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=False),
        sa.Column('link_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column('recipient_id', sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ['link_id'], ['email_link.id'], name='email_link_recipient_link_id_fkey'
        ),
        sa.ForeignKeyConstraint(
            ['recipient_id'],
            ['email_recipient.id'],
            name='email_link_recipient_recipient_id_fkey',
        ),
        sa.PrimaryKeyConstraint(
            'link_id', 'recipient_id', name='email_link_recipient_pkey'
        ),
    )
