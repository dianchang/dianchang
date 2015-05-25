# coding: utf-8
from flask import Blueprint, render_template

bp = Blueprint('topic', __name__)


@bp.route('/topic/square')
def square():
    return render_template('topic/square.html')
