# coding: utf-8
from flask import render_template, Blueprint, request, json
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


@bp.route('/site/search')
def search():
    q = request.args.get('q')
    _type = request.form.get('type', 'question')
    if _type == 'question' and q:
        questions = Question.query_from_es(q)
    return render_template('site/search.html', q=q, questions=questions)
