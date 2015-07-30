# coding: utf-8
from datetime import datetime, date
from flask import Blueprint, render_template, url_for, json, g, request, get_template_attribute
from ..models import db, User, FollowUser, Notification, NOTIFICATION_KIND, UserFeed, USER_FEED_KIND, \
    UserUpvoteStatistic, ComposeFeed, COMPOSE_FEED_KIND, InviteAnswer, NOTIFICATION_KIND_TYPE, \
    HomeFeedBackup, HomeFeed
from ..utils.permissions import UserPermission
from ..utils._qiniu import qiniu
from ..utils.helpers import absolute_url_for
from ..utils.decorators import jsonify

bp = Blueprint('user', __name__)

USER_FEEDS_PER = 15


@bp.route('/people/<int:uid>')
def profile(uid):
    """用户主页"""
    user = User.query.get_or_404(uid)
    feeds = user.feeds.limit(USER_FEEDS_PER)
    total = user.feeds.count()
    _generate_user_image_upload_token(user)
    return render_template('user/profile.html', user=user, feeds=feeds, total=total, per=USER_FEEDS_PER)


@bp.route('/people/<string:url_token>')
def profile_with_url_token(url_token):
    """用户主页（使用url_token）"""
    user = User.query.filter(User.url_token == url_token).first_or_404()
    feeds = user.feeds.limit(USER_FEEDS_PER)
    total = user.feeds.count()
    _generate_user_image_upload_token(user)
    return render_template('user/profile.html', user=user, feeds=feeds, total=total, per=USER_FEEDS_PER)


@bp.route('/user/<int:uid>/loading_user_feeds', methods=['POST'])
@UserPermission()
@jsonify
def loading_user_feeds(uid):
    """动态加载用户 feeds"""
    user = User.query.get_or_404(uid)
    offset = request.args.get('offset', type=int)
    if not offset:
        return {
            'result': False
        }
    feeds = user.feeds.limit(USER_FEEDS_PER).offset(offset)
    feeds_count = feeds.count()
    macro = get_template_attribute("macros/_user.html", "render_user_feeds")
    return {
        'result': True,
        'html': macro(feeds),
        'count': feeds_count
    }


@bp.route('/people/<int:uid>/qa')
def qa(uid):
    """问答"""
    user = User.query.get_or_404(uid)
    _generate_user_image_upload_token(user)
    feeds = user.feeds.filter(UserFeed.kind.in_([USER_FEED_KIND.ASK_QUESTION, USER_FEED_KIND.ANSWER_QUESTION]))
    feeds_count = feeds.count()
    return render_template('user/qa.html', user=user, feeds=feeds.limit(USER_FEEDS_PER),
                           total=feeds_count, per=USER_FEEDS_PER)


@bp.route('/people/<string:url_token>/qa')
def qa_with_url_token(url_token):
    """问答（使用url_token）"""
    user = User.query.filter(User.url_token == url_token).first_or_404()
    _generate_user_image_upload_token(user)
    feeds = user.feeds.filter(UserFeed.kind.in_([USER_FEED_KIND.ASK_QUESTION, USER_FEED_KIND.ANSWER_QUESTION]))
    feeds_count = feeds.count()
    return render_template('user/qa.html', user=user, feeds=feeds.limit(USER_FEEDS_PER),
                           total=feeds_count, per=USER_FEEDS_PER)


@bp.route('/user/<int:uid>/loading_qa', methods=['POST'])
@UserPermission()
@jsonify
def loading_qa(uid):
    """加载用户问答"""
    user = User.query.get_or_404(uid)
    offset = request.args.get('offset', type=int)
    if not offset:
        return {
            'result': False
        }
    feeds = user.feeds. \
        filter(UserFeed.kind.in_([USER_FEED_KIND.ASK_QUESTION, USER_FEED_KIND.ANSWER_QUESTION])). \
        limit(USER_FEEDS_PER).offset(offset)
    feeds_count = feeds.count()
    macro = get_template_attribute("macros/_user.html", "render_user_feeds")
    return {
        'result': True,
        'html': macro(feeds),
        'count': feeds_count
    }


