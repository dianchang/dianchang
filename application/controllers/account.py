# coding: utf-8
from flask import render_template, Blueprint, redirect, request, url_for, flash, g, json, session, \
    get_template_attribute
from ..forms import SigninForm, SignupForm, SettingsForm, ForgotPasswordForm
from ..utils.account import signin_user, signout_user
from ..utils.permissions import VisitorPermission, UserPermission
from ..utils.helpers import get_domain_from_email, absolute_url_for
from ..utils.uploadsets import process_user_avatar, avatars, images, process_user_background
from ..utils._qiniu import qiniu
from ..models import db, User, InvitationCode, Topic, FollowTopic, WorkOnProduct

bp = Blueprint('account', __name__)


@bp.route('/signin', methods=['GET', 'POST'])
@VisitorPermission()
def signin():
    """登录"""
    form = SigninForm()
    if request.method == 'POST':
        if form.validate():
            signin_user(form.user, form.remember.data)
            return json.dumps({
                'result': True,
                'referer': session.get('referer') or url_for('site.index')
            })
        else:
            return json.dumps({
                'result': False,
                'email': form.email.errors[0] if len(form.email.errors) else "",
                'password': form.password.errors[0] if len(form.password.errors) else "",
                'referer': session.get('referer') or url_for('site.index')
            })
    else:
        session['referer'] = request.referrer or url_for('site.index')
    return render_template('account/signin.html')


@bp.route('/account/test_invitation_code', methods=['POST'])
@VisitorPermission()
def test_invitation_code():
    """验证邀请码"""
    code = request.form.get('code')

    if not code:
        return json.dumps({
            'result': False,
            'code': '邀请码不能为空',
        })

    invitation_code = InvitationCode.query.filter(InvitationCode.code == code).first()
    if not invitation_code:
        return json.dumps({
            'result': False,
            'code': '无效的邀请码'
        })
    elif invitation_code.used:
        return json.dumps({
            'result': False,
            'code': '邀请码已被使用'
        })

    return json.dumps({
        'result': True
    })


@bp.route('/signup', methods=['POST'])
@VisitorPermission()
def signup():
    """注册"""
    form = SignupForm()
    if form.validate():
        params = form.data.copy()
        params.pop('code')
        user = User(**params)
        db.session.add(user)
        db.session.commit()

        invitation_code = form.invitation_code
        invitation_code.used = True
        invitation_code.user_id = user.id
        db.session.add(invitation_code)
        # TODO: need to uncomment this in production
        # db.session.commit()

        user.save_to_es()  # 存储到elasticsearch
        signin_user(user)
        return json.dumps({
            'result': True,
            'domain': get_domain_from_email(user.email)
        })
    else:
        return json.dumps({
            'result': False,
            'name': form.name.errors[0] if len(form.name.errors) else "",
            'email': form.email.errors[0] if len(form.email.errors) else "",
            'password': form.password.errors[0] if len(form.password.errors) else ""
        })


@bp.route('/signout')
def signout():
    """登出"""
    signout_user()
    return redirect(request.referrer or url_for('site.index'))


@bp.route('/send_reset_password_mail', methods=['POST'])
def send_reset_password_mail():
    """忘记密码"""
    form = ForgotPasswordForm()
    if form.validate():
        user = User.query.filter(User.email == form.email.data).first()
        if not user.is_active:
            return json.dumps({
                'result': False,
                'email': '该账户尚未激活'
            })

        # TODO: need to uncomment this in production
        # send_reset_password_mail(user)
        return json.dumps({
            'result': True,
            'domain': get_domain_from_email(user.email) or ""
        })
    else:
        return json.dumps({
            'result': False,
            'email': form.email.errors[0] if len(form.email.errors) else ""
        })


@bp.route('/settings', methods=['GET', 'POST'])
@UserPermission()
def settings():
    """个人设置"""
    form = SettingsForm(obj=g.user)

    if form.validate_on_submit():
        form.populate_obj(g.user)
        db.session.add(g.user)
        db.session.commit()
        g.user.save_to_es()
        flash('设置已更新')
        return redirect(url_for('.settings'))
    return render_template('account/settings.html', form=form)


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


@bp.route('/account/upload_avatar', methods=['POST'])
@UserPermission()
def upload_avatar():
    """上传用户头像"""
    try:
        filename = process_user_avatar(request.files['file'], 200)
        g.user.avatar = filename
        db.session.add(g.user)
        db.session.commit()
    except Exception, e:
        return json.dumps({'result': False, 'error': e.__repr__()})
    else:
        return json.dumps({
            'result': True,
            'url': avatars.url(filename),
        })


@bp.route('/account/upload_background', methods=['POST'])
@UserPermission()
def upload_background():
    """上传用户首页背景"""
    try:
        filename = process_user_background(request.files['file'], 200)
        g.user.background = filename
        db.session.add(g.user)
        db.session.commit()
    except Exception, e:
        return json.dumps({'result': False, 'error': e.__repr__()})
    else:
        return json.dumps({
            'result': True,
            'url': images.url(filename)
        })


@bp.route('/reset_password', methods=['POST', 'GET'])
@VisitorPermission()
def reset_password():
    """重设密码"""
    # TODO: need to finish the reset logic
    if request.method == 'POST':
        return json.dumps({
            'result': True
        })
    else:
        return render_template('account/reset_password.html')


