"""Add topic_id to HomeFeed.

Revision ID: 1334692cc30e
Revises: 3ef23c7621bd
Create Date: 2015-07-15 11:44:39.906402

"""

# revision identifiers, used by Alembic.
revision = '1334692cc30e'
down_revision = '3ef23c7621bd'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('home_feed', sa.Column('topic_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'home_feed', 'topic', ['topic_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'home_feed', type_='foreignkey')
    op.drop_column('home_feed', 'topic_id')
    ### end Alembic commands ###
