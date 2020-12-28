"""remove position

Revision ID: 2c4ecefdb853
Revises:
Create Date: 2020-12-28 10:55:00.451324

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c4ecefdb853'
down_revision = None
branch_labels = ('default',)
depends_on = None


def upgrade():
    with op.batch_alter_table('menu_entry') as batch_op:
        batch_op.drop_column('position')


def downgrade():
    with op.batch_alter_table('menu_entry') as batch_op:
        batch_op.add_column(sa.Column('position', sa.INTEGER(), nullable=True, default=0))
