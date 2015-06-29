# coding: utf-8
from datetime import datetime, date
from flask import Blueprint, render_template, url_for, json, g, request, get_template_attribute
from ..models import db, User, FollowUser, Notification, NOTIFICATION_KIND, UserFeed, USER_FEED_KIND, BlockUser, \
    ReportUser, UserUpvoteStatistic, ComposeFeed, COMPOSE_FEED_KIND, InviteAnswer
from ..utils.permissions import UserPermission

bp = Blueprint('user', __name__)


@bp.route('/people/<int:uid>')
def profile(uid):
    """用户主页"""
    user = User.query.get_or_404(uid)
    feeds = user.feeds.limit(15)
    preview = request.args.get('preview', type=int)
    preview = True if preview == 1 else False
    return render_template('user/profile.html', user=user, preview=preview, feeds=feeds)


@bp.route('/people/<string:url_token>')
def profile_with_url_token(url_token):
    """用户主页（使用url_token）"""
    user = User.query.filter(User.url_token == url_token).first_or_404()
    feeds = user.feeds.limit(15)
    preview = request.args.get('preview', type=int)
    preview = True if preview == 1 else False
    return render_template('user/profile.html', user=user, preview=preview, feeds=feeds)


@bp.route('/people/<int:uid>/follow', methods=['POST'])
@UserPermission()
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
        db.session.commit()
        return json.dumps({
            'result': True,
            'followed': False,
            'followers_count': user.followers.count()
        })
    else:
        # 关注
        if g.user.id != uid:
            follow_user = FollowUser(follower_id=g.user.id, following_id=uid)
            db.session.add(follow_user)

            g.user.followings_count += 1
            user.followers_count += 1
            db.session.add(g.user)
            db.session.add(user)

            # NOTI: 插入被关注者的 NOTI（需合并）
            noti = user.notifications.filter(
                Notification.kind == NOTIFICATION_KIND.FOLLOW_ME,
                Notification.unread,
                Notification.created_at_date == date.today()).first()
            if noti:
                # 若当天已经有人关注他，且该条消息未读，则进行消息合并
                noti.add_sender(g.user.id)
                db.session.add(noti)
            else:
                noti = Notification(kind=NOTIFICATION_KIND.FOLLOW_ME, senders_list=json.dumps([g.user.id]))
                user.notifications.append(noti)
                db.session.add(user)

            # USER FEED：插入本人的用户 FEED
            feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_USER, following_id=uid)
            g.user.feeds.append(feed)
            db.session.add(g.user)

            db.session.commit()

            return json.dumps({
                'result': True,
                'followed': True,
                'followers_count': user.followers.count()
            })
        else:
            return json.dumps({
                'result': False,
                'followed': False,
                'followers_count': user.followers.count()
            })


