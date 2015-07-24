# coding: utf-8
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, g, abort, json, get_template_attribute, \
    current_app
from ..models import db, Question, Answer, Topic, QuestionTopic, FollowQuestion, QUESTION_EDIT_KIND, PublicEditLog, \
    UserTopicStatistic, AnswerDraft, UserFeed, USER_FEED_KIND, HomeFeed, HOME_FEED_KIND, Notification, \
    NOTIFICATION_KIND, InviteAnswer, User, ComposeFeed, COMPOSE_FEED_KIND, HomeFeedBackup
from ..utils.permissions import UserPermission
from ..utils.helpers import generate_lcs_html, absolute_url_for
from ..utils.answer import generate_qrcode_for_answer
from ..utils.decorators import jsonify

bp = Blueprint('question', __name__)


@bp.route('/question/<int:uid>')
def view(uid):
    """问题首页"""
    question = Question.query.get_or_404(uid)

    # 当前用户的回答信息
    my_answer_id = 0
    answered = False
    if g.user:
        my_answer = question.answers.filter(Answer.user_id == g.user.id).first()
        if my_answer:
            my_answer_id = my_answer.id
            answered = True

    answers = question.answers.filter(~Answer.hide)
    answerers_id_list = [answer.user_id for answer in answers]
    hided_answers = question.answers.filter(Answer.hide)
    followers = question.followers.order_by(FollowQuestion.created_at.desc()).limit(8)

    # 已邀请
    invited_users = []
    invited_users_id_list = []
    invited_users_count = 0
    if g.user:
        invited_users = InviteAnswer.query. \
            filter(InviteAnswer.question_id == uid,
                   InviteAnswer.inviter_id == g.user.id)
        invited_users_id_list = [invited_user.user_id for invited_user in invited_users]
        invited_users_count = len(invited_users_id_list)

    # 推荐邀请回答的候选人
    invite_candidates = []
    invite_candidates_count = 0
    topics_id_list = [topic.topic_id for topic in question.topics]
    if g.user:
        invite_candidates = UserTopicStatistic.query. \
            filter(UserTopicStatistic.topic_id.in_(topics_id_list)). \
            filter(UserTopicStatistic.user_id.notin_(invited_users_id_list)). \
            filter(UserTopicStatistic.user_id.notin_(answerers_id_list)). \
            filter(UserTopicStatistic.user_id != g.user.id). \
            filter(UserTopicStatistic.user_id != question.user_id). \
            filter(UserTopicStatistic.answers_count != 0). \
            group_by(UserTopicStatistic.user_id). \
            order_by(UserTopicStatistic.score.desc()).limit(16)

    # 话题经验，按 topics_id_list 排序
    topics_experience = []
    if g.user:
        for topic_id in topics_id_list:
            topic_experience = UserTopicStatistic.query. \
                filter(UserTopicStatistic.user_id == g.user.id,
                       UserTopicStatistic.topic_id == topic_id).first()
            if topic_experience:
                topics_experience.append(topic_experience)

    # 草稿
    if g.user:
        draft = question.drafts.filter(AnswerDraft.user_id == g.user.id).first()
        if draft:
            draft = draft.content
    else:
        draft = ""
    return render_template('question/view.html', question=question, draft=draft, answered=answered,
                           my_answer_id=my_answer_id, answers=answers, hided_answers=hided_answers,
                           followers=followers, invited_users=invited_users, invite_candidates=invite_candidates,
                           topics_experience=topics_experience, invited_users_count=invited_users_count)


