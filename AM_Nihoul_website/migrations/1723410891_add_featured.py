"""add featured

Revision ID: 1723410891
Revises: 1723407615
Create Date: 2024-08-11 23:14:51.101254

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1723410891'
down_revision = '1723407615'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'featured',
        sa.Column('title', sa.VARCHAR(length=150), nullable=False),
        sa.Column('link', sa.VARCHAR(length=150), nullable=False),
        sa.Column('link_text', sa.VARCHAR(length=150), nullable=False),
        sa.Column('image_link', sa.VARCHAR(length=150), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.Column('date_modified', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('featured')
    # ### end Alembic commands ###
