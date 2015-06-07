# coding: utf-8
from flask import render_template, Blueprint, redirect, request, url_for, flash, g, json
from ..forms import SigninForm, SignupForm, SettingsForm, ForgotPasswordForm
from ..utils.account import signin_user, signout_user
from ..utils.permissions import VisitorPermission, UserPermission
from ..utils.helpers import get_domain_from_email
from ..utils.uploadsets import process_user_avatar, avatars
from ..models import db, User

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
                'result': True
            })
        else:
            print(dir(form))
            return json.dumps({
                'result': False,
                'email': form.email.errors[0] if len(form.email.errors) else "",
                'password': form.password.errors[0] if len(form.password.errors) else ""
            })
    return render_template('account/signin.html')


@bp.route('/signup', methods=['GET', 'POST'])
@VisitorPermission()
def signup():
    """注册"""
    form = SignupForm()
    if form.validate_on_submit():
        code = form.code.data
        params = form.data.copy()
        params.pop('code')
        user = User(**params)
        db.session.add(user)
        db.session.commit()
        user.save_to_es()  # 存储到elasticsearch
        signin_user(user)
        return redirect(url_for('site.index'))
    return render_template('account/signup.html', form=form)


@bp.route('/signout')
def signout():
    """登出"""
    signout_user()
    return redirect(request.referrer or url_for('site.index'))


@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """忘记密码"""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter(User.email == form.email.data).first()

        if not user.is_active:
            return render_template('site/message.html', title="提示", message='请先完成账号激活')
        # send_reset_password_mail(user)

        email_domain = get_domain_from_email(user.email)
        if email_domain:
            message = "请 <a href='%s' target='_blank'>登录邮箱</a> 完成密码重置" % email_domain
        else:
            message = "请登录邮箱完成密码重置"
        return render_template('site/message.html',
                               title="发送成功",
                               message=message)
    return render_template('account/forgot_password.html', form=form)


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


@bp.route('/account/notification_settings')
@UserPermission()
def notification_settings():
    """消息设置"""
    return render_template('account/notification_settings.html')


@bp.route('/account/privacy_settings')
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
    except Exception, e:
        return json.dumps({'result': False, 'error': e.__repr__()})
    else:
        return json.dumps({
            'result': True,
            'image_url': avatars.url(filename),
        })
