"""add visibility to page

Revision ID: 2ece94d7b5e8
Revises: 83f79ad1fcb5
Create Date: 2020-12-29 11:20:26.892259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2ece94d7b5e8'
down_revision = '83f79ad1fcb5'
branch_labels = ()
depends_on = None


def upgrade():
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.add_column(sa.Column('visible', sa.Boolean(), nullable=False, default=True))


def downgrade():
    with op.batch_alter_table('page', schema=None) as batch_op:
        batch_op.drop_column('visible')
