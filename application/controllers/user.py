# coding: utf-8
from flask import Blueprint, render_template, url_for, json, g, request
from ..models import db, User, FollowUser, Notification, NOTIFICATION_KIND, UserFeed, USER_FEED_KIND
from ..utils.permissions import UserPermission

bp = Blueprint('user', __name__)


@bp.route('/people/<int:uid>')
def profile(uid):
    """用户主页"""
    user = User.query.get_or_404(uid)
    return render_template('user/profile.html', user=user)


@bp.route('/people/<string:url_token>')
def profile_with_url_token(url_token):
    """用户主页（使用url_token）"""
    user = User.query.filter(User.url_token == url_token).first_or_404()
    return render_template('user/profile.html', user=user)


@bp.route('/people/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注某用户"""
    user = User.query.get_or_404(uid)
    follow_user = g.user.followings.filter(FollowUser.following_id == uid)
    # 取消关注
    if follow_user.count() > 0:
        map(db.session.delete, follow_user)
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

            # FEED: 插入被关注者的NOTI
            noti = Notification(kind=NOTIFICATION_KIND.FOLLOW_ME, sender_id=g.user.id)
            user.notifications.append(noti)
            db.session.add(user)

            # FEED：插入本人的用户FEED
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
    return render_template('user/notifications.html')


@bp.route('/compose')
@UserPermission()
def compose():
    """撰写"""
    return render_template('user/compose.html')


@bp.route('/drafts')
def drafts():
    """我的草稿"""
    drafts = g.user.drafts
    return render_template('user/drafts.html', drafts=drafts)


@bp.route('/people/<int:uid>/achievements')
def achievements(uid):
    """成就"""
    user = User.query.get_or_404(uid)
    return render_template('user/achievements.html', user=user)


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