@bp.route('/account/update_setting', methods=['POST'])
@UserPermission()
def update_setting():
    """更新用户设置"""
    key = request.form.get('key')
    value = request.form.get('value')

    if not hasattr(g.user, key):
        return json.dumps({
            'result': False
        })

    setattr(g.user, key, True if value == 'on' else False)
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/account/update_name', methods=['POST'])
@UserPermission()
def update_name():
    """更新称谓"""
    if g.user.name_edit_count == 0:
        return json.dumps({
            'result': False
        })

    name = request.form.get('name')
    if not name:
        return json.dumps({
            'result': False
        })

    if name == g.user.name:
        return json.dumps({
            'result': True,
            'name_edit_count': g.user.name_edit_count
        })

    g.user.name = name
    g.user.name_edit_count -= 1
    db.session.add(g.user)
    db.session.commit()
    return json.dumps({
        'result': True,
        'name_edit_count': g.user.name_edit_count
    })


@bp.route('/account/update_email', methods=['POST'])
@UserPermission()
def update_email():
    """更新邮箱"""
    email = request.form.get('email')
    if not email:
        return json.dumps({
            'result': False
        })

    if email == g.user.email:
        g.user.inactive_email = ""
        db.session.add(g.user)
        db.session.commit()

        return json.dumps({
            'result': True,
            'active': g.user.is_active
        })

    g.user.inactive_email = email
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True,
        'active': False
    })


@bp.route('/account/update_url_token', methods=['POST'])
@UserPermission()
def update_url_token():
    """更新个人主页网址"""
    url_token = request.form.get('url_token')

    if not url_token:
        return json.dumps({
            'result': False
        })

    g.user.url_token = url_token
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/account/update_password', methods=['POST'])
@UserPermission()
def update_password():
    """更新密码"""
    password = request.form.get('password')

    if not password:
        return json.dumps({
            'result': False
        })

    g.user.password = password
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/account/select_interesting_topics')
@UserPermission()
def select_interesting_topics():
    """选择感兴趣的话题"""
    hot_topics = Topic.query.order_by(Topic.questions_count.desc()).limit(20)
    product_topics = Topic.query.filter(Topic.name == '产品').first().descendant_topics.limit(20)
    organization_topics = Topic.query.filter(Topic.name == '组织').first().descendant_topics.limit(20)
    position_topics = Topic.query.filter(Topic.name == '职业').first().descendant_topics.limit(20)
    skill_topics = Topic.query.filter(Topic.name == '技能').first().descendant_topics.limit(20)
    return render_template('account/select_interesting_topics.html', hot_topics=hot_topics,
                           product_topics=product_topics, organization_topics=organization_topics,
                           position_topics=position_topics, skill_topics=skill_topics)


@bp.route('/account/submit_interesting_topics', methods=['POST'])
@UserPermission()
def submit_interesting_topics():
    """提交感兴趣的话题"""
    topics_id_list = request.form.getlist('topic_id', type=int)
    topics_id_list = _remove_repeats(topics_id_list)

    for topic_id in topics_id_list:
        follow_topic = g.user.followed_topics.filter(FollowTopic.topic_id == topic_id).first()
        if not follow_topic:
            follow_topic = FollowTopic(user_id=g.user.id, topic_id=topic_id)
            db.session.add(follow_topic)

    g.user.has_selected_interesting_topics = True
    db.session.add(g.user)
    db.session.commit()

    return json.dumps({
        'result': True
    })


@bp.route('/account/select_products_worked_on')
@UserPermission()
def select_products_worked_on():
    """选择工作过的产品"""
    return render_template('account/select_products_worked_on.html')


@bp.route('/account/submit_product_worked_on', methods=['POST'])
@UserPermission()
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
        return json.dumps({
            'result': False
        })
    else:
        product = WorkOnProduct(topic_id=topic.id, user_id=g.user.id)
        db.session.add(product)
        db.session.commit()

        new_topic = name is not None and name != ""

        if new_topic:
            upload_token = qiniu.generate_token(policy={
                'callbackUrl': absolute_url_for('.update_avatar'),
                'callbackBody': "id=%d&key=$(key)" % topic.id
            })
        else:
            upload_token = ""

        macro = get_template_attribute('macros/_account.html', 'render_product_worked_on')
        return json.dumps({'result': True,
                           'html': macro(product, new_topic, upload_token)})


@bp.route('/account/product_worked_on/<int:uid>/set_current_working_on', methods=['POST'])
@UserPermission()
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
    return json.dumps({
        'result': True
    })


@bp.route('/account/product_worked_on/<int:uid>/cancel_set_current_working_on', methods=['POST'])
@UserPermission()
def cancel_set_product_current_working_on(uid):
    """取消设置为当前就职的产品"""
    product = WorkOnProduct.query.get_or_404(uid)
    product.current = False
    db.session.add(product)
    db.session.commit()
    return json.dumps({
        'result': True
    })


@bp.route('/account/product_worked_on/<int:uid>/remove', methods=['POST'])
@UserPermission()
def remove_product(uid):
    """移除产品"""
    product = WorkOnProduct.query.get_or_404(uid)
    db.session.delete(product)
    db.session.commit()
    return json.dumps({
        'result': True
    })


@bp.route('/account/follow_users')
@UserPermission()
def follow_users():
    """关注感兴趣的人"""
    return render_template('account/follow_users.html')


def _remove_repeats(seq):
    """去除列表中的重复元素"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
