# coding: utf-8
from flask import Blueprint, render_template, json, g, request, redirect, url_for
from ..models import db, Answer, UpvoteAnswer, UserTopicStatistics, DownvoteAnswer, ThankAnswer, NohelpAnswer, \
    AnswerDraft, AnswerComment, LikeAnswerComment
from ..utils.permissions import UserPermission

bp = Blueprint('answer', __name__)


@bp.route('/answer/<int:uid>', methods=['POST', 'GET'])
def view(uid):
    """单个回答页"""
    answer = Answer.query.get_or_404(uid)
    if request.method == 'POST' and request.form.get('comment'):
        permission = UserPermission()
        if not permission.check():
            return permission.deny()

        comment_content = request.form.get('comment')
        comment = AnswerComment(content=comment_content, user_id=g.user.id)
        answer.comments.append(comment)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.view', uid=uid))
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
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistics.cancel_upvote_answer_in_topic(answer.user_id, topic.topic_id)

        # TODO: need to change to answer.upvotes_count
        return json.dumps({
            'result': True,
            'upvoted': False,
            'count': answer.upvotes.count()
        })
    else:  # 赞同
        upvote_answer = UpvoteAnswer(user_id=g.user.id)
        answer.upvotes.append(upvote_answer)

        # 删除对该回答的反对
        downvote_answer = answer.downvotes.filter(DownvoteAnswer.user_id == g.user.id)
        map(db.session.delete, downvote_answer)

        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistics.upvote_answer_in_topic(answer.user_id, topic.topic_id)

        # TODO: need to change to answer.upvotes_count
        return json.dumps({
            'result': True,
            'upvoted': True,
            'count': answer.upvotes.count()
        })


@bp.route('/answer/<int:uid>/downvote', methods=['POST'])
def downvote(uid):
    """反对 & 取消反对"""
    answer = Answer.query.get_or_404(uid)
    downvote_answer = answer.downvotes.filter(DownvoteAnswer.user_id == g.user.id)
    # 取消反对
    if downvote_answer.count():
        map(db.session.delete, downvote_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'downvoted': False
        })
    else:  # 反对
        downvote_answer = DownvoteAnswer(user_id=g.user.id)
        answer.downvotes.append(downvote_answer)

        # 删除对该回答的赞同
        upvote_answer = answer.upvotes.filter(UpvoteAnswer.user_id == g.user.id)
        map(db.session.delete, upvote_answer)

        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'downvoted': True
        })


@bp.route('/answer/<int:uid>/thank', methods=['POST'])
def thank(uid):
    """感谢 & 取消感谢"""
    answer = Answer.query.get_or_404(uid)
    thank_answer = answer.thanks.filter(ThankAnswer.user_id == g.user.id)
    # 取消感谢
    if thank_answer.count():
        map(db.session.delete, thank_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'thanked': False
        })
    else:  # 感谢
        thank_answer = ThankAnswer(user_id=g.user.id)
        answer.thanks.append(thank_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'thanked': True
        })


@bp.route('/answer/<int:uid>/nohelp', methods=['POST'])
def nohelp(uid):
    """没有帮助 & 取消没有帮助"""
    answer = Answer.query.get_or_404(uid)
    nohelp_answer = answer.nohelps.filter(NohelpAnswer.user_id == g.user.id)
    # 取消没有帮助
    if nohelp_answer.count():
        map(db.session.delete, nohelp_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'nohelped': False
        })
    else:  # 没有帮助
        nohelp_answer = NohelpAnswer(user_id=g.user.id)
        answer.nohelps.append(nohelp_answer)
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return json.dumps({
            'result': True,
            'nohelped': True
        })


@bp.route('/answer/draft/<int:uid>/remove', methods=['POST'])
@UserPermission()
def remove_draft(uid):
    """移除草稿"""
    draft = AnswerDraft.query.get_or_404(uid)
    db.session.delete(draft)
    db.session.commit()
    return json.dumps({'result': True})


@bp.route('/answer/comment/<int:uid>/like', methods=['POST'])
@UserPermission()
def like_comment(uid):
    """赞评论"""
    comment = AnswerComment.query.get_or_404(uid)
    like = comment.likes.filter(LikeAnswerComment.user_id == g.user.id)
    if like.count():  # 取消赞
        map(db.session.delete, like)
        db.session.commit()
        # TODO: neet to use comment.likes_count
        return json.dumps({
            'result': True,
            'liked': False,
            'count': comment.likes.count()
        })
    else:
        # 赞评论
        like = LikeAnswerComment(user_id=g.user.id)
        comment.likes.append(like)
        db.session.add(comment)
        db.session.commit()

        # TODO: neet to use comment.likes_count
        return json.dumps({
            'result': True,
            'liked': True,
            'count': comment.likes.count()
        })
