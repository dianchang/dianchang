# coding: utf-8
from datetime import datetime
from ._base import db


class Answer(db.Model):
    """回答"""
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
    """对回答的评论"""
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


class UpvoteAnswer(db.Model):
    """赞同回答"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('upvoter',
                                                          lazy='dynamic',
                                                          order_by='desc(UpvoteAnswer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('upvoted_answers',
                                                      lazy='dynamic',
                                                      order_by='desc(UpvoteAnswer.created_at)'))

    def __repr__(self):
        return '<UpvoteAnswer %s>' % self.id


class DownvoteAnswer(db.Model):
    """反对回答"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('downvoter',
                                                          lazy='dynamic',
                                                          order_by='desc(DownvoteAnswer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('downvoted_answers',
                                                      lazy='dynamic',
                                                      order_by='desc(DownvoteAnswer.created_at)'))

    def __repr__(self):
        return '<DownvoteAnswer %s>' % self.id


class ThankAnswer(db.Model):
    """感谢回答"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('thankers',
                                                          lazy='dynamic',
                                                          order_by='desc(ThankAnswer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('thanked_answers',
                                                      lazy='dynamic',
                                                      order_by='desc(ThankAnswer.created_at)'))

    def __repr__(self):
        return '<ThankAnswer %s>' % self.id


class NohelpAnswer(db.Model):
    """回答没有帮助"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('nohelper',
                                                          lazy='dynamic',
                                                          order_by='desc(NohelpAnswer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('nohelped_answers',
                                                      lazy='dynamic',
                                                      order_by='desc(NohelpAnswer.created_at)'))

    def __repr__(self):
        return '<NohelpAnswer %s>' % self.id
