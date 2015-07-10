# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired
from ..models import Topic


class AdminTopicForm(Form):
    wiki = TextAreaField('话题百科')


class EditTopicWikiForm(Form):
    wiki = TextAreaField('Wiki', validators=[])
