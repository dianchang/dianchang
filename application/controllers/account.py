# coding: utf-8
from flask import render_template, Blueprint, redirect, request, url_for, flash, g, json, session, \
    get_template_attribute
from ..forms import SigninForm, SignupForm, ForgotPasswordForm
from ..utils.account import signin_user, signout_user
from ..utils.permissions import VisitorPermission, UserPermission
from ..utils.helpers import get_domain_from_email, absolute_url_for
from ..utils._qiniu import qiniu
from ..utils.decorators import jsonify
from ..models import db, User, InvitationCode, Topic, FollowTopic, WorkOnProduct, UserTopicStatistic, \
    HomeFeedBackup, HomeFeed, UserFeed, USER_FEED_KIND
from ..models._helpers import pinyin

bp = Blueprint('account', __name__)


@bp.route('/signin')
@VisitorPermission()
def signin():
    """登录"""
    session['referrer'] = request.referrer or url_for('site.index')
    return render_template('account/signin.html')


@bp.route('/signin', methods=['POST'])
@VisitorPermission()
@jsonify
def do_signin():
    form = SigninForm()
    referrer = session.get('referrer') or url_for('site.index')
    session.pop('referrer', None)
    if form.validate():
        signin_user(form.user, form.remember.data)
        return {
            'result': True,
            'referrer': referrer
        }
    else:
        return {
            'result': False,
            'email': form.email.errors[0] if len(form.email.errors) else "",
            'password': form.password.errors[0] if len(form.password.errors) else "",
            'referrer': referrer
        }


@bp.route('/account/test_invitation_code', methods=['POST'])
@VisitorPermission()
@jsonify
def test_invitation_code():
    """验证邀请码"""
    code = request.form.get('code')

    if not code:
        return {
            'result': False,
            'code': '邀请码不能为空',
        }

    invitation_code = InvitationCode.query.filter(InvitationCode.code == code).first()
    if not invitation_code:
        return {
            'result': False,
            'code': '无效的邀请码'
        }
    elif invitation_code.used:
        return {
            'result': False,
            'code': '邀请码已被使用'
        }

    return {
        'result': True
    }


@bp.route('/signup', methods=['POST'])
@VisitorPermission()
@jsonify
def signup():
    """注册"""
    form = SignupForm()
    if form.validate():
        params = form.data.copy()
        params.pop('code')
        user = User(**params)
        db.session.add(user)

        # 设置默认的 url token
        url_token = pinyin(user.name)
        non_repeat_url_token = url_token
        suffix_number = 1
        while True:
            if User.query.filter(User.url_token == non_repeat_url_token).count() == 0:
                break
            non_repeat_url_token = "%s-%d" % (url_token, suffix_number)
            suffix_number += 1
        user.url_token = non_repeat_url_token

        db.session.commit()

        invitation_code = form.invitation_code
        invitation_code.used = True
        invitation_code.user_id = user.id
        db.session.add(invitation_code)
        # TODO: need to uncomment this in production
        # db.session.commit()

        user.save_to_es()  # 存储到elasticsearch
        signin_user(user)
        return {
            'result': True,
            'domain': get_domain_from_email(user.email)
        }
    else:
        return {
            'result': False,
            'name': form.name.errors[0] if len(form.name.errors) else "",
            'email': form.email.errors[0] if len(form.email.errors) else "",
            'password': form.password.errors[0] if len(form.password.errors) else ""
        }


@bp.route('/signout')
def signout():
    """登出"""
    signout_user()
    return redirect(url_for('site.index'))


@bp.route('/send_reset_password_mail', methods=['POST'])
@VisitorPermission()
@jsonify
def send_reset_password_mail():
    """忘记密码"""
    form = ForgotPasswordForm()
    if form.validate():
        user = User.query.filter(User.email == form.email.data).first()
        if not user.is_active:
            return {
                'result': False,
                'email': '该账户尚未激活'
            }

        # TODO: need to uncomment this in production
        # send_reset_password_mail(user)
        return {
            'result': True,
            'domain': get_domain_from_email(user.email) or ""
        }
    else:
        return {
            'result': False,
            'email': form.email.errors[0] if len(form.email.errors) else ""
        }


@bp.route('/settings')
@UserPermission()
def settings():
    """个人设置"""
    return render_template('account/settings.html')


@bp.route('/notification_settings')
@UserPermission()
def notification_settings():
    """消息设置"""
    return render_template('account/notification_settings.html')


@bp.route('/privacy_settings')
@UserPermission()
def privacy_settings():
    """隐私设置"""
    return render_template('account/privacy_settings.html')


@bp.route('/reset_password')
@VisitorPermission()
def reset_password():
    """重设密码"""
    return render_template('account/reset_password.html')


@bp.route('/reset_password', methods=['POST'])
@VisitorPermission()
@jsonify
def do_reset_password():
    """重设密码"""
    # TODO: need to finish the reset logic
    return {
        'result': True
    }


@bp.route('/account/update_setting', methods=['POST'])
@UserPermission()
@jsonify
def update_setting():
    """更新用户设置"""
    key = request.form.get('key')
    value = request.form.get('value')

    if not hasattr(g.user, key):
        return {
            'result': False
        }

    setattr(g.user, key, True if value == 'on' else False)
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True
    }


