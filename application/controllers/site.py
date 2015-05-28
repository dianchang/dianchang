# coding: utf-8
from flask import render_template, Blueprint, request, redirect
from ..models import db, Question, Answer, Topic

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
    _type = request.args.get('type', 'question')
    if not q:
        return redirect(request.referrer)
    if _type == "question":
        results = Question.query_from_es(q)
    elif _type == "topic":
        results = Topic.query_from_es(q)
    return render_template('site/search.html', q=q, results=results, _type=_type)
