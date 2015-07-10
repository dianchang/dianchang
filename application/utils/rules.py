# coding: utf-8
from flask import session, abort, flash, redirect, url_for, g
from permission import Rule
from ..models import User


class VisitorRule(Rule):
    def check(self):
        return 'user_id' not in session

    def deny(self):
        return redirect(url_for('site.index'))


class UserRule(Rule):
    def check(self):
        return 'user_id' in session

    def deny(self):
        return redirect(url_for('account.signin'))


class UserActiveRule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_active

    def deny(self):
        return redirect(url_for('account.settings'))


class AdminRule(Rule):
    def base(self):
        return UserRule()

    def check(self):
        return g.user.is_admin

    def deny(self):
        abort(403)
