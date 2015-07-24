电场
=======

http://119.254.102.136

互联网职业领域问答社区

## 开发环境搭建

Install [FIS](http://fis.baidu.com):

```
npm install -g fis
npm install -g fis-postpackager-simple
```

Install `Flask-Boost` via:

```
sudo pip install git+https://github.com/hustlzp/Flask-Boost.git@fis#egg=flask_boost
```

Update `Flask-Boost` via:

```
sudo pip install -U git+https://github.com/hustlzp/Flask-Boost.git@fis#egg=flask_boost
```  

## Elasticsearch配置

###创建index

```
PUT /dc
{
    "settings": {
        "number_of_shards": 1,
        "analysis": {
            "filter": {
                "autocomplete_filter": {
                    "type":     "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 20
                }
            },
            "analyzer": {
                "autocomplete": {
                    "type":      "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "autocomplete_filter"
                    ]
                }
            }
        }
    }
}
```

###应用analyzer到field

```
PUT /dc/_mapping/topic
{
    "topic": {
        "properties": {
            "name": {
                "type":     "string",
                "analyzer": "autocomplete"
            },
            "name_pinyin": {
                "type":     "string",
                "analyzer": "autocomplete"
            },
            "synonyms": {
                "type":     "string",
                "analyzer": "autocomplete"
            }
        }
    }
}

PUT /dc/_mapping/user
{
    "user": {
        "properties": {
            "name": {
                "type":     "string",
                "analyzer": "autocomplete"
            },
            "name_pinyin": {
                "type":     "string",
                "analyzer": "autocomplete"
            }
        }
    }
}
```

###填充数据

```py
python manage.py index_es

```
