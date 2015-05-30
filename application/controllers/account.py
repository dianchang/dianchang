# coding: utf-8
from flask import render_template, Blueprint, redirect, request, url_for, flash, g
from ..forms import SigninForm, SignupForm, SettingsForm
from ..utils.account import signin_user, signout_user
from ..utils.permissions import VisitorPermission, UserPermission
from ..models import db, User

bp = Blueprint('account', __name__)


@bp.route('/signin', methods=['GET', 'POST'])
@VisitorPermission()
def signin():
    """登录"""
    form = SigninForm()
    if form.validate_on_submit():
        signin_user(form.user, form.remember.data)
        return redirect(url_for('site.index'))
    return render_template('account/signin.html', form=form)


@bp.route('/signup', methods=['GET', 'POST'])
@VisitorPermission()
def signup():
    """注册"""
    form = SignupForm()
    if form.validate_on_submit():
        params = form.data.copy()
        params.pop('repassword')
        user = User(**params)
        db.session.add(user)
        db.session.commit()
        signin_user(user)
        return redirect(url_for('site.index'))
    return render_template('account/signup.html', form=form)


@bp.route('/signout')
def signout():
    """登出"""
    signout_user()
    return redirect(request.referrer or url_for('site.index'))


@bp.route('/account/settings', methods=['GET', 'POST'])
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
