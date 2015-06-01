"""Add name_pinyin to Topic model.

Revision ID: be77483e65b
Revises: 29b3b8eae57a
Create Date: 2015-06-01 15:45:05.357795

"""

# revision identifiers, used by Alembic.
revision = 'be77483e65b'
down_revision = '29b3b8eae57a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic', sa.Column('name_pinyin', sa.String(length=100), nullable=True))
    op.add_column('topic_synonym', sa.Column('synonym', sa.String(length=200), nullable=True))
    op.add_column('topic_synonym', sa.Column('synonym_pinyin', sa.String(length=200), nullable=True))
    op.drop_column('topic_synonym', 'content')
    op.drop_column('topic_synonym', 'pinyin')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic_synonym', sa.Column('pinyin', mysql.VARCHAR(length=200), nullable=True))
    op.add_column('topic_synonym', sa.Column('content', mysql.VARCHAR(length=200), nullable=True))
    op.drop_column('topic_synonym', 'synonym_pinyin')
    op.drop_column('topic_synonym', 'synonym')
    op.drop_column('topic', 'name_pinyin')
    ### end Alembic commands ###
