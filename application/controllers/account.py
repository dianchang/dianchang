# coding: utf-8
from flask import render_template, Blueprint, redirect, request, url_for, flash, g, json, session
from ..forms import SigninForm, SignupForm, SettingsForm, ForgotPasswordForm
from ..utils.account import signin_user, signout_user
from ..utils.permissions import VisitorPermission, UserPermission
from ..utils.helpers import get_domain_from_email
from ..utils.uploadsets import process_user_avatar, avatars, images, process_user_background
from ..models import db, User, InvitationCode

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
                'referer': session['referer'] or url_for('site.index')
            })
        else:
            return json.dumps({
                'result': False,
                'email': form.email.errors[0] if len(form.email.errors) else "",
                'password': form.password.errors[0] if len(form.password.errors) else "",
                'referer': session['referer'] or url_for('site.index')
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
