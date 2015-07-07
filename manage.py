# coding: utf-8
import glob2
import os
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from application import create_app
from application.models import db

# Used by app debug & livereload
PORT = 5000

app = create_app()
manager = Manager(app)

# db migrate commands
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.command
def run():
    """Run app."""
    app.run(port=PORT)


@manager.command
def live():
    """Run livereload server"""
    from livereload import Server

    server = Server(app)

    # html
    for filepath in glob2.glob("application/templates/**/*.html"):
        server.watch(filepath)
    # css
    for filepath in glob2.glob("application/static/css/**/*.css"):
        server.watch(filepath)
    # js
    for filepath in glob2.glob("application/static/js/**/*.js"):
        server.watch(filepath)
    # image
    for filepath in glob2.glob("application/static/image/**/*.*"):
        server.watch(filepath)

    server.serve(port=PORT)


@manager.command
def createdb():
    """Create database."""
    db.create_all()


@manager.command
def save_to_es():
    from application.models import Question, Topic, Answer, User

    with app.app_context():
        for question in Question.query:
            question.save_to_es()
        for topic in Topic.query:
            topic.save_to_es()
        for answer in Answer.query:
            answer.save_to_es()
        for user in User.query:
            user.save_to_es()


@manager.command
def salt():
    from werkzeug.security import gen_salt

    print(gen_salt(7))


@manager.command
def upload():
    """上传静态资源到CDN"""
    from application.utils._qiniu import qiniu

    for root, _, files in os.walk(os.path.join(os.getcwd(), 'output/pkg')):
        for f in files:
            absolute_path = os.path.join(root, f)
            relative_path = absolute_path.split(os.path.join(os.getcwd(), 'output'))[1].lstrip('/')
            qiniu.upload_file(relative_path, absolute_path)
            print("%s - uploaded" % relative_path)

    for root, _, files in os.walk(os.path.join(os.getcwd(), 'output/static')):
        for f in files:
            absolute_path = os.path.join(root, f)
            relative_path = absolute_path.split(os.path.join(os.getcwd(), 'output'))[1].lstrip('/')
            qiniu.upload_file(relative_path, absolute_path)
            print("%s - uploaded" % relative_path)


@manager.command
def build():
    """使用 FIS 编译静态资源"""
    os.chdir('application')
    os.system('fis release -d ../output -opmD')


@manager.command
def test():
    # graph = {'A': ['B', 'C'],
    #          'B': ['C', 'D'],
    #          'C': ['D'],
    #          'D': ['C'],
    #          'E': ['F'],
    #          'F': ['C']}
    #
    # graph1 = {
    #     'A': ['B', 'C'],
    #     'B': ['D'],
    #     'C': ['D']
    # }
    #
    # def find_path(graph, start, end, path=[]):
    #     path = path + [start]
    #     if start == end:
    #         return path
    #     if not graph.has_key(start):
    #         return None
    #     for node in graph[start]:
    #         if node not in path:
    #             newpath = find_path(graph, node, end, path)
    #             if newpath:
    #                 return newpath
    #     return None
    #
    # def find_all_paths(graph, start, end, path=[]):
    #     path = path + [start]
    #     if start == end:
    #         return [path]
    #     if not graph.has_key(start):
    #         return []
    #     paths = []
    #     for node in graph[start]:
    #         if node not in path:
    #             newpaths = find_all_paths(graph, node, end, path)
    #             for newpath in newpaths:
    #                 paths.append(newpath)
    #     return paths
    #
    # print(find_all_paths(graph1, 'A', 'D'))
    from pypinyin import pinyin, lazy_pinyin

    a = unicode("呵呵s")
    print(''.join(lazy_pinyin(a)))


@manager.command
def pinyin():
    from application.models import db, User, Topic

    with app.app_context():
        for user in User.query:
            user.name = user.name
            db.session.add(user)
        for topic in Topic.query:
            topic.name = topic.name
            db.session.add(topic)
        db.session.commit()


@manager.command
def uniform():
    from flask import json
    from application.models import db, User, Answer, Question, AnswerComment, Notification, Topic

    for user in User.query:
        user.followers_count = user.followers.count()
        user.followings_count = user.followings.count()
        user.questions_count = user.questions.count()
        user.answers_count = user.answers.count()
        user.drafts_count = user.drafts.count()
        db.session.add(user)

    for answer in Answer.query:
        answer.comments_count = answer.comments.count()
        answer.upvotes_count = answer.upvotes.count()
        answer.downvotes_count = answer.downvotes.count()
        answer.thanks_count = answer.thanks.count()
        answer.nohelps_count = answer.nohelps.count()
        db.session.add(answer)

    for topic in Topic.query:
        topic.followers_count = topic.followers.count()
        db.session.add(topic)

    for question in Question.query:
        question.answers_count = question.answers.count()
        question.followers_count = question.followers.count()
        db.session.add(question)

    for comment in AnswerComment.query:
        comment.likes_count = comment.likes.count()
        db.session.add(comment)

    # for answer_comment in AnswerComment.query:
    #     answer_comment.question_id = answer_comment.answer.question_id
    #     db.session.add(answer_comment)
    #
    # for noti in Notification.query:
    #     noti.senders_list = json.dumps([noti.sender_id])
    #     db.session.add(noti)

    db.session.commit()


if __name__ == "__main__":
    manager.run()
