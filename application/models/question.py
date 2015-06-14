# coding: utf-8
from datetime import datetime
from flask import g
from ._base import db
from ..utils.es import save_object_to_es, delete_object_from_es, search_objects_from_es


class Question(db.Model):
    """问题"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    desc = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    anonymous = db.Column(db.Boolean, default=False)
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

    def followed_by_user(self):
        """该问题是否被用户关注"""
        return g.user and g.user.followed_questions.filter(FollowQuestion.question_id == self.id).count() > 0

    def __repr__(self):
        return '<Question %s>' % self.name


class QuestionTopic(db.Model):
    """问题所属的话题"""
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

    def __repr__(self):
        return '<FollowQuestion %s>' % self.id


class QuestionComment(db.Model):
    """对问题的评论"""
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
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 被邀请者
    user = db.relationship('User', foreign_keys=[user_id])

    inviter_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 邀请者
    inviter = db.relationship('User', foreign_keys=[inviter_id])

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('invites',
                                                              lazy='dynamic',
                                                              order_by='desc(InviteAnswer.created_at)'))
