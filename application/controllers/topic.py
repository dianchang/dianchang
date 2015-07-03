# coding: utf-8
from datetime import datetime
from flask import Blueprint, render_template, request, json, get_template_attribute, g, redirect, url_for
from ..models import db, Topic, Question, QuestionTopic, FollowTopic, TopicWikiContributor, UserTopicStatistic, \
    PublicEditLog, TOPIC_EDIT_KIND, Answer, TopicSynonym, UserFeed, USER_FEED_KIND, ApplyTopicDeletion
from ..utils.permissions import UserPermission
from ..utils.helpers import generate_lcs_html, absolute_url_for
from ..utils.uploadsets import process_topic_avatar, topic_avatars
from ..utils._qiniu import qiniu
from ..forms import AdminTopicForm

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
                            'id': topic.id,
                            'followers_count': topic.followers_count}
                           for topic in topics])
    else:
        return json.dumps({})


@bp.route('/topic/<int:uid>')
def view(uid):
    """话题详情页"""
    topic = Topic.query.get_or_404(uid)
    page = request.args.get('page', 1, int)
    answers = topic.all_answers.order_by(Answer.score.desc()).paginate(page, 15)
    return render_template('topic/view.html', topic=topic, answers=answers)


@bp.route('/topic/<int:uid>/rank')
def rank(uid):
    """话题榜单"""
    topic = Topic.query.get_or_404(uid)
    page = request.args.get('page', 1, int)
    experts = UserTopicStatistic.query. \
        filter(UserTopicStatistic.topic_id == uid,
               UserTopicStatistic.score != 0). \
        order_by(UserTopicStatistic.score.desc()).paginate(page, 15)
    return render_template('topic/rank.html', topic=topic, experts=experts)


@bp.route('/topic/<int:uid>/wiki')
def wiki(uid):
    """话题wiki"""
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/wiki.html', topic=topic)


@bp.route('/topic/<int:uid>/admin', methods=['POST', 'GET'])
@UserPermission()
def admin(uid):
    """话题管理"""
    topic = Topic.query.get_or_404(uid)
    form = AdminTopicForm()
    uptoken = qiniu.generate_token(policy={
        'callbackUrl': absolute_url_for('.update_avatar'),
        'callbackBody': "id=%d&key=$(key)" % uid
    })
    if form.validate_on_submit():
        # Update name log
        if topic.name != form.name.data:
            log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_NAME, user_id=g.user.id, topic_id=uid, before=topic.name,
                                after=form.name.data)
            db.session.add(log)

        # Update wiki log
        if (topic.wiki or "") != form.wiki.data:
            log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_WIKI, user_id=g.user.id, topic_id=uid,
                                before=topic.wiki, after=form.wiki.data,
                                compare=generate_lcs_html(topic.wiki, form.wiki.data))
            db.session.add(log)

        # 记录wiki贡献者
        contributor = topic.wiki_contributors.filter(TopicWikiContributor.user_id == g.user.id).first()
        if contributor:
            contributor.count += 1
            contributor.last_contributed_at = datetime.now()
            db.session.add(contributor)
        else:
            contributor = TopicWikiContributor(topic_id=uid, user_id=g.user.id, count=1)
            db.session.add(contributor)

        form.populate_obj(topic)
        db.session.add(topic)
        db.session.commit()
        topic.save_to_es()
        return redirect(url_for('.view', uid=uid))
    return render_template('topic/admin.html', topic=topic, form=form, uptoken=uptoken)


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
    return json.dumps({
        'id': topic.id,
        'name': topic.name,
        'followers_count': topic.followers_count
    })


