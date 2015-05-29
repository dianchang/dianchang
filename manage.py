# coding: utf-8
import glob2
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from application import create_app
from application.models import db
from application.utils.assets import build, upload

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
def build_assets():
    build(app)


@manager.command
def upload_assets():
    upload(app)


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


if __name__ == "__main__":
    manager.run()
