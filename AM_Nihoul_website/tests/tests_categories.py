import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Category
from AM_Nihoul_website.tests import TestFlask


class TestCategories(TestFlask):

    def setUp(self):
        super().setUp()

        # add categories
        # NOTE: for the order to be set, each category should be added individually
        self.category = Category.create('test')
        db.session.add(self.category)
        db.session.commit()

        self.other_category = Category.create('another test')
        db.session.add(self.other_category)
        db.session.commit()

        self.yet_another_category = Category.create('another other test')
        db.session.add(self.yet_another_category)
        db.session.commit()

        self.num_cat = Category.query.count()
        self.login()  # logged in by default, as all stuffs require admin power anyway!

    def test_category_create_ok(self):
        self.assertEqual(Category.query.count(), self.num_cat)

        name = 'other test'

        response = self.client.post(flask.url_for('admin.categories'), data={
            'name': name,
            'is_create': 1
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Category.query.count(), self.num_cat + 1)

        c = Category.query.order_by(Category.id.desc()).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.name, name)

    def test_category_create_not_admin_ko(self):
        self.assertEqual(Category.query.count(), self.num_cat)
        self.logout()

        name = 'other test'

        response = self.client.post(flask.url_for('admin.categories'), data={
            'name': name,
            'is_create': 1
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Category.query.count(), self.num_cat)

    def test_category_edit_ok(self):
        self.assertEqual(Category.query.count(), self.num_cat)
        name = 'other cat'

        response = self.client.post(flask.url_for('admin.categories'), data={
            'name': name,
            'id_category': self.category.id
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = self.db_session.get(Category, self.category.id)
        self.assertIsNotNone(c)
        self.assertEqual(c.name, name)

    def test_category_edit_not_admin_ko(self):
        self.assertEqual(Category.query.count(), self.num_cat)
        self.logout()
        name = 'other cat'

        response = self.client.post(flask.url_for('admin.categories'), data={
            'name': name,
            'id_category': self.category.id
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = self.db_session.get(Category, self.category.id)
        self.assertIsNotNone(c)
        self.assertNotEqual(c.name, name)

    def test_category_delete_ok(self):
        self.assertEqual(Category.query.count(), self.num_cat)

        response = self.client.post(flask.url_for('admin.category-delete', id=self.category.id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Category.query.count(), self.num_cat - 1)
        self.assertIsNone(self.db_session.get(Category, self.category.id))

    def test_category_delete_not_admin_ko(self):
        self.assertEqual(Category.query.count(), self.num_cat)
        self.logout()

        response = self.client.post(flask.url_for('admin.category-delete', id=self.category.id), follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Category.query.count(), self.num_cat)
        self.assertIsNotNone(self.db_session.get(Category, self.category.id))

    def test_category_move_ok(self):
        self.assertEqual(
            [self.category, self.other_category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='down'))
        self.assertEqual(
            [self.category, self.other_category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='up'))
        self.assertEqual(
            [self.other_category, self.category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='up'))
        self.assertEqual(
            [self.other_category, self.yet_another_category, self.category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='up'))
        self.assertEqual(
            [self.other_category, self.yet_another_category, self.category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='down'))
        self.assertEqual(
            [self.other_category, self.category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

        self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='down'))
        self.assertEqual(
            [self.category, self.other_category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

    def test_category_move_not_admin_ko(self):
        self.assertEqual(
            [self.category, self.other_category, self.yet_another_category],
            Category.query.order_by(Category.order).all())

        self.logout()

        response = self.client.get(flask.url_for('admin.category-move', id=self.category.id, action='up'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            [self.category, self.other_category, self.yet_another_category],
            Category.query.order_by(Category.order).all())
