# coding: utf-8
from flask import Blueprint, render_template, redirect, url_for, request, g, abort, json, get_template_attribute
from ..forms import AddQuestionForm
from ..models import db, Question, Answer, Topic, QuestionTopic, FollowQuestion, QUESTION_EDIT_KIND, PublicEditLog, \
    UserTopicStatistic, AnswerDraft, UserFeed, USER_FEED_KIND, HomeFeed, HOME_FEED_KIND, Notification, \
    NOTIFICATION_KIND, InviteAnswer, User, ComposeFeed, COMPOSE_FEED_KIND
from ..utils.permissions import UserPermission
from ..utils.helpers import generate_lcs_html

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

    # 推荐邀请回答候选人
    invite_candidates = []
    invite_candidates_count = 0
    topics_id_list = [topic.topic_id for topic in question.topics]
    if g.user:
        invite_candidates = UserTopicStatistic.query. \
            filter(UserTopicStatistic.topic_id.in_(topics_id_list)). \
            filter(UserTopicStatistic.user_id.notin_(invited_users_id_list)). \
            filter(UserTopicStatistic.user_id.notin_(answerers_id_list)). \
            filter(UserTopicStatistic.user_id != g.user.id). \
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
def add():
    """添加问题"""
    title = request.form.get('title')
    desc = request.form.get('desc')
    anonymous = request.form.get('anonymous') is not None
    title = _add_question_mark_to_title(title)

    if not title:
        return json.dumps({
            'result': False
        })

    question = Question(title=title, desc=desc, user_id=g.user.id, anonymous=anonymous)

    if not question.anonymous:
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

    # 自动关注该问题
    follow_question = FollowQuestion(question_id=question.id, user_id=g.user.id)
    db.session.add(follow_question)

    if not anonymous:
        # FEED: 插入本人的用户FEED
        feed = UserFeed(kind=USER_FEED_KIND.ASK_QUESTION, question_id=question.id)
        g.user.feeds.append(feed)
        db.session.add(g.user)

        # FEED: 插入followers的首页FEED
        # TODO: 采用消息队列进行插入操作
        for follower in g.user.followers:
            home_feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_ASK_QUESTION, sender_id=g.user.id,
                                 question_id=question.id)
            follower.follower.home_feeds.append(home_feed)
            db.session.add(follower.follower)

    db.session.commit()

    return json.dumps({
        'result': True,
        'id': question.id
    })


@bp.route('/question/<int:uid>/add_topic', methods=['POST'])
@UserPermission()
def add_topic(uid):
    """添加话题"""
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
        # Add topic log
        log = PublicEditLog(question_id=uid, user_id=g.user.id, after=topic.name, after_id=topic.id,
                            kind=QUESTION_EDIT_KIND.ADD_TOPIC)
        db.session.add(log)
        db.session.add(question_topic)
        db.session.commit()

    # 更新话题统计数据
    answer = question.answers.filter(Answer.user_id == g.user.id).first()
    if answer:
        UserTopicStatistic.add_answer_in_topic(g.user.id, topic.id)
        if answer.upvotes_count > 0:
            UserTopicStatistic.upvote_answer_in_topic(g.user.id, topic.id, answer.upvotes_count)

    topic.questions_count += 1
    db.session.add(topic)
    db.session.commit()

    macro = get_template_attribute('macros/_topic.html', 'topic_wap')
    return json.dumps({'result': True,
                       'id': topic.id,
                       'html': macro(topic)})


@bp.route('/question/<int:uid>/remove_topic/<int:topic_id>', methods=['POST'])
@UserPermission()
def remove_topic(uid, topic_id):
    """移除话题"""
    question = Question.query.get_or_404(uid)
    topic = Topic.query.get_or_404(topic_id)
    topic_questions = QuestionTopic.query.filter(
        QuestionTopic.topic_id == topic_id,
        QuestionTopic.question_id == uid)
    for topic_question in topic_questions:
        db.session.delete(topic_question)

    # Remove topic log
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

    return json.dumps({'result': True})


@bp.route('/question/<int:uid>/follow', methods=['POST'])
@UserPermission()
def follow(uid):
    """关注 & 取消关注话题"""
    question = Question.query.get_or_404(uid)
    follow_question = FollowQuestion.query.filter(FollowQuestion.question_id == uid,
                                                  FollowQuestion.user_id == g.user.id)
    # 取消关注
    if follow_question.count():
        map(db.session.delete, follow_question)
        db.session.commit()
        return json.dumps({'result': True, 'followed': False, 'followers_count': question.followers.count()})
    else:
        # 关注
        follow_question = FollowQuestion(question_id=uid, user_id=g.user.id)
        db.session.add(follow_question)

        # FEED: 插入到本人的用户FEED
        user_feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_QUESTION, question_id=uid)
        g.user.feeds.append(user_feed)
        db.session.add(g.user)

        # FEED: 插入到followers的首页FEED中
        for follower in g.user.followers:
            feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_FOLLOW_QUESTION, sender_id=g.user.id,
                            question_id=uid)
            follower.follower.home_feeds.append(feed)
            db.session.add(follower.follower)

        db.session.commit()
        return json.dumps({'result': True, 'followed': True, 'followers_count': question.followers.count()})


@bp.route('/question/<int:uid>/logs')
def logs(uid):
    question = Question.query.get_or_404(uid)
    return render_template('question/logs.html', question=question)


