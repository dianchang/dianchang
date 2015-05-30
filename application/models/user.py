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
    is_active = db.Column(db.Boolean, default=False)
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
    def query_from_es(q, page=1, per_page=10):
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
            },
            "from": per_page * (page - 1),
            "size": per_page
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

        return result_users, results["hits"]["total"], results['took']

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('invitation_code',
                                              cascade="all, delete, delete-orphan",
                                              uselist=False),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User',
                             backref=db.backref('sended_invitation_codes',
                                                cascade="all, delete, delete-orphan",
                                                uselist=False),
                             foreign_keys=[sender_id])


class USER_FEED_KIND(object):
    """用户feed类型"""
    ASK_QUESTION = "gN02m2F"
    ANSWER_QUESTION = "J8AbTDT"
    FOLLOW_QUESTION = "4MYN2Ui"
    UPVOTE_ANSWER = "F9FqDKa"
    FOLLOW_TOPIC = "wa3PMng"
    FOLLOW_USER = "rDtV02F"


class UserFeed(db.Model):
    """用户feed"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('feeds',
                                              lazy='dynamic',
                                              order_by='desc(UserFeed.created_at)'),
                           foreign_keys=[user_id])

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic')

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer')

    following_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    following = db.relationship('User', foreign_keys=[following_id])


class NOTIFICATION_KIND(object):
    """用户消息类型"""
    UPVOTE_ANSWER = "Vu69o4V"
    THANK_ANSWER = "gIWr7dg"
    FOLLOW_YOU = "nK8BQ99"
    INVITE_TO_ANSWER = "WaO3vxo"
    ANSWER_QUESTION = "W4XBoRf"


class Notification(db.Model):
    """用户消息"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('notifications',
                                              lazy='dynamic',
                                              order_by='desc(UserFeed.created_at)'),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', foreign_keys=[sender_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer')


class HOME_FEED_KIND(object):
    """首页feed类型"""
    FOLLOWING_UPVOTE_ANSWER = "UdW38Gw"
    FOLLOWING_ASK_QUESTION = "groYn17"
    FOLLOWING_ANSWER_QUESTION = "wFyvyTI"
    ANSWER_FROM_FOLLOWED_TOPIC = "HVKEV0N"


class HomeFeed(db.Model):
    """登录用户的首页feed"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('home_feeds',
                                              lazy='dynamic',
                                              order_by='desc(UserFeed.created_at)'),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', foreign_keys=[sender_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer')


class COMPOSE_FEED_KIND(object):
    """撰写feed类型"""
    pass


class ComposeFeed(db.Model):
    """撰写feed"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('compose_feeds',
                                              lazy='dynamic',
                                              order_by='desc(UserFeed.created_at)'))

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')
