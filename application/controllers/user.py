# coding: utf-8
from flask import Blueprint, render_template, url_for, json, g
from ..models import db, User, FollowUser
from ..utils.permissions import UserPermission

bp = Blueprint('user', __name__)


@bp.route('/people/<int:uid>')
def profile(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/profile.html', user=user)


@bp.route('/people/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注某用户"""
    user = User.query.get_or_404(uid)
    follow_user = g.user.followings.filter(FollowUser.following_id == uid)
    if follow_user.count() > 0:
        map(db.session.delete, follow_user)
        db.session.commit()
        return json.dumps({
            'result': True,
            'followed': False,
            'followers_count': user.followers.count()
        })
    else:
        follow_user = FollowUser(follower_id=g.user.id, following_id=uid)
        db.session.add(follow_user)
        db.session.commit()
        return json.dumps({
            'result': True,
            'followed': True,
            'followers_count': user.followers.count()
        })


@bp.route('/user/<int:uid>/answers')
def answers(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/answers.html', user=user)
    pass


@bp.route('/user/<int:uid>/questions')
def questions(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/questions.html', user=user)


@bp.route('/user/<int:uid>/collects')
def collects(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/collects.html', user=user)


@bp.route('/user/<int:uid>/edits')
def edits(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/edits.html', user=user)


@bp.route('/user/<int:uid>/followings')
def followings(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/followings.html', user=user)


@bp.route('/user/<int:uid>/followers')
def followers(uid):
    user = User.query.get_or_404(uid)
    return render_template('user/followers.html', user=user)
