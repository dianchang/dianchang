"""Add experience to UserTopicStatistics.

Revision ID: 4876cee49bef
Revises: 3e1dd0faf4b9
Create Date: 2015-05-31 23:15:19.443529

"""

# revision identifiers, used by Alembic.
revision = '4876cee49bef'
down_revision = '3e1dd0faf4b9'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_topic_statistics', sa.Column('experience', sa.String(length=200), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_topic_statistics', 'experience')
    ### end Alembic commands ###
