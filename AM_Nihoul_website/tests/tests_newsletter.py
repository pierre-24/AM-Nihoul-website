import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import NewsletterRecipient
from AM_Nihoul_website.tests import TestFlask


class TestNewsletter(TestFlask):

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

    def test_subscribe_second_step_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertFalse(self.subscribed_first_step.confirmed, False)

        self.client.get(flask.url_for(
            'visitor.newsletter-confirm',
            id=self.subscribed_first_step.id,
            hash=self.subscribed_first_step.hash))

        r = NewsletterRecipient.query.get(self.subscribed_first_step.id)
        self.assertTrue(r.confirmed)

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

        self.client.get(flask.url_for(
            'visitor.newsletter-confirm',
            id=self.subscribed_first_step.id,
            hash=wrong_hash))

        r = NewsletterRecipient.query.get(self.subscribed_first_step.id)
        self.assertFalse(r.confirmed)

    def test_unsubscribe_wrong_hash_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        wrong_hash = self.subscribed_first_step.hash
        wrong_hash = wrong_hash[:-1] + ('a' if wrong_hash[-1] != 'a' else 'b')

        self.client.get(flask.url_for(
            'visitor.newsletter-unsubscribe',
            id=self.subscribed.id,
            hash=wrong_hash))

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertIsNotNone(NewsletterRecipient.query.get(self.subscribed.id))
