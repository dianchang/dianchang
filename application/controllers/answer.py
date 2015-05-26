# coding: utf-8
from flask import Blueprint, render_template
from ..models import db, Answer

bp = Blueprint('answer', __name__)


@bp.route('/answer/<int:uid>')
def view(uid):
    answer = Answer.query.get_or_404(uid)
    return render_template('answer/view.html', answer=answer)
