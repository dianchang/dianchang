"""Add TopicClosure table.

Revision ID: 35ff8c684ce1
Revises: 503ae17078fe
Create Date: 2015-05-25 16:53:32.429369

"""

# revision identifiers, used by Alembic.
revision = '35ff8c684ce1'
down_revision = '503ae17078fe'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('topic_closure',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ancestor_id', sa.Integer(), nullable=True),
    sa.Column('descendant_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['ancestor_id'], ['topic.id'], ),
    sa.ForeignKeyConstraint(['descendant_id'], ['topic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('topic_closure')
    ### end Alembic commands ###