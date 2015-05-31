# coding: utf-8
from datetime import datetime
from flask import Blueprint, render_template, request, json, get_template_attribute, g, redirect, url_for
from ..models import db, Topic, Question, QuestionTopic, FollowTopic, TopicWikiContributor, UserTopicStatistics, \
    PublicEditLog, TOPIC_EDIT_KIND
from ..utils.permissions import UserPermission
from ..utils.helpers import generate_lcs_html
from ..forms import AdminTopicForm, EditTopicWikiForm

bp = Blueprint('topic', __name__)


@bp.route('/topic/square')
def square():
    """话题广场"""
    return render_template('topic/square.html')


@bp.route('/topic/query', methods=['POST'])
@UserPermission()
def query():
    """查询话题"""
    q = request.form.get('q')
    question_id = request.form.get('question_id')  # 不包括此问题的话题（用于给问题添加话题）
    ancestor_topic_id = request.form.get('ancestor_topic_id')  # 不为此话题的子孙话题的话题（用于给话题添加子话题）
    descendant_topic_id = request.form.get('descendant_topic_id')  # 不为此话题的祖先话题的话题（用于给话题添加父话题）
    if q:
        topics = Topic.query.filter(Topic.name.like("%%%s%%" % q))
        if question_id:  # 排除该问题的所有话题
            topics = topics.filter(
                ~Topic.questions.any(QuestionTopic.question_id == question_id))
        if ancestor_topic_id:  # 排除该话题及其所有子话题
            ancestor_topic = Topic.query.get(ancestor_topic_id)
            if ancestor_topic:
                excluded_list = ancestor_topic.descendant_topics_id_list
                excluded_list.append(ancestor_topic_id)
                topics = topics.filter(Topic.id.notin_(excluded_list))
        if descendant_topic_id:  # 排除该话题及其所有父话题
            descendant_topic = Topic.query.get(descendant_topic_id)
            if descendant_topic:
                excluded_list = descendant_topic.ancestor_topics_id_list
                excluded_list.append(descendant_topic_id)
                topics = topics.filter(Topic.id.notin_(excluded_list))
        return json.dumps([{'name': topic.name,
                            'id': topic.id}
                           for topic in topics])
    else:
        return json.dumps({})


@bp.route('/topic/<int:uid>')
def view(uid):
    """话题详情页"""
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/view.html', topic=topic)


@bp.route('/topic/<int:uid>/rank')
def rank(uid):
    """话题榜单"""
    topic = Topic.query.get_or_404(uid)
    page = request.args.get('page', 1, int)
    experts = UserTopicStatistics.query. \
        filter(UserTopicStatistics.topic_id == uid,
               UserTopicStatistics.score != 0). \
        order_by(UserTopicStatistics.score.desc()).paginate(page, 15)
    return render_template('topic/rank.html', topic=topic, experts=experts)


@bp.route('/topic/<int:uid>/wiki')
def wiki(uid):
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/wiki.html', topic=topic)


@bp.route('/topic/<int:uid>/admin', methods=['POST', 'GET'])
@UserPermission()
def admin(uid):
    """话题管理"""
    topic = Topic.query.get_or_404(uid)
    form = AdminTopicForm()
    if form.validate_on_submit():
        # Update name log
        if topic.name != form.name.data:
            log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_NAME, user_id=g.user.id, topic_id=uid, before=topic.name,
                                after=form.name.data)
            db.session.add(log)
        # Update desc log
        if (topic.desc or "") != form.desc.data:
            log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_DESC, user_id=g.user.id, topic_id=uid,
                                before=topic.desc, after=form.desc.data,
                                compare=generate_lcs_html(topic.desc, form.desc.data))
            db.session.add(log)
        form.populate_obj(topic)
        db.session.add(topic)
        db.session.commit()
        topic.save_to_es()
        return redirect(url_for('.view', uid=uid))
    return render_template('topic/admin.html', topic=topic, form=form)


@bp.route('/topic/<int:uid>/add_parent_topic/<int:parent_topic_id>', methods=['POST'])
@UserPermission()
def add_parent_topic(uid, parent_topic_id):
    """添加直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic = Topic.query.get_or_404(parent_topic_id)
    topic.add_parent_topic(parent_topic_id)

    # Add parent topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=parent_topic.name, after_id=parent_topic_id)
    db.session.add(log)
    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'parent_topic_edit_wap')
    return json.dumps({
        'result': True,
        'html': macro(parent_topic)
    })


@bp.route('/topic/<int:uid>/remove_parent_topic/<int:parent_topic_id>', methods=['POST'])
@UserPermission()
def remove_parent_topic(uid, parent_topic_id):
    """删除直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic = Topic.query.get_or_404(parent_topic_id)
    topic.remove_parent_topic(parent_topic_id)

    # Remove parent topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        before=parent_topic.name, before_id=parent_topic_id)
    db.session.add(log)
    db.session.commit()

    return json.dumps({'result': True})


