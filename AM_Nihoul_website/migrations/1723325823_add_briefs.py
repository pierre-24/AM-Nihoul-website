"""add briefs

Revision ID: 1723325823
Revises: 1723319933
Create Date: 2024-08-10 23:37:03.097447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1723325823'
down_revision = '1723319933'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'brief',
        sa.Column('visible', sa.Boolean(), nullable=False),
        sa.Column('title', sa.VARCHAR(length=150), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('slug', sa.VARCHAR(length=150), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.Column('date_modified', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('brief')
    # ### end Alembic commands ###
