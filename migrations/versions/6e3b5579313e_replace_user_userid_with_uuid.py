"""Replace user.userid with uuid

Revision ID: 6e3b5579313e
Revises: 1ba0d0459d7f
Create Date: 2023-07-07 12:34:58.418861

"""

import sqlalchemy as sa
from alembic import op

from coaster.utils import uuid_from_base64, uuid_to_base64

# revision identifiers, used by Alembic.
revision = '6e3b5579313e'
down_revision = '1ba0d0459d7f'


user_table = sa.table(
    'user',
    sa.column('id', sa.Integer()),
    sa.column('userid', sa.Unicode),
    sa.column('uuid', sa.Uuid()),
)


def upgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('uuid', sa.Uuid(), nullable=True))

    conn = op.get_bind()
    users = conn.execute(sa.select(user_table))
    for user in users:
        op.execute(
            user_table.update()
            .where(user_table.c.id == user.id)
            .values(uuid=uuid_from_base64(user.userid))
        )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('uuid', nullable=False)
        batch_op.create_unique_constraint('user_uuid_key', ['uuid'])
        batch_op.drop_constraint('user_userid_key', type_='unique')
        batch_op.drop_column('userid')


def downgrade() -> None:
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('userid', sa.VARCHAR(length=22), nullable=True))

    conn = op.get_bind()
    users = conn.execute(sa.select(user_table))
    for user in users:
        op.execute(
            user_table.update()
            .where(user_table.c.id == user.id)
            .values(userid=uuid_to_base64(user.uuid))
        )

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('userid', nullable=False)
        batch_op.create_unique_constraint('user_userid_key', ['userid'])
        batch_op.drop_constraint('user_uuid_key', type_='unique')
        batch_op.drop_column('uuid')
