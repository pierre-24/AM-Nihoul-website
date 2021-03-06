import flask
import datetime
import os

from AM_Nihoul_website.tests import TestFlask
from AM_Nihoul_website import db, settings, bot
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email, Newsletter


class TestFakeMailClient(TestFlask):
    def test_fake_ok(self):
        f = bot.FakeMailClient()

        subject = 'test'
        content = 'test1325'
        to = 'test@xyz.com'
        sender = 'me@xyz.com'

        f.send_message(to, sender, subject, content)

        with open(os.path.join(self.data_files_directory, bot.FakeMailClient.OUT)) as f:
            f_content = f.read()
            self.assertIn(subject, f_content)
            self.assertIn(to, f_content)
            self.assertIn(content, f_content)


class TestNewsletterRecipient(TestFlask):

    def setUp(self):
        super().setUp()

        self.subscribed_first_step = NewsletterRecipient.create('test1', 'x1@yz.com')
        self.subscribed = NewsletterRecipient.create('test2', 'x2@yz.com', confirmed=True)

        db.session.add(self.subscribed_first_step)
        db.session.add(self.subscribed)
        db.session.commit()

        self.num_recipients = NewsletterRecipient.query.count()
        self.login()

    def test_subscribe_first_step_ok(self):
        name = 'test3'
        email = 'x3@yz.com'

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        response = self.client.post(
            flask.url_for('visitor.newsletter-subscribe'),
            data={
                'name': name,
                'email': email,
                'opt_in': True
            },
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.num_recipients + 1, NewsletterRecipient.query.count())

        r = NewsletterRecipient.query.order_by(NewsletterRecipient.id.desc()).first()
        self.assertEqual(r.name, name)
        self.assertEqual(r.email, email)
        self.assertFalse(r.confirmed)

        # an email was sent:
        self.assertEqual(1, Email.query.filter(Email.recipient_id.is_(r.id)).count())

    def test_subscribe_first_step_already_in_ko(self):
        name = 'test3'

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        response = self.client.post(
            flask.url_for('visitor.newsletter-subscribe'),
            data={
                'name': name,
                'email': self.subscribed_first_step.email,
                'opt_in': True
            },
            follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertEqual(
            1,
            NewsletterRecipient.query.filter(NewsletterRecipient.email.is_(self.subscribed_first_step.email)).count())

        # no email was sent
        self.assertEqual(0, Email.query.filter(Email.recipient_id.is_(self.subscribed_first_step.id)).count())

    def test_subscribe_second_step_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertFalse(self.subscribed_first_step.confirmed, False)

        self.client.get(flask.url_for(
            'visitor.newsletter-confirm',
            id=self.subscribed_first_step.id,
            hash=self.subscribed_first_step.hash))

        r = NewsletterRecipient.query.get(self.subscribed_first_step.id)
        self.assertTrue(r.confirmed)

    def test_subscribe_second_step_already_done_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertTrue(self.subscribed.confirmed)

        response = self.client.get(flask.url_for(
            'visitor.newsletter-confirm',
            id=self.subscribed.id,
            hash=self.subscribed.hash))

        self.assertEqual(response.status_code, 404)

    def test_unsubscribe_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        self.client.get(flask.url_for(
            'visitor.newsletter-unsubscribe',
            id=self.subscribed.id,
            hash=self.subscribed.hash))

        self.assertEqual(self.num_recipients - 1, NewsletterRecipient.query.count())
        self.assertIsNone(NewsletterRecipient.query.get(self.subscribed.id))

    def test_subscribe_second_step_wrong_hash_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertFalse(self.subscribed_first_step.confirmed, False)

        wrong_hash = self.subscribed_first_step.hash
        wrong_hash = wrong_hash[:-1] + ('a' if wrong_hash[-1] != 'a' else 'b')

        self.client.get(flask.url_for('visitor.newsletter-confirm', id=self.subscribed_first_step.id, hash=wrong_hash))

        r = NewsletterRecipient.query.get(self.subscribed_first_step.id)
        self.assertFalse(r.confirmed)

    def test_unsubscribe_wrong_hash_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        wrong_hash = self.subscribed_first_step.hash
        wrong_hash = wrong_hash[:-1] + ('a' if wrong_hash[-1] != 'a' else 'b')

        self.client.get(flask.url_for('visitor.newsletter-unsubscribe', id=self.subscribed.id, hash=wrong_hash))

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertIsNotNone(NewsletterRecipient.query.get(self.subscribed.id))

    def test_removed_by_bot_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.subscribed_first_step.date_created -= settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA']
        self.subscribed_first_step.date_created -= datetime.timedelta(seconds=1)  # now I'm sure it's good!

        bot.bot_iteration()

        self.assertEqual(self.num_recipients - 1, NewsletterRecipient.query.count())
        self.assertIsNone(NewsletterRecipient.query.get(self.subscribed_first_step.id))

    def test_not_removed_by_bot_above_limit_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        bot.bot_iteration()

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        n = NewsletterRecipient.query.get(self.subscribed_first_step.id)
        db.session.add(n)
        self.assertIsNotNone(n)

    def test_not_removed_by_bot_confirmed_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        self.subscribed.date_created -= settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA']
        self.subscribed.date_created -= datetime.timedelta(seconds=1)  # now I'm sure it's good!

        bot.bot_iteration()

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertIsNotNone(NewsletterRecipient.query.get(self.subscribed.id))

    def test_sent_by_bot(self):
        # add an email
        e = Email.create('test', 'test', recipient_id=self.subscribed_first_step.id)
        self.assertFalse(e.sent)
        db.session.add(e)
        db.session.commit()

        bot.bot_iteration()

        self.assertTrue(Email.query.get(e.id).sent)


class TestNewsletter(TestFlask):

    def setUp(self):
        super().setUp()

        self.subscribed_first_step = NewsletterRecipient.create('test1', 'x1@yz.com')
        self.subscribed = NewsletterRecipient.create('test2', 'x2@yz.com', confirmed=True)

        db.session.add(self.subscribed_first_step)
        db.session.add(self.subscribed)

        self.draft_newsletter = Newsletter.create('test1', 'content of test1')
        self.published_newsletter = Newsletter.create('test2', 'content of test2', draft=False)

        db.session.add(self.draft_newsletter)
        db.session.add(self.published_newsletter)

        db.session.commit()

        self.num_recipients = NewsletterRecipient.query.count()
        self.num_newsletter = Newsletter.query.count()
        self.num_email = Email.query.count()
        self.login()

    def test_create_newsletter_ok(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())

        title = 'this is a new title'
        content = 'this is a new text'

        response = self.client.post(
            flask.url_for('admin.newsletter-create'),
            data={
                'title': title,
                'content': content
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.num_newsletter + 1, Newsletter.query.count())

        n = Newsletter.query.order_by(Newsletter.id.desc()).first()
        self.assertEqual(n.title, title)
        self.assertEqual(n.content, content)
        self.assertTrue(n.draft)

    def test_create_newsletter_not_admin_ko(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())
        self.logout()

        title = 'this is a new title'
        content = 'this is a new text'

        response = self.client.post(
            flask.url_for('admin.newsletter-create'),
            data={
                'title': title,
                'content': content
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.num_newsletter, Newsletter.query.count())

    def test_view_newsletter_admin_ok(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())

        response = self.client.get(flask.url_for('admin.newsletter-view', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.draft_newsletter.title, response.get_data(as_text=True))

    def test_view_newsletter_not_admin_ko(self):
        self.logout()

        response = self.client.get(flask.url_for('admin.newsletter-view', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 302)

    def test_view_newsletter_ok(self):
        # admin
        response = self.client.get(flask.url_for(
            'visitor.newsletter-view', id=self.published_newsletter.id, slug=self.published_newsletter.slug))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.published_newsletter.content, response.get_data(as_text=True))

        # visitor
        self.logout()
        response = self.client.get(flask.url_for(
            'visitor.newsletter-view', id=self.published_newsletter.id, slug=self.published_newsletter.slug))

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.published_newsletter.content, response.get_data(as_text=True))

    def test_visit_draft_newsletter_ko(self):
        # admin
        response = self.client.get(flask.url_for(
            'visitor.newsletter-view', id=self.draft_newsletter.id, slug=self.draft_newsletter.slug))
        self.assertEqual(response.status_code, 404)

        # visitor
        self.logout()
        response = self.client.get(flask.url_for(
            'visitor.newsletter-view', id=self.draft_newsletter.id, slug=self.draft_newsletter.slug))
        self.assertEqual(response.status_code, 404)

    def test_edit_newsletter_draft_ok(self):
        title = 'this is a new title'
        content = 'this is a new text'

        old_slug = self.draft_newsletter.slug

        response = self.client.post(
            flask.url_for(
                'admin.newsletter-edit', id=self.draft_newsletter.id, slug=self.draft_newsletter.slug),
            data={
                'title': title,
                'content': content
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        n = Newsletter.query.get(self.draft_newsletter.id)
        self.assertEqual(n.title, title)
        self.assertEqual(n.content, content)
        self.assertNotEqual(n.slug, old_slug)

    def test_edit_newsletter_draft_not_admin_ko(self):
        title = 'this is a new title'
        content = 'this is a new text'
        self.logout()

        old_slug = self.draft_newsletter.slug

        response = self.client.post(
            flask.url_for(
                'admin.newsletter-edit', id=self.draft_newsletter.id, slug=self.draft_newsletter.slug),
            data={
                'title': title,
                'content': content
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        n = Newsletter.query.get(self.draft_newsletter.id)
        self.assertNotEqual(n.title, title)
        self.assertNotEqual(n.content, content)
        self.assertEqual(n.slug, old_slug)

    def test_edit_newsletter_published_ok(self):
        title = 'this is a new title'
        content = 'this is a new text'

        old_slug = self.published_newsletter.slug

        response = self.client.post(
            flask.url_for(
                'admin.newsletter-edit', id=self.published_newsletter.id, slug=self.published_newsletter.slug),
            data={
                'title': title,
                'content': content
            }, follow_redirects=False)

        self.assertEqual(response.status_code, 302)

        n = Newsletter.query.get(self.published_newsletter.id)
        self.assertEqual(n.title, title)
        self.assertEqual(n.content, content)
        self.assertEqual(n.slug, old_slug)  # slug does not change, as it is published

    def test_delete_newsletter_ok(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())

        response = self.client.delete(flask.url_for('admin.newsletter-delete', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_newsletter - 1, Newsletter.query.count())
        self.assertIsNone(Newsletter.query.get(self.draft_newsletter.id))

    def test_delete_newsletter_not_admin_ko(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())
        self.logout()

        response = self.client.delete(flask.url_for('admin.newsletter-delete', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_newsletter, Newsletter.query.count())
        self.assertIsNotNone(Newsletter.query.get(self.draft_newsletter.id))

    def test_publish_newsletter_ok(self):
        self.assertTrue(self.draft_newsletter.draft)

        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = Newsletter.query.get(self.draft_newsletter.id)
        self.assertFalse(n.draft)

        # check email
        self.assertEqual(self.num_email + 1, Email.query.count())
        e = Email.query.order_by(Email.id.desc()).first()
        self.assertEqual(e.recipient, self.subscribed)

        self.assertIn(n.title, e.content)
        self.assertIn(n.content, e.content)

    def test_publish_newsletter_not_admin_ko(self):
        self.assertTrue(self.draft_newsletter.draft)
        self.logout()

        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = Newsletter.query.get(self.draft_newsletter.id)
        self.assertTrue(n.draft)
