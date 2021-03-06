"""Add setting fields to User model.

Revision ID: 902805df097
Revises: 419760db35ea
Create Date: 2015-06-20 19:41:28.282663

"""

# revision identifiers, used by Alembic.
revision = '902805df097'
down_revision = '419760db35ea'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('answer_question_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('answer_question_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('answer_question_message_via_notification', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('follow_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('follow_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('follow_message_via_notification', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('invite_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('invite_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('invite_message_via_notification', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('like_comment_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('like_comment_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('like_comment_message_via_notification', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('receive_activity_message', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('receive_weekly_digest_message', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('reply_comment_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('reply_comment_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('reply_comment_message_via_notification', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('show_to_search_engine', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('upvote_answer_message_from_all', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('upvote_answer_message_via_mail', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('upvote_answer_message_via_notification', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'upvote_answer_message_via_notification')
    op.drop_column('user', 'upvote_answer_message_via_mail')
    op.drop_column('user', 'upvote_answer_message_from_all')
    op.drop_column('user', 'show_to_search_engine')
    op.drop_column('user', 'reply_comment_message_via_notification')
    op.drop_column('user', 'reply_comment_message_via_mail')
    op.drop_column('user', 'reply_comment_message_from_all')
    op.drop_column('user', 'receive_weekly_digest_message')
    op.drop_column('user', 'receive_activity_message')
    op.drop_column('user', 'like_comment_message_via_notification')
    op.drop_column('user', 'like_comment_message_via_mail')
    op.drop_column('user', 'like_comment_message_from_all')
    op.drop_column('user', 'invite_message_via_notification')
    op.drop_column('user', 'invite_message_via_mail')
    op.drop_column('user', 'invite_message_from_all')
    op.drop_column('user', 'follow_message_via_notification')
    op.drop_column('user', 'follow_message_via_mail')
    op.drop_column('user', 'follow_message_from_all')
    op.drop_column('user', 'answer_question_message_via_notification')
    op.drop_column('user', 'answer_question_message_via_mail')
    op.drop_column('user', 'answer_question_message_from_all')
    ### end Alembic commands ###