@bp.route('/question/<int:uid>/update', methods=['POST'])
@UserPermission()
def update(uid):
    """通过Ajax更新问题的title和desc"""
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

    print(desc is None)
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

    return json.dumps({
        'result': True,
        'title': question.title,
        'desc': question.desc
    })


@bp.route('/question/similar', methods=['POST'])
def similar():
    """类似问题"""
    title = request.form.get('title')
    if not title:
        return ""
    similar_questions, total, took = Question.query_from_es(title, only_title=True, page=1, per_page=5)
    macro = get_template_attribute('macros/_question.html', 'similar_questions')
    return json.dumps({
        'count': len(similar_questions),
        'html': macro(similar_questions)
    })


@bp.route('/question/<int:uid>/save_answer_draft', methods=['POST'])
@UserPermission()
def save_answer_draft(uid):
    """保存回答草稿"""
    question = Question.query.get_or_404(uid)
    content = request.form.get('content', '')
    draft = question.drafts.filter(AnswerDraft.user_id == g.user.id).first()
    if draft:
        draft.content = content
        db.session.add(draft)
        db.session.commit()
    else:
        draft = AnswerDraft(user_id=g.user.id, question_id=uid, content=content)
        g.user.drafts_count += 1
        db.session.add(g.user)
        db.session.add(draft)
        db.session.commit()
    return json.dumps({'result': True})


@bp.route('/question/<int:uid>/answer', methods=['POST'])
@UserPermission()
def answer(uid):
    """回答问题"""
    question = Question.query.get_or_404(uid)
    content = request.form.get('answer')
    identity = request.form.get('identity', 'original')
    experience = request.form.get('experience')

    if not content:
        return json.dumps({
            'result': False
        })

    # 存储回答
    answer = Answer(question_id=uid, content=content, user_id=g.user.id, topic_experience=experience)
    if identity in ['anonymous', 'organization-anonymous']:  # 匿名
        answer.anonymous = True
        if identity == 'anonymous':
            answer.identity = "匿名用户"
        else:
            answer.identity = "匿名%s员工" % (g.user.organization)
    db.session.add(answer)

    # 删除草稿
    draft = question.drafts.filter(AnswerDraft.user_id == g.user.id).first()
    if draft:
        g.user.drafts_count -= 1
        db.session.add(g.user)
        db.session.delete(draft)

    db.session.commit()
    answer.save_to_es()

    # 自动关注该问题
    follow_question = g.user.followed_questions.filter(FollowQuestion.question_id == uid).first()
    if not follow_question:
        follow_question = FollowQuestion(question_id=uid, user_id=g.user.id)
        db.session.add(follow_question)

    # FEED: 插入提问者的用户NOTI
    if g.user.id != question.user_id:
        noti = Notification(kind=NOTIFICATION_KIND.ANSWER_FROM_ASKED_QUESTION, sender_id=g.user.id,
                            answer_id=answer.id)
        question.user.notifications.append(noti)
        db.session.add(question.user)

    if not answer.anonymous:
        # 更新话题统计数据
        for topic in question.topics:
            UserTopicStatistic.add_answer_in_topic(g.user.id, topic.topic_id)

        # FEED: 插入本人的用户FEED
        user_feed = UserFeed(kind=USER_FEED_KIND.ANSWER_QUESTION, answer_id=answer.id)
        g.user.feeds.append(user_feed)
        db.session.add(g.user)

        # FEED: 插入followers的HOME FEED
        # TODO: 使用消息队列
        for follower in g.user.followers:
            home_feed = HomeFeed(kind=HOME_FEED_KIND.FOLLOWING_ANSWER_QUESTION, sender_id=g.user.id,
                                 answer_id=answer.id)
            follower.follower.home_feeds.append(home_feed)
            db.session.add(home_feed)

    question.answers_count += 1
    g.user.answers_count += 1
    db.session.add(question)
    db.session.add(g.user)
    db.session.commit()

    macro = get_template_attribute("macros/_answer.html", "render_answer_in_question")
    return json.dumps({
        'result': True,
        'html': macro(answer)
    })


@bp.route('/question/<int:uid>/invite/<int:user_id>', methods=['POST'])
@UserPermission()
def invite(uid, user_id):
    """邀请回答"""
    if user_id == g.user.id:
        return json.dumps({
            'result': False
        })

    question = Question.query.get_or_404(uid)
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
        return json.dumps({
            'result': True,
            'invited': False
        })
    else:
        # 邀请
        invitation = InviteAnswer(question_id=uid, user_id=user_id, inviter_id=g.user.id)
        db.session.add(invitation)
        db.session.commit()

        # FEED：插入到用户的撰写FEED中
        feed = ComposeFeed(kind=COMPOSE_FEED_KIND.INVITE_TO_ANSWER, invitation_id=invitation.id,
                           user_id=user_id)
        db.session.add(feed)
        db.session.commit()

        macro = get_template_attribute("macros/_question.html", "invited_user_wap")
        return json.dumps({
            'result': True,
            'invited': True,
            'username': user.name,
            'user_profile_url': user.profile_url,
            'html': macro(user)
        })


def _add_question_mark_to_title(title):
    """在问题末尾追加问号"""
    if title:
        if title.endswith('?'):
            title = title.rstrip('?') + "？"

        if not title.endswith('？'):
            print(title)
            title += "？"
    return title
