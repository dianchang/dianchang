# coding: utf-8
from datetime import datetime
from flask import g, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from ._base import db
from ..utils.uploadsets import avatars, images
from ..utils.helpers import pinyin
from ..utils.es import save_object_to_es, delete_object_from_es, search_objects_from_es


class User(db.Model):
    """用户"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True)
    name_pinyin = db.Column(db.String(200))
    email = db.Column(db.String(50), unique=True)
    desc = db.Column(db.String(200), )
    avatar = db.Column(db.String(200), default='default.png')
    background = db.Column(db.String(200))
    password = db.Column(db.String(200))
    url_token = db.Column(db.String(100))
    location = db.Column(db.String(100))
    organization = db.Column(db.String(100))
    position = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    is_active = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    has_seleted_expert_topics = db.Column(db.Boolean, default=False)

    followers_count = db.Column(db.Integer, default=0)
    followings_count = db.Column(db.Integer, default=0)
    thanks_count = db.Column(db.Integer, default=0)
    questions_count = db.Column(db.Integer, default=0)
    answers_count = db.Column(db.Integer, default=0)

    def __setattr__(self, name, value):
        # Hash password when set it.
        if name == 'password':
            value = generate_password_hash(value)
        elif name == 'name':
            # 为name赋值时，自动设置其拼音
            super(User, self).__setattr__('name_pinyin', pinyin(value))
        super(User, self).__setattr__(name, value)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def followed_by_user(self):
        """该用户是否被当前用户关注"""
        return g.user and g.user.followers.filter(FollowUser.follower_id == g.user.id).count() > 0

    @property
    def profile_url(self):
        """用户个人主页url"""
        if self.url_token:
            return url_for('user.profile_with_url_token', url_token=self.url_token)
        else:
            return url_for('user.profile', uid=self.id)

    @property
    def avatar_url(self):
        """用户头像"""
        return avatars.url(self.avatar)

    @property
    def background_url(self):
        """背景图片"""
        return images.url(self.background) if self.background else None

    @property
    def random_answers(self, count=3):
        """随机回答"""
        from .answer import Answer

        return self.answers.filter(~Answer.hide).order_by(db.func.random()).limit(count)

    @property
    def expert_topics(self):
        """用户擅长话题

        当该用户未选择擅长话题时，返回score最高的话题；
        当已选择时，返回选择的擅长话题。
        """
        from .topic import UserTopicStatistics

        if self.has_seleted_expert_topics:
            return UserTopicStatistics.query.filter(UserTopicStatistics.user_id == self.id,
                                                    UserTopicStatistics.selected == True). \
                order_by(UserTopicStatistics.show_order.desc()).limit(8)
        else:
            return UserTopicStatistics.query.filter(UserTopicStatistics.user_id == self.id,
                                                    UserTopicStatistics.score != 0). \
                order_by(UserTopicStatistics.score.desc()).limit(8)

    def save_to_es(self):
        """保存此用户到elasticsearch"""
        return save_object_to_es('user', self.id, {
            'name': self.name,
            'name_pinyin': self.name_pinyin,
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
                    "fields": ["name", "name_pinyin", "desc"]
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
    ASK_QUESTION = "gN02m2F"  # 提问
    ANSWER_QUESTION = "J8AbTDT"  # 回答问题
    UPVOTE_ANSWER = "F9FqDKa"  # 赞同回答
    FOLLOW_QUESTION = "4MYN2Ui"  # 关注问题
    FOLLOW_TOPIC = "wa3PMng"  # 关注话题


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
    ANSWER_FROM_ASKED_QUESTION = "WFHhwmW"  # 回答了我提出的问题
    FOLLOW_ME = "nK8BQ99"  # 关注了我
    UPVOTE_ANSWER = "Vu69o4V"  # 赞同了我的回答
    THANK_ANSWER = "gIWr7dg"  # 感谢了我的回答
    COMMENT_ANSWER = "Fk3cIIH"  # 评论了我的回答
    REPLY_ANSWER_COMMENT = "ibWxLaC"  # 回复了我的评论
    LIKE_ANSWER_COMMENT = "1oY78lq"  # 赞了我的评论
    GOOD_ANSWER_FROM_FOLLOWED_TOPIC = "FAKeWIP"  # 关注的问题有了精彩的回答
    SYSTEM_NOTI = "ezjwiCu"  # 系统通知
    HIDE_ANSWER = "E0CzTCk"  # 回答被折叠


class Notification(db.Model):
    """用户消息"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('notifications',
                                              lazy='dynamic',
                                              order_by='desc(Notification.created_at)'),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', foreign_keys=[sender_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer')

    answer_comment_id = db.Column(db.Integer, db.ForeignKey('answer_comment.id'))
    answer_comment = db.relationship('AnswerComment')


class HOME_FEED_KIND(object):
    """首页feed类型"""
    FOLLOWING_UPVOTE_ANSWER = "UdW38Gw"  # 我关注的人赞同某个回答
    FOLLOWING_ASK_QUESTION = "groYn17"  # 我关注的人提出了问题
    FOLLOWING_ANSWER_QUESTION = "wFyvyTI"  # 我关注的人回答了问题
    WAITING_FOR_ANSWER_QUESTION_FROM_EXPERT_TOPIC = "6UEXA9U"  # 我擅长的话题的热门待回答问题
    GOOD_ANSWER_FROM_FOLLOWED_TOPIC = "HVKEV0N"  # 关注的话题下的精彩回答
    NEW_ANSWER_FROM_FOLLOWED_TOPIC = "VpuedTz"  # 关注的话题下的新人回答、刚出炉的回答


class HomeFeed(db.Model):
    """登录用户的首页feed"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('home_feeds',
                                              lazy='dynamic',
                                              order_by='desc(HomeFeed.created_at)'),
                           foreign_keys=[user_id])

    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', foreign_keys=[sender_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer')


class COMPOSE_FEED_KIND(object):
    """撰写feed类型"""
    WAITING_FOR_ANSWER_QUESTION_FROM_EXPERT_TOPIC = "v0KJCX3"  # 我擅长的话题下的待回答问题
    INVITE_TO_ANSWER = "kdcKRfi"  # 别人邀请我回答的问题
    WAITING_FOR_ANSWER_QUESTION_FROM_ALL = "4Q8wfm9"  # 全站热门的待回答问题
    WAITING_FOR_ANSWER_QUESTION_FROM_ANSWERD_TOPIC = "JlPzjXf"  # 我没有写进擅长话题，但我之前有过回答的话题下的热门待回答问题


class ComposeFeed(db.Model):
    """撰写feed"""
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('compose_feeds',
                                              lazy='dynamic',
                                              order_by='desc(ComposeFeed.created_at)'))

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')
