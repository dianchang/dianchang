# coding: utf-8
from datetime import date
from flask import Blueprint, render_template, json, g, request, redirect, url_for, get_template_attribute
from ..models import db, Answer, UpvoteAnswer, UserTopicStatistic, DownvoteAnswer, ThankAnswer, NohelpAnswer, \
    AnswerDraft, AnswerComment, LikeAnswerComment, UserFeed, USER_FEED_KIND, HomeFeed, HOME_FEED_KIND, Notification, \
    NOTIFICATION_KIND, UserUpvoteStatistic, HomeFeedBackup
from ..utils.permissions import UserPermission
from ..utils.decorators import jsonify

bp = Blueprint('answer', __name__)


@bp.route('/answer/<int:uid>')
def view(uid):
    """单个回答页"""
    answer = Answer.query.get_or_404(uid)
    return render_template('answer/view.html', answer=answer)


@bp.route('/answer/<int:uid>/mobile_view')
def mobile_view(uid):
    """单个回答页（适配移动端）"""
    answer = Answer.query.get_or_404(uid)
    return render_template('answer/mobile_view.html', answer=answer)


@bp.route('/answer/<int:uid>/update', methods=['POST'])
@UserPermission()
@jsonify
def update(uid):
    answer = Answer.query.get_or_404(uid)
    content = request.form.get('content', '')

    if not content:
        return {'result': False}

    answer.content = content
    db.session.add(answer)

    # 删除草稿
    if answer.draft:
        db.session.delete(answer.draft)
        g.user.drafts_count -= 1
        db.session.add(g.user)

    db.session.commit()
    return {'result': True, 'content': answer.content}


@bp.route('/answer/<int:uid>/upvote', methods=['POST'])
@UserPermission()
@jsonify
def upvote(uid):
    """赞同 & 取消赞同回答"""
    answer = Answer.query.get_or_404(uid)
    upvote_answer = answer.upvotes.filter(UpvoteAnswer.user_id == g.user.id)
    # 取消赞同
    if upvote_answer.count():
        map(db.session.delete, upvote_answer)
        answer.calculate_score()  # 更新回答分值
        answer.upvotes_count -= 1
        answer.user.upvotes_count -= 1
        db.session.add(answer)
        db.session.add(answer.user)

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistic.cancel_upvote_answer_in_topic(answer.user_id, topic.topic_id)

        # 更新用户赞同统计数据
        statistic = UserUpvoteStatistic.query.filter(UserUpvoteStatistic.upvoter_id == g.user.id,
                                                     UserUpvoteStatistic.user_id == answer.user_id).first()
        if statistic:
            statistic.upvotes_count -= 1
            statistic.upvoter_followings_count = g.user.followings_count
        statistic.update()
        db.session.add(statistic)

        db.session.commit()

        return {
            'result': True,
            'upvoted': False,
            'count': answer.upvotes_count
        }
    else:  # 赞同
        upvote_answer = UpvoteAnswer(user_id=g.user.id)
        answer.upvotes.append(upvote_answer)

        # 删除对该回答的反对
        downvote_answer = answer.downvotes.filter(DownvoteAnswer.user_id == g.user.id)
        map(db.session.delete, downvote_answer)

        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)

        # USER FEED: 插入到本人的用户FEED
        user_feed = UserFeed(kind=USER_FEED_KIND.UPVOTE_ANSWER, answer_id=uid)
        g.user.feeds.append(user_feed)
        db.session.add(g.user)

        # HOME FEED: 插入到 followers 的首页 FEED
        # TODO: 使用消息队列进行插入操作
        for follower in g.user.followers:
            # 赞同的回答若是该 follower 创建的，则不插入此条 feed
            if follower.follower_id != answer.user_id:
                home_feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_UPVOTE_ANSWER, sender_id=g.user.id,
                                     answer_id=uid)
                follower.follower.home_feeds.append(home_feed)
                db.session.add(follower.follower)

        # HOME FEED: 备份
        home_feed_backup = HomeFeedBackup(kind=HOME_FEED_KIND.FOLLOWING_UPVOTE_ANSWER,
                                          sender_id=g.user.id, answer_id=uid)
        db.session.add(home_feed_backup)

        # NOTI: 插入到被赞回答者的 NOTI（需合并）
        if g.user.id != answer.user_id:
            noti = answer.user.notifications.filter(
                Notification.kind == NOTIFICATION_KIND.UPVOTE_ANSWER,
                Notification.unread,
                Notification.created_at_date == date.today()).first()
            if noti:
                noti.add_sender(g.user.id)
                db.session.add(noti)
            else:
                noti = Notification(kind=NOTIFICATION_KIND.UPVOTE_ANSWER, senders_list=json.dumps([g.user.id]),
                                    answer_id=uid)
                answer.user.notifications.append(noti)
                db.session.add(answer.user)

        # 更新话题统计数据
        for topic in answer.question.topics:
            UserTopicStatistic.upvote_answer_in_topic(answer.user_id, topic.topic_id)

        # 更新用户赞同统计数据
        if g.user.id != answer.user_id:
            statistic = UserUpvoteStatistic.query.filter(UserUpvoteStatistic.upvoter_id == g.user.id,
                                                         UserUpvoteStatistic.user_id == answer.user_id).first()
            if statistic:
                statistic.upvotes_count += 1
                statistic.upvoter_followings_count = g.user.followings_count
            else:
                statistic = UserUpvoteStatistic(upvoter_id=g.user.id, user_id=answer.user_id,
                                                upvotes_count=1, upvoter_followings_count=g.user.followings_count)
            statistic.update()
            db.session.add(statistic)

        # 更新用户获得的赞同数
        answer.user.upvotes_count += 1
        answer.upvotes_count += 1
        db.session.add(answer.user)

        db.session.commit()

        return {
            'result': True,
            'upvoted': True,
            'count': answer.upvotes_count
        }