@bp.route('/question/add', methods=['POST'])
@UserPermission()
@jsonify
def add():
    """添加问题"""
    title = request.form.get('title')
    desc = request.form.get('desc')
    anonymous = request.form.get('anonymous') is not None
    title = _add_question_mark_to_title(title)

    if not title:
        return {
            'result': False
        }

    question = Question(title=title, desc=desc, user_id=g.user.id, anonymous=anonymous)

    if not question.anonymous:
        # Log
        create_log = PublicEditLog(kind=QUESTION_EDIT_KIND.CREATE, user_id=g.user.id,
                                   original_title=question.title, original_desc=question.desc)
        question.logs.append(create_log)

    # 添加话题
    topics_id_list = request.form.getlist('topic')
    if len(topics_id_list) == 0:
        return {
            'result': False,
            'error': 'notopic'
        }
    for topic_id in topics_id_list:
        topic = Topic.query.get(topic_id)
        if topic:
            question_topic = QuestionTopic(topic_id=topic_id)
            question.topics.append(question_topic)
            # Add topic log
            add_topic_log = PublicEditLog(kind=QUESTION_EDIT_KIND.ADD_TOPIC, after=topic.name,
                                          after_id=topic_id, user_id=g.user.id)
            question.logs.append(add_topic_log)

            # MERGE: 若该话题被合并到其他话题，则也对此问题添加 merge_to_topic
            if topic.merge_to_topic_id:
                question_merge_to_topic = QuestionTopic(topic_id=topic.merge_to_topic_id, from_merge=True)
                question.topics.append(question_merge_to_topic)
                db.session.add(question_merge_to_topic)

            topic.updated_at = datetime.now()
            db.session.add(topic)

    g.user.questions_count += 1
    db.session.add(g.user)

    db.session.add(question)
    db.session.commit()
    question.save_to_es()

    # 自动关注该问题
    follow_question = FollowQuestion(question_id=question.id, user_id=g.user.id)
    db.session.add(follow_question)
    question.followers_count += 1
    db.session.add(question)

    if not anonymous:
        # USER FEED: 插入本人的用户 FEED
        feed = UserFeed(kind=USER_FEED_KIND.ASK_QUESTION, question_id=question.id)
        g.user.feeds.append(feed)
        db.session.add(g.user)

        # HOME FEED: 插入 followers 的首页 FEED
        # TODO: 使用消息队列进行插入操作
        for follower in g.user.followers:
            home_feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_ASK_QUESTION, sender_id=g.user.id,
                                 question_id=question.id)
            follower.follower.home_feeds.append(home_feed)
            db.session.add(follower.follower)

        # HOME FEED: 备份
        home_feed_backup = HomeFeedBackup(kind=HOME_FEED_KIND.FOLLOWING_ASK_QUESTION,
                                          sender_id=g.user.id, question_id=question.id)
        db.session.add(home_feed_backup)

    db.session.commit()

    return {
        'result': True,
        'id': question.id
    }


@bp.route('/question/<int:uid>/add_topic', methods=['POST'])
@UserPermission()
@jsonify
def add_topic(uid):
    """添加话题"""
    question = Question.query.get_or_404(uid)
    topic_id = request.form.get('topic_id', type=int)
    name = request.form.get('name', '').strip()

    if topic_id is None and name == "":
        return {'result': False}

    topic = None
    if name:
        topic = Topic.get_by_name(name, user_id=g.user.id, create_if_not_exist=True)
    else:
        topic = Topic.query.get_or_404(topic_id)

    if not topic:
        abort(404)

    # 添加话题
    question_topic = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic.id,
        QuestionTopic.question_id == uid).first()
    if question_topic:
        return {'result': False}

    question_topic = QuestionTopic(topic_id=topic.id, question_id=uid)

    # Log
    log = PublicEditLog(question_id=uid, user_id=g.user.id, after=topic.name, after_id=topic.id,
                        kind=QUESTION_EDIT_KIND.ADD_TOPIC)
    db.session.add(log)
    db.session.add(question_topic)

    # MERGE: 若该话题被合并到其他话题，则也对此问题添加 merge_to_topic
    if topic.merge_to_topic_id:
        question_merge_to_topic = topic.merge_to_topic.questions.filter(QuestionTopic.question_id == uid).first()
        if not question_merge_to_topic:
            question_merge_to_topic = QuestionTopic(topic_id=topic.merge_to_topic_id, question_id=uid,
                                                    from_merge=True)
            db.session.add(question_merge_to_topic)

    db.session.commit()

    # 更新话题统计数据
    answer = question.answers.filter(Answer.user_id == g.user.id).first()
    if answer:
        UserTopicStatistic.add_answer_in_topic(g.user.id, topic.id)
        if answer.upvotes_count > 0:
            UserTopicStatistic.upvote_answer_in_topic(g.user.id, topic.id, answer.upvotes_count)

    topic.questions_count += 1
    topic.updated_at = datetime.now()
    db.session.add(topic)
    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'topic_wap')
    return {
        'result': True,
        'id': topic.id,
        'html': macro(topic)
    }


