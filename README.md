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
curl -XPUT 'http://localhost:9200/dc' -d '
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
}'
```

###应用analyzer到field

```
curl -XPUT 'http://localhost:9200/dc/_mapping/topic' -d '
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
}'

curl -XPUT 'http://localhost:9200/dc/_mapping/user' -d '
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
}'
```

###填充数据

```py
python manage.py index_es

```
