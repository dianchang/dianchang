# coding: utf-8
from flask import Blueprint, render_template, redirect, url_for, request, g, abort, json, get_template_attribute
from ..forms import AddQuestionForm
from ..models import db, Question, Answer, Topic, QuestionTopic, FollowQuestion
from ..utils.permissions import UserPermission

bp = Blueprint('question', __name__)


@bp.route('/question/add', methods=['GET', 'POST'])
@UserPermission()
def add():
    """添加话题"""
    form = AddQuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, desc=form.desc.data, user_id=g.user.id)
        # 添加话题
        topics_id_list = request.form.getlist('topic')
        for topic_id in topics_id_list:
            topic = Topic.query.get(topic_id)
            if topic:
                question_topic = QuestionTopic(topic_id=topic_id)
                question.topics.append(question_topic)
        db.session.add(question)
        db.session.commit()
        question.save_to_es()
        return redirect(url_for('.view', uid=question.id))
    return render_template('question/add.html', form=form)


@bp.route('/question/<int:uid>', methods=['GET', 'POST'])
def view(uid):
    question = Question.query.get_or_404(uid)
    if request.method == 'POST' and request.form.get('answer'):
        answer = Answer(question_id=uid, content=request.form.get('answer'), user_id=g.user.id)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.view', uid=uid))
    return render_template('question/view.html', question=question)


@bp.route('/question/<int:uid>/add_to_topic', methods=['POST'])
@UserPermission()
def add_to_topic(uid):
    question = Question.query.get_or_404(uid)
    name = request.form.get('name')
    topic_id = request.form.get('topic_id')

    topic = None
    if name:
        topic = Topic.get_by_name(name, create_if_not_exist=True)
    elif topic_id:
        topic = Topic.query.get_or_404(topic_id)

    if not topic:
        abort(404)

    # 若该句集尚未收录此句子，则收录
    question_topic = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic.id,
        QuestionTopic.question_id == uid).first()
    if not question_topic:
        question_topic = QuestionTopic(topic_id=topic.id, question_id=uid)
        # log
        # log = PieceEditLog(piece_id=uid, user_id=g.user.id,
        #                    after=topic.title, after_id=topic.id,
        #                    kind=PIECE_EDIT_KIND.ADD_TO_COLLECTION)
        # db.session.add(log)
        db.session.add(question_topic)
        db.session.commit()
    macro = get_template_attribute('macros/_topic.html', 'render_topic_wap')
    return json.dumps({'result': True,
                       'id': topic.id,
                       'html': macro(topic)})


@bp.route('/question/<int:uid>/remove_from_topic/<int:topic_id>', methods=['POST'])
@UserPermission()
def remove_from_topic(uid, topic_id):
    """将问题从话题中移除"""
    question = Question.query.get_or_404(uid)
    topic = Topic.query.get_or_404(topic_id)
    topic_questions = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic_id,
        QuestionTopic.question_id == uid)
    for topic_question in topic_questions:
        db.session.delete(topic_question)
        # log
        # log = PieceEditLog(piece_id=uid, user_id=g.user.id,
        #                    before=collection.title, before_id=collection_id,
        #                    kind=PIECE_EDIT_KIND.REMOVE_FROM_COLLECTION)
        # db.session.add(log)
    db.session.commit()
    return json.dumps({'result': True})


@bp.route('/question/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注话题"""
    question = Question.query.get_or_404(uid)
    follow_question = FollowQuestion.query.filter(FollowQuestion.question_id == uid,
                                                  FollowQuestion.user_id == g.user.id)
    if follow_question.count():
        map(db.session.delete, follow_question)
        db.session.commit()
        return json.dumps({'result': True, 'followed': False, 'followers_count': question.followers.count()})
    else:
        follow_question = FollowQuestion(question_id=uid, user_id=g.user.id)
        db.session.add(follow_question)
        db.session.commit()
        return json.dumps({'result': True, 'followed': True, 'followers_count': question.followers.count()})