@bp.route('/question/<int:uid>/remove_topic/<int:topic_id>', methods=['POST'])
@UserPermission()
@jsonify
def remove_topic(uid, topic_id):
    """移除话题"""
    question = Question.query.get_or_404(uid)
    topic = Topic.query.get_or_404(topic_id)
    topic_questions = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic_id,
        QuestionTopic.question_id == uid)
    for topic_question in topic_questions:
        db.session.delete(topic_question)

    # MERGE: 若该话题被合并到其他话题，则也将这个话题从问题中移除
    if topic.merge_to_topic_id:
        question_merge_to_topic = topic.merge_to_topic.questions.filter(QuestionTopic.question_id == uid,
                                                                        QuestionTopic.from_merge).first()
        if question_merge_to_topic:
            db.session.delete(question_merge_to_topic)

    # Log
    log = PublicEditLog(question_id=uid, user_id=g.user.id, before=topic.name, before_id=topic_id,
                        kind=QUESTION_EDIT_KIND.REMOVE_TOPIC)
    db.session.add(log)

    # 更新话题统计数据
    answer = question.answers.filter(Answer.user_id == g.user.id).first()
    if answer:
        UserTopicStatistic.remove_answer_from_topic(g.user.id, topic.id)
        if answer.upvotes_count > 0:
            UserTopicStatistic.cancel_upvote_answer_in_topic(g.user.id, topic.id, answer.upvotes_count)

    topic.questions_count -= 1
    db.session.add(topic)
    db.session.commit()

    return {
        'result': True
    }


@bp.route('/question/<int:uid>/follow', methods=['POST'])
@UserPermission()
@jsonify
def follow(uid):
    """关注 & 取消关注话题"""
    question = Question.query.get_or_404(uid)
    follow_question = FollowQuestion.query. \
        filter(FollowQuestion.question_id == uid,
               FollowQuestion.user_id == g.user.id).first()
    # 取消关注
    if follow_question:
        db.session.delete(follow_question)
        question.followers_count -= 1
        db.session.add(question)
        db.session.commit()
        return {
            'result': True,
            'followed': False,
            'followers_count': question.followers_count
        }
    else:
        # 关注
        follow_question = FollowQuestion(question_id=uid, user_id=g.user.id)
        db.session.add(follow_question)

        question.followers_count += 1
        db.session.add(question)

        # USER FEED: 插入到本人的用户FEED
        user_feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_QUESTION, question_id=uid)
        g.user.feeds.append(user_feed)
        db.session.add(g.user)

        # HOME FEED: 插入到 followers 的首页 FEED
        # TODO: 使用消息队列进行插入操作
        for follower in g.user.followers:
            feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_FOLLOW_QUESTION, sender_id=g.user.id,
                            question_id=uid)
            follower.follower.home_feeds.append(feed)
            db.session.add(follower.follower)

        # HOME FEED: 备份
        home_feed_backup = HomeFeedBackup(kind=HOME_FEED_KIND.FOLLOWING_FOLLOW_QUESTION,
                                          sender_id=g.user.id, question_id=uid)
        db.session.add(home_feed_backup)

        db.session.commit()
        return {
            'result': True,
            'followed': True,
            'followers_count': question.followers_count
        }


@bp.route('/question/<int:uid>/logs')
def logs(uid):
    question = Question.query.get_or_404(uid)
    return render_template('question/logs.html', question=question)


