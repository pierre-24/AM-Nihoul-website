import os
import shutil
import time

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
import flask_uploads
from flask_uploads import UploadSet, configure_uploads
import flask_login
from flask_apscheduler import APScheduler
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from AM_Nihoul_website import settings
from AM_Nihoul_website.base_filters import filters


# init modules
db = SQLAlchemy(session_options={'expire_on_commit': False})
uploads_set = UploadSet('uploads', flask_uploads.DEFAULTS)
login_manager = flask_login.LoginManager()
scheduler = APScheduler()
bootstrap = Bootstrap()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)


class User(flask_login.UserMixin):
    def __init__(self, id_):
        super().__init__()
        self.id = id_


@login_manager.user_loader
def load_user(login):
    if login != settings.APP_CONFIG['USERNAME']:
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

    # directories
    data_dir = settings.DATA_DIRECTORY
    upload_dir = current_app.config['UPLOADED_UPLOADS_DEST']

    if os.path.exists(data_dir):
        shutil.rmtree(data_dir)

    os.mkdir(data_dir)
    print('!! Data directory in {}'.format(data_dir))

    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)

    os.mkdir(upload_dir)
    print('!! Upload directory in {}'.format(upload_dir))

    # DB:
    db.create_all()
    print('!! database created')

    # bootstrap
    from AM_Nihoul_website.app_bootstrap import bootstrap
    bootstrap()


@click.command('bot')
@with_appcontext
def bot_command():
    from AM_Nihoul_website import bot
    while True:
        bot.bot_iteration()
        time.sleep(settings.APP_CONFIG['JOBS'][0]['seconds'])


def create_app():
    app = Flask(__name__)
    app.config.update(settings.APP_CONFIG)
    db.init_app(app)
    db.app = app
    configure_uploads(app, (uploads_set, ))

    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'  # automatic redirection

    bootstrap.init_app(app)
    migrate.init_app(app, db)
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
    if settings.APP_CONFIG['LAUNCH_BOT']:
        scheduler.init_app(app)
        scheduler.start()

    return app
