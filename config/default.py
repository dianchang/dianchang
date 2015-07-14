# coding: utf-8
import os


class Config(object):
    """Base config class."""
    # Flask app config
    DEBUG = False
    TESTING = False
    SECRET_KEY = "\xb5\xb3}#\xb7A\xcac\x9d0\xb6\x0f\x80z\x97\x00\x1e\xc0\xb8+\xe9)\xf0}"
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7
    SESSION_COOKIE_NAME = 'dianchang_session'

    # Root path of project
    PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Site domain
    SITE_TITLE = "dianchang"
    SITE_DOMAIN = "http://localhost:5000"
    DC_DOMAIN = SITE_DOMAIN

    # SQLAlchemy config
    # See:
    # https://pythonhosted.org/Flask-SQLAlchemy/config.html#connection-uri-format
    # http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:password@host/database"
    SQLALCHEMY_BINDS = {
        'dc': "mysql+pymysql://user:password@host/database"
    }

    # Uploadsets config
    UPLOADS_DEFAULT_DEST = "%s/uploads" % PROJECT_PATH
    UPLOADS_DEFAULT_URL = "%s/uploads/" % SITE_DOMAIN

    # Flask-DebugToolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Sentry config
    SENTRY_DSN = ''

    # Host string, used by fabric
    HOST_STRING = "root@12.34.56.78"