@bp.route('/people/<int:uid>/achievements')
def achievements(uid):
    """成就"""
    user = User.query.get_or_404(uid)
    _generate_user_image_upload_token(user)
    upvoters = user.upvoters.filter(UserUpvoteStatistic.upvotes_count != 0)
    upvoters_count = upvoters.count()
    return render_template('user/achievements.html', user=user, upvoters=upvoters, upvoters_count=upvoters_count)


@bp.route('/people/<string:url_token>/achievements')
def achievements_with_url_token(url_token):
    """成就（使用url_token）"""
    user = User.query.filter(User.url_token == url_token).first_or_404()
    _generate_user_image_upload_token(user)
    upvoters = user.upvoters.filter(UserUpvoteStatistic.upvotes_count != 0)
    upvoters_count = upvoters.count()
    return render_template('user/achievements.html', user=user, upvoters=upvoters, upvoters_count=upvoters_count)


@bp.route('/people/<int:uid>/follow', methods=['POST'])
@UserPermission()
@jsonify
def follow(uid):
    """关注 & 取消关注某用户"""
    user = User.query.get_or_404(uid)
    follow_user = g.user.followings.filter(FollowUser.following_id == uid).first()
    # 取消关注
    if follow_user:
        db.session.delete(follow_user)
        g.user.followings_count -= 1
        user.followers_count -= 1
        db.session.add(g.user)
        db.session.add(user)

        # HOME FEED：从本人首页 feed 中删除该用户的相关记录
        for home_feed in g.user.home_feeds.filter(HomeFeed.sender_id == uid):
            db.session.delete(home_feed)

        db.session.commit()

        return {'result': True, 'followed': False, 'followers_count': user.followers.count()}
    else:
        # 关注
        if g.user.id == uid:
            return {'result': False, 'followed': False, 'followers_count': user.followers.count()}

        follow_user = FollowUser(follower_id=g.user.id, following_id=uid)
        db.session.add(follow_user)

        g.user.followings_count += 1
        user.followers_count += 1
        db.session.add(g.user)
        db.session.add(user)

        # NOTI: 关注某人
        Notification.follow_me(g.user, user)

        # USER FEED: 关注用户
        UserFeed.follow_user(g.user, user)

        # HOME FEED: 插入该用户最近 10 条动态到本人的首页 feed 中
        for home_feed_backup in HomeFeedBackup.query. \
                filter(HomeFeedBackup.sender_id == uid). \
                order_by(HomeFeedBackup.created_at.desc()).limit(10):
            home_feed = HomeFeed(kind=home_feed_backup.kind, sender_id=home_feed_backup.sender_id,
                                 user_id=g.user.id, question_id=home_feed_backup.question_id,
                                 answer_id=home_feed_backup.answer_id, topic_id=home_feed_backup.topic_id,
                                 created_at=home_feed_backup.created_at)
            db.session.add(home_feed)

        db.session.commit()

        return {'result': True, 'followed': True, 'followers_count': user.followers.count()}


