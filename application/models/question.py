# coding: utf-8
from datetime import datetime
from ._base import db
from ._helpers import save_object_to_es, delete_object_from_es, search_objects_from_es


class Question(db.Model):
    """问题"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    desc = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    anonymous = db.Column(db.Boolean, default=False)  # 匿名提问
    created_at = db.Column(db.DateTime, default=datetime.now)

    answers_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    followers_count = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('questions',
                                                      lazy='dynamic',
                                                      order_by='desc(Question.created_at)'))

    def save_to_es(self):
        """保存此问题到elasticsearch"""
        return save_object_to_es('question', self.id, {
            'title': self.title,
            'desc': self.desc,
            'created_at': self.created_at
        })

    def delete_from_es(self):
        """从elasticsearch中删除此问题"""
        return delete_object_from_es('question', self.id)

    @staticmethod
    def query_from_es(q, only_title=False, page=1, per_page=10):
        """在elasticsearch中查询话题"""
        if only_title:
            query_fields = ["title"]
        else:
            query_fields = ["title", "desc"]

        results = search_objects_from_es(doc_type='question', body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": query_fields
                }
            },
            "highlight": {
                "fields": {
                    "title": {},
                    "desc": {}
                }
            },
            "from": per_page * (page - 1),
            "size": per_page
        })

        result_questions = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            question = Question.query.get(id)
            if "highlight" in result:
                if "title" in result["highlight"]:
                    question.highlight_title = result["highlight"]["title"][0]
                if "desc" in result["highlight"]:
                    question.highlight_desc = result["highlight"]["desc"][0]
            result_questions.append(question)

        return result_questions, results["hits"]["total"], results['took']

    @property
    def relevant_questions(self):
        """在elasticsearch中查询相关话题"""
        results = search_objects_from_es(doc_type='question', body={
            "query": {
                "match": {
                    "title": self.title
                }
            },
            "filter": {
                "not": {
                    "term": {
                        "_id": self.id
                    }
                }
            },
            "min_score": 0.05
        })

        result_questions = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            question = Question.query.get(id)
            result_questions.append(question)

        return result_questions

    def followed_by_user(self, user_id):
        """该问题是否被用户关注"""
        return FollowQuestion.query.filter(FollowQuestion.question_id == self.id,
                                           FollowQuestion.user_id == user_id).count() > 0

    def answered_by_user(self, user_id):
        """该问题是否被用户回答"""
        from .answer import Answer

        return Answer.query.filter(Answer.user_id == user_id,
                                   Answer.question_id == self.id).count() > 0

    def __repr__(self):
        return '<Question %s>' % self.name


class QuestionTopic(db.Model):
    """问题所属的话题"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('topics',
                                                              lazy='dynamic',
                                                              order_by='asc(QuestionTopic.created_at)'))

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic', backref=db.backref('questions',
                                                        lazy='dynamic',
                                                        order_by='desc(QuestionTopic.created_at)'))

    def __repr__(self):
        return '<QuestionTopic %s>' % self.id


class FollowQuestion(db.Model):
    """关注问题"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('followers',
                                                              lazy='dynamic',
                                                              order_by='desc(FollowQuestion.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('followed_questions',
                                                      lazy='dynamic',
                                                      order_by='desc(FollowQuestion.created_at)'))

    def last_followed_in_that_day(self, user_id):
        """该问题是否为当天最晚关注的问题"""
        day = self.created_at.date()
        last_followed_question = FollowQuestion.query. \
            filter(FollowQuestion.user_id == user_id,
                   db.func.date(FollowQuestion.created_at) == day). \
            order_by(FollowQuestion.created_at.desc()).first()
        return last_followed_question and last_followed_question.id == self.id

    def __repr__(self):
        return '<FollowQuestion %s>' % self.id


class QuestionComment(db.Model):
    """对问题的评论"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('comments',
                                                              lazy='dynamic',
                                                              order_by='desc(QuestionComment.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('question_comments',
                                                      lazy='dynamic',
                                                      order_by='desc(QuestionComment.created_at)'))

    def __repr__(self):
        return '<QuestionComment %s>' % self.id


class InviteAnswer(db.Model):
    """邀请回答"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    ignore = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 被邀请者
    user = db.relationship('User', foreign_keys=[user_id])

    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 邀请者
    inviter = db.relationship('User', foreign_keys=[inviter_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('invites',
                                                              lazy='dynamic',
                                                              order_by='desc(InviteAnswer.created_at)'))


class RejectInvitationFromUser(db.Model):
    """拒绝来自某用户的邀请"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reject_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 被拒绝用户


class RejectInvitationFromTopic(db.Model):
    """拒绝某话题下的邀请"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))


class NotGoodAtTopic(db.Model):
    """不擅长某话题

    即该话题下的问题不会出现在撰写页。
    """
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
