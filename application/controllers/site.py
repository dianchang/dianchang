# coding: utf-8
from flask import render_template, Blueprint
from ..models import db, Question, Answer

bp = Blueprint('site', __name__)


@bp.route('/')
def index():
    """Index page."""
    answers = Answer.query.limit(5)
    return render_template('site/index.html', answers=answers)


@bp.route('/about')
def about():
    """About page."""
    return render_template('site/about.html')