@bp.route('/people/<int:uid>/answers')
def answers(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/answers.html', user=user)


@bp.route('/people/<int:uid>/collects')
def collects(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/collects.html', user=user)


@bp.route('/people/<int:uid>/edits')
def edits(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/edits.html', user=user)


@bp.route('/people/<int:uid>/followings')
def followings(uid):
    """关注"""
    user = User.query.get_or_404(uid)
    followings = user.followings.limit(100)
    return render_template('user/followings.html', user=user, followings=followings)


@bp.route('/people/<int:uid>/followers')
def followers(uid):
    """关注者"""
    user = User.query.get_or_404(uid)
    followers = user.followers.limit(100)
    return render_template('user/followers.html', user=user, followers=followers)


NOTIFICATIONS_PER = 15


@bp.route('/notifications')
@UserPermission()
def notifications():
    """用户全部消息

    不显示关注类消息。
    """
    notifications = g.user.notifications.filter(Notification.kind != NOTIFICATION_KIND_TYPE.USER)
    total = notifications.count()
    template_html = render_template('user/notifications.html', notifications=notifications.limit(NOTIFICATIONS_PER),
                                    total=total, per=NOTIFICATIONS_PER)
    for noti in g.user.notifications.filter(Notification.unread):
        noti.unread = False
        db.session.add(noti)
    g.user.last_read_notifications_at = datetime.now()
    db.session.add(g.user)
    db.session.commit()
    return template_html


@bp.route('/user/loading_notifications', methods=['POST'])
@UserPermission()
@jsonify
def loading_notifications():
    """加载通知"""
    offset = request.args.get('offset', type=int)
    if not offset:
        return {'result': False}

    notifications = g.user.notifications.filter(Notification.kind != NOTIFICATION_KIND_TYPE.USER).limit(
        NOTIFICATIONS_PER).offset(offset)
    count = notifications.count()
    macro = get_template_attribute("macros/_user.html", "render_all_notifications")
    return {
        'result': True,
        'html': macro(notifications),
        'count': count
    }


COMPOSE_FEEDS_PER = 10


@bp.route('/compose')
@UserPermission()
def compose():
    """撰写"""
    feeds = g.user.compose_feeds.filter(~ComposeFeed.ignore)
    total = feeds.count()
    html = render_template('user/compose.html', feeds=feeds.limit(COMPOSE_FEEDS_PER),
                           total=total, per=COMPOSE_FEEDS_PER)

    for feed in feeds.filter(ComposeFeed.unread):
        feed.unread = False
        db.session.add(feed)

    g.user.last_read_compose_feeds_at = datetime.now()
    db.session.add(g.user)
    db.session.commit()
    return html


@bp.route('/user/loading_compose_feeds', methods=['POST'])
@UserPermission()
@jsonify
def loading_compose_feeds():
    """加载撰写feed"""
    offset = request.args.get('offset', type=int)
    if not offset:
        return {
            'result': False
        }

    feeds = g.user.compose_feeds.filter(~ComposeFeed.ignore).limit(COMPOSE_FEEDS_PER).offset(offset)
    feeds_count = feeds.count()
    macro = get_template_attribute("macros/_user.html", "render_compose_feeds")
    return {
        'result': True,
        'html': macro(feeds),
        'count': feeds_count
    }


@bp.route('/compose_feed/<int:uid>/ignore', methods=['POST'])
@UserPermission()
@jsonify
def ignore_compose_feed(uid):
    """忽略邀请回答 & 推荐回答"""
    feed = ComposeFeed.query.get_or_404(uid)
    feed.ignore = True
    db.session.add(feed)
    if feed.kind == COMPOSE_FEED_KIND.INVITE_TO_ANSWER:
        invitation = InviteAnswer.query.get_or_404(feed.invitation_id)
        invitation.ignore = True
        db.session.add(invitation)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/compose_feed/<int:uid>/recover', methods=['POST'])
@UserPermission()
@jsonify
def recover_compose_feed(uid):
    """撤销对邀请回答 & 推荐回答的忽略"""
    feed = ComposeFeed.query.get_or_404(uid)
    feed.ignore = False
    db.session.add(feed)
    if feed.kind == COMPOSE_FEED_KIND.INVITE_TO_ANSWER:
        invitation = InviteAnswer.query.get_or_404(feed.invitation_id)
        invitation.ignore = False
        db.session.add(invitation)
    db.session.commit()
    return {
        'result': True
    }


DRAFTS_PER = 10


@bp.route('/drafts')
@UserPermission()
def drafts():
    """我的草稿"""
    drafts = g.user.drafts
    total = drafts.count()
    return render_template('user/drafts.html', drafts=drafts.limit(DRAFTS_PER),
                           total=total, per=DRAFTS_PER)


@bp.route('/user/loading_drafts', methods=['POST'])
@UserPermission()
@jsonify
def loading_drafts():
    """加载草稿"""
    offset = request.args.get('offset', type=int)
    if not offset:
        return {
            'result': False
        }

    drafts = g.user.drafts.limit(DRAFTS_PER).offset(offset)
    drafts_count = drafts.count()
    macro = get_template_attribute("macros/_user.html", "render_drafts")
    return {
        'result': True,
        'html': macro(drafts),
        'count': drafts_count
    }


@bp.route('/user/update_desc', methods=['POST'])
@UserPermission()
@jsonify
def update_desc():
    """更新描述"""
    desc = request.form.get('desc')
    g.user.desc = desc
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True
    }


@bp.route('/user/update_meta_info', methods=['POST'])
@UserPermission()
@jsonify
def update_meta_info():
    """更新城市、组织、职位"""
    location = request.form.get('location')
    organization = request.form.get('organization')
    position = request.form.get('position')
    g.user.location = location
    g.user.organization = organization
    g.user.position = position
    db.session.add(g.user)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/user/query', methods=['POST'])
@UserPermission()
@jsonify
def query():
    """查询用户"""
    q = request.form.get('q')
    exclude_id = request.form.get('exclude_id', type=int)
    users, total, took = User.query_from_es(q, page=1, per_page=10)
    results = []
    for user in users:
        if user.id != exclude_id:
            results.append({
                'id': user.id,
                'name': user.name,
                'avatar': user.avatar_url
            })
    return results


FOLLOWED_QUESTIONS_PER = 15


@bp.route('/user/followed_questions')
@UserPermission()
def followed_questions():
    """我关注的问题"""
    questions = g.user.followed_questions
    total = questions.count()
    return render_template('user/followed_questions.html', questions=questions.limit(FOLLOWED_QUESTIONS_PER),
                           total=total, per=FOLLOWED_QUESTIONS_PER)


@bp.route('/user/loading_followed_questions', methods=['POST'])
@UserPermission()
@jsonify
def loading_followed_questions():
    """加载关注的问题"""
    offset = request.args.get('offset', type=int)
    if not offset:
        return {
            'result': False
        }

    questions = g.user.followed_questions.limit(FOLLOWED_QUESTIONS_PER).offset(offset)
    count = questions.count()
    macro = get_template_attribute("macros/_user.html", "render_followed_questions")
    return {
        'result': True,
        'html': macro(questions),
        'count': count
    }


@bp.route('/user/<int:uid>/get_data_for_card', methods=['POST'])
@jsonify
def get_data_for_card(uid):
    """获取用于显示用户卡片的数据"""
    user = User.query.get_or_404(uid)
    return {
        'result': True,
        'user': {
            'id': uid,
            'name': user.name,
            'avatar_url': user.avatar_url,
            'profile_url': user.profile_url,
            'desc': user.desc or "",
            'organization': user.organization or "",
            'position': user.position or "",
            'followed': bool(g.user and user.followed_by_user(g.user.id)),
            'followers_count': user.followers_count,
            'myself': bool(g.user and g.user.id == user.id)
        }
    }


@bp.route('/user/get_notifications_html', methods=['POST'])
@UserPermission()
@jsonify
def get_notifications_html():
    """获取用于导航栏的通知HTML"""
    message_notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.MESSAGE))
    message_notifications_macro = get_template_attribute('macros/_user.html', 'render_message_notifications')
    message_notifications_html = message_notifications_macro(message_notifications.limit(20))

    thanks_notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.THANKS))
    thanks_notifications_macro = get_template_attribute('macros/_user.html', 'render_thanks_notifications')
    thanks_notifications_html = thanks_notifications_macro(thanks_notifications.limit(20))

    user_notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.USER))
    user_notifications_macro = get_template_attribute('macros/_user.html', 'render_user_notifications')
    user_notifications_html = user_notifications_macro(user_notifications.limit(20))

    g.user.last_read_notifications_at = datetime.now()
    db.session.add(g.user)
    db.session.commit()
    return {
        'result': True,
        'message_notifications_html': message_notifications_html,
        'user_notifications_html': user_notifications_html,
        'thanks_notifications_html': thanks_notifications_html
    }


