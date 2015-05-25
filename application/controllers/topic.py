# coding: utf-8
from flask import Blueprint, render_template

bp = Blueprint('topic', __name__)


@bp.route('/topic/action')
def action():
    return render_template('topic/action.html')
