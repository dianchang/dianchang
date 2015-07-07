# coding: utf-8
import sys
import os

# Insert project root path to sys.path
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

import time
import logging
from flask import Flask, request, url_for, g, render_template
from flask_wtf.csrf import CsrfProtect
from flask.ext.uploads import configure_uploads
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.contrib.fixers import ProxyFix
from flask_turbolinks import turbolinks
from six import iteritems
from .utils.account import get_current_user
from config import load_config

# convert python's encoding to utf8
try:
    from imp import reload

    reload(sys)
    sys.setdefaultencoding('utf8')
except (AttributeError, NameError):
    pass


def create_app():
    """Create Flask app."""
    config = load_config()

    if config.DEBUG or config.TESTING:
        app = Flask(__name__)
    else:
        app = Flask(__name__, template_folder=os.path.join(project_path, 'output/templates'))

    app.config.from_object(config)

    if not hasattr(app, 'production'):
        app.production = not app.debug and not app.testing

    # Proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # CSRF protect
    CsrfProtect(app)

    # Log errors to stderr in production mode
    if app.production:
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.ERROR)
        turbolinks(app)

        # Enable Sentry
        if app.config.get('SENTRY_DSN'):
            from .utils.sentry import sentry

            sentry.init_app(app, dsn=app.config.get('SENTRY_DSN'))
    else:
        DebugToolbarExtension(app)

        # Serve static files during development
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/uploads': os.path.join(app.config.get('PROJECT_PATH'), 'uploads')
        })

    # Register components
    register_db(app)
    register_routes(app)
    register_jinja(app)
    register_error_handle(app)
    register_uploadsets(app)
    register_hooks(app)
    register_qiniu(app)

    return app


def register_jinja(app):
    """Register jinja filters, vars, functions."""
    from .utils import filters, permissions, helpers
    from .models import QUESTION_EDIT_KIND, USER_FEED_KIND, NOTIFICATION_KIND, TOPIC_EDIT_KIND, HOME_FEED_KIND, \
        COMPOSE_FEED_KIND

    app.jinja_env.filters.update({
        'timesince': filters.timesince,
        'cn_month': filters.cn_month,
        'day': filters.day
    })

    def url_for_other_page(page):
        """Generate url for pagination."""
        view_args = request.view_args.copy()
        args = request.args.copy().to_dict()
        combined_args = dict(view_args.items() + args.items())
        combined_args['page'] = page
        return url_for(request.endpoint, **combined_args)

    # routes
    rules = {}
    for endpoint, _rules in iteritems(app.url_map._rules_by_endpoint):
        if any(item in endpoint for item in ['_debug_toolbar', 'debugtoolbar', 'static']):
            continue
        rules[endpoint] = [{'rule': rule.rule} for rule in _rules]

    def page_id(template_reference):
        """Generate page with format: page-<controller>-<action>."""
        template_name = _get_template_name(template_reference)
        return "page-%s" % template_name.replace('.html', '').replace('/', '-').replace('_', '-')

    app.jinja_env.globals.update({
        'absolute_url_for': helpers.absolute_url_for,
        'url_for_other_page': url_for_other_page,
        'rules': rules,
        'permissions': permissions,
        'page_id': page_id,
        'QUESTION_EDIT_KIND': QUESTION_EDIT_KIND,
        'TOPIC_EDIT_KIND': TOPIC_EDIT_KIND,
        'NOTIFICATION_KIND': NOTIFICATION_KIND,
        'USER_FEED_KIND': USER_FEED_KIND,
        'HOME_FEED_KIND': HOME_FEED_KIND,
        'COMPOSE_FEED_KIND': COMPOSE_FEED_KIND
    })


def register_db(app):
    """Register models."""
    from .models import db, init_models

    init_models(app)


def register_routes(app):
    """Register routes."""
    from . import controllers
    from flask.blueprints import Blueprint

    for module in _import_submodules_from_package(controllers):
        bp = getattr(module, 'bp')
        if bp and isinstance(bp, Blueprint):
            app.register_blueprint(bp)


def register_error_handle(app):
    """Register HTTP error pages."""

    @app.errorhandler(403)
    def page_403(error):
        return render_template('site/403.html'), 403

    @app.errorhandler(404)
    def page_404(error):
        return render_template('site/404.html'), 404

    @app.errorhandler(500)
    def page_500(error):
        return render_template('site/500.html'), 500


def register_uploadsets(app):
    """Register UploadSets."""
    from .utils.uploadsets import avatars, topic_avatars, images

    configure_uploads(app, (avatars, topic_avatars, images))


def register_hooks(app):
    """Register hooks."""

    @app.before_request
    def before_request():
        from application.models import Notification, NOTIFICATION_KIND, NOTIFICATION_KIND_TYPE
        from application.utils._qiniu import qiniu
        from application.utils.helpers import absolute_url_for

        g.user = get_current_user()
        if g.user and g.user.is_admin:
            g._before_request_time = time.time()

        # 是否有新的撰写消息
        if not g.user:
            g.has_new_compose_feeds = False
        else:
            latest_compose_feed = g.user.compose_feeds.first()
            if not latest_compose_feed:
                g.has_new_compose_feeds = False
            else:
                g.has_new_compose_feeds = g.user.last_read_compose_feeds_at < latest_compose_feed.created_at

        # 新消息条数
        if not g.user:
            g.notifications_count = 0
            g.message_notifications_count = 0
            g.user_notifications_count = 0
            g.thanks_notifications_count = 0
        else:
            g.notifications_count = g.user.notifications.filter(Notification.unread).count()
            if g.notifications_count != 0:
                g.message_notifications_count = g.user.notifications.filter(
                    Notification.unread, Notification.kind.in_(NOTIFICATION_KIND_TYPE.MESSAGE)).count()
                g.user_notifications_count = g.user.notifications.filter(
                    Notification.unread, Notification.kind.in_(NOTIFICATION_KIND_TYPE.USER)).count()
                g.thanks_notifications_count = g.user.notifications.filter(
                    Notification.unread, Notification.kind.in_(NOTIFICATION_KIND_TYPE.THANKS)).count()
            else:
                g.message_notifications_count = 0
                g.user_notifications_count = 0
                g.thanks_notifications_count = 0

        # Simditor 上传七牛 token
        g.editorUptoken = qiniu.generate_token(policy={
            'callbackUrl': absolute_url_for('site.qiniu_upload_callback_for_simditor'),
            'callbackBody': "key=$(key)"
        })

    @app.after_request
    def after_request(response):
        if hasattr(g, '_before_request_time'):
            delta = time.time() - g._before_request_time
            response.headers['X-Render-Time'] = delta * 1000
        return response


def register_qiniu(app):
    from .utils._qiniu import qiniu

    qiniu.init_app(app)


def _get_template_name(template_reference):
    """Get current template name."""
    return template_reference._TemplateReference__context.name


def _import_submodules_from_package(package):
    import pkgutil

    modules = []
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__,
                                                         prefix=package.__name__ + "."):
        modules.append(__import__(modname, fromlist="dummy"))
    return modules


def _get_template_name(template_reference):
    """Get current template name."""
    return template_reference._TemplateReference__context.name
