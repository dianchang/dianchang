# coding: utf-8
import math
from flask import render_template, Blueprint, request, redirect, abort
from ..models import db, Question, Answer, Topic, User

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


@bp.route('/search')
def search():
    q = request.args.get('q')
    page = request.args.get('page', 1, int)
    per_page = 10
    _type = request.args.get('type', 'question')
    if not q:
        return redirect(request.referrer)
    if _type == "topic":
        results, total, took = Topic.query_from_es(q, page, per_page)
    elif _type == 'answer':
        results, total, took = Answer.query_from_es(q, page, per_page)
    elif _type == 'user':
        results, total, took = User.query_from_es(q, page, per_page)
    else:
        results, total, took = Question.query_from_es(q, page, per_page)
    pages = int(math.ceil(float(total) / per_page))
    pre_page = None if page <= 1 else page - 1
    next_page = None if page >= pages else page + 1
    return render_template('site/search.html', q=q, results=results, _type=_type,
                           page=page, pre_page=pre_page, next_page=next_page,
                           total=total, took=took)
