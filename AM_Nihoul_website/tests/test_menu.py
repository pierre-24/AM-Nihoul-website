import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import MenuEntry, MenuType
from AM_Nihoul_website.tests import TestFlask


class TestMenus(TestFlask):

    def setUp(self):
        super().setUp()

        # NOTE: for the order to be set, each one should be added individually
        self.menu_1 = MenuEntry.create('test1', 'http://x.com/a1.html')
        db.session.add(self.menu_1)
        db.session.commit()

        self.menu_2 = MenuEntry.create('test2', 'http://x.com/a2.html')
        db.session.add(self.menu_2)
        db.session.commit()

        self.menu_3 = MenuEntry.create('test1', 'http://x.com/b.html')
        db.session.add(self.menu_3)
        db.session.commit()

        self.num_menus = MenuEntry.query.count()
        self.login()

    def test_menu_create_ok(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': MenuType.main.value,
            'is_create': 1,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus + 1)

        c = MenuEntry.query.order_by(MenuEntry.id.desc()).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)
        self.assertEqual(c.position, MenuType.main)

    def test_menu_create_secondary_ok(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': MenuType.secondary.value,
            'is_create': 1,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus + 1)

        c = MenuEntry.query.order_by(MenuEntry.id.desc()).first()
        self.assertEqual(c.position, MenuType.secondary)

    def test_menu_create_not_admin_ko(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.logout()

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'is_create': 1,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(MenuEntry.query.count(), self.num_menus)

    def test_menu_edit_ok(self):
        text = 'xyz'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': MenuType.main.value,
            'id_menu': self.menu_3.id,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = self.db_session.get(MenuEntry, self.menu_3.id)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)

    def test_menu_edit_not_admin_ko(self):
        text = 'xyz'
        url = 'http://x.com/b2.html'
        self.logout()

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'id_menu': self.menu_3.id,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = self.db_session.get(MenuEntry, self.menu_3.id)
        self.assertNotEqual(c.text, text)
        self.assertNotEqual(c.url, url)
        self.assertFalse(c.highlight)

    def test_menu_delete_ok(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_3.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus - 1)
        self.assertIsNone(self.db_session.get(MenuEntry, self.menu_3.id))

    def test_menu_delete_not_admin_ko(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.logout()

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_3.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.assertIsNotNone(self.db_session.get(MenuEntry, self.menu_3.id))

    def test_menu_move_ok(self):
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_1, self.menu_2, self.menu_3])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_1.id, action='up'))
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_2, self.menu_1, self.menu_3])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_1.id, action='down'))
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_1, self.menu_2, self.menu_3])

    def test_menu_move_not_admin_ko(self):
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_1, self.menu_2, self.menu_3])
        self.logout()

        r = self.client.get(flask.url_for('admin.menu-move', id=self.menu_1.id, action='up'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_1, self.menu_2, self.menu_3])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_2.id, action='down'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            MenuEntry.ordered_items().all(), [self.menu_1, self.menu_2, self.menu_3])
