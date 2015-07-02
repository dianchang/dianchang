# dc-models

## Usage

```py
from models import init_models

init_models(app)
```

`app` should has `ROOT_TOPIC_ID`, `DEFAULT_PARENT_TOPIC_ID`, `ELASTICSEARCH_HOST` configs in addition to SQLAlchemy configs.