@bp.route('/account/update_name', methods=['POST'])
@UserPermission()
@jsonify
def update_name():
    """更新称谓"""
    if g.user.name_edit_count == 0:
        return {
            'result': False
        }

    name = request.form.get('name')
    if not name:
        return {
            'result': False
        }

    if name == g.user.name:
        return {
            'result': True,
            'name_edit_count': g.user.name_edit_count
        }

    g.user.name = name
    g.user.name_edit_count -= 1
    db.session.add(g.user)
    db.session.commit()
    return {
        'result': True,
        'name_edit_count': g.user.name_edit_count
    }


@bp.route('/account/update_email', methods=['POST'])
@UserPermission()
@jsonify
def update_email():
    """更新邮箱"""
    email = request.form.get('email')
    if not email:
        return {
            'result': False
        }

    if email == g.user.email:
        g.user.inactive_email = ""
        db.session.add(g.user)
        db.session.commit()

        return {
            'result': True,
            'active': g.user.is_active
        }

    g.user.inactive_email = email
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True,
        'active': False
    }


@bp.route('/account/update_url_token', methods=['POST'])
@UserPermission()
@jsonify
def update_url_token():
    """更新个人主页网址"""
    url_token = request.form.get('url_token')

    if not url_token:
        return {
            'result': False
        }

    g.user.url_token = url_token
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True
    }


@bp.route('/account/update_password', methods=['POST'])
@UserPermission()
@jsonify
def update_password():
    """更新密码"""
    password = request.form.get('password')

    if not password:
        return {
            'result': False
        }

    g.user.password = password
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True
    }


INTERESTING_TOPICS_PER = 20


@bp.route('/account/select_interesting_topics')
@UserPermission()
def select_interesting_topics():
    """选择感兴趣的话题"""
    hot_topics = Topic.query.order_by(Topic.questions_count.desc())
    hot_topics_total = hot_topics.count()

    product_topics = Topic.query.filter(Topic.name == '产品').first().descendant_topics
    product_topics_total = product_topics.count()

    organization_topics = Topic.query.filter(Topic.name == '组织').first().descendant_topics
    organization_topics_total = organization_topics.count()

    position_topics = Topic.query.filter(Topic.name == '职业').first().descendant_topics
    position_topics_total = position_topics.count()

    skill_topics = Topic.query.filter(Topic.name == '技能').first().descendant_topics
    skill_topics_total = skill_topics.count()

    return render_template('account/select_interesting_topics.html',
                           hot_topics=hot_topics.limit(INTERESTING_TOPICS_PER),
                           hot_topics_total=hot_topics_total,

                           product_topics=product_topics.limit(INTERESTING_TOPICS_PER),
                           product_topics_total=product_topics_total,

                           organization_topics=organization_topics.limit(INTERESTING_TOPICS_PER),
                           organization_topics_total=organization_topics_total,

                           position_topics=position_topics.limit(INTERESTING_TOPICS_PER),
                           position_topics_total=position_topics_total,

                           skill_topics=skill_topics.limit(INTERESTING_TOPICS_PER),
                           skill_topics_total=skill_topics_total,

                           per=INTERESTING_TOPICS_PER)


@bp.route('/account/loading_interesting_topics', methods=['POST'])
@UserPermission()
@jsonify
def loading_interesting_topics():
    """加载感兴趣的话题"""
    _type = request.args.get('type')
    offset = request.args.get('offset', type=int)
    if not offset or not _type:
        return {
            'result': False
        }

    if _type == 'hot':
        topics = Topic.query.order_by(Topic.questions_count.desc())
    elif _type == 'product':
        topics = Topic.query.filter(Topic.name == '产品').first().descendant_topics
    elif _type == 'organization':
        topics = Topic.query.filter(Topic.name == '组织').first().descendant_topics
    elif _type == 'position':
        topics = Topic.query.filter(Topic.name == '职业').first().descendant_topics
    else:
        topics = Topic.query.filter(Topic.name == '技能').first().descendant_topics

    topics = topics.limit(INTERESTING_TOPICS_PER).offset(offset)
    topics_count = topics.count()
    macro = get_template_attribute("macros/_account.html", "render_interesting_topics")

    return {
        'result': True,
        'html': macro(topics),
        'count': topics_count
    }


@bp.route('/account/submit_interesting_topics', methods=['POST'])
@UserPermission()
@jsonify
def submit_interesting_topics():
    """提交感兴趣的话题"""
    topics_id_list = request.form.getlist('topic_id', type=int)
    topics_id_list = _remove_repeats(topics_id_list)

    for topic_id in topics_id_list:
        # 关注话题
        follow_topic = g.user.followed_topics.filter(FollowTopic.topic_id == topic_id).first()
        if not follow_topic:
            follow_topic = FollowTopic(user_id=g.user.id, topic_id=topic_id)
            db.session.add(follow_topic)

            topic = Topic.query.get_or_404(topic_id)
            topic.followers_count += 1
            db.session.add(topic)

        # USER FEED: 插入到用户 feed 中
        user_feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_TOPIC, user_id=g.user.id, topic_id=topic_id)
        db.session.add(user_feed)

    g.user.has_selected_interesting_topics = True
    db.session.add(g.user)
    db.session.commit()

    return {
        'result': True
    }


