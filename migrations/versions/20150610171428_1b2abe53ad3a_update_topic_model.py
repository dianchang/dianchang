"""Update Topic model.

Revision ID: 1b2abe53ad3a
Revises: 433420363893
Create Date: 2015-06-10 17:14:28.311548

"""

# revision identifiers, used by Alembic.
revision = '1b2abe53ad3a'
down_revision = '433420363893'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic', sa.Column('wiki_preview', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic', 'wiki_preview')
    ### end Alembic commands ###
