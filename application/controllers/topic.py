# coding: utf-8
from flask import Blueprint, render_template, request, json, get_template_attribute
from ..models import db, Topic, Question, QuestionTopic
from ..utils.permissions import UserPermission
from ..forms import AdminTopicForm

bp = Blueprint('topic', __name__)


@bp.route('/topic/square')
def square():
    return render_template('topic/square.html')


@bp.route('/topic/query', methods=['POST'])
@UserPermission()
def query():
    q = request.form.get('q')
    question_id = request.form.get('question_id')  # 不包括此问题的话题（用于给问题添加话题）
    ancestor_topic_id = request.form.get('ancestor_topic_id')  # 不为此话题的子孙话题的话题（用于给话题添加子话题）
    descendant_topic_id = request.form.get('descendant_topic_id')  # 不为此话题的祖先话题的话题（用于给话题添加父话题）
    if q:
        topics = Topic.query.filter(Topic.name.like("%%%s%%" % q))
        if question_id:
            topics = topics.filter(
                ~Topic.questions.any(QuestionTopic.question_id == question_id))
        if ancestor_topic_id:
            ancestor_topic = Topic.query.get(ancestor_topic_id)
            if ancestor_topic:
                topics = topics.filter(Topic.id.notin_(ancestor_topic.descendant_topics_id_list))
        if descendant_topic_id:
            descendant_topic = Topic.query.get(descendant_topic_id)
            if descendant_topic:
                topics = topics.filter(Topic.id.notin_(descendant_topic.ancestor_topics_id_list))
        return json.dumps([{'name': topic.name,
                            'id': topic.id}
                           for topic in topics])
    else:
        return json.dumps({})


@bp.route('/topic/<int:uid>')
def view(uid):
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/view.html', topic=topic)


@bp.route('/topic/<int:uid>/rank')
def rank(uid):
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/rank.html', topic=topic)


@bp.route('/topic/<int:uid>/wiki')
def wiki(uid):
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/wiki.html', topic=topic)


@bp.route('/topic/<int:uid>/admin', methods=['POST', 'GET'])
def admin(uid):
    """话题管理"""
    topic = Topic.query.get_or_404(uid)
    form = AdminTopicForm()
    if form.validate_on_submit():
        form.populate_obj(topic)
        db.session.add(topic)
        db.session.commit()
    return render_template('topic/admin.html', topic=topic, form=form)


@bp.route('/topic/<int:uid>/add_parent_topic/<int:parent_topic_id>', methods=['GET', 'POST'])
def add_parent_topic(uid, parent_topic_id):
    """添加直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic = Topic.query.get_or_404(parent_topic_id)
    topic.add_parent_topic(parent_topic_id)
    macro = get_template_attribute('macros/_topic.html', 'parent_topic_edit_wap')

    return json.dumps({
        'result': True,
        'html': macro(parent_topic)
    })


@bp.route('/topic/<int:uid>/remove_parent_topic/<int:parent_topic_id>', methods=['POST'])
def remove_parent_topic(uid, parent_topic_id):
    """删除直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic = Topic.query.get_or_404(parent_topic_id)
    topic.remove_parent_topic(parent_topic_id)
    return json.dumps({'result': True})
