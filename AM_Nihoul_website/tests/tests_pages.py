import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Page, Category
from AM_Nihoul_website.tests import TestFlask


class TestPage(TestFlask):

    def setUp(self):
        super().setUp()

        # add category
        self.category = Category.create('test')
        db.session.add(self.category)
        db.session.commit()

        # add some pages
        self.unprotected_page = Page.create('test but unprotected', 'test')
        self.protected_page = Page.create('test but protected', 'test', protected=True)
        self.page_with_cat = Page.create('test with cat', 'test', category_id=self.category.id)

        db.session.add(self.unprotected_page)
        db.session.add(self.protected_page)
        db.session.add(self.page_with_cat)

        db.session.commit()

        self.num_pages = Page.query.count()
        self.login()  # logged in by default, as all stuffs require admin power anyway

    def test_create_page_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        title = 'test'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.page-create'), data={
            'title': title,
            'content': text,
            'category': -1
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Page.query.count(), self.num_pages + 1)

        p = Page.query.order_by(Page.id.desc()).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.title, title)
        self.assertEqual(p.content, text)
        self.assertFalse(p.protected)
        self.assertIsNone(p.category)

    def test_create_page_not_admin_ko(self):
        self.assertEqual(Page.query.count(), self.num_pages)
        self.logout()

        title = 'test'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.page-create'), data={
            'title': title,
            'content': text,
            'category': -1
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Page.query.count(), self.num_pages)

    def test_create_page_with_category_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        # create page
        title = 'test'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.page-create'), data={
            'title': title,
            'content': text,
            'category': self.category.id
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Page.query.count(), self.num_pages + 1)

        p = Page.query.order_by(Page.id.desc()).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.title, title)
        self.assertEqual(p.content, text)
        self.assertFalse(p.protected)
        self.assertEqual(self.category, p.category)

    def test_edit_page_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        new_title = 'this is a new title'
        new_text = 'whatever'

        # edit unprotected page is ok
        self.assertNotEqual(self.unprotected_page.title, new_title)
        self.assertNotEqual(self.unprotected_page.content, new_text)

        response = self.client.post(
            flask.url_for('admin.page-edit', id=self.unprotected_page.id, slug=self.unprotected_page.slug),
            data={
                'title': new_title,
                'content': new_text,
                'category': self.unprotected_page.category_id
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = Page.query.get(self.unprotected_page.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, new_title)
        self.assertEqual(p.content, new_text)
        self.assertEqual(self.unprotected_page.category, p.category)

    def test_edit_page_not_admin_ko(self):
        self.assertEqual(Page.query.count(), self.num_pages)
        self.logout()

        new_title = 'this is a new title'
        new_text = 'whatever'

        response = self.client.post(
            flask.url_for('admin.page-edit', id=self.unprotected_page.id, slug=self.unprotected_page.slug),
            data={
                'title': new_title,
                'content': new_text,
                'category': self.unprotected_page.category_id
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        # it remains untouched
        p = Page.query.get(self.unprotected_page.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, self.unprotected_page.title)
        self.assertEqual(p.content, self.unprotected_page.content)
        self.assertEqual(self.unprotected_page.category, p.category)

    def test_edit_protected_page_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        new_title = 'this is a new title'
        new_text = 'whatever'

        self.assertNotEqual(self.protected_page.title, new_title)
        self.assertNotEqual(self.protected_page.content, new_text)

        response = self.client.post(
            flask.url_for('admin.page-edit', id=self.protected_page.id, slug=self.protected_page.slug),
            data={
                'title': new_title,
                'content': new_text,
                'category': self.protected_page.category_id
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = Page.query.get(self.protected_page.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, new_title)
        self.assertEqual(p.content, new_text)
        self.assertEqual(self.protected_page.category, p.category)

    def test_edit_page_with_cat_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        new_title = 'this is a new title'
        new_text = 'whatever'

        self.assertNotEqual(self.page_with_cat.title, new_title)
        self.assertNotEqual(self.page_with_cat.content, new_text)
        self.assertEqual(self.page_with_cat.category_id, self.category.id)

        response = self.client.post(
            flask.url_for('admin.page-edit', id=self.page_with_cat.id, slug=self.page_with_cat.slug),
            data={
                'title': new_title,
                'content': new_text,
                'category': self.category.id
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = Page.query.get(self.page_with_cat.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, new_title)
        self.assertEqual(p.content, new_text)
        self.assertEqual(self.category, p.category)

    def test_edit_change_cat_ok(self):
        cat = Category.create('test')
        db.session.add(cat)
        db.session.commit()

        self.assertEqual(Page.query.count(), self.num_pages)

        self.assertNotEqual(self.page_with_cat.category, cat)

        response = self.client.post(
            flask.url_for('admin.page-edit', id=self.page_with_cat.id, slug=self.page_with_cat.slug),
            data={
                'title': self.page_with_cat.title,
                'content': self.page_with_cat.content,
                'category': cat.id
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = Page.query.get(self.page_with_cat.id)
        self.assertEqual(cat, p.category)

    def test_delete_page_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        response = self.client.delete(
            flask.url_for('admin.page-delete', id=self.unprotected_page.id, slug=self.unprotected_page.slug),
            follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Page.query.count(), self.num_pages - 1)

        self.assertIsNone(Page.query.get(self.unprotected_page.id))

    def test_delete_page_not_admin_ko(self):
        self.assertEqual(Page.query.count(), self.num_pages)
        self.logout()

        response = self.client.delete(
            flask.url_for('admin.page-delete', id=self.unprotected_page.id, slug=self.unprotected_page.slug),
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Page.query.count(), self.num_pages)
        self.assertIsNotNone(Page.query.get(self.unprotected_page.id))

    def test_delete_page_with_cat_ok(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        response = self.client.delete(
            flask.url_for('admin.page-delete', id=self.page_with_cat.id, slug=self.page_with_cat.slug),
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Page.query.count(), self.num_pages - 1)
        self.assertIsNone(Page.query.get(self.page_with_cat.id))
        self.assertIsNotNone(Category.query.get(self.category.id))

    def test_delete_protected_page_ko(self):
        self.assertEqual(Page.query.count(), self.num_pages)

        response = self.client.delete(
            flask.url_for('admin.page-delete', id=self.protected_page.id, slug=self.protected_page.slug),
            follow_redirects=False)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Page.query.count(), self.num_pages)
        self.assertIsNotNone(Page.query.get(self.unprotected_page.id))

    def test_visitor_view_ok(self):
        title = 'a special title'
        content = 'test with a very special content: "pôtichat"!'

        p = Page.create(title, content)
        db.session.add(p)
        db.session.commit()

        # view as admin
        response = self.client.get(flask.url_for('visitor.page-view', id=p.id, slug=p.slug))
        self.assertIn(title, response.get_data(as_text=True))
        self.assertIn(content, response.get_data(as_text=True))

        # view as visitor
        self.logout()
        response = self.client.get(flask.url_for('visitor.page-view', id=p.id, slug=p.slug))
        self.assertIn(title, response.get_data(as_text=True))
        self.assertIn(content, response.get_data(as_text=True))
