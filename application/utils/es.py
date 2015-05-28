# coding: utf-8
from elasticsearch import Elasticsearch

es = Elasticsearch()


def save_object_to_es(doc_type, id, body):
    """保存object到elasticsearch"""
    return es.index(index='dc', doc_type=doc_type, id=id, body=body)['created']


def delete_object_from_es(doc_type, id):
    """从elasticsearch中删除object"""
    return es.delete(index='dc', doc_type=doc_type, id=id)['found']


def search_objects_from_es(doc_type, body):
    """从elasticsearch中查询符合要求的objects"""
    return es.search(index="dc", doc_type=doc_type, body=body)
