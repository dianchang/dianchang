# coding: utf-8
import re
from pypinyin import lazy_pinyin
from HTMLParser import HTMLParser
from elasticsearch import Elasticsearch


def pinyin(text):
    """将文本转换为拼音"""
    return ''.join(lazy_pinyin(unicode(text)))


def get_pure_content(content):
    """获取用于摘要的文本"""

    pure_content = remove_html(content)  # 去除HTML标签
    pure_content = pure_content.strip().strip('　')  # 去除首位的空格、缩进
    pure_content = pure_content.replace('　', ' ')  # 将缩进替换为空格
    pure_content = re.sub('\s+', ' ', pure_content)  # 将多个空格替换为单个空格
    return pure_content


class MLStripper(HTMLParser):
    """
    See: http://stackoverflow.com/questions/753052/strip-html-from-strings-in-python
    """

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def remove_html(text):
    """Remove HTML elements from string."""
    s = MLStripper()
    s.feed(text)
    return s.get_data()


class ES(object):
    es = None


def init_es(hosts=None):
    ES.es = Elasticsearch(hosts)


def save_object_to_es(doc_type, id, body):
    """保存object到elasticsearch"""
    return ES.es.index(index='dc', doc_type=doc_type, id=id, body=body)['created']


def delete_object_from_es(doc_type, id):
    """从elasticsearch中删除object"""
    return ES.es.delete(index='dc', doc_type=doc_type, id=id)['found']


def search_objects_from_es(doc_type, body):
    """从elasticsearch中查询符合要求的objects"""
    return ES.es.search(index="dc", doc_type=doc_type, body=body)
