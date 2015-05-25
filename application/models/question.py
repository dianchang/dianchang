# coding: utf-8
from datetime import datetime
from ._base import db


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    desc = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<Topic %s>' % self.name


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    clicks = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return '<Question %s>' % self.name


class QuestionTopic(db.Model):
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


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('answers',
                                                              lazy='dynamic',
                                                              order_by='desc(Answer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('answers',
                                                      lazy='dynamic',
                                                      order_by='desc(Answer.created_at)'))

    def __repr__(self):
        return '<Answer %s>' % self.name


class AnswerComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('comments',
                                                          lazy='dynamic',
                                                          order_by='desc(AnswerComment.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('answer_comments',
                                                      lazy='dynamic',
                                                      order_by='desc(AnswerComment.created_at)'))

    def __repr__(self):
        return '<AnswerComment %s>' % self.id
