from flask import Flask
from ._base import db
from .user import *
from .question import *
from .topic import *
from .answer import *
from .log import *


def init_models(app):
    from ._helpers import es
    from elasticsearch import Elasticsearch

    db.init_app(app)
    db.config = {
        'ROOT_TOPIC_ID': app.config.get('ROOT_TOPIC_ID'),
        'DEFAULT_PARENT_TOPIC_ID': app.config.get('DEFAULT_PARENT_TOPIC_ID')
    }

    es = Elasticsearch(hosts=[app.config.get('ELASTICSEARCH_HOST')])
