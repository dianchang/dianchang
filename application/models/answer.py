# coding: utf-8
from datetime import datetime
from ._base import db
from ._helpers import save_object_to_es, delete_object_from_es, search_objects_from_es, get_pure_content


class Answer(db.Model):
    """回答"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    content_preview = db.Column(db.Text)
    content_preview_truncated = db.Column(db.Boolean, default=False)  # content_preview是否被截断
    content_preview_length = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    hide = db.Column(db.Boolean, default=False)
    anonymous = db.Column(db.Boolean, default=False)  # 匿名
    identity = db.Column(db.String(200))  # 显示身份
    topic_experience = db.Column(db.String(100))  # 用户在回答时采用的话题经验
    created_at = db.Column(db.DateTime, default=datetime.now)

    comments_count = db.Column(db.Integer, default=0)
    upvotes_count = db.Column(db.Integer, default=0)
    downvotes_count = db.Column(db.Integer, default=0)
    thanks_count = db.Column(db.Integer, default=0)
    nohelps_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('answers',
                                                              lazy='dynamic',
                                                              order_by='desc(Answer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('answers',
                                                      lazy='dynamic',
                                                      order_by='desc(Answer.created_at)'))

    def __setattr__(self, name, value):
        # 每当设置 content 时，更新 content_length 和 content_preview
        if name == 'content':
            pure_content = get_pure_content(value)
            if len(pure_content) > 100:
                content_preview = pure_content[:100].rstrip('.') + "..."
                content_preview_truncated = True
            else:
                content_preview = pure_content
                content_preview_truncated = False
            super(Answer, self).__setattr__('content_preview', content_preview)
            super(Answer, self).__setattr__('content_preview_truncated', content_preview_truncated)
        super(Answer, self).__setattr__(name, value)

    def calculate_score(self):
        """回答分值，体现该回答的精彩程度"""
        self.score = self.upvotes_count + self.thanks_count + self.comments_count \
                     - self.downvotes_count - self.nohelps_count

    def upvoted_by_user(self, user_id):
        """该回答被当前用户赞同"""
        return self.upvotes.filter(UpvoteAnswer.user_id == user_id).count() > 0

    def downvoted_by_user(self, user_id):
        """该回答被当前用户反对"""
        return self.downvotes.filter(DownvoteAnswer.user_id == user_id).count() > 0

    def thanked_by_user(self, user_id):
        """该回答被当前用户感谢"""
        return self.thanks.filter(ThankAnswer.user_id == user_id).count() > 0

    def nohelped_by_user(self, user_id):
        """该回答被当前用户标记为没有帮助"""
        return self.nohelps.filter(NohelpAnswer.user_id == user_id).count() > 0

    def save_to_es(self):
        """保存此回答到elasticsearch"""
        return save_object_to_es('answer', self.id, {
            'content_preview': self.content_preview,
            'question_title': self.question.title,
            'created_at': self.created_at
        })

    def delete_from_es(self):
        """从elasticsearch中删除此回答"""
        return delete_object_from_es('answer', self.id)

    @property
    def root_comments(self):
        return self.comments.filter(AnswerComment.parent_id == None)

    @staticmethod
    def query_from_es(q, page=1, per_page=10):
        """在elasticsearch中查询回答"""
        results = search_objects_from_es(doc_type='answer', body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": ["content_preview", "question_title"]
                }
            },
            "highlight": {
                "fields": {
                    "content_preview": {},
                    "question_title": {}
                }
            },
            "from": per_page * (page - 1),
            "size": per_page
        })

        result_answers = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            answer = Answer.query.get(id)
            if "highlight" in result:
                if "content_preview" in result["highlight"]:
                    answer.highlight_content_preview = result["highlight"]["content_preview"][0]
                if "question_title" in result["highlight"]:
                    answer.highlight_question_title = result["highlight"]["question_title"][0]
            result_answers.append(answer)

        return result_answers, results["hits"]["total"], results['took']

    def __repr__(self):
        return '<Answer %s>' % self.name


class AnswerDraft(db.Model):
    """回答草稿"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question', backref=db.backref('drafts',
                                                              lazy='dynamic',
                                                              order_by='desc(AnswerDraft.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('drafts',
                                                      lazy='dynamic',
                                                      order_by='desc(AnswerDraft.created_at)'))


class UpvoteAnswer(db.Model):
    """赞同回答"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('upvotes',
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
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('downvotes',
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
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('thanks',
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
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('nohelps',
                                                          lazy='dynamic',
                                                          order_by='desc(NohelpAnswer.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('nohelped_answers',
                                                      lazy='dynamic',
                                                      order_by='desc(NohelpAnswer.created_at)'))

    def __repr__(self):
        return '<NohelpAnswer %s>' % self.id


class AnswerComment(db.Model):
    """对回答的评论"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)

    likes_count = db.Column(db.Integer, default=0)

    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    answer = db.relationship('Answer', backref=db.backref('comments',
                                                          lazy='dynamic',
                                                          order_by='asc(AnswerComment.created_at)'))

    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
    question = db.relationship('Question')

    parent_id = db.Column(db.Integer, db.ForeignKey('answer_comment.id'))
    parent = db.relationship('AnswerComment', remote_side=[id], foreign_keys=[parent_id])

    root_id = db.Column(db.Integer, db.ForeignKey('answer_comment.id'))
    root = db.relationship('AnswerComment',
                           remote_side=[id],
                           backref=db.backref('sub_comments',
                                              lazy='dynamic',
                                              order_by='asc(AnswerComment.created_at)'),
                           foreign_keys=[root_id])

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('answer_comments',
                                                      lazy='dynamic',
                                                      order_by='desc(AnswerComment.created_at)'))

    def liked_by_user(self, user_id):
        """该评论是否被用户赞过"""
        return self.likes.filter(LikeAnswerComment.user_id == user_id).count() > 0

    def __repr__(self):
        return '<AnswerComment %s>' % self.id


class LikeAnswerComment(db.Model):
    """赞回答评论"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    comment_id = db.Column(db.Integer, db.ForeignKey('answer_comment.id'))
    comment = db.relationship('AnswerComment',
                              backref=db.backref('likes',
                                                 lazy='dynamic',
                                                 order_by='desc(LikeAnswerComment.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('liked_answer_comments',
                                                      lazy='dynamic',
                                                      order_by='desc(LikeAnswerComment.created_at)'))

    def __repr__(self):
        return '<LikeAnswerComment %s>' % self.id


class UserUpvoteStatistic(db.Model):
    """用户赞同数据统计"""
    __bind_key__ = 'dc'
    id = db.Column(db.Integer, primary_key=True)
    upvotes_count = db.Column(db.Integer, default=0)
    upvoter_followings_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('upvoters',
                                                      lazy='dynamic',
                                                      order_by='desc(UserUpvoteStatistic.score)'),
                           foreign_keys=[user_id])

    upvoter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    upvoter = db.relationship('User', foreign_keys=[upvoter_id])

    def update(self):
        """更新 upvoter_followings_count 和 score"""
        self.score = self.upvotes_count * 0.4 + self.upvoter_followings_count * 0.6
