# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from ..models import Topic


class AdminTopicForm(Form):
    name = StringField('话题名称', validators=[DataRequired('话题名称不能为空')])
    desc = TextAreaField('话题描述')

    def validate_name(self, field):
        topic = Topic.get_by_name(field.data)
        if topic:
            raise ValueError('话题名称已存在')


class EditTopicWikiForm(Form):
    wiki = TextAreaField('Wiki', validators=[])
