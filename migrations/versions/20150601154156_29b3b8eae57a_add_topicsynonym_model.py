"""Add TopicSynonym model.

Revision ID: 29b3b8eae57a
Revises: 27651591b3f5
Create Date: 2015-06-01 15:41:56.570502

"""

# revision identifiers, used by Alembic.
revision = '29b3b8eae57a'
down_revision = '27651591b3f5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('topic_synonym',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('content', sa.String(length=200), nullable=True),
    sa.Column('pinyin', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('topic_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['topic_id'], ['topic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('topic_synonym')
    ### end Alembic commands ###
