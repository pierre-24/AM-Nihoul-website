import flask

import os

from AM_Nihoul_website.tests import TestFlask
from AM_Nihoul_website.visitor.models import Album, Picture
from AM_Nihoul_website import db


class TestsAlbum(TestFlask):

    def setUp(self):
        super().setUp()

        # add albums
        self.album_1 = Album.create('Album 1', 'a description')
        db.session.add(self.album_1)

        self.album_2 = Album.create('Album 2', 'a description')
        db.session.add(self.album_2)

        db.session.commit()

        self.num_albums = Album.query.count()
        self.login()

    def test_view_ok(self):
        response = self.client.get(flask.url_for('admin.albums'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(flask.url_for('admin.album', id=self.album_1.id))
        self.assertEqual(response.status_code, 200)

    def test_view_not_admin_ko(self):
        self.logout()

        response = self.client.get(flask.url_for('admin.albums'))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(flask.url_for('admin.album', id=self.album_1.id))
        self.assertEqual(response.status_code, 302)

    def test_create_album_ok(self):
        self.assertEqual(Album.query.count(), self.num_albums)

        title = 'other test'
        description = 'the description'

        response = self.client.post(flask.url_for('admin.albums'), data={
            'title': title,
            'description': description,
            'is_create': 1,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Album.query.count(), self.num_albums + 1)

        album = Album.query.order_by(Album.id.desc()).first()
        self.assertEqual(album.title, title)
        self.assertEqual(album.description, description)

    def test_create_album_not_admin_ko(self):
        self.logout()
        self.assertEqual(Album.query.count(), self.num_albums)

        title = 'other test'
        description = 'the description'

        response = self.client.post(flask.url_for('admin.albums'), data={
            'title': title,
            'description': description,
            'is_create': 1,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Album.query.count(), self.num_albums)

    def test_edit_album_ok(self):
        title = 'another title'
        description = 'another description'

        response = self.client.post(flask.url_for('admin.albums'), data={
            'title': title,
            'description': description,
            'id_album': self.album_1.id
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        album = self.album_1.query.get(self.album_1.id)
        self.assertEqual(album.title, title)
        self.assertEqual(album.description, description)

    def test_edit_album_not_admin_nok(self):
        self.logout()

        title = 'another title'
        description = 'another description'

        response = self.client.post(flask.url_for('admin.albums'), data={
            'title': title,
            'description': description,
            'id_album': self.album_1.id
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        album = self.album_1.query.get(self.album_1.id)
        self.assertNotEqual(album.title, title)
        self.assertNotEqual(album.description, description)

    def test_delete_album_ok(self):
        self.assertEqual(Album.query.count(), self.num_albums)

        response = self.client.delete(flask.url_for('admin.album-delete', id=self.album_1.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Album.query.count(), self.num_albums - 1)
        self.assertIsNone(Album.query.get(self.album_1.id))

    def test_delete_album_not_admin_nok(self):
        self.logout()
        self.assertEqual(Album.query.count(), self.num_albums)

        response = self.client.delete(flask.url_for('admin.album-delete', id=self.album_1.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Album.query.count(), self.num_albums)
        self.assertIsNotNone(Album.query.get(self.album_1.id))


class TestsPicture(TestFlask):

    def setUp(self):
        super().setUp()

        # add albums
        self.album_1 = Album.create('Album 1', 'a description')
        db.session.add(self.album_1)

        self.album_2 = Album.create('Album 2', 'a description')
        db.session.add(self.album_2)

        db.session.commit()

        self.num_albums = Album.query.count()

        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.file = os.path.join(self.dir, 'random_pic.jpg')
        self.file2 = os.path.join(self.dir, 'random_pic2.png')

        self.num_pictures = Picture.query.count()

        self.login()

    def upload_pic(self, fname: str, path: str, album: Album):
        n = Picture.query.count()
        response = self.client.post(
            flask.url_for('admin.album', id=album.id), data={
                'file_uploaded': (open(path, 'rb'), fname)
            })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Picture.query.count(), n + 1)

        return Picture.query.order_by(Picture.id.desc()).first()

    def test_upload_and_delete_ok(self):
        fname = 'whatever.jpg'

        p = self.upload_pic(fname, self.file, self.album_1)
        self.assertEqual(p.picture_name, fname)
        self.assertTrue(os.path.exists(p.path()))
        self.assertTrue(os.path.exists(p.path_thumb()))

        self.assertEqual(p.album_id, self.album_1.id)

        response = self.client.delete(flask.url_for('admin.picture-delete', id=p.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Picture.query.count(), self.num_pictures)
        self.assertIsNone(Picture.query.get(p.id))

        self.assertFalse(os.path.exists(p.path()))
        self.assertFalse(os.path.exists(p.path_thumb()))

    def test_upload_same_name_different_files_ok(self):
        fname = 'whatever.jpg'
        p1 = self.upload_pic(fname, self.file, self.album_1)
        p2 = self.upload_pic(fname, self.file, self.album_1)

        self.assertEqual(p1.picture_name, fname)
        self.assertNotEqual(p2.picture_name, fname)
        self.assertNotEqual(p1.path(), p2.path())

    def test_upload_not_admin_ko(self):
        self.logout()

        self.assertEqual(Picture.query.count(), self.num_pictures)
        fname = 'whatever.jpg'

        response = self.client.post(
            flask.url_for('admin.album', id=self.album_1.id), data={
                'file_uploaded': (open(self.file, 'rb'), fname)
            })
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Picture.query.count(), self.num_pictures)

    def test_delete_not_admin_ko(self):
        p1 = self.upload_pic('test1.jpg', self.file, self.album_1)
        self.assertEqual(Picture.query.count(), self.num_pictures + 1)

        self.logout()

        response = self.client.delete(flask.url_for('admin.picture-delete', id=p1.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Picture.query.count(), self.num_pictures + 1)
        self.assertIsNotNone(Picture.query.get(p1.id))

    def test_delete_album_also_delete_picture_ok(self):
        self.assertEqual(Picture.query.count(), self.num_pictures)

        p1 = self.upload_pic('test1.jpg', self.file, self.album_1)
        p2 = self.upload_pic('test2.jpg', self.file, self.album_1)
        p3 = self.upload_pic('test3.jpg', self.file, self.album_2)

        self.assertEqual(Picture.query.count(), self.num_pictures + 3)

        response = self.client.delete(flask.url_for('admin.album-delete', id=self.album_1.id))
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(Album.query.get(self.album_1.id))

        self.assertEqual(Picture.query.count(), self.num_pictures + 1)

        self.assertIsNone(Picture.query.get(p1.id))
        self.assertIsNone(Picture.query.get(p2.id))
        self.assertIsNotNone(Picture.query.get(p3.id))

    def test_album_thumbnail_ok(self):
        self.assertEqual(Picture.query.count(), self.num_pictures)

        p1 = self.upload_pic('test1.jpg', self.file, self.album_1)
        p2 = self.upload_pic('test2.jpg', self.file, self.album_1)
        p3 = self.upload_pic('test3.jpg', self.file, self.album_2)

        self.assertEqual(Picture.query.count(), self.num_pictures + 3)

        # by default, first to be uploaded
        self.assertEqual(self.album_1.get_thumbnail().id, p1.id)
        self.assertEqual(self.album_2.get_thumbnail().id, p3.id)

        # change thumbnail of album 1
        response = self.client.get(flask.url_for('admin.album-set-thumbnail', id=self.album_1.id, picture=p2.id))
        self.assertEqual(response.status_code, 302)

        album_1 = Album.query.get(self.album_1.id)
        self.assertEqual(album_1.get_thumbnail().id, p2.id)

    def test_visitor_views_ok(self):
        # need thumbnails
        self.upload_pic('test1.jpg', self.file, self.album_1)
        self.upload_pic('test2.jpg', self.file, self.album_2)

        # works as admin
        response = self.client.get(flask.url_for('visitor.albums'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(flask.url_for('visitor.album', id=self.album_1.id, slug=self.album_1.slug))
        self.assertEqual(response.status_code, 200)

        # works also as a normal person as well!
        self.logout()

        response = self.client.get(flask.url_for('visitor.albums'))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(flask.url_for('visitor.album', id=self.album_1.id, slug=self.album_1.slug))
        self.assertEqual(response.status_code, 200)

    def test_visitor_view_wrong_slug_ko(self):
        response = self.client.get(flask.url_for('visitor.album', id=self.album_1.id, slug=self.album_1.slug))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(flask.url_for('visitor.album', id=self.album_1.id, slug=self.album_1.slug + 'x'))
        self.assertEqual(response.status_code, 404)