@bp.route('/user/read_user_notifications', methods=['POST'])
@UserPermission()
@jsonify
def read_user_notifications():
    """标记用户类通知为已读"""
    notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.USER))
    for noti in notifications:
        noti.unread = False
        db.session.add(noti)
    db.session.commit()
    return {
        'result': True,
    }


@bp.route('/user/read_message_notifications', methods=['POST'])
@UserPermission()
@jsonify
def read_message_notifications():
    """标记消息类通知为已读"""
    notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.MESSAGE))
    for noti in notifications:
        noti.unread = False
        db.session.add(noti)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/user/read_thanks_notifications', methods=['POST'])
@UserPermission()
@jsonify
def read_thanks_notifications():
    """标记感谢类通知为已读"""
    notifications = g.user.notifications.filter(Notification.kind.in_(NOTIFICATION_KIND_TYPE.THANKS))
    for noti in notifications:
        noti.unread = False
        db.session.add(noti)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/user/update_avatar', methods=['POST'])
@jsonify
def update_avatar():
    """更新头像"""
    id = request.form.get('id', type=int)
    user = User.query.get_or_404(id)
    avatar = request.form.get('key')
    user.avatar = avatar
    db.session.add(user)
    db.session.commit()
    return {
        'result': True,
        'url': user.avatar_url
    }


