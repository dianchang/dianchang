from flask import Flask
from ._base import db
from .user import *
from .question import *
from .topic import *
from .answer import *
from .log import *


def init_models(app):
    db.init_app(app)
    db.config = {
        'ROOT_TOPIC_ID': app.config['ROOT_TOPIC_ID'],
        'DEFAULT_PARENT_TOPIC_ID': app.config['DEFAULT_PARENT_TOPIC_ID']
    }
