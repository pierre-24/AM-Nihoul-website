import os
import shutil

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
import flask_uploads
from flask_uploads import UploadSet, configure_uploads
import flask_login

from AM_Nihoul_website import settings
from AM_Nihoul_website.base_filters import filters


# init modules
db = SQLAlchemy()

uploads_set = UploadSet('uploads', flask_uploads.DEFAULTS)


# login manager
login_manager = flask_login.LoginManager()


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


def create_app():
    app = Flask(__name__)
    app.config.update(settings.APP_CONFIG)
    db.init_app(app)
    configure_uploads(app, (uploads_set, ))
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'  # automatic redirection

    # add cli
    app.cli.add_command(init_command)

    # add blueprint(s)
    from AM_Nihoul_website.visitor.views import visitor_blueprint
    app.register_blueprint(visitor_blueprint)

    from AM_Nihoul_website.admin.views import admin_blueprint
    app.register_blueprint(admin_blueprint)

    # add filters
    app.jinja_env.filters.update(**filters)

    return app
