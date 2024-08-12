import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Featured
from AM_Nihoul_website.tests import TestFlask


class TestFeatured(TestFlask):

    def setUp(self):
        super().setUp()

        # add a featured
        self.featured = Featured.create(
            'test', 'http://test.com/p1', 'test1', 'http://test.com/i1.jpg', 'text1')
        self.other_featured = Featured.create(
            'test', 'http://test.com/p2', 'test2', 'http://test.com/i2.jpg', 'text2')
        self.yet_another_featured = Featured.create(
            'test', 'http://test.com/p3', 'test3', 'http://test.com/i3.jpg', 'text3')

        # order them before add
        self.featured.order, self.other_featured.order, self.yet_another_featured.order = 0, 1, 2

        db.session.add(self.featured)
        db.session.add(self.other_featured)
        db.session.add(self.yet_another_featured)

        db.session.commit()
        db.session.commit()

        self.num_featureds = Featured.query.count()
        self.login()  # logged in by default, as all stuffs require admin power anyway

    def test_create_featured_ok(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)

        title = 'test'
        link = 'http://test.com/test.html'
        link_text = 'test'
        image_link = 'http://test.com/im2.jpg'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.featured-create'), data={
            'title': title,
            'link': link,
            'link_text': link_text,
            'image_link': image_link,
            'text': text,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Featured.query.count(), self.num_featureds + 1)

        p = Featured.query.order_by(Featured.id.desc()).first()

        self.assertIsNotNone(p)
        self.assertEqual(p.title, title)
        self.assertEqual(p.link, link)
        self.assertEqual(p.link_text, link_text)
        self.assertEqual(p.image_link, image_link)
        self.assertEqual(p.text, text)

    def test_create_featured_not_admin_ko(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)
        self.logout()

        title = 'test'
        link = 'http://test.com/test.html'
        link_text = 'test'
        image_link = 'http://test.com/im2.jpg'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.featured-create'), data={
            'title': title,
            'link': link,
            'link_text': link_text,
            'image_link': image_link,
            'text': text,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Featured.query.count(), self.num_featureds)

    def test_edit_featured_ok(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)

        new_title = 'this is a new title'
        new_link = 'http://test.com/test.html'
        new_link_text = 'test2'
        new_image_link = 'http://test.com/im2.jpg'
        new_text = 'whatever'

        self.assertNotEqual(self.featured.title, new_title)
        self.assertNotEqual(self.featured.text, new_text)

        response = self.client.post(
            flask.url_for('admin.featured-edit', id=self.featured.id),
            data={
                'title': new_title,
                'link': new_link,
                'link_text': new_link_text,
                'image_link': new_image_link,
                'text': new_text,
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = db.session.get(Featured, self.featured.id)
        self.assertEqual(p.title, new_title)
        self.assertEqual(p.link, new_link)
        self.assertEqual(p.link_text, new_link_text)
        self.assertEqual(p.image_link, new_image_link)
        self.assertEqual(p.text, new_text)

    def test_edit_featured_not_admin_ko(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)
        self.logout()

        new_title = 'this is a new title'
        new_text = 'whatever'

        response = self.client.post(
            flask.url_for('admin.featured-edit', id=self.featured.id),
            data={
                'title': new_title,
                'content': new_text,
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        # it remains untouched
        p = db.session.get(Featured, self.featured.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, self.featured.title)
        self.assertEqual(p.text, self.featured.text)

    def test_delete_featured_ok(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)

        response = self.client.delete(
            flask.url_for('admin.featured-delete', id=self.featured.id),
            follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Featured.query.count(), self.num_featureds - 1)

        self.assertIsNone(db.session.get(Featured, self.featured.id))

    def test_delete_featured_not_admin_ko(self):
        self.assertEqual(Featured.query.count(), self.num_featureds)
        self.logout()

        response = self.client.delete(
            flask.url_for('admin.featured-delete', id=self.featured.id),
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Featured.query.count(), self.num_featureds)
        self.assertIsNotNone(db.session.get(Featured, self.featured.id))

    def test_featured_move_ok(self):
        self.assertEqual(
            [self.featured, self.other_featured, self.yet_another_featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='down'))
        self.assertEqual(
            [self.featured, self.other_featured, self.yet_another_featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='up'))
        self.assertEqual(
            [self.other_featured, self.featured, self.yet_another_featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='up'))
        self.assertEqual(
            [self.other_featured, self.yet_another_featured, self.featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='up'))
        self.assertEqual(
            [self.other_featured, self.yet_another_featured, self.featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='down'))
        self.assertEqual(
            [self.other_featured, self.featured, self.yet_another_featured],
            Featured.query.order_by(Featured.order).all())

        self.client.get(flask.url_for('admin.featured-move', id=self.featured.id, action='down'))
        self.assertEqual(
            [self.featured, self.other_featured, self.yet_another_featured],
            Featured.query.order_by(Featured.order).all())
