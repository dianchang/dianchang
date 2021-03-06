"""Update User model.

Revision ID: 3e72085bf89b
Revises: 5532ac2b35c2
Create Date: 2015-06-13 16:45:20.154536

"""

# revision identifiers, used by Alembic.
revision = '3e72085bf89b'
down_revision = '5532ac2b35c2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('shares_count', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('upvotes_count', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'upvotes_count')
    op.drop_column('user', 'shares_count')
    ### end Alembic commands ###
