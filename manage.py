# coding: utf-8
import glob2
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


if __name__ == "__main__":
    manager.run()
