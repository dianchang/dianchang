from ._base import db
from .user import *
from .question import *
from .topic import *
from .answer import *
from .log import *


def init_models(app):
    from ._helpers import init_es

    db.init_app(app)
    db.config = {
        'CDN_HOST': app.config.get('CDN_HOST'),
        'ROOT_TOPIC_ID': app.config.get('ROOT_TOPIC_ID'),
        'DEFAULT_PARENT_TOPIC_ID': app.config.get('DEFAULT_PARENT_TOPIC_ID')
    }

    init_es(app.config.get('ELASTICSEARCH_HOSTS'))