@bp.route('/topic/<int:uid>/add_child_topic/<int:child_topic_id>', methods=['POST'])
@UserPermission()
def add_child_topic(uid, child_topic_id):
    """添加直接子话题"""
    topic = Topic.query.get_or_404(uid)
    child_topic = Topic.query.get_or_404(child_topic_id)
    topic.add_child_topic(child_topic_id)

    # Add child topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_CHILD_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=child_topic.name, after_id=child_topic_id)
    db.session.add(log)
    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'child_topic_edit_wap')
    return json.dumps({
        'result': True,
        'html': macro(child_topic)
    })


@bp.route('/topic/<int:uid>/remove_child_topic/<int:child_topic_id>', methods=['POST'])
@UserPermission()
def remove_child_topic(uid, child_topic_id):
    """删除直接子话题"""
    topic = Topic.query.get_or_404(uid)
    child_topic = Topic.query.get_or_404(child_topic_id)
    topic.remove_child_topic(child_topic_id)

    # Remove child topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_CHILD_TOPIC, topic_id=uid, user_id=g.user.id,
                        before=child_topic.name, before_id=child_topic_id)
    db.session.add(log)
    db.session.commit()

    return json.dumps({'result': True})


@bp.route('/topic/get_by_name/<string:name>', methods=['POST'])
@UserPermission()
def get_by_name(name):
    """通过name获取话题，若不存在则创建"""
    topic = Topic.get_by_name(name, create_if_not_exist=True)
    return json.dumps({'id': topic.id, 'name': topic.name})


@bp.route('/topic/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注话题"""
    topic = Topic.query.get_or_404(uid)
    follow_topic = FollowTopic.query.filter(FollowTopic.topic_id == uid, FollowTopic.user_id == g.user.id)
    if follow_topic.count():
        map(db.session.delete, follow_topic)
        db.session.commit()
        return json.dumps({'result': True, 'followed': False, 'followers_count': topic.followers.count()})
    else:
        follow_topic = FollowTopic(topic_id=uid, user_id=g.user.id)
        db.session.add(follow_topic)
        db.session.commit()
        return json.dumps({'result': True, 'followed': True, 'followers_count': topic.followers.count()})


@bp.route('/topic/<int:uid>/edit_wiki', methods=['GET', 'POST'])
@UserPermission()
def edit_wiki(uid):
    """编辑话题Wiki"""
    topic = Topic.query.get_or_404(uid)
    form = EditTopicWikiForm(obj=topic)
    if form.validate_on_submit():
        topic.wiki = form.wiki.data
        db.session.add(topic)

        # 记录贡献者
        contributor = topic.wiki_contributors.filter(TopicWikiContributor.user_id == g.user.id).first()
        if contributor:
            contributor.count += 1
            contributor.last_contributed_at = datetime.now()
            db.session.add(contributor)
        else:
            contributor = TopicWikiContributor(topic_id=uid, user_id=g.user.id, count=1)
            db.session.add(contributor)
        db.session.commit()
        return redirect(url_for('.wiki', uid=uid))
    return render_template('topic/edit_wiki.html', topic=topic, form=form)


@bp.route('/topic/<int:uid>/questions')
def questions(uid):
    """话题下的全部问题"""
    topic = Topic.query.get_or_404(uid)
    page = request.args.get('page', 1, int)
    questions = topic.all_questions.paginate(page, 15)
    return render_template('topic/questions.html', topic=topic, questions=questions)


@bp.route('/topic/<int:uid>/waiting')
def waiting_for_answer(uid):
    """话题下等待回答的问题"""
    topic = Topic.query.get_or_404(uid)
    page = request.args.get('page', 1, int)
    waiting_for_answer_questions = topic.all_questions.filter(Question.answers_count == 0). \
        paginate(page, 15)
    return render_template('topic/waiting_for_answer.html', topic=topic,
                           waiting_for_answer_questions=waiting_for_answer_questions)


@bp.route('/topic/<int:uid>/logs')
def logs(uid):
    """话题日志"""
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/logs.html', topic=topic)
