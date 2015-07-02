# coding: utf-8
from .default import Config


class DevelopmentConfig(Config):
    # App config
    DEBUG = True

    # SQLAlchemy config
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:password@localhost/dianchang"
    SQLALCHEMY_BINDS = {
        'dc': "mysql+pymysql://root:password@localhost/dianchang"
    }
