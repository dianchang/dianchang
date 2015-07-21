# coding: utf-8
import glob2
import os
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand
from application import create_app
from application.models import db, QuestionTopic, RelevantTopic, User, Answer, Question, \
    AnswerComment, Topic
from application.utils.answer import generate_qrcode_for_answer

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
    upload_dir('output/pkg')
    upload_dir('output/static')


def upload_dir(dir_name):
    """上传文件夹中的文件到七牛"""
    from application.utils._qiniu import qiniu

    for root, _, files in os.walk(os.path.join(os.getcwd(), dir_name)):
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
    pass


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

    db.session.commit()


@manager.command
def relevant_topics():
    import operator

    for topic in Topic.query.filter(Topic.id == 13):
        map(db.session.delete, topic.relevant_topics)

        relevant_topics = {}
        for question in topic.questions:
            for _topic in question.question.topics.filter(QuestionTopic.topic_id != topic.id):
                if _topic.topic_id in relevant_topics:
                    relevant_topics[_topic.topic_id] += 1
                else:
                    relevant_topics[_topic.topic_id] = 0

        relevant_topics = sorted(relevant_topics.items(), key=operator.itemgetter(1))
        relevant_topics.reverse()
        for relevant_topic_id, score in relevant_topics:
            relevant_topic = RelevantTopic(topic_id=topic.id, relevant_topic_id=relevant_topic_id, score=score)
            db.session.add(relevant_topic)
        db.session.commit()


@manager.command
def make_answer_qrcodes():
    with app.app_context():
        for answer in Answer.query:
            generate_qrcode_for_answer(answer)
            db.session.add(answer)
        db.session.commit()


if __name__ == "__main__":
    manager.run()
