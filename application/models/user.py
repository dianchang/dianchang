# coding: utf-8
from datetime import datetime
from flask import g
from werkzeug.security import generate_password_hash, check_password_hash
from ._base import db
from ..utils.uploadsets import avatars
from ..utils.es import save_object_to_es, delete_object_from_es, search_objects_from_es


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

    def followed_by_user(self):
        """该用户是否被当前用户关注"""
        return g.user and g.user.followers.filter(FollowUser.follower_id == g.user.id).count() > 0

    @property
    def avatar_url(self):
        return avatars.url(self.avatar)

    def save_to_es(self):
        """保存此用户到elasticsearch"""
        return save_object_to_es('user', self.id, {
            'name': self.name,
            'desc': self.desc,
            'created_at': self.created_at
        })

    def delete_from_es(self):
        """从elasticsearch中删除此用户"""
        return delete_object_from_es('user', self.id)

    @staticmethod
    def query_from_es(q):
        """在elasticsearch中查询用户"""
        results = search_objects_from_es(doc_type='user', body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["name", "desc"]
                }
            },
            "highlight": {
                "fields": {
                    "name": {},
                    "desc": {}
                }
            }
        })

        result_users = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            user = User.query.get(id)
            if "highlight" in result:
                if "name" in result["highlight"]:
                    user.highlight_name = result["highlight"]["name"][0]
                if "desc" in result["highlight"]:
                    user.highlight_desc = result["highlight"]["desc"][0]
            result_users.append(user)

        return result_users

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
