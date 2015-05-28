# coding: utf-8
from datetime import datetime
from ._base import db
from ..utils.es import save_object_to_es, delete_object_from_es, search_objects_from_es


class Answer(db.Model):
    """回答"""
    id = db.Column(db.Integer, primary_key=True)
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

    def save_to_es(self):
        """保存此回答到elasticsearch"""
        return save_object_to_es('answer', self.id, {
            'content': self.content,
            'question_title': self.question.title,
            'created_at': self.created_at
        })

    def delete_from_es(self):
        """从elasticsearch中删除此回答"""
        return delete_object_from_es('answer', self.id)

    @staticmethod
    def query_from_es(q):
        """在elasticsearch中查询回答"""
        results = search_objects_from_es(doc_type='answer', body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["content", "question_title"]
                }
            },
            "highlight": {
                "fields": {
                    "content": {},
                    "question_title": {}
                }
            }
        })

        result_answers = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            answer = Answer.query.get(id)
            if "highlight" in result:
                if "content" in result["highlight"]:
                    answer.content = result["highlight"]["content"][0]
                if "question_title" in result["highlight"]:
                    answer.question.title = result["highlight"]["question_title"][0]
            result_answers.append(answer)
        return result_answers

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
