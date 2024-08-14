___version__ = '0.8.2'

import pathlib
import shutil
import time
from datetime import timedelta

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
import flask_uploads
import flask_login
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap4
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_alembic import Alembic

from AM_Nihoul_website.base_filters import filters

LOGLEVEL = 'INFO'


class Config:
    # Flask secret key: generate a new one with
    # `python -c "import random; print(repr(''.join([chr(random.randrange(32, 126)) for _ in range(24)])))"`
    SECRET_KEY = ';+b&#Yl] U$y7dzmW&IRh$GO'

    # change that in production
    SERVER_NAME = '127.0.0.1:5000'

    # username/password to access admin (change that in production)
    USERNAME = 'admin'
    PASSWORD = 'admin'

    # data
    DATA_DIRECTORY = pathlib.Path('data/')

    # database
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # alembic
    ALEMBIC_CONTEXT = {
        # useful since the database is sqlite (https://alembic.sqlalchemy.org/en/latest/batch.html)!
        'render_as_batch': True
    }

    # upload
    UPLOADED_PICTURES_URL = '/photos/'
    UPLOAD_CONVERT_TO_JPG = 250 * 1024
    PICTURE_THUMB_SIZE = (400, 300)

    # newsletter
    REMOVE_RECIPIENTS_DELTA = timedelta(days=5)
    NEWSLETTER_SENDER_EMAIL = 'xyz@test.com'
    NEWSLETTER_REPLY_TO_EMAIL = None
    USE_FAKE_MAIL_SENDER = False
    LAUNCH_BOT = True
    BOT_SERVICE_NAME = None
    NEWSLETTER_LOGO = 'AM_Nihoul_website/assets/images/newsletter_logo.png'

    # scheduler
    JOBS = [
        {
            'id': 'bot',
            'func': 'AM_Nihoul_website:bot.bot_iteration',
            'trigger': 'interval',
            'seconds': 60
        }
    ]

    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 1
    }

    # important pages
    PAGES = {
        'visitor_index': 1,
        'admin_index': 2,
        'contact_page': 3,
    }

    # recaptcha secret key
    RECAPTCHA_SECRET_KEY = ''


WEBPAGE_INFO = {
    'author_url': 'https://pierrebeaujean.net/fr.html',
    'author_name': 'Pierre Beaujean',
    'repo_url': 'https://github.com/pierre-24/AM-Nihoul-website',
    'site_name': 'Association Anne-Marie Nihoul ASBL',
    'site_description': 'aide aux malades',
    'site_keywords': 'leucémie, aide au malades',
    'site_version': '0.8.2',

    # trumpbowyg
    'trumbowyg_version': '2.27.3',

    # external services
    'fa_kit': '',  # FontAwesome
    'gtag': '',  # Google Analytics
    'cookies_explain_page': '',  # if `gtag` is set, you MUST have a page that explains the cookies
    'recaptcha_public_key': ''
}

# limiter
NEWSLETTER_LIMIT = '10/hour;1 per 5 second'
LOGIN_LIMIT = '10/hour;1 per 5 second'

# init modules
db = SQLAlchemy(session_options={'expire_on_commit': False})
uploads_set = flask_uploads.UploadSet('uploads', flask_uploads.DEFAULTS + ('gpx', ))
pictures_set = flask_uploads.UploadSet('pictures', flask_uploads.IMAGES)
login_manager = flask_login.LoginManager()
scheduler = APScheduler()
bootstrap = Bootstrap4()
alembic = Alembic()
limiter = Limiter(key_func=get_remote_address)


class User(flask_login.UserMixin):
    def __init__(self, id_):
        super().__init__()
        self.id = id_


@login_manager.user_loader
def load_user(login):
    if login != current_app.config['USERNAME']:
        return

    return User(login)


@click.command('init')
@with_appcontext
def init_command():
    """Initializes stuffs:

    + directories
    + database
    + bootstrap data
    """

    def delete_then_create(directory: pathlib.Path):
        if directory.exists():
            shutil.rmtree(directory)

        directory.mkdir()

    # directories
    data_dir: pathlib.Path = current_app.config['DATA_DIRECTORY']
    upload_dir: pathlib.Path = current_app.config['UPLOADED_UPLOADS_DEST']
    picture_dir: pathlib.Path = current_app.config['UPLOADED_PICTURES_DEST']

    delete_then_create(data_dir)
    print('!! Data directory in {}'.format(data_dir))

    delete_then_create(upload_dir)
    print('!! Upload directory in {}'.format(upload_dir))

    delete_then_create(picture_dir)
    print('!! Picture directory in {}'.format(picture_dir))

    # DB:
    db.create_all()
    print('!! database created')

    # bootstrap
    from AM_Nihoul_website.app_bootstrap import bootstrap
    bootstrap()

    # stamp the version of the database as being the latest version (with all the migrations)
    alembic.stamp()


@click.command('bot')
@with_appcontext
def bot_command():
    from AM_Nihoul_website import bot
    while True:
        bot.bot_iteration()
        time.sleep(current_app.config['JOBS'][0]['seconds'])


def create_app(instance_relative_config=True):
    app = Flask(__name__, instance_relative_config=instance_relative_config)
    app.config.from_object(Config())
    app.config.from_pyfile('settings.py', silent=True)

    # db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(
        app.config['DATA_DIRECTORY'].resolve() / 'database.db')
    db.init_app(app)

    # uploads
    app.config.update(
        UPLOADED_UPLOADS_DEST=app.config['DATA_DIRECTORY'] / 'uploads',
        UPLOADED_PICTURES_DEST=app.config['DATA_DIRECTORY'] / 'pictures',
    )
    flask_uploads.configure_uploads(app, (uploads_set, pictures_set))

    # login
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'  # automatic redirection

    # bootstrap
    bootstrap.init_app(app)

    # alembic
    alembic.init_app(app)

    # limiter
    limiter.init_app(app)

    # add cli
    app.cli.add_command(init_command)
    app.cli.add_command(bot_command)

    # add blueprint(s)
    from AM_Nihoul_website.visitor.views import visitor_blueprint
    app.register_blueprint(visitor_blueprint)

    from AM_Nihoul_website.admin.views import admin_blueprint
    app.register_blueprint(admin_blueprint)

    # add filters
    app.jinja_env.filters.update(**filters)

    # launch bot, if any
    if app.config['LAUNCH_BOT']:
        scheduler.init_app(app)
        scheduler.start()

    return app
