# coding: utf-8
from flask import Blueprint, render_template, url_for
from ..models import db, User

bp = Blueprint('people', __name__)


@bp.route('/people/<int:uid>')
def profile(uid):
    user = User.query.get_or_404(uid)
    return render_template('people/profile.html', user=user)