@bp.route('/answer/<int:uid>/downvote', methods=['POST'])
@UserPermission()
@jsonify
def downvote(uid):
    """反对 & 取消反对"""
    answer = Answer.query.get_or_404(uid)
    downvote_answer = answer.downvotes.filter(DownvoteAnswer.user_id == g.user.id).first()
    # 取消反对
    if downvote_answer.count():
        db.session.delete(downvote_answer)
        answer.downvotes_count -= 1
        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return {
            'result': True,
            'downvoted': False
        }
    else:  # 反对
        downvote_answer = DownvoteAnswer(user_id=g.user.id)
        answer.downvotes.append(downvote_answer)
        answer.downvotes_count += 1

        # 删除对该回答的赞同
        upvote_answer = answer.upvotes.filter(UpvoteAnswer.user_id == g.user.id).first()
        if upvote_answer:
            db.session.delete(upvote_answer)
            answer.upvotes_count -= 1
            answer.user.upvotes_count -= 1
            db.session.add(answer.user)

        answer.calculate_score()  # 更新回答分值
        db.session.add(answer)
        db.session.commit()

        return {
            'result': True,
            'downvoted': True
        }


@bp.route('/answer/<int:uid>/thank', methods=['POST'])
@UserPermission()
@jsonify
def thank(uid):
    """感谢（无法取消感谢）"""
    answer = Answer.query.get_or_404(uid)
    thank_answer = answer.thanks.filter(ThankAnswer.user_id == g.user.id)

    # 感谢
    if not thank_answer.count():
        thank_answer = ThankAnswer(user_id=g.user.id)
        answer.thanks.append(thank_answer)
        answer.calculate_score()  # 更新回答分值
        answer.thanks_count += 1
        answer.user.thanks_count += 1
        db.session.add(answer.user)
        db.session.add(answer)

        # NOTI: 插入被感谢者的 NOTI（需合并）
        if g.user.id != answer.user_id:
            noti = answer.user.notifications.filter(
                Notification.unread,
                Notification.kind == NOTIFICATION_KIND.THANK_ANSWER,
                Notification.created_at_date == date.today()).first()
            if noti:
                noti.add_sender(g.user.id)
                db.session.add(noti)
            else:
                noti = Notification(kind=NOTIFICATION_KIND.THANK_ANSWER, senders_list=json.dumps([g.user.id]),
                                    answer_id=uid)
                answer.user.notifications.append(noti)
                db.session.add(answer.user)

        db.session.commit()

    return {
        'result': True,
        'thanked': True
    }


@bp.route('/answer/<int:uid>/nohelp', methods=['POST'])
@UserPermission()
@jsonify
def nohelp(uid):
    """没有帮助 & 取消没有帮助"""
    answer = Answer.query.get_or_404(uid)
    nohelp_answer = answer.nohelps.filter(NohelpAnswer.user_id == g.user.id)
    # 取消没有帮助
    if nohelp_answer.count():
        map(db.session.delete, nohelp_answer)
        answer.calculate_score()  # 更新回答分值
        answer.nohelps_count -= 1
        db.session.add(answer)
        db.session.commit()

        return {
            'result': True,
            'nohelped': False
        }
    else:  # 没有帮助
        nohelp_answer = NohelpAnswer(user_id=g.user.id)
        answer.nohelps.append(nohelp_answer)
        answer.calculate_score()  # 更新回答分值
        answer.nohelps_count += 1
        db.session.add(answer)
        db.session.commit()

        return {
            'result': True,
            'nohelped': True
        }


