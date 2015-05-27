# coding: utf-8
from flask import Blueprint, render_template, request, json
from ..models import db, Topic, Question, QuestionTopic
from ..utils.permissions import UserPermission
from ..forms import AdminTopicForm

bp = Blueprint('topic', __name__)


@bp.route('/topic/square')
def square():
    return render_template('topic/square.html')


@bp.route('/collection/query', methods=['POST'])
@UserPermission()
def query():
    q = request.form.get('q')
    question_id = request.form.get('question_id')
    if q:
        topics = Topic.query.filter(Topic.name.like("%%%s%%" % q))
        if question_id:
            topics = topics.filter(
                ~Topic.questions.any(QuestionTopic.question_id == question_id))
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
