"""add next in Page

Revision ID: 83f79ad1fcb5
Revises: 2c4ecefdb853
Create Date: 2020-12-28 12:05:31.173189

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '83f79ad1fcb5'
down_revision = '2c4ecefdb853'
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_next_id', 'page', ['next_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.drop_constraint('fk_next_id', type_='foreignkey')
