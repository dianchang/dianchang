# coding: utf-8
from flask import Blueprint, render_template, redirect, url_for, request, g
from ..forms import AddQuestionForm
from ..models import db, Question, Answer

bp = Blueprint('question', __name__)


@bp.route('/question/add', methods=['GET', 'POST'])
def add():
    form = AddQuestionForm()
    if form.validate_on_submit():
        question = Question(**form.data)
        question.user_id = g.user.id
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('.view', uid=question.id))
    return render_template('question/add.html', form=form)


@bp.route('/question/<int:uid>', methods=['GET', 'POST'])
def view(uid):
    question = Question.query.get_or_404(uid)
    if request.method == 'POST' and request.form.get('answer'):
        answer = Answer(question_id=uid, content=request.form.get('answer'), user_id=g.user.id)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('.view', uid=uid))
    return render_template('question/view.html', question=question)