@bp.route('/user/update_background', methods=['POST'])
@jsonify
def update_background():
    """更新首页背景"""
    id = request.form.get('id', type=int)
    user = User.query.get_or_404(id)
    background = request.form.get('key')
    user.background = background
    db.session.add(user)
    db.session.commit()
    return {
        'result': True,
        'url': user.background_url
    }


@bp.route('/user/<int:uid>/get_followed_users_html', methods=['POST'])
@UserPermission()
@jsonify
def get_followed_users_html(uid):
    """获取关注的用户HTML"""
    user = User.query.get_or_404(uid)
    macro = get_template_attribute('macros/_user.html', 'render_followed_users')
    return {
        'result': True,
        'html': macro(user.followings.limit(15))
    }


@bp.route('/user/<int:uid>/get_followed_topics_html', methods=['POST'])
@UserPermission()
@jsonify
def get_followed_topics_html(uid):
    """获取关注的话题HTML"""
    user = User.query.get_or_404(uid)
    macro = get_template_attribute('macros/_user.html', 'render_followed_topics')
    return {
        'result': True,
        'html': macro(user.followed_topics.limit(15))
    }


@bp.route('/user/<int:uid>/get_followers_html', methods=['POST'])
@UserPermission()
@jsonify
def get_followers_html(uid):
    """获取关注者HTML"""
    user = User.query.get_or_404(uid)
    macro = get_template_attribute('macros/_user.html', 'render_followers')
    return {
        'result': True,
        'html': macro(user.followers.limit(15))
    }


def _generate_user_image_upload_token(user):
    """生成上传用户头像与背景图片的token"""
    if g.user and g.user.id == user.id:
        user.avatar_uptoken = qiniu.generate_token(policy={
            'callbackUrl': absolute_url_for('.update_avatar'),
            'callbackBody': "id=%d&key=$(key)" % user.id
        })
        user.background_uptoken = qiniu.generate_token(policy={
            'callbackUrl': absolute_url_for('.update_background'),
            'callbackBody': "id=%d&key=$(key)" % user.id
        })
    else:
        user.avatar_uptoken = ""
        user.background_uptoken = ""
