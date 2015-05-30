"""Add anonymous to Question model.

Revision ID: 53468a636652
Revises: 7183a00cf0c
Create Date: 2015-05-30 10:40:14.465887

"""

# revision identifiers, used by Alembic.
revision = '53468a636652'
down_revision = '7183a00cf0c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('question', sa.Column('anonymous', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('question', 'anonymous')
    ### end Alembic commands ###