@bp.route('/topic/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注话题"""
    topic = Topic.query.get_or_404(uid)
    follow_topic = FollowTopic.query.filter(FollowTopic.topic_id == uid,
                                            FollowTopic.user_id == g.user.id).first()
    # 取消关注
    if follow_topic:
        db.session.delete(follow_topic)
        topic.followers_count -= 1
        db.session.add(topic)
        db.session.commit()
        return json.dumps({'result': True, 'followed': False, 'followers_count': topic.followers.count()})
    else:
        # 关注
        follow_topic = FollowTopic(topic_id=uid, user_id=g.user.id)
        db.session.add(follow_topic)

        topic.followers_count += 1
        db.session.add(topic)

        # USER FEED: 插入本人的用户FEED
        feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_TOPIC, topic_id=uid)
        g.user.feeds.append(feed)
        db.session.add(g.user)

        db.session.commit()
        return json.dumps({'result': True, 'followed': True, 'followers_count': topic.followers.count()})


@bp.route('/topic/<int:uid>/add_synonym', methods=['POST'])
def add_synonym(uid):
    """添加话题同义词"""
    topic = Topic.query.get_or_404(uid)
    synonym = request.form.get('synonym')
    if synonym:
        topic_synonym = topic.synonyms.filter(TopicSynonym.synonym == synonym).first()
        if not topic_synonym:
            topic_synonym = TopicSynonym(synonym=synonym)
            topic.synonyms.append(topic_synonym)
            db.session.add(topic)

            # log
            log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_SYNONYM, after=synonym,
                                user_id=g.user.id, topic_id=uid)
            db.session.add(log)
            db.session.commit()
            topic.save_to_es()
        macro = get_template_attribute('macros/_topic.html', 'topic_synonym_edit_wap')
        return json.dumps({
            'result': True,
            'html': macro(topic_synonym)
        })
    else:
        return json.dumps({'result': False})


@bp.route('/topic/synonym/<int:uid>/remove', methods=['POST'])
def remove_synonym(uid):
    """移除话题同义词"""
    topic_synonym = TopicSynonym.query.get_or_404(uid)

    # log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_SYNONYM, before=topic_synonym.synonym,
                        user_id=g.user.id, topic_id=topic_synonym.topic_id)
    db.session.add(log)
    db.session.delete(topic_synonym)
    topic_synonym.topic.save_to_es()
    db.session.commit()
    return json.dumps({'result': True})


@bp.route('/topic/<int:uid>/upload_avatar', methods=['POST'])
@UserPermission()
def upload_avatar(uid):
    """上传话题头像"""
    topic = Topic.query.get_or_404(uid)
    try:
        filename = process_topic_avatar(request.files['file'], 200)

        # Update avatar log
        log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_AVATAR, before=topic.avatar_url,
                            after=topic_avatars.url(filename), user_id=g.user.id)
        topic.logs.append(log)

        topic.avatar = filename
        db.session.add(topic)
        db.session.commit()
    except Exception, e:
        return json.dumps({'result': False, 'error': e.__repr__()})
    else:
        return json.dumps({
            'result': True,
            'image_url': topic_avatars.url(filename),
        })


@bp.route('/topic/<int:uid>/update_experience', methods=['POST'])
@UserPermission()
def update_experience(uid):
    """更新当前用户在该话题下的话题经验"""
    topic = Topic.query.get_or_404(uid)
    experience = request.form.get('experience', '')
    from_compose = request.form.get('compose', type=int) == 1

    statistic = UserTopicStatistic.query.filter(UserTopicStatistic.topic_id == uid,
                                                UserTopicStatistic.user_id == g.user.id).first()
    if statistic:
        statistic.experience = experience
    else:
        statistic = UserTopicStatistic(topic_id=uid, user_id=g.user.id, experience=experience)
    db.session.add(statistic)

    if not g.user.has_seleted_expert_topics:
        for expert in g.user.expert_topics:
            expert.selected = True
            db.session.add(expert)
        g.user.has_seleted_expert_topics = True
        db.session.add(g.user)

    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/apply_for_deletion', methods=['POST'])
@UserPermission()
def apply_for_deletion(uid):
    """申请删除话题"""
    topic = Topic.query.get_or_404(uid)
    apply = ApplyTopicDeletion(user_id=g.user.id, topic_id=uid)
    db.session.add(apply)
    db.session.commit()
    return json.dumps({
        'result': True
    })


