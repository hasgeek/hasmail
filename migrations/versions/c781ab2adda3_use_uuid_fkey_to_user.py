"""Use uuid fkey to user

Revision ID: c781ab2adda3
Revises: 6e3b5579313e
Create Date: 2023-07-07 13:32:39.389807

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c781ab2adda3'
down_revision = '6e3b5579313e'


user_table = sa.table(
    'user',
    sa.column('id', sa.Integer()),
    sa.column('uuid', sa.Uuid()),
)

email_campaign_table = sa.table(
    'email_campaign',
    sa.column('id', sa.Integer()),
    sa.column('user_id', sa.Integer()),
    sa.column('user_uuid', sa.Uuid()),
)


def upgrade() -> None:
    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_uuid', sa.Uuid(), nullable=True))

    conn = op.get_bind()
    campaign_fkeys = conn.execute(
        sa.select(
            email_campaign_table.c.id.label('campaign_id'),
            email_campaign_table.c.user_id.label('user_id'),
            user_table.c.uuid.label('user_uuid'),
        ).where(email_campaign_table.c.user_id == user_table.c.id)
    )
    for campaign in campaign_fkeys:
        op.execute(
            email_campaign_table.update()
            .where(email_campaign_table.c.id == campaign.campaign_id)
            .values(user_uuid=campaign.user_uuid)
        )

    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.alter_column('user_uuid', nullable=False)
        batch_op.drop_constraint('email_campaign_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'email_campaign_user_uuid_fkey', 'user', ['user_uuid'], ['uuid']
        )
        batch_op.drop_column('user_id')


def downgrade() -> None:
    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Uuid(), nullable=True))

    conn = op.get_bind()
    campaign_fkeys = conn.execute(
        sa.select(
            email_campaign_table.c.id.label('campaign_id'),
            email_campaign_table.c.user_uuid.label('user_uuid'),
            user_table.c.id.label('user_id'),
        ).where(email_campaign_table.c.user_uuid == user_table.c.uuid)
    )
    for campaign in campaign_fkeys:
        op.execute(
            email_campaign_table.update()
            .where(email_campaign_table.c.id == campaign.campaign_id)
            .values(user_id=campaign.user_id)
        )

    with op.batch_alter_table('email_campaign', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.drop_constraint('email_campaign_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'email_campaign_user_id_fkey', 'user', ['user_id'], ['id']
        )
        batch_op.drop_column('user_uuid')
