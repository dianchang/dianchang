# coding: utf-8
from datetime import datetime
from flask import Blueprint, render_template, request, json, get_template_attribute, g, redirect, url_for, abort
from ..models import db, Topic, Question, QuestionTopic, FollowTopic, TopicWikiContributor, UserTopicStatistic, \
    PublicEditLog, TOPIC_EDIT_KIND, Answer, TopicSynonym, UserFeed, USER_FEED_KIND, ApplyTopicDeletion, TopicClosure
from ..utils.permissions import UserPermission, AdminPermission
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
    limit = request.form.get('limit', type=int)  # 话题个数限制
    with_create = request.form.get('create')  # 当找不到名称完全匹配的topic时，是否返回创建选项
    question_id = request.form.get('question_id')  # 不包括此问题的话题（用于给问题添加话题）
    ancestor_topic_id = request.form.get('ancestor_topic_id')  # 不为此话题的子孙话题的话题（用于给话题添加子话题）
    descendant_topic_id = request.form.get('descendant_topic_id')  # 不为此话题的祖先话题的话题（用于给话题添加父话题）
    if q:
        topics_id_list = Topic.query_from_es(q, page=1, per_page=10, only_id_list=True)
        topics = Topic.query.filter(Topic.id.in_(topics_id_list))
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
        if limit:
            topics = topics[:5]
        topics_data = [{'name': topic.name,
                        'id': topic.id,
                        'avatar_url': topic.avatar_url,
                        'followers_count': topic.followers_count}
                       for topic in topics]
        if with_create:
            exact_topic = Topic.query.filter(Topic.name == q).first() is not None
            if not exact_topic:
                topics_data.insert(0, {
                    'name': q,
                    'create': True
                })
        return json.dumps(topics_data)
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
        order_by(UserTopicStatistic.week_score.desc()).paginate(page, 15)
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
    uptoken = qiniu.generate_token(policy={
        'callbackUrl': absolute_url_for('.update_avatar'),
        'callbackBody': "id=%d&key=$(key)" % uid
    })
    return render_template('topic/admin.html', topic=topic, uptoken=uptoken)


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


@bp.route('/topic/<int:uid>/add_parent_topic', methods=['POST'])
@UserPermission()
def add_parent_topic(uid):
    """添加直接父话题"""
    topic = Topic.query.get_or_404(uid)

    if topic.parent_topics_locked or topic.root:
        return json.dumps({
            'result': False
        })

    parent_topic_id = request.form.get('parent_topic_id', type=int)
    name = request.form.get('name', '').strip()

    if parent_topic_id:
        parent_topic = Topic.query.get_or_404(parent_topic_id)
    elif name:
        parent_topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)
    else:
        return json.dumps({
            'result': False
        })

    topic.add_parent_topic(parent_topic.id)

    # Add parent topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=parent_topic.name, after_id=parent_topic.id)
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

    if topic.parent_topics_locked:
        return json.dumps({
            'result': False
        })

    parent_topic = Topic.query.get_or_404(parent_topic_id)
    topic.remove_parent_topic(parent_topic_id)

    # Remove parent topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        before=parent_topic.name, before_id=parent_topic_id)
    db.session.add(log)
    db.session.commit()

    return json.dumps({'result': True})


@bp.route('/topic/<int:uid>/add_child_topic', methods=['POST'])
@UserPermission()
def add_child_topic(uid):
    """添加直接子话题"""
    topic = Topic.query.get_or_404(uid)

    if topic.child_topics_locked:
        return json.dumps({
            'result': False
        })

    child_topic_id = request.form.get('child_topic_id', type=int)
    name = request.form.get('name', '').strip()

    if child_topic_id:
        child_topic = Topic.query.get_or_404(child_topic_id)
    elif name:
        child_topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)
    else:
        return json.dumps({
            'result': False
        })

    topic.add_child_topic(child_topic.id)

    # Add child topic log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_CHILD_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=child_topic.name, after_id=child_topic.id)
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

    if topic.child_topics_locked:
        return json.dumps({
            'result': False
        })

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
    topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)
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
        return json.dumps({'result': True, 'error': e.__repr__()})
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

    if not g.user.has_selected_expert_topics:
        for expert in g.user.expert_topics:
            expert.selected = True
            db.session.add(expert)
        g.user.has_selected_expert_topics = True
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
    if not g.user.has_selected_expert_topics:
        for expert in g.user.expert_topics:
            expert.selected = True
            db.session.add(expert)
        g.user.has_selected_expert_topics = True
        db.session.add(g.user)
        db.session.commit()
    expert_topic.selected = False
    db.session.add(expert_topic)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/add_expert', methods=['POST'])
