# dc-models

## Usage

Clone it as git submodule:

```sh
$ git submodule add https://github.com/dianchang/dianchang-models models
```

Then:

```py
from models import init_models

init_models(app)
```

`app` should has `ROOT_TOPIC_ID`, `DEFAULT_PARENT_TOPIC_ID`, `ELASTICSEARCH_HOST` configs in addition to SQLAlchemy configs.
