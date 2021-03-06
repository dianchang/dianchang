"""Add updated_at to Topic.

Revision ID: 42eacc1e5733
Revises: 15f3d22cf56e
Create Date: 2015-07-20 19:59:41.118834

"""

# revision identifiers, used by Alembic.
revision = '42eacc1e5733'
down_revision = '15f3d22cf56e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic', sa.Column('updated_at', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic', 'updated_at')
    ### end Alembic commands ###
