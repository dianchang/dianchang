# coding: utf-8
from flask import render_template, Blueprint
from ..models import db, Question

bp = Blueprint('site', __name__)


@bp.route('/')
def index():
    """Index page."""
    questions = Question.query.limit(5)
    return render_template('site/index.html', questions=questions)


@bp.route('/about')
def about():
    """About page."""
    return render_template('site/about.html')