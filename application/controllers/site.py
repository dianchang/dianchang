# coding: utf-8
import math
from flask import render_template, Blueprint, request, redirect, g, json, current_app, get_template_attribute
from ..models import db, Question, Answer, Topic, User
from ..utils.permissions import UserPermission
from ..utils.uploadsets import process_site_image, images

bp = Blueprint('site', __name__)

HOME_FEEDS_PER_PAGE = 10


@bp.route('/')
def index():
    """首页"""
    if not g.user:
        answers = Answer.query.order_by(Answer.created_at.desc()).limit(5)
        return render_template('site/index.html', answers=answers)
    else:
        feeds = g.user.home_feeds.limit(HOME_FEEDS_PER_PAGE)
        total = g.user.home_feeds.count()
        hot_topics = Topic.query.limit(8)
        return render_template('site/index_signin.html', hot_topics=hot_topics, feeds=feeds,
                               total=total, per_page=HOME_FEEDS_PER_PAGE)


@bp.route('/site/loading_home_feeds', methods=['POST'])
@UserPermission()
def loading_home_feeds():
    """加载首页 feeds"""
    offset = request.args.get('offset', type=int)
    if not offset:
        return json.dumps({
            'result': False
        })

    feeds = g.user.home_feeds.limit(HOME_FEEDS_PER_PAGE).offset(offset)
    feeds_count = feeds.count()
    macro = get_template_attribute("macros/_user.html", "render_user_home_feeds")
    return json.dumps({
        'result': True,
        'html': macro(feeds),
        'count': feeds_count
    })


@bp.route('/about')
def about():
    """关于页"""
    return render_template('site/about.html')


@bp.route('/search')
def search():
    """搜索页"""
    q = request.args.get('q', '')
    q = q.strip()
    page = request.args.get('page', 1, int)
    per_page = 10
    _type = request.args.get('type', 'question')
    if not q:
        return redirect(request.referrer)
    if _type == "topic":
        results, total, took = Topic.query_from_es(q, page=page, per_page=per_page)
    elif _type == 'answer':
        results, total, took = Answer.query_from_es(q, page=page, per_page=per_page)
    elif _type == 'user':
        results, total, took = User.query_from_es(q, page=page, per_page=per_page)
    else:
        # 默认为问题
        _type = 'question'
        results, total, took = Question.query_from_es(q, page=page, per_page=per_page)

    # 在问题页、回答页中，若存在精准匹配的人、话题，则显示在右侧
    if _type in ['question', 'answer']:
        exact_user = User.query.filter(User.name == q).first()
        exact_topic = Topic.query.filter(Topic.name == q).first()
    else:
        exact_user = None
        exact_topic = None

    pages = int(math.ceil(float(total) / per_page))
    pre_page = None if page <= 1 else page - 1
    next_page = None if page >= pages else page + 1
    return render_template('site/search.html', q=q, results=results, _type=_type,
                           page=page, pre_page=pre_page, next_page=next_page,
                           total=total, took=took, exact_user=exact_user,
                           exact_topic=exact_topic)


@bp.route('/upload_image', methods=['POST'])
@UserPermission()
def upload_image():
    """上传通用图片"""
    try:
        filename = process_site_image(request.files['file'])
    except Exception, e:
        return json.dumps({'result': False, 'error': e.__repr__()})
    else:
        return json.dumps({
            'success': True,
            'file_path': images.url(filename),
        })


@bp.route('/qiniu_upload_callback_for_simditor', methods=['POST'])
def qiniu_upload_callback_for_simditor():
    """用于七牛上传回调"""
    key = request.form.get('key')
    cdn_host = current_app.config.get('CDN_HOST')
    return json.dumps({
        'success': True,
        'file_path': "%s/%s" % (cdn_host, key)
    })
