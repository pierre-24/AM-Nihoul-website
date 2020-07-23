import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import MenuEntry
from AM_Nihoul_website.tests import TestFlask


class TestMenus(TestFlask):

    def setUp(self):
        super().setUp()

        # NOTE: for the order to be set, each one should be added individually
        self.menu_small = MenuEntry.create('test1', 'http://x.com/a1.html', MenuEntry.MENU_SMALL)
        db.session.add(self.menu_small)
        db.session.commit()

        self.menu_small_2 = MenuEntry.create('test2', 'http://x.com/a2.html', MenuEntry.MENU_SMALL)
        db.session.add(self.menu_small_2)
        db.session.commit()

        self.menu_big = MenuEntry.create('test1', 'http://x.com/b.html', MenuEntry.MENU_BIG)
        db.session.add(self.menu_big)
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
            'position': MenuEntry.MENU_BIG,
            'is_create': 1,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus + 1)

        c = MenuEntry.query.order_by(MenuEntry.id.desc()).first()
        self.assertIsNotNone(c)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)
        self.assertEqual(c.position, MenuEntry.MENU_BIG)
        self.assertTrue(c.highlight)

    def test_menu_create_not_admin_ko(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.logout()

        text = 'other test'
        url = 'http://x.com/b2.html'

        response = self.client.post(flask.url_for('admin.menus'), data={
            'text': text,
            'url': url,
            'position': MenuEntry.MENU_BIG,
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
            'id_menu': self.menu_big.id,
            'highlight': True
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        c = MenuEntry.query.get(self.menu_big.id)
        self.assertEqual(c.text, text)
        self.assertEqual(c.url, url)
        self.assertEqual(c.position, MenuEntry.MENU_BIG)
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

        c = MenuEntry.query.get(self.menu_big.id)
        self.assertNotEqual(c.text, text)
        self.assertNotEqual(c.url, url)
        self.assertFalse(c.highlight)

    def test_menu_delete_ok(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_big.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus - 1)
        self.assertIsNone(MenuEntry.query.get(self.menu_big.id))

    def test_menu_delete_not_admin_ko(self):
        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.logout()

        response = self.client.delete(flask.url_for('admin.menu-delete', id=self.menu_big.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(MenuEntry.query.count(), self.num_menus)
        self.assertIsNotNone(MenuEntry.query.get(self.menu_big.id))

    def test_menu_move_ok(self):
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='up'))
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small_2, self.menu_small])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='down'))
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

    def test_menu_move_not_admin_ko(self):
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])
        self.logout()

        r = self.client.get(flask.url_for('admin.menu-move', id=self.menu_small.id, action='up'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])

        self.client.get(flask.url_for('admin.menu-move', id=self.menu_small_2.id, action='down'))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(
            MenuEntry.ordered_items(position=MenuEntry.MENU_SMALL).all(), [self.menu_small, self.menu_small_2])
