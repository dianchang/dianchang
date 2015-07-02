# coding: utf-8
from datetime import datetime
from ._base import db


class QUESTION_EDIT_KIND(object):
    CREATE = "5cu8iyb"
    ADD_TOPIC = "LRzz833"
    REMOVE_TOPIC = "5HnrfHj"
    UPDATE_TITLE = "PaNulbw"
    UPDATE_DESC = "RcTRjzz"


class TOPIC_EDIT_KIND(object):
    CREATE = "RVa9saF"
    UPDATE_AVATAR = "Z0YVIUM"
    UPDATE_NAME = "4Rhuxhl"
    UPDATE_WIKI = "dw8xA42"
    ADD_PARENT_TOPIC = "vim7OUT"
    REMOVE_PARENT_TOPIC = "fC3fNIl"
    ADD_CHILD_TOPIC = "D0qZIv7"
    REMOVE_CHILD_TOPIC = "tCsTnWa"
    ADD_SYNONYM = "E9Ob9il"
    REMOVE_SYNONYM = "hWv1VIC"


class PublicEditLog(db.Model):
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    kind = db.Column(db.String(50), nullable=False)
    before = db.Column(db.Text)
    before_id = db.Column(db.Integer)
    after = db.Column(db.Text)
    after_id = db.Column(db.Integer)
    compare = db.Column(db.String(500))
    original_name = db.Column(db.String(200))
    original_title = db.Column(db.String(200))
    original_desc = db.Column(db.Text())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',
                           backref=db.backref('edits',
                                              lazy='dynamic',
                                              order_by='desc(PublicEditLog.created_at), desc(PublicEditLog.id)'))

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question',
                               backref=db.backref('logs',
                                                  lazy='dynamic',
                                                  order_by='desc(PublicEditLog.created_at), desc(PublicEditLog.id)'))

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic', backref=db.backref('logs',
                                                        lazy='dynamic',
                                                        order_by='desc(PublicEditLog.created_at), desc(PublicEditLog.id)'))
