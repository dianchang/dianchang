"""Add root_id to AnswerComment.

Revision ID: 3cf652d92bfc
Revises: 4e4b09398ef6
Create Date: 2015-06-10 09:06:16.174430

"""

# revision identifiers, used by Alembic.
revision = '3cf652d92bfc'
down_revision = '4e4b09398ef6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('answer_comment', sa.Column('root_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'answer_comment', 'answer_comment', ['root_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'answer_comment', type_='foreignkey')
    op.drop_column('answer_comment', 'root_id')
    ### end Alembic commands ###