@UserPermission()
def add_expert():
    """添加擅长话题"""
    # 最多设置 8 个擅长话题
    if g.user.expert_topics.count() == 8:
        return json.dumps({
            'result': True
        })

    id = request.form.get('id', type=int)
    name = request.form.get('name', '').strip()

    if id:
        topic = Topic.query.get_or_404(id)
    else:
        topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)

    new_expert_topic = UserTopicStatistic.query.filter(UserTopicStatistic.topic_id == topic.id,
                                                       UserTopicStatistic.user_id == g.user.id).first()
    if not new_expert_topic:
        new_expert_topic = UserTopicStatistic(topic_id=topic.id, user_id=g.user.id, selected=True)
        db.session.add(new_expert_topic)
    else:
        if new_expert_topic.selected:
            return json.dumps({
                'result': True
            })
        else:
            new_expert_topic.selected = True

    if not g.user.has_selected_expert_topics:
        max_show_order_topic = 0
        for index, expert_topic in enumerate(g.user.expert_topics):
            expert_topic.show_order = index
            expert_topic.selected = True
            db.session.add(expert_topic)
            max_show_order_topic = index
        new_expert_topic.show_order = max_show_order_topic + 1
        g.user.has_selected_expert_topics = True
        db.session.add(g.user)
        db.session.add(new_expert_topic)
    else:
        max_show_order_topic = g.user.expert_topics.from_self().order_by(UserTopicStatistic.show_order.desc()).first()
        if max_show_order_topic:
            new_expert_topic.show_order = max_show_order_topic.show_order + 1

    db.session.commit()

    macro = get_template_attribute("macros/_topic.html", "render_expert_topic")
    return json.dumps({
        'result': True,
        'html': macro(new_expert_topic),
        'full': g.user.expert_topics.count() == 8
    })


@bp.route('/topic/update_show_order', methods=['POST'])
@UserPermission()
def update_show_order():
    show_orders = request.form.get('show_orders')
    if not show_orders:
        return json.dumps({
            'result': True
        })

    # 若从未编辑过擅长话题，则首先赋予 show_order
    if not g.user.has_selected_expert_topics:
        for index, expert_topic in enumerate(g.user.expert_topics):
            expert_topic.show_order = index
            expert_topic.selected = True
            db.session.add(expert_topic)

        g.user.has_selected_expert_topics = True
        db.session.add(g.user)

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

    if topic.avatar_locked:
        return json.dumps({
            'result': False
        })

    avatar = request.form.get('key')
    topic.avatar = avatar
    db.session.add(topic)
    db.session.commit()
    return json.dumps({
        'result': True,
        'url': topic.avatar_url,
        'id': topic.id
    })


@bp.route('/topic/<int:uid>/edit_wiki', methods=['GET', 'POST'])
def edit_wiki(uid):
    """编辑话题百科"""
    topic = Topic.query.get_or_404(uid)

    if topic.wiki_locked:
        abort(403)

    form = AdminTopicForm()
    if form.validate_on_submit():
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
    return render_template('topic/edit_wiki.html', topic=topic)


@bp.route('/topic/<int:uid>/update_name', methods=['POST'])
@UserPermission()
def update_name(uid):
    """更新话题名称"""
    topic = Topic.query.get_or_404(uid)

    if topic.name_locked:
        return json.dumps({
            'result': False
        })

    name = request.form.get('name')

    if name is not None:
        name = name.strip()
    else:
        return json.dumps({
            'result': False
        })

    if name == '':
        return json.dumps({
            'result': False
        })

    # 话题名称不可重复
    if Topic.query.filter(Topic.name == name, Topic.id != uid).first():
        return json.dumps({
            'result': False
        })

    # Update name log
    if topic.name != name:
        log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_NAME, user_id=g.user.id, topic_id=uid, before=topic.name,
                            after=name)
        db.session.add(log)

    topic.name = name
    topic.save_to_es()
    db.session.add(topic)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/lock', methods=['POST'])
@AdminPermission()
def lock(uid):
    """锁定话题"""
    topic = Topic.query.get_or_404(uid)
    target = request.form.get('target')

    if not target:
        return json.dumps({
            'result': True
        })

    attr = '%s_locked' % target

    if not hasattr(topic, attr):
        return json.dumps({
            'result': True
        })

    locked = bool(getattr(topic, attr))
    setattr(topic, attr, not locked)

    # log
    log = PublicEditLog(user_id=g.user.id, topic_id=uid)
    if locked:
        log.kind = TOPIC_EDIT_KIND.UNLOCK
        log.before = attr
    else:
        log.kind = TOPIC_EDIT_KIND.LOCK
        log.after = attr
    db.session.add(log)

    if target == 'all':
        if topic.all_locked:
            topic.avatar_locked = True
            topic.name_locked = True
            topic.wiki_locked = True
            topic.parent_topics_locked = True
            topic.child_topics_locked = True
            topic.merge_topic_locked = True
            topic.topic_kind_locked = True
        else:
            topic.avatar_locked = False
            topic.name_locked = False
            topic.wiki_locked = False
            topic.parent_topics_locked = False
            topic.child_topics_locked = False
            topic.merge_topic_locked = False
            topic.topic_kind_locked = False

    if topic.avatar_locked and topic.name_locked and topic.wiki_locked and topic.parent_topics_locked \
            and topic.child_topics_locked and topic.merge_topic_locked and topic.topic_kind_locked:
        topic.all_locked = True
    else:
        topic.all_locked = False

    # TODO: 更新日志

    db.session.add(topic)
    db.session.commit()

    return json.dumps({
        'result': True,
        'locked': not locked
    })


