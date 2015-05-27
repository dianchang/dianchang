# coding: utf-8
from datetime import datetime
from ._base import db


class Question(db.Model):
    """问题"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    desc = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('questions',
                                                      lazy='dynamic',
                                                      order_by='desc(Question.created_at)'))

    def __repr__(self):
        return '<Question %s>' % self.name


class QuestionTopic(db.Model):
    """问题所属的话题"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('topics',
                                                              lazy='dynamic',
                                                              order_by='desc(QuestionTopic.created_at)'))

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
