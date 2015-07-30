# coding: utf-8
from datetime import datetime
from flask import Blueprint, render_template, request, json, get_template_attribute, g, redirect, url_for, abort, \
    current_app
from ..models import db, Topic, Question, QuestionTopic, FollowTopic, TopicWikiContributor, UserTopicStatistic, \
    PublicEditLog, TOPIC_EDIT_KIND, Answer, TopicSynonym, UserFeed, ApplyTopicDeletion, HomeFeed, HOME_FEED_KIND
from ..utils.permissions import UserPermission, AdminPermission
from ..utils.helpers import absolute_url_for, text_diff
from ..utils._qiniu import qiniu
from ..utils.decorators import jsonify
from ..forms import AdminTopicForm

bp = Blueprint('topic', __name__)

TOPICS_PER = 45


@bp.route('/topic/square')
def square():
    """话题广场"""
    config = current_app.config

    product_topic = Topic.query.get_or_404(config.get('PRODUCT_TOPIC_ID'))
    product_descendant_topics = product_topic.descendant_topics.order_by(Topic.avg.desc())
    product_total = product_descendant_topics.count()

    organization_topic = Topic.query.get_or_404(config.get('ORGANIZATION_TOPIC_ID'))
    organization_descendant_topics = organization_topic.descendant_topics.order_by(Topic.avg.desc())
    organization_total = organization_descendant_topics.count()

    position_topic = Topic.query.get_or_404(config.get('POSITION_TOPIC_ID'))
    position_descendant_topics = position_topic.descendant_topics.order_by(Topic.avg.desc())
    position_total = position_descendant_topics.count()

    skill_topic = Topic.query.get_or_404(config.get('SKILL_TOPIC_ID'))
    skill_descendant_topics = skill_topic.descendant_topics.order_by(Topic.avg.desc())
    skill_total = skill_descendant_topics.count()

    other_descendant_topics = Topic.other_topics()
    other_total = other_descendant_topics.count()

    return render_template('topic/square.html', per=TOPICS_PER,
                           product_topic=product_topic,
                           product_descendant_topics=product_descendant_topics.limit(TOPICS_PER),
                           product_total=product_total,
                           organization_topic=organization_topic,
                           organization_descendant_topics=organization_descendant_topics.limit(TOPICS_PER),
                           organization_total=organization_total,
                           position_topic=position_topic,
                           position_descendant_topics=position_descendant_topics.limit(TOPICS_PER),
                           position_total=position_total,
                           skill_topic=skill_topic,
                           skill_descendant_topics=skill_descendant_topics.limit(TOPICS_PER),
                           skill_total=skill_total,
                           other_descendant_topics=other_descendant_topics.limit(TOPICS_PER),
                           other_total=other_total)


@bp.route('/topic/loading_topics_in_square', methods=['POST'])
@jsonify
def loading_topics_in_square():
    """在话题广场"""
    config = current_app.config
    offset = request.args.get('offset', type=int)
    _type = request.args.get('type', 'product')

    if not offset:
        return {'result': False}

    if _type == 'product':
        descendant_topics = Topic.query.get_or_404(config.get('PRODUCT_TOPIC_ID')).descendant_topics
    elif _type == 'organization':
        descendant_topics = Topic.query.get_or_404(config.get('ORGANIZATION_TOPIC_ID')).descendant_topics
    elif _type == 'position':
        descendant_topics = Topic.query.get_or_404(config.get('POSITION_TOPIC_ID')).descendant_topics
    elif _type == 'skill':
        descendant_topics = Topic.query.get_or_404(config.get('SKILL_TOPIC_ID')).descendant_topics
    else:
        descendant_topics = Topic.other_topics()

    descendant_topics = descendant_topics.order_by(Topic.avg.desc()).limit(TOPICS_PER).offset(offset)
    count = descendant_topics.count()
    macro = get_template_attribute("macros/_topic.html", "render_topics")
    return {'result': True, 'html': macro(descendant_topics), 'count': count}


