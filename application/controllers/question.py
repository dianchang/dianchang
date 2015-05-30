# coding: utf-8
from flask import Blueprint, render_template, redirect, url_for, request, g, abort, json, get_template_attribute
from ..forms import AddQuestionForm
from ..models import db, Question, Answer, Topic, QuestionTopic, FollowQuestion, QUESTION_EDIT_KIND, PublicEditLog, \
    UserTopicStatistics
from ..utils.permissions import UserPermission
from ..utils.helpers import generate_lcs_html

bp = Blueprint('question', __name__)


@bp.route('/question/add', methods=['GET', 'POST'])
@UserPermission()
def add():
    """添加话题"""
    form = AddQuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, desc=form.desc.data, user_id=g.user.id)
        # Create question log
        create_log = PublicEditLog(kind=QUESTION_EDIT_KIND.CREATE, user_id=g.user.id,
                                   original_title=question.title, original_desc=question.desc)
        question.logs.append(create_log)

        # 添加话题
        topics_id_list = request.form.getlist('topic')
        for topic_id in topics_id_list:
            topic = Topic.query.get(topic_id)
            if topic:
                question_topic = QuestionTopic(topic_id=topic_id)
                question.topics.append(question_topic)
                # Add topic log
                add_topic_log = PublicEditLog(kind=QUESTION_EDIT_KIND.ADD_TOPIC, after=topic.name,
                                              after_id=topic_id, user_id=g.user.id)
                question.logs.append(add_topic_log)

        db.session.add(question)
        db.session.commit()
        question.save_to_es()
        return redirect(url_for('.view', uid=question.id))
    return render_template('question/add.html', form=form)


@bp.route('/question/<int:uid>', methods=['GET', 'POST'])
def view(uid):
    question = Question.query.get_or_404(uid)
    if request.method == 'POST' and request.form.get('answer'):
        # 回答话题
        answer = Answer(question_id=uid, content=request.form.get('answer'), user_id=g.user.id)
        # 更新话题专精
        for topic in question.topics:
            UserTopicStatistics.add_answer_in_topic(g.user.id, topic.topic_id)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.view', uid=uid))
    return render_template('question/view.html', question=question)


@bp.route('/question/<int:uid>/add_topic', methods=['POST'])
@UserPermission()
def add_topic(uid):
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

    # 添加话题
    question_topic = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic.id,
        QuestionTopic.question_id == uid).first()
    if not question_topic:
        question_topic = QuestionTopic(topic_id=topic.id, question_id=uid)
        # Add toic log
        log = PublicEditLog(question_id=uid, user_id=g.user.id,
                            after=topic.name, after_id=topic.id,
                            kind=QUESTION_EDIT_KIND.ADD_TOPIC)
        db.session.add(log)
        db.session.add(question_topic)
        db.session.commit()

    # 更新话题专精
    answer = question.answers.filter(Answer.user_id == g.user.id).first()
    if answer:
        UserTopicStatistics.add_answer_in_topic(g.user.id, topic.id)
    answer_thankers_count = answer.thankers.count()
    if answer_thankers_count > 0:
        UserTopicStatistics.upvote_answer_in_topic(g.user.id, topic.id, answer_thankers_count)

    macro = get_template_attribute('macros/_topic.html', 'render_topic_wap')
    return json.dumps({'result': True,
                       'id': topic.id,
                       'html': macro(topic)})


@bp.route('/question/<int:uid>/remove_topic/<int:topic_id>', methods=['POST'])
@UserPermission()
def remove_topic(uid, topic_id):
    """将问题从话题中移除"""
    question = Question.query.get_or_404(uid)
    topic = Topic.query.get_or_404(topic_id)
    topic_questions = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic_id,
        QuestionTopic.question_id == uid)
    for topic_question in topic_questions:
        db.session.delete(topic_question)

    # Remove topic log
    log = PublicEditLog(question_id=uid, user_id=g.user.id,
                        before=topic.name, before_id=topic_id,
                        kind=QUESTION_EDIT_KIND.REMOVE_TOPIC)
    db.session.add(log)
    db.session.commit()

    # 更新话题专精
    answer = question.answers.filter(Answer.user_id == g.user.id).first()
    if answer:
        UserTopicStatistics.remove_answer_from_topic(g.user.id, topic.id)
    answer_thankers_count = answer.thankers.count()
    if answer_thankers_count > 0:
        UserTopicStatistics.cancel_upvote_answer_in_topic(g.user.id, topic.id, answer_thankers_count)
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


@bp.route('/question/<int:uid>/log')
def log(uid):
    question = Question.query.get_or_404(uid)
    return render_template('question/log.html', question=question)


@bp.route('/question/<int:uid>/update', methods=['POST'])
@UserPermission()
def update(uid):
    """通过Ajax更新问题的title和desc"""
    question = Question.query.get_or_404(uid)
    title = request.form.get('title', "")
    desc = request.form.get('desc', "")
    if title and title != question.title:
        # Update title log
        title_log = PublicEditLog(kind=QUESTION_EDIT_KIND.UPDATE_TITLE, before=question.title, after=title,
                                  user_id=g.user.id, compare=generate_lcs_html(question.title, title))
        question.logs.append(title_log)
        question.title = title
        # 更新es中的answer
        for answer in question.answers:
            answer.save_to_es()
    if desc != (question.desc or ""):
        # Desc log
        desc_log = PublicEditLog(kind=QUESTION_EDIT_KIND.UPDATE_DESC, before=question.desc, after=desc,
                                 user_id=g.user.id, compare=generate_lcs_html(question.desc, desc))
        question.logs.append(desc_log)
        question.desc = desc
    db.session.add(question)
    db.session.commit()
    # 更新es中的question
    question.save_to_es()
    return json.dumps({'result': True})
