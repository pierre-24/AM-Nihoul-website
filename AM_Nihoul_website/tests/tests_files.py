import flask
import os
import base64

from AM_Nihoul_website.visitor.models import UploadedFile
from AM_Nihoul_website.tests import TestFlask

from AM_Nihoul_website import settings


class TestFiles(TestFlask):

    def setUp(self):
        super().setUp()

        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.file = os.path.join(self.dir, 'random_pic.jpg')
        self.file2 = os.path.join(self.dir, 'random_pic2.png')

        self.num_uploads = UploadedFile.query.count()
        self.login()

    def test_upload_and_delete_ok(self):
        self.assertEqual(UploadedFile.query.count(), self.num_uploads)

        desc = 'a description'
        fname = 'tmp.jpg'

        response = self.client.post(
            flask.url_for('admin.files'), data={
                'description': desc,
                'file_uploaded': (open(self.file, 'rb'), fname)
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 1)

        u = UploadedFile.query.order_by(UploadedFile.id.desc()).first()
        self.assertIsNotNone(u)

        self.assertEqual(u.description, desc)
        self.assertEqual(u.base_file_name, fname)
        self.assertTrue(os.path.exists(u.path()))
        self.assertEqual(u.possible_mime, 'image/jpeg')

        # test delete directly, as it is easier to upload a file this way
        self.client.delete(flask.url_for('admin.file-delete', id=u.id))
        self.assertEqual(UploadedFile.query.count(), self.num_uploads)
        self.assertIsNone(UploadedFile.query.get(u.id))
        self.assertFalse(os.path.exists(u.path()))

    def test_upload_api_ok(self):
        """Test upload with a JSON answer"""
        self.assertEqual(UploadedFile.query.count(), self.num_uploads)

        context = 'life'  # context is found in filename

        with open(self.file2, 'rb') as f:
            b64str = base64.b64encode(f.read())

        response = self.client.post(
            flask.url_for('admin.image-base64') + '?context={}'.format(context), data={
                'image': 'data:image/png;base64,' + b64str.decode('utf-8'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 1)

        u = UploadedFile.query.order_by(UploadedFile.id.desc()).first()

        self.assertIsNotNone(u)
        self.assertTrue(os.path.exists(u.path()))
        self.assertIn(context, u.file_name)
        self.assertEqual(u.possible_mime, 'image/png')
        self.assertEqual(
            response.json['url'], flask.url_for('visitor.upload-view', id=u.id, filename=u.file_name, _external=True))

        # now, set a ridiculously low size
        self.app_context.push()
        sz = settings.APP_CONFIG['UPLOAD_CONVERT_TO_JPG']
        settings.APP_CONFIG['UPLOAD_CONVERT_TO_JPG'] = 1 * 1024

        response = self.client.post(
            flask.url_for('admin.image-base64') + '?context={}'.format(context), data={
                'image': 'data:image/png;base64,' + b64str.decode('utf-8'),
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json['success'])

        settings.APP_CONFIG['UPLOAD_CONVERT_TO_JPG'] = sz

        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 2)

        u = UploadedFile.query.order_by(UploadedFile.id.desc()).first()

        self.assertIsNotNone(u)
        self.assertTrue(os.path.exists(u.path()))
        self.assertIn(context, u.file_name)
        self.assertEqual(u.possible_mime, 'image/jpeg')
        self.assertEqual(
            response.json['url'], flask.url_for('visitor.upload-view', id=u.id, filename=u.file_name, _external=True))

        self.app_context.pop()

    def test_visitor_view_ok(self):
        # upload file first (as admin)
        desc = 'a description'
        fname = 'tmp.jpg'

        response = self.client.post(
            flask.url_for('admin.files'), data={
                'description': desc,
                'file_uploaded': (open(self.file, 'rb'), fname)
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 1)

        u = UploadedFile.query.order_by(UploadedFile.id.desc()).first()
        self.assertIsNotNone(u)

        # view file as admin
        with open(self.file, 'rb') as f:
            content = f.read()

        response = self.client.get(flask.url_for('visitor.upload-view', id=u.id, filename=u.file_name))
        self.assertEqual(content, response.data)
        self.assertEqual(response.headers.get('Content-Disposition'), 'attachment; filename={}'.format(u.file_name))

        # view file as visitor
        self.logout()

        response = self.client.get(flask.url_for('visitor.upload-view', id=u.id, filename=u.file_name))
        self.assertEqual(content, response.data)
        self.assertEqual(response.headers.get('Content-Disposition'), 'attachment; filename={}'.format(u.file_name))

    def test_upload_not_admin_ko(self):
        self.assertEqual(UploadedFile.query.count(), self.num_uploads)
        self.logout()

        desc = 'a description'
        fname = 'tmp.jpg'

        response = self.client.post(
            flask.url_for('admin.files'), data={
                'description': desc,
                'file_uploaded': (open(self.file, 'rb'), fname)
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.query.count(), self.num_uploads)

    def test_delete_file_not_admin_ko(self):
        # upload file (as admin)
        desc = 'a description'
        fname = 'tmp.jpg'

        response = self.client.post(
            flask.url_for('admin.files'), data={
                'description': desc,
                'file_uploaded': (open(self.file, 'rb'), fname)
            })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 1)

        u = UploadedFile.query.order_by(UploadedFile.id.desc()).first()
        self.assertIsNotNone(u)

        # try to delete
        self.logout()
        self.client.delete(flask.url_for('admin.file-delete', id=u.id))
        self.assertEqual(UploadedFile.query.count(), self.num_uploads + 1)
        self.assertIsNotNone(UploadedFile.query.get(u.id))