@bp.route('/topic/query', methods=['POST'])
@UserPermission()
@jsonify
def query():
    """查询话题"""
    q = request.form.get('q')
    limit = request.form.get('limit', type=int)  # 话题个数限制
    with_create = request.form.get('create') == 'true'  # 当找不到名称完全匹配的topic时，是否返回创建选项
    if q:
        topics, _, _ = Topic.query_from_es(q, page=1, per_page=10)
        topics = [topic for topic in topics if topic.merge_to_topic_id is None]  # 不显示被合并的话题
        if limit:
            topics = topics[:limit]
        topics_data = [{'name': topic.name, 'id': topic.id, 'avatar_url': topic.avatar_url,
                        'followers_count': topic.followers_count} for topic in topics]
        if with_create:
            exact_topic = Topic.query.filter(Topic.name == q).first() is not None
            if not exact_topic:
                topics_data.insert(0, {'name': q, 'create': True})
        return topics_data
    else:
        return {[]}


TOPIC_FANTASTIC_ANSWERS_PER = 15


@bp.route('/topic/<int:uid>')
def view(uid):
    """话题详情页"""
    topic = Topic.query.get_or_404(uid)
    need_redirect = request.args.get('redirect', type=int)
    from_id = request.args.get('from_id', type=int)
    if from_id:
        from_topic = Topic.query.get_or_404(from_id)
    else:
        from_topic = None
    if topic.merge_to_topic_id and need_redirect != 0:
        return redirect(url_for('.view', uid=topic.merge_to_topic_id, from_id=topic.id))
    answers = topic.all_answers.order_by(Answer.score.desc())
    total = answers.count()
    return render_template('topic/view.html', topic=topic, answers=answers.limit(TOPIC_FANTASTIC_ANSWERS_PER),
                           from_topic=from_topic, total=total, per=TOPIC_FANTASTIC_ANSWERS_PER)


@bp.route('/topic/<int:uid>/loading_fantastic_answers', methods=['POST'])
@UserPermission()
@jsonify
def loading_fantastic_answers(uid):
    """加载话题下的精彩回答"""
    topic = Topic.query.get_or_404(uid)
    offset = request.args.get('offset', type=int)
    if not offset:
        return {'result': False}

    answers = topic.all_answers.order_by(Answer.score.desc()).limit(TOPIC_FANTASTIC_ANSWERS_PER).offset(offset)
    count = answers.count()
    macro = get_template_attribute("macros/_topic.html", "render_topic_fantastic_answers")
    return {'result': True, 'html': macro(answers, topic), 'count': count}


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
    merged_topics = Topic.query.filter(Topic.merge_to_topic_id == uid)
    uptoken = qiniu.generate_token(policy={
        'callbackUrl': absolute_url_for('.update_avatar'),
        'callbackBody': "id=%d&key=$(key)" % uid
    })
    return render_template('topic/admin.html', topic=topic, uptoken=uptoken, merged_topics=merged_topics)


ALL_QUESTIONS_PER = 15


@bp.route('/topic/<int:uid>/questions')
def questions(uid):
    """话题下的全部问题"""
    topic = Topic.query.get_or_404(uid)
    questions = topic.all_questions
    total = questions.count()
    return render_template('topic/questions.html', topic=topic, questions=questions.limit(ALL_QUESTIONS_PER),
                           total=total, per=ALL_QUESTIONS_PER)


@bp.route('/topic/<int:uid>/loading_all_questions', methods=['POST'])
@UserPermission()
@jsonify
def loading_all_questions(uid):
    """加载话题下的全部问题"""
    topic = Topic.query.get_or_404(uid)
    offset = request.args.get('offset', type=int)
    if not offset:
        return {'result': False}

    questions = topic.all_questions.limit(ALL_QUESTIONS_PER).offset(offset)
    count = questions.count()
    macro = get_template_attribute("macros/_topic.html", "render_all_questions")
    return {'result': True, 'html': macro(questions, topic), 'count': count}


WAITING_FOR_ANSWER_QUESTIONS_PER = 15


