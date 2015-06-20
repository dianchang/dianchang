"""Update topic model.

Revision ID: 419760db35ea
Revises: 2a0d468e36e7
Create Date: 2015-06-20 14:35:10.901310

"""

# revision identifiers, used by Alembic.
revision = '419760db35ea'
down_revision = '2a0d468e36e7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic', sa.Column('all_questions_count', sa.Integer(), nullable=True))
    op.add_column('topic', sa.Column('questions_count', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic', 'questions_count')
    op.drop_column('topic', 'all_questions_count')
    ### end Alembic commands ###