@bp.route('/topic/<int:uid>/update_kind', methods=['POST'])
@UserPermission()
def update_kind(uid):
    """更新话题类型"""
    topic = Topic.query.get_or_404(uid)

    if topic.topic_kind_locked:
        return json.dumps({
            'result': False
        })

    kind = request.form.get('kind', type=int)
    if not kind or kind < 1 or kind > 6:
        return json.dumps({
            'result': False
        })

    # log
    if topic.kind != kind:
        log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_KIND, user_id=g.user.id, before=topic.kind,
                            after=kind, topic_id=uid)
        db.session.add(log)

    topic.kind = kind
    db.session.add(topic)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/update_other_kind', methods=['POST'])
@UserPermission()
def update_other_kind(uid):
    """更新话题其他类型"""
    topic = Topic.query.get_or_404(uid)
    kind = request.form.get('kind', '').strip()
    topic.other_kind = kind
    db.session.add(topic)
    db.session.commit()
    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/merge_to/<int:merge_to_topic_id>', methods=['POST'])
@UserPermission()
def merge_to(uid, merge_to_topic_id):
    """将本话题合并至另一话题"""
    topic = Topic.query.get_or_404(uid)
    merge_to_topic = Topic.query.get_or_404(merge_to_topic_id)

    if topic.merge_topic_locked or topic.merge_to_topic_id:
        return json.dumps({
            'result': False
        })

    topic.merge_to_topic_id = merge_to_topic.id

    # 话题类型统一为与 merge_to_topic 一致，并锁定
    topic.kind = merge_to_topic.kind
    topic.other_kind = merge_to_topic.other_kind
    topic.topic_kind_locked = True
    db.session.add(topic)

    # 将该话题的名称设为 merge_to_topic 的同义词
    topic_synonym = merge_to_topic.synonyms.filter(TopicSynonym.synonym == topic.name).first()
    if not topic_synonym:
        topic_synonym = TopicSynonym(synonym=topic.name, topic_id=merge_to_topic.id, from_merge=True)
        db.session.add(topic_synonym)

    # 迁移问题
    for question_topic in topic.questions:
        _question_topic = merge_to_topic.questions.filter(QuestionTopic.question == question_topic.question_id).first()
        if not _question_topic:
            _question_topic = QuestionTopic(question_id=question_topic.question_id, topic_id=merge_to_topic.id,
                                            from_merge=True)
            db.session.add(_question_topic)

    # 迁移子话题
    for child_topic_id in topic.child_topics_id_list:
        merge_to_topic.add_child_topic(child_topic_id, from_merge=True)

    # 迁移关注者
    for follow_topic in topic.followers:
        _topic_follower = merge_to_topic.followers.filter(FollowTopic.user_id == follow_topic.user_id).first()
        if not _topic_follower:
            _topic_follower = FollowTopic(topid_id=merge_to_topic.id, user_id=follow_topic.user_id,
                                          from_merge=True)
            db.session.add(_topic_follower)

    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/topic/<int:uid>/unmerge_from/<int:unmerge_from_topic_id>', methods=['POST'])
@UserPermission()
def unmerge_from(uid, unmerge_from_topic_id):
    """取消话题合并"""
    topic = Topic.query.get_or_404(uid)
    unmerge_from_topic = Topic.query.get_or_404(unmerge_from_topic_id)

    if topic.merge_topic_locked or topic.merge_to_topic_id != unmerge_from_topic_id:
        return json.dumps({
            'result': False
        })

    topic.merge_to_topic_id = None

    # 解锁话题类型
    topic.topic_kind_locked = False

    # 移除同义词
    topic_synonym = unmerge_from_topic.synonyms.filter(TopicSynonym.synonym == topic.name,
                                                       TopicSynonym.from_merge).first()
    db.session.delete(topic_synonym)

    # 迁回问题
    for question_topic in topic.questions:
        _question_topic = unmerge_from_topic.questions.filter(QuestionTopic.question == question_topic.question_id,
                                                              QuestionTopic.from_merge).first()
        db.session.delete(_question_topic)

    # 迁回子话题
    for child_topic_id in topic.child_topics_id_list:
        unmerge_from_topic.remove_child_topic(child_topic_id, from_merge=True)

    # 迁回关注者
    for follow_topic in topic.followers:
        _topic_follower = unmerge_from_topic.followers.filter(FollowTopic.user_id == follow_topic.user_id,
                                                              FollowTopic.from_merge).first()
        db.session.delete(_topic_follower)

    db.session.commit()

    return json.dumps({
        'result': True
    })