@bp.route('/topic/<int:uid>/waiting')
def waiting_for_answer(uid):
    """话题下等待回答的问题"""
    topic = Topic.query.get_or_404(uid)
    questions = topic.all_questions.filter(Question.answers_count == 0)
    total = questions.count()

    return render_template('topic/waiting_for_answer.html', topic=topic,
                           questions=questions.limit(WAITING_FOR_ANSWER_QUESTIONS_PER),
                           total=total, per=WAITING_FOR_ANSWER_QUESTIONS_PER)


@bp.route('/topic/<int:uid>/loading_waiting_for_answer_questions', methods=['POST'])
@UserPermission()
@jsonify
def loading_waiting_for_answer_questions(uid):
    """加载话题下的待回答问题"""
    topic = Topic.query.get_or_404(uid)
    offset = request.args.get('offset', type=int)
    if not offset:
        return {'result': False}

    questions = topic.all_questions.filter(Question.answers_count == 0). \
        limit(WAITING_FOR_ANSWER_QUESTIONS_PER).offset(offset)
    count = questions.count()
    macro = get_template_attribute("macros/_topic.html", "render_topic_waiting_for_answer_questions")
    return {'result': True, 'html': macro(questions, topic), 'count': count}


@bp.route('/topic/<int:uid>/logs')
def logs(uid):
    """话题日志"""
    topic = Topic.query.get_or_404(uid)
    return render_template('topic/logs.html', topic=topic)


