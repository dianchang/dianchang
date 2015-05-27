# coding: utf-8
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from ._base import db
from ..utils.uploadsets import avatars


class User(db.Model):
    """用户"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(50), unique=True)
    desc = db.Column(db.String(200), )
    avatar = db.Column(db.String(200), default='default.png')
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)
    organization = db.Column(db.String(100))
    city = db.Column(db.String(100))
    position = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    followers_count = db.Column(db.Integer, default=0)
    followings_count = db.Column(db.Integer, default=0)
    thanks_count = db.Column(db.Integer, default=0)
    questions_count = db.Column(db.Integer, default=0)
    answers_count = db.Column(db.Integer, default=0)

    def __setattr__(self, name, value):
        # Hash password when set it.
        if name == 'password':
            value = generate_password_hash(value)
        super(User, self).__setattr__(name, value)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def avatar_url(self):
        return avatars.url(self.avatar)

    def __repr__(self):
        return '<User %s>' % self.name


class FollowUser(db.Model):
    """关注用户"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    follower = db.relationship('User', backref=db.backref('followings',
                                                          lazy='dynamic',
                                                          order_by='desc(FollowUser.created_at)'),
                               foreign_keys=[follower_id])

    following_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    following = db.relationship('User', backref=db.backref('followers',
                                                           lazy='dynamic',
                                                           order_by='desc(FollowUser.created_at)'),
                                foreign_keys=[following_id])

    def __repr__(self):
        return '<FollowUser %s>' % self.id


class InvitationCode(db.Model):
    """邀请码"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(200))
    email = db.Column(db.String(100))
    used = db.Column(db.Boolean, default=False)
    sended_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 当用户使用此邀请码注册后，填充user_id字段
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=None)
    user = db.relationship('User',
                           backref=db.backref('invitation_code',
                                              cascade="all, delete, delete-orphan",
                                              uselist=False),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), default=None)
    sender = db.relationship('User',
                             backref=db.backref('sended_invitation_codes',
                                                cascade="all, delete, delete-orphan",
                                                uselist=False),
                             foreign_keys=[sender_id])