@bp.route('/account/select_products_worked_on')
@UserPermission()
def select_products_worked_on():
    """选择工作过的产品"""
    return render_template('account/select_products_worked_on.html')


@bp.route('/account/submit_product_worked_on', methods=['POST'])
@UserPermission()
@jsonify
def submit_product_worked_on():
    """添加话题"""
    name = request.form.get('name')
    topic_id = request.form.get('topic_id')

    topic = None
    if name:
        topic = Topic.get_by_name(name, user_id=g.user.id, create_if_not_exist=True)
    elif topic_id:
        topic = Topic.query.get_or_404(topic_id)

    # 添加产品
    product = WorkOnProduct.query.filter(
        WorkOnProduct.topic_id == topic.id,
        WorkOnProduct.user_id == g.user.id).first()

    if product:
        return {
            'result': False
        }
    else:
        product = WorkOnProduct(topic_id=topic.id, user_id=g.user.id)
        db.session.add(product)

        # 自动关注话题
        follow_topic = FollowTopic.query.filter(FollowTopic.topic_id == topic.id,
                                                FollowTopic.user_id == g.user.id).first()
        if not follow_topic:
            follow_topic = FollowTopic(topic_id=topic.id, user_id=g.user.id)
            db.session.add(follow_topic)

            topic.followers_count += 1
            db.session.add(topic)

            # USER FEED: 插入到用户 feed 中
            user_feed = UserFeed(kind=USER_FEED_KIND.FOLLOW_TOPIC, user_id=g.user.id, topic_id=topic.id)
            db.session.add(user_feed)

        # 在 UserTopicStatistic 中标记该话题
        topic_statistic = UserTopicStatistic.query.filter(UserTopicStatistic.topic_id == topic.id,
                                                          UserTopicStatistic.user_id == g.user.id).first()
        if topic_statistic:
            topic_statistic.worked_on = True
        else:
            topic_statistic = UserTopicStatistic(topic_id=topic.id, user_id=g.user.id, worked_on=True)
            db.session.add(topic_statistic)

        db.session.commit()

        new_topic = name is not None and name != ""
        if new_topic:
            upload_token = qiniu.generate_token(policy={
                'callbackUrl': absolute_url_for('topic.update_avatar'),
                'callbackBody': "id=%d&key=$(key)" % topic.id
            })
        else:
            upload_token = ""

        macro = get_template_attribute('macros/_account.html', 'render_product_worked_on')
        return {
            'result': True,
            'html': macro(product, new_topic, upload_token)
        }


@bp.route('/account/product_worked_on/<int:uid>/set_current_working_on', methods=['POST'])
@UserPermission()
@jsonify
def set_product_current_working_on(uid):
    """设置为当前就职的产品"""
    product = WorkOnProduct.query.get_or_404(uid)
    for p in g.user.products_worked_on:
        if p.id != uid:
            p.current = False
            db.session.add(p)
    product.current = True
    db.session.add(product)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/account/product_worked_on/<int:uid>/cancel_set_current_working_on', methods=['POST'])
@UserPermission()
@jsonify
def cancel_set_product_current_working_on(uid):
    """取消设置为当前就职的产品"""
    product = WorkOnProduct.query.get_or_404(uid)
    product.current = False
    db.session.add(product)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/account/product_worked_on/<int:uid>/remove', methods=['POST'])
@UserPermission()
@jsonify
def remove_product(uid):
    """移除产品"""
    product = WorkOnProduct.query.get_or_404(uid)
    db.session.delete(product)
    db.session.commit()
    return {
        'result': True
    }


@bp.route('/account/follow_users')
@UserPermission()
def follow_users():
    """关注感兴趣的人"""
    topics_id_list = [followed_topic.topic_id for followed_topic in g.user.followed_topics]
    recommend_users = UserTopicStatistic.query. \
        filter(UserTopicStatistic.topic_id.in_(topics_id_list)). \
        filter(UserTopicStatistic.user_id != g.user.id). \
        filter(UserTopicStatistic.answers_count != 0). \
        group_by(UserTopicStatistic.user_id). \
        order_by(UserTopicStatistic.score.desc()).limit(24)
    return render_template('account/follow_users.html', recommend_users=recommend_users)


def _remove_repeats(seq):
    """去除列表中的重复元素"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


@bp.route('/account/finish_guide', methods=['POST'])
@UserPermission()
@jsonify
def finish_guide():
    """完成引导步骤"""
    current_step = request.form.get('step', type=int)
    if current_step < 1 or current_step > 6:
        return {
            'result': False
        }
    if current_step < 6:
        g.user.current_guide_step = current_step + 1
    else:
        g.user.current_guide_step = 6
        g.user.has_finish_guide_steps = True
    db.session.add(g.user)
    db.session.commit()
    return {
        'result': True
    }
