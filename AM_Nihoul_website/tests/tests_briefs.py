import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Brief
from AM_Nihoul_website.tests import TestFlask


class TestBrief(TestFlask):

    def setUp(self):
        super().setUp()

        # add some briefs
        self.visible_brief = Brief.create('test but visible', '', 'test', visible=True)
        self.invisible_brief = Brief.create('test but invisible', '', 'test', visible=False)

        db.session.add(self.visible_brief)
        db.session.add(self.invisible_brief)

        db.session.commit()
        db.session.commit()

        self.num_briefs = Brief.query.count()
        self.login()  # logged in by default, as all stuffs require admin power anyway

    def test_create_brief_ok(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)

        title = 'test'
        text = 'this is a test'
        summary = 'a summary'

        response = self.client.post(flask.url_for('admin.brief-create'), data={
            'title': title,
            'content': text,
            'summary': summary
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Brief.query.count(), self.num_briefs + 1)

        p = Brief.query.order_by(Brief.id.desc()).first()
        self.assertIsNotNone(p)
        self.assertEqual(p.title, title)
        self.assertEqual(p.content, text)
        self.assertFalse(p.visible)
        self.assertEqual(p.summary, summary)

    def test_create_brief_not_admin_ko(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)
        self.logout()

        title = 'test'
        text = 'this is a test'

        response = self.client.post(flask.url_for('admin.brief-create'), data={
            'title': title,
            'content': text,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Brief.query.count(), self.num_briefs)

    def test_edit_brief_ok(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)

        new_title = 'this is a new title'
        new_text = 'whatever'
        new_summary = 'this is a new summary'

        # edit unprotected brief is ok
        self.assertNotEqual(self.visible_brief.title, new_title)
        self.assertNotEqual(self.visible_brief.content, new_text)

        response = self.client.post(
            flask.url_for('admin.brief-edit', id=self.visible_brief.id, slug=self.visible_brief.slug),
            data={
                'title': new_title,
                'content': new_text,
                'summary': new_summary
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        p = db.session.get(Brief, self.visible_brief.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, new_title)
        self.assertEqual(p.content, new_text)
        self.assertEqual(p.summary, new_summary)

    def test_edit_brief_not_admin_ko(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)
        self.logout()

        new_title = 'this is a new title'
        new_text = 'whatever'

        response = self.client.post(
            flask.url_for('admin.brief-edit', id=self.visible_brief.id, slug=self.visible_brief.slug),
            data={
                'title': new_title,
                'content': new_text,
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        # it remains untouched
        p = db.session.get(Brief, self.visible_brief.id)
        self.assertIsNotNone(p)
        self.assertEqual(p.title, self.visible_brief.title)
        self.assertEqual(p.content, self.visible_brief.content)

    def test_toggle_visibility_ok(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)

        self.assertFalse(db.session.get(Brief, self.invisible_brief.id).visible)

        response = self.client.get(flask.url_for('admin.brief-toggle-visibility', id=self.invisible_brief.id))
        self.assertEqual(response.status_code, 302)

        self.assertTrue(db.session.get(Brief, self.invisible_brief.id).visible)

        response = self.client.get(flask.url_for('admin.brief-toggle-visibility', id=self.invisible_brief.id))
        self.assertEqual(response.status_code, 302)

        self.assertFalse(db.session.get(Brief, self.invisible_brief.id).visible)

    def test_delete_brief_ok(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)

        response = self.client.delete(
            flask.url_for('admin.brief-delete', id=self.visible_brief.id),
            follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Brief.query.count(), self.num_briefs - 1)

        self.assertIsNone(db.session.get(Brief, self.visible_brief.id))

    def test_delete_brief_not_admin_ko(self):
        self.assertEqual(Brief.query.count(), self.num_briefs)
        self.logout()

        response = self.client.delete(
            flask.url_for('admin.brief-delete', id=self.visible_brief.id),
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Brief.query.count(), self.num_briefs)
        self.assertIsNotNone(db.session.get(Brief, self.visible_brief.id))

    def test_visitor_view_ok(self):

        p = self.visible_brief

        # view as admin
        response = self.client.get(flask.url_for('visitor.brief-view', id=p.id, slug=p.slug))
        self.assertIn(p.title, response.get_data(as_text=True))
        self.assertIn(p.content, response.get_data(as_text=True))

        # view as visitor
        self.logout()
        response = self.client.get(flask.url_for('visitor.brief-view', id=p.id, slug=p.slug))
        self.assertIn(p.title, response.get_data(as_text=True))
        self.assertIn(p.content, response.get_data(as_text=True))

    def test_visitor_hidden_brief_ko(self):

        p = self.invisible_brief

        # view as admin
        response = self.client.get(flask.url_for('visitor.brief-view', id=p.id, slug=p.slug))
        self.assertIn(p.title, response.get_data(as_text=True))
        self.assertIn(p.content, response.get_data(as_text=True))  # ok :)

        # view as visitor
        self.logout()
        response = self.client.get(flask.url_for('visitor.brief-view', id=p.id, slug=p.slug))
        self.assertEqual(response.status_code, 404)  # cannot view