@bp.route('/topic/expert/<int:uid>/remove', methods=['POST'])
@UserPermission()
def remove_expert(uid):
    """移除擅长话题"""
    expert_topic = UserTopicStatistic.query.get_or_404(uid)
    if not g.user.has_seleted_expert_topics:
        for expert in g.user.expert_topics:
            expert.selected = True
            db.session.add(expert)
        g.user.has_seleted_expert_topics = True
        db.session.add(g.user)
        db.session.commit()
    expert_topic.selected = False
    db.session.add(expert_topic)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/add_expert', methods=['POST'])
@UserPermission()
def add_expert(uid):
    """添加擅长话题"""
    # 最多设置 8 个擅长话题
    if g.user.expert_topics.count() == 8:
        return json.dumps({
            'result': False
        })

    topic = Topic.query.get_or_404(uid)
    expert_topic = UserTopicStatistic.query.filter(UserTopicStatistic.topic_id == uid,
                                                   UserTopicStatistic.user_id == g.user.id).first()
    if not expert_topic:
        expert_topic = UserTopicStatistic(topic_id=uid, user_id=g.user.id, selected=True)
        db.session.add(expert_topic)
    else:
        if expert_topic.selected:
            return json.dumps({
                'result': False
            })
        else:
            expert_topic.selected = True

    if not g.user.has_seleted_expert_topics:
        g.user.has_seleted_expert_topics = True
        db.session.add(g.user)
        max_show_order_topic = 0
        for index, expert_topic in enumerate(g.user.expert_topics):
            expert_topic.show_order = index
            expert_topic.selected = True
            db.session.add(expert_topic)
            max_show_order_topic = index
        expert_topic.show_order = max_show_order_topic + 1
        db.session.add(expert_topic)
    else:
        max_show_order_topic = g.user.expert_topics.from_self().order_by(UserTopicStatistic.show_order.desc()).first()
        if max_show_order_topic:
            expert_topic.show_order = max_show_order_topic.show_order + 1

    db.session.commit()

    macro = get_template_attribute("macros/_topic.html", "render_expert_topic_in_compose_page")
    return json.dumps({
        'result': True,
        'html': macro(expert_topic),
        'full': g.user.expert_topics.count() == 8
    })


@bp.route('/topic/update_show_order', methods=['POST'])
@UserPermission()
def update_show_order():
    show_orders = request.form.get('show_orders')
    if not show_orders:
        return json.dumps({
            'result': False
        })

    # 若从未编辑过擅长话题，则首先赋予 show_order
    if not g.user.has_seleted_expert_topics:
        g.user.has_seleted_expert_topics = True
        db.session.add(g.user)

        for index, expert_topic in enumerate(g.user.expert_topics):
            expert_topic.show_order = index
            expert_topic.selected = True
            db.session.add(expert_topic)

    show_orders = json.loads(show_orders)
    for item in show_orders:
        id = item['id']
        show_order = item['show_order']
        expert_topic = UserTopicStatistic.query.get(id)
        if expert_topic:
            expert_topic.show_order = show_order
            db.session.add(expert_topic)

    db.session.commit()
    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/get_card', methods=['POST'])
def get_card(uid):
    """获取话题卡片"""
    topic = Topic.query.get_or_404(uid)
    macro = get_template_attribute('macros/_topic.html', 'topic_card')
    return json.dumps({
        'result': True,
        'html': macro(topic)
    })


@bp.route('/topic/update_avatar', methods=['POST'])
def update_avatar():
    """更新话题头像"""
    id = request.form.get('id', type=int)
    topic = Topic.query.get_or_404(id)
    avatar = request.form.get('key')
    topic.avatar = avatar
    db.session.add(topic)
    db.session.commit()
    return json.dumps({
        'result': True,
        'url': topic.avatar_url
    })
