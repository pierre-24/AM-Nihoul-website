"""add email attachements

Revision ID: 7ec03b1d7c82
Revises: 2ece94d7b5e8
Create Date: 2021-04-12 07:57:17.425399

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7ec03b1d7c82'
down_revision = '2ece94d7b5e8'
branch_labels = ()
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'email_image_attachment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date_created', sa.DateTime(), nullable=True),
        sa.Column('date_modified', sa.DateTime(), nullable=True),
        sa.Column('email_id', sa.Integer(), nullable=True),
        sa.Column('image_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['email_id'], ['email.id'], ),
        sa.ForeignKeyConstraint(['image_id'], ['uploaded_file.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('email_image_attachment')
    # ### end Alembic commands ###
