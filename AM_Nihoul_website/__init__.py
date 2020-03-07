import os
import shutil

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
import flask_uploads
from flask_uploads import UploadSet, configure_uploads

from AM_Nihoul_website import settings

db = SQLAlchemy()

uploads_set = UploadSet('uploads', flask_uploads.DEFAULTS)


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initializes the database."""
    db.create_all()
    print('!! database created')


@click.command('init-directories')
@with_appcontext
def init_directories_command():
    """Initializes the upload and data directories."""

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


def create_app():
    app = Flask(__name__)
    app.config.update(settings.APP_CONFIG)
    db.init_app(app)
    configure_uploads(app, (uploads_set, ))

    # add cli
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_directories_command)

    # add blueprint(s)
    from AM_Nihoul_website.visitor.views import visitor_blueprint
    app.register_blueprint(visitor_blueprint)

    from AM_Nihoul_website.admin.views import admin_blueprint
    app.register_blueprint(admin_blueprint)

    return app