@bp.route('/topic/<int:uid>/add_parent_topic', methods=['POST'])
@UserPermission()
@jsonify
def add_parent_topic(uid):
    """添加直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic_id = request.form.get('parent_topic_id', type=int)
    name = request.form.get('name', '').strip()
    config = current_app.config
    NC_TOPIC_ID = config.get('NC_TOPIC_ID')

    if topic.parent_topics_locked or (parent_topic_id is None and name == ''):
        return {'result': False}

    if parent_topic_id:
        parent_topic = Topic.query.get_or_404(parent_topic_id)
    else:
        parent_topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)

    if parent_topic.child_topics_locked:
        return {'result': False}

    # 不允许添加以下话题为该话题的直接父话题：
    # 1. 自己
    # 2. 直接父话题
    # 3. 子孙话题
    if parent_topic.id == topic.id \
            or parent_topic.id in topic.descendant_topics_id_list \
            or parent_topic.id in topic.parent_topics:
        return {'result': False}

    # 若该话题只有一个父话题“未分类”，则将其移除
    parent_topics_id_list = topic.parent_topics_id_list
    if len(parent_topics_id_list) == 1 and parent_topics_id_list[0] == NC_TOPIC_ID and parent_topic.id != NC_TOPIC_ID:
        topic.remove_parent_topic(NC_TOPIC_ID)

    topic.add_parent_topic(parent_topic.id)

    # MERGE: 若父话题被合并到其他话题，则也将此话题作为子话题添加
    if parent_topic.merge_to_topic_id:
        parent_topic.merge_to_topic.add_child_topic(topic.id, from_merge=True)

    # 子话题 log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=parent_topic.name, after_id=parent_topic.id)
    db.session.add(log)

    # 父话题 log
    parent_topic_log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_CHILD_TOPIC, topic_id=parent_topic.id,
                                     user_id=g.user.id, after=topic.name, after_id=uid)
    db.session.add(parent_topic_log)

    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'parent_topic_edit_wap')
    return {'result': True, 'html': macro(parent_topic)}


@bp.route('/topic/<int:uid>/remove_parent_topic/<int:parent_topic_id>', methods=['POST'])
@UserPermission()
@jsonify
def remove_parent_topic(uid, parent_topic_id):
    """删除直接父话题"""
    topic = Topic.query.get_or_404(uid)
    parent_topic = Topic.query.get_or_404(parent_topic_id)

    if topic.parent_topics_locked or parent_topic.child_topics_locked:
        return {'result': False}

    topic.remove_parent_topic(parent_topic_id)

    # MERGE: 若父话题被合并到其他话题，则也将此话题作为子话题添加
    if parent_topic.merge_to_topic_id:
        parent_topic.merge_to_topic.remove_child_topic(topic.id, from_merge=True)

    # 子话题 log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_PARENT_TOPIC, topic_id=uid, user_id=g.user.id,
                        before=parent_topic.name, before_id=parent_topic_id)
    db.session.add(log)

    # 父话题 log
    parent_topic_log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_CHILD_TOPIC, topic_id=parent_topic.id,
                                     user_id=g.user.id, before=topic.name, before_id=uid)
    db.session.add(parent_topic_log)

    db.session.commit()

    return {'result': True}


@bp.route('/topic/<int:uid>/add_child_topic', methods=['POST'])
@UserPermission()
@jsonify
def add_child_topic(uid):
    """添加直接子话题"""
    topic = Topic.query.get_or_404(uid)
    child_topic_id = request.form.get('child_topic_id', type=int)
    name = request.form.get('name', '').strip()
    config = current_app.config
    NC_TOPIC_ID = config.get('NC_TOPIC_ID')

    if topic.child_topics_locked or (child_topic_id is None and name == ''):
        return {'result': False}

    if child_topic_id:
        child_topic = Topic.query.get_or_404(child_topic_id)
    else:
        child_topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)

    if child_topic.parent_topics_locked:
        return {'result': False}

    # 不允许以下的话题添加为该话题的直接子话题
    # 1. 自己
    # 2. 直接子话题
    # 3. 祖先话题
    if child_topic_id == uid \
            or child_topic_id in topic.ancestor_topics_id_list \
            or child_topic_id in topic.child_topics_id_list:
        return {'result': False}

    # 若子话题只有一个父话题“未分类”，则将其移除
    parent_topics_id_list = child_topic_id.parent_topics_id_list
    if len(parent_topics_id_list) == 1 and parent_topics_id_list[0] == NC_TOPIC_ID and topic.id != NC_TOPIC_ID:
        child_topic.remove_parent_topic(NC_TOPIC_ID)

    topic.add_child_topic(child_topic.id)

    # MERGE: 若该话题被合并到其他话题，则也进行子话题添加
    if topic.merge_to_topic_id:
        topic.merge_to_topic.add_child_topic(child_topic.id, from_merge=True)

    # 父话题 log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_CHILD_TOPIC, topic_id=uid, user_id=g.user.id,
                        after=child_topic.name, after_id=child_topic.id)
    db.session.add(log)

    # 子话题 log
    child_topic_log = PublicEditLog(kind=TOPIC_EDIT_KIND.ADD_PARENT_TOPIC, topic_id=child_topic.id, user_id=g.user.id,
                                    after=topic.name, after_id=uid)
    db.session.add(child_topic_log)

    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'child_topic_edit_wap')
    return {'result': True, 'html': macro(child_topic)}


@bp.route('/topic/<int:uid>/remove_child_topic/<int:child_topic_id>', methods=['POST'])
@UserPermission()
@jsonify
def remove_child_topic(uid, child_topic_id):
    """删除直接子话题"""
    topic = Topic.query.get_or_404(uid)
    child_topic = Topic.query.get_or_404(child_topic_id)

    if topic.child_topics_locked or child_topic.parent_topics_locked:
        return {'result': False}

    topic.remove_child_topic(child_topic_id)

    # MERGE: 若该话题被合并到其他话题，则也进行子话题添加
    if topic.merge_to_topic_id:
        topic.merge_to_topic.remove_child_topic(child_topic.id, from_merge=True)

    # 父话题 log
    log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_CHILD_TOPIC, topic_id=uid, user_id=g.user.id,
                        before=child_topic.name, before_id=child_topic_id)
    db.session.add(log)

    # 子话题 log
    child_topic_log = PublicEditLog(kind=TOPIC_EDIT_KIND.REMOVE_PARENT_TOPIC, topic_id=child_topic.id,
                                    user_id=g.user.id, before=topic.name, before_id=uid)
    db.session.add(child_topic_log)

    db.session.commit()
    return {'result': True}


@bp.route('/topic/get_by_name/<string:name>', methods=['POST'])
@UserPermission()
@jsonify
def get_by_name(name):
    """通过name获取话题，若不存在则创建"""
    topic = Topic.get_by_name(name, g.user.id, create_if_not_exist=True)
    return {'id': topic.id, 'name': topic.name, 'followers_count': topic.followers_count}


@bp.route('/topic/<int:uid>/follow', methods=['POST'])
@UserPermission()
@jsonify
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

        # MERGE: 若该话题合并到其他话题，则也同时取消关注
        if topic.merge_to_topic_id:
            follow_merge_to_topic = topic.merge_to_topic.followers.filter(FollowTopic.user_id == g.user.id,
                                                                          FollowTopic.from_merge).first()
            db.session.delete(follow_merge_to_topic)
            topic.merge_to_topic.followers_count -= 1
            db.session.add(topic.merge_to_topic)

        # HOME FEED: 从首页 feed 中删除与此话题相关的条目
        for feed in g.user.home_feeds.filter(HomeFeed.topic_id == uid,
                                             HomeFeed.kind == HOME_FEED_KIND.FANTASTIC_ANSWER_FROM_FOLLOWED_TOPIC):
            db.session.delete(feed)

        db.session.commit()

        return {'result': True, 'followed': False, 'followers_count': topic.followers_count}
    else:
        # 关注
        follow_topic = FollowTopic(topic_id=uid, user_id=g.user.id)
        db.session.add(follow_topic)

        topic.followers_count += 1
        db.session.add(topic)

        # MERGE: 若该话题合并到其他话题，则也同时关注
        if topic.merge_to_topic_id:
            follow_merge_to_topic = topic.merge_to_topic.followers.filter(FollowTopic.user_id == g.user.id).first()
            if not follow_merge_to_topic:
                follow_merge_to_topic = FollowTopic(topic_id=topic.merge_to_topic_id, user_id=g.user.id,
                                                    from_merge=True)
                db.session.add(follow_merge_to_topic)
                topic.merge_to_topic.followers_count += 1
                db.session.add(topic.merge_to_topic)

        # USER FEED: 关注话题
        UserFeed.follow_topic(g.user, topic)

        # HOME FEED: 向首页 feed 中插入该话题的精彩回答 10 条
        for answer in topic.all_answers.filter(Answer.fantastic).order_by(Answer.created_at.desc()).limit(5):
            home_feed = g.user.home_feeds.filter(HomeFeed.kind == HOME_FEED_KIND.FANTASTIC_ANSWER_FROM_FOLLOWED_TOPIC,
                                                 HomeFeed.answer_id == answer.id).first()
            if not home_feed:
                home_feed = HomeFeed(kind=HOME_FEED_KIND.FANTASTIC_ANSWER_FROM_FOLLOWED_TOPIC, answer_id=answer.id,
                                     user_id=g.user.id, topic_id=topic.id)
                db.session.add(home_feed)

        db.session.commit()

        return {'result': True, 'followed': True, 'followers_count': topic.followers_count}


@bp.route('/topic/<int:uid>/add_synonym', methods=['POST'])
@jsonify
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
            return {'result': True, 'html': macro(topic_synonym)}
        else:
            return {'result': False}
    else:
        return {'result': False}


@bp.route('/topic/synonym/<int:uid>/remove', methods=['POST'])
@jsonify
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
    return {'result': True}


@bp.route('/topic/<int:uid>/update_experience', methods=['POST'])
@UserPermission()
@jsonify
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

    return {'result': True}


@bp.route('/topic/<int:uid>/apply_for_deletion', methods=['POST'])
@UserPermission()
@jsonify
def apply_for_deletion(uid):
    """申请删除话题"""
    topic = Topic.query.get_or_404(uid)
    apply = ApplyTopicDeletion(user_id=g.user.id, topic_id=uid)
    db.session.add(apply)
    db.session.commit()
    return {'result': True}


@bp.route('/topic/expert/<int:uid>/remove', methods=['POST'])
@UserPermission()
@jsonify
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
    return {'result': True}


@bp.route('/topic/add_expert', methods=['POST'])
@UserPermission()
@jsonify
def add_expert():
    """添加擅长话题"""
    # 最多设置 8 个擅长话题
    if g.user.expert_topics.count() == 8:
        return {'result': True}

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
            return {'result': True}
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
    return {
        'result': True,
        'html': macro(new_expert_topic, myself=True),
        'full': g.user.expert_topics.count() == 8
    }


@bp.route('/topic/update_show_order', methods=['POST'])
@UserPermission()
@jsonify
def update_show_order():
    show_orders = request.form.get('show_orders')
    if not show_orders:
        return {'result': True}

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
    return {'result': True}


@bp.route('/topic/<int:uid>/get_data_for_card', methods=['POST'])
@jsonify
def get_data_for_card(uid):
    """获取话题卡片"""
    topic = Topic.query.get_or_404(uid)
    return {
        'result': True,
        'topic': {
            'id': uid,
            'name': topic.name,
            'url': url_for('.view', uid=uid),
            'avatar_url': topic.avatar_url,
            'followers_count': topic.followers_count,
            'followed': bool(g.user and topic.followed_by_user(g.user.id)),
            'wiki_preview': topic.wiki_preview
        }
    }


@bp.route('/topic/update_avatar', methods=['POST'])
@jsonify
def update_avatar():
    """更新话题头像"""
    id = request.form.get('id', type=int)
    topic = Topic.query.get_or_404(id)

    if topic.avatar_locked:
        return {'result': False}

    avatar = request.form.get('key')
    topic.avatar = avatar
    db.session.add(topic)
    db.session.commit()
    return {'result': True, 'url': topic.avatar_url, 'id': topic.id}


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
                                compare=text_diff(topic.wiki, form.wiki.data))
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
@jsonify
def update_name(uid):
    """更新话题名称"""
    topic = Topic.query.get_or_404(uid)
    name = request.form.get('name', '').strip()

    if topic.name_locked or not name:
        return {'result': False}

    # 话题名称不可重复
    if Topic.query.filter(Topic.name == name, Topic.id != uid).first():
        return {'result': False}

    # Update name log
    if topic.name != name:
        log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_NAME, user_id=g.user.id, topic_id=uid, before=topic.name,
                            after=name)
        db.session.add(log)

    topic.name = name
    topic.save_to_es()
    db.session.add(topic)
    db.session.commit()

    return {'result': True}


@bp.route('/topic/<int:uid>/lock', methods=['POST'])
@AdminPermission()
@jsonify
def lock(uid):
    """锁定话题"""
    topic = Topic.query.get_or_404(uid)
    target = request.form.get('target')

    if not target:
        return {'result': True}

    attr = '%s_locked' % target

    if not hasattr(topic, attr):
        return {'result': True}

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

    db.session.add(topic)
    db.session.commit()

    return {'result': True, 'locked': not locked}


@bp.route('/topic/<int:uid>/update_kind', methods=['POST'])
@UserPermission()
@jsonify
def update_kind(uid):
    """更新话题类型"""
    topic = Topic.query.get_or_404(uid)
    kind = request.form.get('kind', type=int)

    if topic.topic_kind_locked or not kind or kind < 1 or kind > 6:
        return {'result': False}

    # log
    if topic.kind != kind:
        log = PublicEditLog(kind=TOPIC_EDIT_KIND.UPDATE_KIND, user_id=g.user.id, before=topic.kind,
                            after=kind, topic_id=uid)
        db.session.add(log)

    topic.kind = kind
    db.session.add(topic)
    db.session.commit()

    return {'result': True}


@bp.route('/topic/<int:uid>/update_other_kind', methods=['POST'])
@UserPermission()
@jsonify
def update_other_kind(uid):
    """更新话题其他类型"""
    topic = Topic.query.get_or_404(uid)
    kind = request.form.get('kind', '').strip()
    topic.other_kind = kind
    db.session.add(topic)
    db.session.commit()
    return {'result': True}


@bp.route('/topic/<int:uid>/merge_to', methods=['POST'])
@AdminPermission()
@jsonify
def merge_to(uid):
    """将本话题合并至另一话题"""
    topic = Topic.query.get_or_404(uid)

    if topic.merge_topic_locked or topic.merge_to_topic_id:
        return {'result': False}

    merge_to_topic_id = request.form.get('merge_to_topic_id', type=int)
    name = request.form.get('name', '').strip()

    if merge_to_topic_id:
        if uid == merge_to_topic_id:
            return {'result': False}
        merge_to_topic = Topic.query.get_or_404(merge_to_topic_id)
    else:
        merge_to_topic = Topic.get_by_name(name)
        if not merge_to_topic:
            return {'result': False}

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
        merge_to_topic.save_to_es()

    # 迁移问题
    for question_topic in topic.questions:
        _question_topic = merge_to_topic.questions.filter(
            QuestionTopic.question_id == question_topic.question_id).first()
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
            _topic_follower = FollowTopic(topic_id=merge_to_topic.id, user_id=follow_topic.user_id,
                                          from_merge=True)
            db.session.add(_topic_follower)
            merge_to_topic.followers_count += 1
    db.session.add(merge_to_topic)

    # 被合并的话题 Log
    merge_to_log = PublicEditLog(kind=TOPIC_EDIT_KIND.MERGE_TO, user_id=g.user.id, topic_id=uid,
                                 after_id=merge_to_topic.id, after=merge_to_topic.name)
    db.session.add(merge_to_log)

    # 合并至的话题 Log
    merge_in_log = PublicEditLog(kind=TOPIC_EDIT_KIND.MERGE_IN, user_id=g.user.id, topic_id=merge_to_topic.id,
                                 after_id=uid, after=topic.name)
    db.session.add(merge_in_log)

    db.session.commit()
    return {'id': merge_to_topic.id, 'name': merge_to_topic.name, 'result': True}


@bp.route('/topic/<int:uid>/unmerge_from/<int:unmerge_from_topic_id>', methods=['POST'])
@AdminPermission()
@jsonify
def unmerge_from(uid, unmerge_from_topic_id):
    """取消话题合并"""
    topic = Topic.query.get_or_404(uid)
    unmerge_from_topic = Topic.query.get_or_404(unmerge_from_topic_id)

    if topic.merge_topic_locked or topic.merge_to_topic_id != unmerge_from_topic_id:
        return {'result': False}

    topic.merge_to_topic_id = None

    # 解锁话题类型
    topic.topic_kind_locked = False

    # 移除同义词
    topic_synonym = unmerge_from_topic.synonyms.filter(TopicSynonym.synonym == topic.name,
                                                       TopicSynonym.from_merge).first()
    unmerge_from_topic.save_to_es()

    db.session.delete(topic_synonym)

    # 迁回问题
    for question_topic in topic.questions:
        _question_topic = unmerge_from_topic.questions.filter(QuestionTopic.question_id == question_topic.question_id,
                                                              QuestionTopic.from_merge).first()
        db.session.delete(_question_topic)

    # 迁回子话题
    for child_topic_id in topic.child_topics_id_list:
        unmerge_from_topic.remove_child_topic(child_topic_id, from_merge=True)

    # 迁回关注者
    for follow_topic in topic.followers:
        _topic_follower = unmerge_from_topic.followers.filter(FollowTopic.user_id == follow_topic.user_id,
                                                              FollowTopic.from_merge).first()
        if _topic_follower:
            db.session.delete(_topic_follower)
            unmerge_from_topic.followers_count -= 1
    db.session.add(unmerge_from_topic)

    db.session.add(topic)

    # 取消合并至话题 log
    unmerge_from_log = PublicEditLog(kind=TOPIC_EDIT_KIND.UNMERGE_FROM, user_id=g.user.id,
                                     topic_id=uid, before=unmerge_from_topic.name,
                                     before_id=unmerge_from_topic.id)
    db.session.add(unmerge_from_log)

    # 从话题中移出 log
    unmerge_out_log = PublicEditLog(kind=TOPIC_EDIT_KIND.UNMERGE_OUT, user_id=g.user.id,
                                    topic_id=unmerge_from_topic.id, before=topic.name,
                                    before_id=topic.id)
    db.session.add(unmerge_out_log)

    db.session.commit()

    return {'result': True}
