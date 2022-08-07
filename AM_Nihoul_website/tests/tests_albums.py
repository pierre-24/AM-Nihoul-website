import flask

from AM_Nihoul_website.tests import TestFlask
from AM_Nihoul_website.visitor.models import Album
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
