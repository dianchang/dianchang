# coding: utf-8
from flask import Blueprint, render_template, request, json
from ..models import Topic, Question, QuestionTopic
from ..utils.permissions import UserPermission

bp = Blueprint('topic', __name__)


@bp.route('/topic/square')
def square():
    return render_template('topic/square.html')


@bp.route('/collection/query', methods=['POST'])
@UserPermission()
def query():
    q = request.form.get('q')
    question_id = request.form.get('piece_id')
    if q:
        topics = Topic.query.filter(Topic.name.like("%%%s%%" % q))
        if question_id:
            topics = topics.filter(
                ~Topic.pieces.any(QuestionTopic.question_id == question_id))
        return json.dumps([{'name': topic.name,
                            'id': topic.id}
                           for topic in topics])
    else:
        return json.dumps({})
