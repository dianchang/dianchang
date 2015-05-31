# coding: utf-8
from datetime import datetime
from flask import g
from ._base import db
from ..utils.uploadsets import topic_avatars
from ..utils.es import save_object_to_es, delete_object_from_es, search_objects_from_es


class Topic(db.Model):
    """话题"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    desc = db.Column(db.Text)
    wiki = db.Column(db.Text(4294967295))
    avatar = db.Column(db.String(200), default='default.png')
    clicks = db.Column(db.Integer, default=0)
    locked = db.Column(db.Boolean, default=False)  # 话题锁定
    created_at = db.Column(db.DateTime, default=datetime.now)

    @property
    def avatar_url(self):
        """话题图像"""
        return topic_avatars.url(self.avatar)

    def followed_by_user(self):
        """此话题是否被用户关注"""
        return g.user and g.user.followed_topics.filter(FollowTopic.topic_id == self.id).count() > 0

    def save_to_es(self):
        """保存此话题到elasticsearch"""
        return save_object_to_es('topic', self.id, {
            'name': self.name,
            'created_at': self.created_at
        })

    def delete_from_es(self):
        """从elasticsearch中删除此话题"""
        return delete_object_from_es('topic', self.id)

    @staticmethod
    def query_from_es(q, page=1, per_page=10):
        """在elasticsearch中查询话题"""
        results = search_objects_from_es(doc_type='topic', body={
            "query": {
                "match": {
                    "name": q
                }
            },
            "highlight": {
                "fields": {
                    "name": {}
                }
            },
            "from": per_page * (page - 1),
            "size": per_page
        })

        result_topics = []

        for result in results["hits"]["hits"]:
            id = result["_id"]
            topic = Topic.query.get(id)
            if "highlight" in result:
                if "name" in result["highlight"]:
                    topic.highlight_name = result["highlight"]["name"][0]
            result_topics.append(topic)

        return result_topics, results["hits"]["total"], results['took']

    @staticmethod
    def get_by_name(name, create_if_not_exist=False):
        """通过name获取句集"""
        from .log import PublicEditLog, TOPIC_EDIT_KIND

        name = name or ""
        name = name.strip()
        if name:
            # 若不存在该name的句集，则创建
            topic = Topic.query.filter(Topic.name == name).first()
            if not topic and create_if_not_exist:
                topic = Topic(name=name)
                db.session.add(topic)
                db.session.commit()

                # Create topic log
                log = PublicEditLog(kind=TOPIC_EDIT_KIND.CREATE, user_id=g.user.id, after=name, after_id=topic.id,
                                    original_name=topic.name)
                topic.logs.append(log)
                db.session.add(topic)

                # Add topic closure
                topic_closure = TopicClosure(ancestor_id=topic.id, descendant_id=topic.id, path_length=0)
                db.session.add(topic_closure)
                db.session.commit()
            return topic
        else:
            return None

    @property
    def all_questions(self):
        """该话题下的所有问题（包括子话题的问题）"""
        from .question import QuestionTopic, Question

        topics_id_list = self.descendant_topics_id_list
        topics_id_list.append(self.id)
        return Question.query.filter(Question.topics.any(QuestionTopic.topic_id.in_(topics_id_list)))

    @property
    def parent_topics(self):
        """直接父话题"""
        parent_topics_id_list = db.session.query(TopicClosure.ancestor_id). \
            filter(TopicClosure.descendant_id == self.id,
                   TopicClosure.ancestor_id != self.id,
                   TopicClosure.path_length == 1). \
            all()
        parent_topics_id_list = [item.ancestor_id for item in parent_topics_id_list]
        return Topic.query.filter(Topic.id.in_(parent_topics_id_list))

    @property
    def ancestor_topics_id_list(self):
        """祖先话题id列表"""
        ancestor_topics_id_list = db.session.query(TopicClosure.ancestor_id). \
            filter(TopicClosure.descendant_id == self.id,
                   TopicClosure.ancestor_id != self.id). \
            all()
        return [item.ancestor_id for item in ancestor_topics_id_list]

    @property
    def ancestor_topics(self):
        """祖先话题"""
        return Topic.query.filter(Topic.id.in_(self.ancestor_topics_id_list))

    @property
    def child_topics(self):
        """直接子话题"""
        sub_topics_id_list = db.session.query(TopicClosure.descendant_id). \
            filter(TopicClosure.ancestor_id == self.id,
                   TopicClosure.descendant_id != self.id,
                   TopicClosure.path_length == 1). \
            all()
        sub_topics_id_list = [item.descendant_id for item in sub_topics_id_list]
        return Topic.query.filter(Topic.id.in_(sub_topics_id_list))

    @property
    def descendant_topics_id_list(self):
        """子孙话题id列表"""
        descendant_topics_id_list = db.session.query(TopicClosure.descendant_id). \
            filter(TopicClosure.ancestor_id == self.id,
                   TopicClosure.descendant_id != self.id). \
            all()
        return [item.descendant_id for item in descendant_topics_id_list]

    @property
    def descendant_topics(self):
        """子孙话题"""
        return Topic.query.filter(Topic.id.in_(self.descendant_topics_id_list))

    def add_parent_topic(self, parent_topic_id):
        """添加直接父话题"""
        for ancestor_topic in TopicClosure.query.filter(TopicClosure.descendant_id == parent_topic_id):
            for descendant_topic in TopicClosure.query.filter(TopicClosure.ancestor_id == self.id):
                new_closure = TopicClosure(ancestor_id=ancestor_topic.ancestor_id,
                                           descendant_id=descendant_topic.descendant_id,
                                           path_length=ancestor_topic.path_length + descendant_topic.path_length + 1)
                db.session.add(new_closure)
        db.session.commit()

    def remove_parent_topic(self, parent_topic_id):
        """删除直接父话题"""
        for ancestor_topic in TopicClosure.query.filter(TopicClosure.descendant_id == parent_topic_id):
            for descendant_topic in TopicClosure.query.filter(TopicClosure.ancestor_id == self.id):
                closure = TopicClosure.query.filter(TopicClosure.ancestor_id == ancestor_topic.ancestor_id,
                                                    TopicClosure.descendant_id == descendant_topic.descendant_id)
                map(db.session.delete, closure)
        db.session.commit()

    def add_child_topic(self, child_topic_id):
        """添加直接子话题"""
        for ancestor_topic in TopicClosure.query.filter(TopicClosure.descendant_id == self.id):
            for descendant_topic in TopicClosure.query.filter(TopicClosure.ancestor_id == child_topic_id):
                new_closure = TopicClosure(ancestor_id=ancestor_topic.ancestor_id,
                                           descendant_id=descendant_topic.descendant_id,
                                           path_length=ancestor_topic.path_length + descendant_topic.path_length + 1)
                db.session.add(new_closure)
        db.session.commit()

    def remove_child_topic(self, child_topic_id):
        """删除直接子话题"""
        for ancestor_topic in TopicClosure.query.filter(TopicClosure.descendant_id == self.id):
            for descendant_topic in TopicClosure.query.filter(TopicClosure.ancestor_id == child_topic_id):
                closure = TopicClosure.query.filter(TopicClosure.ancestor_id == ancestor_topic.ancestor_id,
                                                    TopicClosure.descendant_id == descendant_topic.descendant_id)
                map(db.session.delete, closure)
        db.session.commit()

    def __repr__(self):
        return '<Topic %s>' % self.name


class TopicClosure(db.Model):
    """话题的closure table"""
    id = db.Column(db.Integer, primary_key=True)
    ancestor_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    descendant_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    path_length = db.Column(db.Integer)

    def __repr__(self):
        return '<TopicClosure %d-%d>' % (self.ancestor_id, self.descendant_id)


class FollowTopic(db.Model):
    """关注话题"""
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic', backref=db.backref('followers',
                                                        lazy='dynamic',
                                                        order_by='desc(FollowTopic.created_at)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('followed_topics',
                                                      lazy='dynamic',
                                                      order_by='desc(FollowTopic.created_at)'))

    def __repr__(self):
        return '<FollowQuestion %s>' % self.id


class TopicWikiContributor(db.Model):
    """话题Wiki贡献者"""
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)
    last_contributed_at = db.Column(db.DateTime, default=datetime.now)
    created_at = db.Column(db.DateTime, default=datetime.now)

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic', backref=db.backref('wiki_contributors',
                                                        lazy='dynamic',
                                                        order_by='desc(TopicWikiContributor.count)'))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref=db.backref('contributed_topics',
                                                      lazy='dynamic',
                                                      order_by='desc(TopicWikiContributor.count)'))


class UserTopicStatistics(db.Model):
    """话题统计：用于分析某用户对某话题的擅长程度"""
    id = db.Column(db.Integer, primary_key=True)
    upvotes_count = db.Column(db.Integer, default=0)
    answers_count = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)
    show_order = db.Column(db.Integer, default=0)
    selected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    topic = db.relationship('Topic')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')

    @staticmethod
    def add_answer_in_topic(user_id, topic_id):
        """在某话题下回答"""
        topic_expert = UserTopicStatistics.query.filter(
            UserTopicStatistics.topic_id == topic_id,
            UserTopicStatistics.user_id == user_id).first()
        if topic_expert:
            topic_expert.answers_count += 1
        else:
            topic_expert = UserTopicStatistics(topic_id=topic_id, user_id=user_id, answers_count=1, upvotes_count=0)
        topic_expert.calculate_score()
        db.session.add(topic_expert)
        db.session.commit()

    @staticmethod
    def remove_answer_from_topic(user_id, topic_id):
        """从某话题中移除回答"""
        topic_expert = UserTopicStatistics.query.filter(UserTopicStatistics.topic_id == topic_id,
                                                        UserTopicStatistics.user_id == user_id).first()
        if topic_expert:
            if topic_expert.answers_count > 0:
                topic_expert.answers_count -= 1
            else:
                topic_expert.answers_count = 0
        else:
            topic_expert = UserTopicStatistics(topic_id=topic_id, user_id=user_id, answers_count=0, upvotes_count=0)
        topic_expert.calculate_score()
        db.session.add(topic_expert)
        db.session.commit()

    @staticmethod
    def upvote_answer_in_topic(user_id, topic_id, count=1):
        """感谢某话题下的回答"""
        topic_expert = UserTopicStatistics.query.filter(UserTopicStatistics.topic_id == topic_id,
                                                        UserTopicStatistics.user_id == user_id).first()
        if topic_expert:
            topic_expert.upvotes_count += count
        else:
            topic_expert = UserTopicStatistics(topic_id=topic_id, user_id=user_id, upvotes_count=count, answers_count=0)
        topic_expert.calculate_score()
        db.session.add(topic_expert)
        db.session.commit()

    @staticmethod
    def cancel_upvote_answer_in_topic(user_id, topic_id, count=1):
        """取消感谢某话题下的回答"""
        topic_expert = UserTopicStatistics.query.filter(UserTopicStatistics.topic_id == topic_id,
                                                        UserTopicStatistics.user_id == user_id).first()
        if topic_expert:
            if topic_expert.upvotes_count >= count:
                topic_expert.upvotes_count -= count
            else:
                topic_expert.upvotes_count = 0
        else:
            topic_expert = UserTopicStatistics(topic_id=topic_id, user_id=user_id, answers_count=0, upvotes_count=0)
        topic_expert.calculate_score()
        db.session.add(topic_expert)
        db.session.commit()

    def calculate_score(self):
        """计算擅长度"""
        self.score = self.answers_count + self.upvotes_count