@bp.route('/question/<int:uid>/update', methods=['POST'])
@UserPermission()
@jsonify
def update(uid):
    """更新问题的title和desc"""
    question = Question.query.get_or_404(uid)
    title = request.form.get('title')
    desc = request.form.get('desc')

    if title is not None and title != question.title:
        title = title.strip()
        title = _add_question_mark_to_title(title)
        # Update title log
        title_log = PublicEditLog(kind=QUESTION_EDIT_KIND.UPDATE_TITLE, before=question.title, after=title,
                                  user_id=g.user.id, compare=generate_lcs_html(question.title, title))
        question.logs.append(title_log)
        question.title = title

        # 更新es中的answer
        for answer in question.answers:
            answer.save_to_es()

    # TODO: 对描述进行处理
    # if desc:
    #     desc = desc.strip()
    #     desc = desc.replace("<p>", "<br>").replace("</p>", ""). \
    #         replace("<div>", "<br>").replace("</div>", "")

    if desc is not None and desc != (question.desc or ""):
        desc = desc.strip()
        # Update desc log
        desc_log = PublicEditLog(kind=QUESTION_EDIT_KIND.UPDATE_DESC, before=question.desc, after=desc,
                                 user_id=g.user.id, compare=generate_lcs_html(question.desc, desc))
        question.logs.append(desc_log)
        question.desc = desc
    db.session.add(question)
    db.session.commit()
    question.save_to_es()  # 更新es中的question

    return {
        'result': True,
        'title': question.title,
        'desc': question.desc
    }


@bp.route('/question/similar', methods=['POST'])
@jsonify
def similar():
    """类似问题"""
    title = request.form.get('title')
    if not title:
        return ""
    similar_questions, total, took = Question.query_from_es(title, only_title=True, page=1, per_page=5)
    macro = get_template_attribute('macros/_question.html', 'similar_questions')
    return {
        'count': len(similar_questions),
        'html': macro(similar_questions)
    }


@bp.route('/question/<int:uid>/save_answer_draft', methods=['POST'])
@UserPermission()
@jsonify
def save_answer_draft(uid):
    """保存回答草稿"""
    question = Question.query.get_or_404(uid)
    content = request.form.get('content', '')
    draft = question.drafts.filter(AnswerDraft.user_id == g.user.id).first()
    if draft:
        content = content.strip()
        if content == '':
            db.session.delete(draft)
            g.user.drafts_count -= 1
        else:
            draft.content = content
            db.session.add(draft)
    else:
        draft = AnswerDraft(user_id=g.user.id, question_id=uid, content=content)
        g.user.drafts_count += 1
        db.session.add(g.user)
        db.session.add(draft)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/question/<int:uid>/answer', methods=['POST'])
