import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Menu
from AM_Nihoul_website.tests import TestFlask


class TestMenus(TestFlask):

    def setUp(self):
        super().setUp()

        # NOTE: for the order to be set, each one should be added individually
        self.menu_small = Menu.create('test1', 'http://x.com/a1.html', Menu.MENU_SMALL)
        db.session.add(self.menu_small)
        db.session.commit()

        self.menu_small_2 = Menu.create('test2', 'http://x.com/a2.html', Menu.MENU_SMALL)
        db.session.add(self.menu_small_2)
        db.session.commit()

        self.menu_big = Menu.create('test1', 'http://x.com/b.html', Menu.MENU_BIG)
        db.session.add(self.menu_big)
        db.session.commit()

        self.num_menus = Menu.query.count()
        self.login()

    def test_menu_create_ok(self):
        self.assertEqual(Menu.query.count(), self.num_menus)

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': Menu.MENU_BIG,
            'is_create': 1,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Menu.query.count(), self.num_menus + 1)

        c = Menu.query.order_by(Menu.id.desc()).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)
        self.assertEqual(c.position, Menu.MENU_BIG)
        self.assertTrue(c.highlight)

    def test_menu_create_not_admin_ko(self):
        self.assertEqual(Menu.query.count(), self.num_menus)
        self.logout()

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': Menu.MENU_BIG,
            'is_create': 1,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Menu.query.count(), self.num_menus)

    def test_menu_edit_ok(self):
        text = 'xyz'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'id_menu': self.menu_big.id,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = Menu.query.get(self.menu_big.id)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)
        self.assertEqual(c.position, Menu.MENU_BIG)
        self.assertTrue(c.highlight)

    def test_menu_edit_not_admin_ko(self):
        text = 'xyz'
        url = 'http://x.com/b2.html'
        self.logout()

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'id_menu': self.menu_big.id,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = Menu.query.get(self.menu_big.id)
        self.assertNotEqual(c.text, text)
        self.assertNotEqual(c.url, url)
        self.assertFalse(c.highlight)

    def test_menu_delete_ok(self):
        self.assertEqual(Menu.query.count(), self.num_menus)

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_big.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Menu.query.count(), self.num_menus - 1)
        self.assertIsNone(Menu.query.get(self.menu_big.id))

    def test_menu_delete_not_admin_ko(self):
        self.assertEqual(Menu.query.count(), self.num_menus)
        self.logout()

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_big.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Menu.query.count(), self.num_menus)
        self.assertIsNotNone(Menu.query.get(self.menu_big.id))

    def test_menu_move_ok(self):
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='up'))
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small_2, self.menu_small])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='down'))
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

    def test_menu_move_not_admin_ko(self):
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])
        self.logout()

        r = self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='up'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small_2.id, action='down'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Menu.ordered_items(position=Menu.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])
