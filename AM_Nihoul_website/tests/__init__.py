import tempfile
from unittest import TestCase
import shutil
import os

import flask

from AM_Nihoul_website import create_app, settings, db


class TestFlask(TestCase):

    def setUp(self):
        # setup settings
        self.data_files_directory = tempfile.mkdtemp()
        settings.DATA_DIRECTORY = self.data_files_directory

        settings.APP_CONFIG['TESTING'] = True
        settings.APP_CONFIG['USE_FAKE_MAIL_SENDER'] = True
        settings.APP_CONFIG['LAUNCH_BOT'] = False
        settings.APP_CONFIG['WTF_CSRF_ENABLED'] = False
        # TODO: sort out this whole SERVER_NAME stuff
        # settings.APP_CONFIG['SERVER_NAME'] = 'local.domain'
        settings.APP_CONFIG['UPLOADED_UPLOADS_DEST'] = os.path.join(self.data_files_directory, 'uploads/')
        settings.APP_CONFIG['UPLOADED_PICTURES_DEST'] = os.path.join(self.data_files_directory, 'pictures/')

        self.app = create_app()

        # push context
        self.app_context = self.app.app_context()
        self.app_context.push()

        # use temporary database
        self.db_file = 'temp.db'
        self.app.config['SQLALCHEMY_DATABASE_URI'] = \
            'sqlite:///' + os.path.join(self.data_files_directory, self.db_file)

        db.create_all()
        self.db_session = db.session

        # create client
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        shutil.rmtree(self.data_files_directory)
        self.app_context.pop()

    def login(self):
        """Login client."""

        self.client.post(flask.url_for('admin.login'), data={
            'login': settings.APP_CONFIG['USERNAME'],
            'password': settings.APP_CONFIG['PASSWORD']
        }, follow_redirects=False)

        response = self.client.get(flask.url_for('admin.index'), follow_redirects=False)
        self.assertEqual(response.status_code, 200)

    def logout(self):
        """Logout client"""
        self.client.get(flask.url_for('admin.logout'), follow_redirects=False)

        response = self.client.get(flask.url_for('admin.index'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
