# coding: utf-8
from flask_wtf import Form
from wtforms import StringField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Optional


class AddQuestionForm(Form):
    title = StringField('问题', validators=[DataRequired('问题不能为空')])
    desc = TextAreaField('补充问题描述', validators=[Optional()])
