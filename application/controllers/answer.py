# coding: utf-8
from flask import Blueprint, render_template, json, g
from ..models import db, Answer, UpvoteAnswer, UserTopicStatistics
from ..utils.permissions import UserPermission

bp = Blueprint('answer', __name__)


@bp.route('/answer/<int:uid>')
def view(uid):
    answer = Answer.query.get_or_404(uid)
    return render_template('answer/view.html', answer=answer)


@bp.route('/answer/<int:uid>/upvote', methods=['POST'])
@UserPermission()
def upvote(uid):
    """赞同 & 取消赞同回答"""
    answer = Answer.query.get_or_404(uid)
    upvote_answer = answer.upvotes.filter(UpvoteAnswer.user_id == g.user.id)
    # 取消赞同
    if upvote_answer.count():
        map(db.session.delete, upvote_answer)
        db.session.commit()

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistics.downvote_answer_in_topic(answer.user_id, topic.topic_id)

        return json.dumps({
            'result': True,
            'thanked': False
        })
    else:  # 赞同
        upvote_answer = UpvoteAnswer(user_id=g.user.id)
        answer.upvotes.append(upvote_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistics.upvote_answer_in_topic(answer.user_id, topic.topic_id)

        return json.dumps({
            'result': True,
            'thanked': True
        })