@UserPermission()
@jsonify
def answer(uid):
    """回答问题"""
    question = Question.query.get_or_404(uid)
    content = request.form.get('answer')
    identity = request.form.get('identity', 'original')
    experience = request.form.get('experience')

    if not content:
        return {
            'result': False
        }

    # 保存回答
    answer = Answer(question_id=uid, content=content, user_id=g.user.id, topic_experience=experience)
    if identity in ['anonymous', 'organization-anonymous']:  # 匿名
        answer.anonymous = True
        if identity == 'anonymous':
            answer.identity = "匿名用户"
        else:
            answer.identity = "匿名%s员工" % (g.user.organization)
    db.session.add(answer)

    db.session.commit()

    if current_app.production:
        generate_qrcode_for_answer(answer)

    answer.save_to_es()

    # 自动关注该问题
    follow_question = g.user.followed_questions.filter(FollowQuestion.question_id == uid).first()
    if not follow_question:
        follow_question = FollowQuestion(question_id=uid, user_id=g.user.id)
        db.session.add(follow_question)
        question.followers_count += 1
        db.session.add(question)

    # NOTI: 插入提问者的用户 NOTI
    if g.user.id != question.user_id:
        noti = Notification(kind=NOTIFICATION_KIND.ANSWER_FROM_ASKED_QUESTION, senders_list=json.dumps([g.user.id]),
                            answer_id=answer.id)
        question.user.notifications.append(noti)
        db.session.add(question.user)

    if not answer.anonymous:
        # 更新话题统计数据
        for topic in question.topics:
            UserTopicStatistic.add_answer_in_topic(g.user.id, topic.topic_id)

        # USER FEED: 插入本人的用户FEED
        user_feed = UserFeed(kind=USER_FEED_KIND.ANSWER_QUESTION, answer_id=answer.id)
        g.user.feeds.append(user_feed)
        db.session.add(g.user)

        # HOME FEED: 插入 followers 的首页 FEED
        # TODO: 使用消息队列进行插入操作
        for follower in g.user.followers:
            # 若该问题为 follower 提出，则不插入此条 feed
            if follower.follower_id != question.user_id:
                home_feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_ANSWER_QUESTION, sender_id=g.user.id,
                                     answer_id=answer.id)
                follower.follower.home_feeds.append(home_feed)
                db.session.add(home_feed)

        # HOME FEED: 备份
        home_feed_backup = HomeFeedBackup(kind=HOME_FEED_KIND.FOLLOWING_ANSWER_QUESTION,
                                          sender_id=g.user.id, answer_id=answer.id)
        db.session.add(home_feed_backup)

    # 标记 InviteAnswer 中的相关条目为 answered
    invite_answer = InviteAnswer.query.filter(InviteAnswer.user_id == g.user.id,
                                              InviteAnswer.question_id == question.id).first()
    if invite_answer:
        invite_answer.answered = True
        db.session.add(invite_answer)

    # 标记 ComposeFeed 中的相关条目为 answered
    compose_feed = g.user.compose_feeds.filter(ComposeFeed.question_id == question.id).first()
    if compose_feed:
        compose_feed.answered = True
        db.session.add(compose_feed)

    # 更新话题 update 时间
    for topic in question.topics:
        topic.topic.updated_at = datetime.now()
        db.session.add(topic.topic)

    question.answers_count += 1
    g.user.answers_count += 1
    db.session.add(question)
    db.session.add(g.user)

    # 删除草稿
    draft = question.drafts.filter(AnswerDraft.user_id == g.user.id).first()
    if draft:
        g.user.drafts_count -= 1
        db.session.add(g.user)
        db.session.delete(draft)

    db.session.commit()

    macro = get_template_attribute("macros/_answer.html", "render_answer_in_question")
    return {
        'result': True,
        'html': macro(answer)
    }


@bp.route('/question/<int:uid>/invite/<int:user_id>', methods=['POST'])
@UserPermission()
@jsonify
def invite(uid, user_id):
    """邀请回答"""
    question = Question.query.get_or_404(uid)

    if user_id == g.user.id or user_id == question.user_id:
        return {
            'result': False
        }

    user = User.query.get_or_404(user_id)

    # 取消邀请
    invitation = InviteAnswer.query.filter(InviteAnswer.question_id == uid,
                                           InviteAnswer.user_id == user_id,
                                           InviteAnswer.inviter_id == g.user.id).first()
    if invitation:
        feed = ComposeFeed.query.filter(ComposeFeed.invitation_id == invitation.id).first()
        db.session.delete(feed)
        db.session.delete(invitation)
        db.session.commit()
        return {
            'result': True,
            'invited': False
        }
    else:
        # 邀请
        invitation = InviteAnswer(question_id=uid, user_id=user_id, inviter_id=g.user.id)
        db.session.add(invitation)
        db.session.commit()

        # FEED：插入到用户的撰写FEED中
        feed = ComposeFeed(kind=COMPOSE_FEED_KIND.INVITE_TO_ANSWER, invitation_id=invitation.id,
                           user_id=user_id, question_id=uid)
        db.session.add(feed)
        db.session.commit()

        macro = get_template_attribute("macros/_question.html", "invited_user_wap")
        return {
            'result': True,
            'invited': True,
            'username': user.name,
            'user_profile_url': user.profile_url,
            'html': macro(user)
        }


def _add_question_mark_to_title(title):
    """在问题末尾追加问号"""
    if title:
        if title.endswith('?'):
            title = title.rstrip('?') + "？"

        if not title.endswith('？'):
            title += "？"
    return title