@bp.route('/people/<int:uid>/answers')
def answers(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/answers.html', user=user)


@bp.route('/people/<int:uid>/questions_and_answers')
def questions_and_answers(uid):
    """问答"""
    user = User.query.get_or_404(uid)
    feeds = user.feeds.filter(UserFeed.kind.in_([USER_FEED_KIND.ASK_QUESTION, USER_FEED_KIND.ANSWER_QUESTION]))
    return render_template('user/questions_and_answers.html', user=user, feeds=feeds)


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
    return render_template('user/followings.html', user=user)


@bp.route('/people/<int:uid>/followers')
def followers(uid):
    """关注者"""
    user = User.query.get_or_404(uid)
    return render_template('user/followers.html', user=user)


@bp.route('/notifications')
@UserPermission()
def notifications():
    """用户消息"""
    last_read_notifications_at = g.user.last_read_notifications_at
    g.user.last_read_notifications_at = datetime.now()
    for noti in g.user.notifications.filter(Notification.unread):
        noti.unread = False
        db.session.add(noti)
    db.session.commit()
    notifications = g.user.notifications.limit(20)
    return render_template('user/notifications.html', last_read_notifications_at=last_read_notifications_at,
                           notifications=notifications)


@bp.route('/compose')
@UserPermission()
def compose():
    """撰写"""
    feeds = g.user.compose_feeds.filter(~ComposeFeed.ignore)
    last_read_compose_feeds_at = g.user.last_read_compose_feeds_at
    g.user.last_read_compose_feeds_at = datetime.now()
    db.session.add(g.user)
    db.session.commit()
    return render_template('user/compose.html', feeds=feeds, last_read_compose_feeds_at=last_read_compose_feeds_at)


@bp.route('/compose_feed/<int:uid>/ignore', methods=['POST'])
@UserPermission()
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
    return json.dumps({
        'result': True
    })


@bp.route('/compose_feed/<int:uid>/recover', methods=['POST'])
@UserPermission()
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
    return json.dumps({
        'result': True
    })


@bp.route('/drafts')
def drafts():
    """我的草稿"""
    drafts = g.user.drafts
    return render_template('user/drafts.html', drafts=drafts)


@bp.route('/people/<int:uid>/achievements')
def achievements(uid):
    """成就"""
    user = User.query.get_or_404(uid)
    upvoters = user.upvoters.filter(UserUpvoteStatistic.upvotes_count != 0)
    upvoters_count = upvoters.count()
    return render_template('user/achievements.html', user=user, upvoters=upvoters, upvoters_count=upvoters_count)


@bp.route('/user/update_desc', methods=['POST'])
@UserPermission()
def update_desc():
    """更新描述"""
    desc = request.form.get('desc')
    g.user.desc = desc
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/user/update_meta_info', methods=['POST'])
@UserPermission()
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

    return json.dumps({
        'result': True
    })


@bp.route('/people/<int:uid>/block', methods=['POST'])
@UserPermission()
def block(uid):
    """屏蔽用户"""
    user = User.query.get_or_404(uid)
    blocked_user = g.user.blocks.filter(BlockUser.blocked_user_id == uid)
    # 取消屏蔽
    if blocked_user.count() > 0:
        map(db.session.delete, blocked_user)
        db.session.commit()
        return json.dumps({
            'result': True,
            'blocked': False
        })
    else:
        # 屏蔽
        if g.user.id != uid:
            blocked_user = BlockUser(user_id=g.user.id, blocked_user_id=uid)
            db.session.add(blocked_user)

            db.session.commit()
            return json.dumps({
                'result': True,
                'blocked': True
            })
        else:
            return json.dumps({
                'result': False,
                'blocked': False
            })


@bp.route('/people/<int:uid>/report', methods=['POST'])
@UserPermission()
def report(uid):
    """举报用户"""
    user = User.query.get_or_404(uid)
    if g.user.id != uid:
        reported_user = ReportUser(user_id=g.user.id, reported_user_id=uid)
        db.session.add(reported_user)

        db.session.commit()
        return json.dumps({
            'result': True
        })
    else:
        return json.dumps({
            'result': False
        })


@bp.route('/user/query', methods=['POST'])
@UserPermission()
def query():
    """查询用户"""
    q = request.form.get('q')
    exclude_id = request.form.get('exclude_id', type=int)
    users, total, took = User.query_from_es(q)
    results = []
    for user in users:
        if user.id != exclude_id:
            results.append({
                'id': user.id,
                'name': user.name
            })
    return json.dumps(results)


@bp.route('/user/followed_questions')
@UserPermission()
def followed_questions():
    """我关注的问题"""
    page = request.args.get('page', type=int, default=1)
    questions = g.user.followed_questions.paginate(page, 15)
    return render_template('user/followed_questions.html', questions=questions)


@bp.route('/user/<int:uid>/get_card', methods=['POST'])
def get_card(uid):
    """获取用于显示用户卡片的数据"""
    user = User.query.get_or_404(uid)
    macro = get_template_attribute('macros/_user.html', 'user_card')
    return json.dumps({
        'result': True,
        'html': macro(user)
    })


@bp.route('/user/get_message_notifications', methods=['POST'])
@UserPermission()
def get_message_notifications():
    """获取消息类通知"""
    notifications = g.user.notifications.filter(Notification.kind.in_([
        NOTIFICATION_KIND.ANSWER_FROM_ASKED_QUESTION,
        NOTIFICATION_KIND.COMMENT_ANSWER,
        NOTIFICATION_KIND.REPLY_ANSWER_COMMENT,
        NOTIFICATION_KIND.GOOD_ANSWER_FROM_FOLLOWED_TOPIC,
        NOTIFICATION_KIND.SYSTEM_NOTI,
        NOTIFICATION_KIND.HIDE_ANSWER
    ]))

    g.user.last_read_notifications_at = datetime.now()
    db.session.add(g.user)

    for noti in notifications:
        noti.unread = False
        db.session.add(noti)

    db.session.commit()

    macro = get_template_attribute('macros/_user.html', 'render_message_notifications')
    return json.dumps({
        'result': True,
        'html': macro(notifications.limit(20))
    })


@bp.route('/user/get_user_notifications', methods=['POST'])
@UserPermission()
def get_user_notifications():
    """获取用户类通知"""
    for noti in g.user.notifications.filter(Notification.kind == NOTIFICATION_KIND.FOLLOW_ME):
        noti.unread = False
        db.session.add(noti)

    g.user.last_read_notifications_at = datetime.now()
    db.session.add(g.user)

    db.session.commit()

    macro = get_template_attribute('macros/_user.html', 'render_user_notifications')
    return json.dumps({
        'result': True,
        'html': macro(g.user.followers.limit(20))
    })


@bp.route('/user/get_thanks_notifications', methods=['POST'])
@UserPermission()
def get_thanks_notifications():
    """获取感谢类通知"""
    notifications = g.user.notifications.filter(Notification.kind.in_([
        NOTIFICATION_KIND.UPVOTE_ANSWER,
        NOTIFICATION_KIND.THANK_ANSWER,
        NOTIFICATION_KIND.LIKE_ANSWER_COMMENT
    ]))

    g.user.last_read_notifications_at = datetime.now()
    db.session.add(g.user)

    for noti in notifications:
        noti.unread = False
        db.session.add(noti)

    db.session.commit()

    macro = get_template_attribute('macros/_user.html', 'render_thanks_notifications')
    return json.dumps({
        'result': True,
        'html': macro(notifications.limit(20))
    })