@bp.route('/answer/draft/<int:uid>/remove', methods=['POST'])
@UserPermission()
@jsonify
def remove_draft(uid):
    """移除草稿"""
    draft = AnswerDraft.query.get_or_404(uid)
    g.user.drafts_count -= 1
    db.session.add(g.user)
    db.session.delete(draft)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/answer/comment/<int:uid>/like', methods=['POST'])
@UserPermission()
@jsonify
def like_comment(uid):
    """赞评论"""
    comment = AnswerComment.query.get_or_404(uid)
    like = comment.likes.filter(LikeAnswerComment.user_id == g.user.id).first()
    if like:  # 取消赞
        db.session.delete(like)
        comment.likes_count -= 1
        db.session.add(comment)
        db.session.commit()
        return {
            'result': True,
            'liked': False,
            'count': comment.likes_count
        }
    else:
        # 赞评论
        like = LikeAnswerComment(user_id=g.user.id)
        comment.likes.append(like)
        comment.likes_count += 1
        db.session.add(comment)

        # NOTI: 插入被赞者的 NOTI（需合并）
        if g.user.id != comment.user_id:
            noti = comment.user.notifications.filter(
                Notification.unread,
                Notification.kind == NOTIFICATION_KIND.LIKE_ANSWER_COMMENT,
                Notification.created_at_date == date.today()).first()
            if noti:
                noti.add_sender(g.user.id)
                db.session.add(noti)
            else:
                noti = Notification(kind=NOTIFICATION_KIND.LIKE_ANSWER_COMMENT, senders_list=json.dumps([g.user.id]),
                                    answer_comment_id=uid)
                comment.user.notifications.append(noti)
                db.session.add(comment.user)

                db.session.commit()

    return {
        'result': True,
        'liked': True,
        'count': comment.likes_count
    }


@bp.route('/answer/comment/<int:uid>/reply', methods=['POST'])
@UserPermission()
@jsonify
def reply_comment(uid):
    """回复评论"""
    parent_comment = AnswerComment.query.get_or_404(uid)
    comment_content = request.form.get('content')
    new_comment = AnswerComment(user_id=g.user.id, answer_id=parent_comment.answer_id, parent_id=uid,
                                content=comment_content, root_id=parent_comment.root_id or uid,
                                question_id=parent_comment.question_id)
    db.session.add(new_comment)
    parent_comment.answer.comments_count += 1
    db.session.add(parent_comment.answer)
    db.session.commit()

    # NOTI: 插入到被回复者的 NOTI
    if g.user.id != parent_comment.user_id:
        noti = Notification(kind=NOTIFICATION_KIND.REPLY_ANSWER_COMMENT, senders_list=json.dumps([g.user.id]),
                            answer_comment_id=new_comment.id)
        parent_comment.user.notifications.append(noti)
        db.session.add(parent_comment.user)
        db.session.commit()

    macro = get_template_attribute('macros/_answer.html', 'render_answer_comment')
    return {
        'result': True,
        'html': macro(new_comment)
    }


@bp.route('/answer/<int:uid>/comment', methods=['POST'])
@jsonify
def comment(uid):
    answer = Answer.query.get_or_404(uid)
    permission = UserPermission()
    if not permission.check():
        return permission.deny()

    # 评论回答
    comment_content = request.form.get('content')
    if not comment_content:
        return {
            'result': False
        }

    comment = AnswerComment(content=comment_content, user_id=g.user.id, question_id=answer.question_id)
    answer.comments.append(comment)
    answer.comments_count += 1
    db.session.add(answer)
    db.session.commit()

    # NOTI: 插入被评论回答者的 NOTI
    if g.user.id != answer.user_id:
        noti = Notification(kind=NOTIFICATION_KIND.COMMENT_ANSWER, senders_list=json.dumps([g.user.id]),
                            answer_comment_id=comment.id)
        answer.user.notifications.append(noti)
        db.session.add(answer.user)

    db.session.commit()

    macro = get_template_attribute('macros/_answer.html', 'render_answer_comment')
    return {
        'result': True,
        'html': macro(comment)
    }


@bp.route('/answer/<int:uid>/load_comments_wap', methods=['POST'])
@jsonify
def load_comments_wap(uid):
    """加载回答的评论wap"""
    answer = Answer.query.get_or_404(uid)
    macro = get_template_attribute('macros/_answer.html', 'render_answer_comments')
    return {
        'result': True,
        'html': macro(answer)
    }
