"""Add url_token to User model.

Revision ID: 3d98cd8a86fa
Revises: 2f8569f1066
Create Date: 2015-06-02 11:18:34.216778

"""

# revision identifiers, used by Alembic.
revision = '3d98cd8a86fa'
down_revision = '2f8569f1066'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('url_token', sa.String(length=100), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'url_token')
    ### end Alembic commands ###
