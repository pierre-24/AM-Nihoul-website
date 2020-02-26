import os
import shutil

import click
from flask import Flask, current_app
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
# from flask_uploads import UploadSet, ALL as ALL_EXTENSIONS, configure_uploads

from AM_Nihoul_website import settings

db = SQLAlchemy()


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
    # configure_uploads(app, (UploadSet('uploads', ALL_EXTENSIONS),))

    # add cli
    app.cli.add_command(init_db_command)
    app.cli.add_command(init_directories_command)

    @app.route('/')
    def index():
        return 'test'

    return app
