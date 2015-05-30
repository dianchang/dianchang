"""Add score to TopicExpert.

Revision ID: 2f41be73a5ba
Revises: 41f27a2f2eb1
Create Date: 2015-05-30 09:48:40.221319

"""

# revision identifiers, used by Alembic.
revision = '2f41be73a5ba'
down_revision = '41f27a2f2eb1'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic_expert', sa.Column('score', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic_expert', 'score')
    ### end Alembic commands ###
