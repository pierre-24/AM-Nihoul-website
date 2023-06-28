import flask
import datetime
import os
import pathlib
from bs4 import BeautifulSoup

from werkzeug.datastructures import FileStorage

from AM_Nihoul_website.tests import TestFlask
from AM_Nihoul_website import db, settings, bot
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email, Newsletter, UploadedFile, EmailImageAttachment
from AM_Nihoul_website.admin.utils import Message
from AM_Nihoul_website.visitor.utils import make_summary


BASE = pathlib.Path(__file__).parent.parent


class TestFakeMailClient(TestFlask):
    def test_fake_ok(self):
        f = bot.FakeMailClient()

        message = Message(
            recipient='test@xyz.com',
            sender='me@xyz.com',
            subject='test',
            msg_html='test1325'
        )

        f.send(message)

        with open(os.path.join(self.data_files_directory, bot.FakeMailClient.OUT)) as f:
            f_content = f.read()
            self.assertIn(message.subject, f_content)
            self.assertIn(message.recipient, f_content)
            self.assertIn(message.msg_plain, f_content)


class TestNewsletterRecipient(TestFlask):

    def setUp(self):
        super().setUp()

        self.subscribed_first_step = NewsletterRecipient.create('test1', 'x1@yz.com')
        self.subscribed = NewsletterRecipient.create('test2', 'x2@yz.com', confirmed=True)

        db.session.add(self.subscribed_first_step)
        db.session.add(self.subscribed)

        self.num_recipients = NewsletterRecipient.query.count()
        self.login()

        # mute recaptcha
        settings.WEBPAGE_INFO['recaptcha_public_key'] = ''

        # add image
        with (BASE / './assets/images/favicon.png').open('rb') as f:
            storage = FileStorage(stream=f, filename='favicon.png', content_type='image/png')
            self.image = UploadedFile.create(storage, storage.filename)
            db.session.add(self.image)

        # commit everything
        db.session.commit()

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

        r = self.db_session.get(NewsletterRecipient, self.subscribed_first_step.id)
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
        self.assertIsNone(self.db_session.get(NewsletterRecipient, self.subscribed.id))

    def test_subscribe_second_step_wrong_hash_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertFalse(self.subscribed_first_step.confirmed, False)

        wrong_hash = self.subscribed_first_step.hash
        wrong_hash = wrong_hash[:-1] + ('a' if wrong_hash[-1] != 'a' else 'b')

        self.client.get(flask.url_for('visitor.newsletter-confirm', id=self.subscribed_first_step.id, hash=wrong_hash))

        r = self.db_session.get(NewsletterRecipient, self.subscribed_first_step.id)
        self.assertFalse(r.confirmed)

    def test_unsubscribe_wrong_hash_ko(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        wrong_hash = self.subscribed_first_step.hash
        wrong_hash = wrong_hash[:-1] + ('a' if wrong_hash[-1] != 'a' else 'b')

        self.client.get(flask.url_for('visitor.newsletter-unsubscribe', id=self.subscribed.id, hash=wrong_hash))

        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.assertIsNotNone(self.db_session.get(NewsletterRecipient, self.subscribed.id))

    def test_removed_by_bot_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
        self.subscribed_first_step.date_created -= settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA']
        self.subscribed_first_step.date_created -= datetime.timedelta(seconds=1)  # now I'm sure it's good!

        self.db_session.add(self.subscribed_first_step)
        self.db_session.commit()

        bot.bot_iteration()

        with db.app.app_context():
            self.assertEqual(self.num_recipients - 1, NewsletterRecipient.query.count())
            self.assertIsNone(self.db_session.get(NewsletterRecipient, self.subscribed_first_step.id))

    def test_not_removed_by_bot_above_limit_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        bot.bot_iteration()

        with db.app.app_context():
            self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        n = self.db_session.get(NewsletterRecipient, self.subscribed_first_step.id)
        db.session.add(n)
        self.assertIsNotNone(n)

    def test_not_removed_by_bot_confirmed_ok(self):
        self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())

        self.subscribed.date_created -= settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA']
        self.subscribed.date_created -= datetime.timedelta(seconds=1)  # now I'm sure it's good!

        self.db_session.add(self.subscribed_first_step)
        self.db_session.commit()

        bot.bot_iteration()

        with db.app.app_context():
            self.assertEqual(self.num_recipients, NewsletterRecipient.query.count())
            self.assertIsNotNone(self.db_session.get(NewsletterRecipient, self.subscribed.id))

    def test_sent_by_bot(self):
        # add an email
        e = Email.create('test', 'test', recipient_id=self.subscribed_first_step.id)
        self.assertFalse(e.sent)
        db.session.add(e)
        db.session.commit()

        # add attachment
        attachment = EmailImageAttachment.create(e.id, self.image.id)
        db.session.add(attachment)
        db.session.commit()

        # send it
        bot.bot_iteration()

        # check
        with db.app.app_context():
            self.assertTrue(self.db_session.get(Email, e.id).sent)

        with open(os.path.join(self.data_files_directory, bot.FakeMailClient.OUT)) as f:
            content = f.read()

            self.assertIn(self.subscribed_first_step.email, content)
            self.assertIn(self.image.base_file_name, content)


class TestNewsletter(TestFlask):

    def setUp(self):
        super().setUp()

        # add image
        with (BASE / './assets/images/favicon.png').open('rb') as f:
            storage = FileStorage(stream=f, filename='favicon.png', content_type='image/png')
            self.image = UploadedFile.create(storage, storage.filename)
            db.session.add(self.image)

        db.session.add(self.image)
        db.session.commit()

        # add others
        self.subscribed_first_step = NewsletterRecipient.create('test1', 'x1@yz.com')
        self.subscribed = NewsletterRecipient.create('test2', 'x2@yz.com', confirmed=True)

        db.session.add(self.subscribed_first_step)
        db.session.add(self.subscribed)

        self.draft_newsletter = Newsletter.create('test1', 'content of test1')
        self.published_newsletter = Newsletter.create('test2', 'content of test2', draft=False)
        self.draft_newsletter_with_image = Newsletter.create(
            'test3',
            'content: <img src="{p}" alt="test" /> <img src="{p}" alt="test2" />'.format(p=flask.url_for(
                'visitor.upload-view', id=self.image.id, filename=self.image.file_name, _external=True)))
        self.draft_newsletter_with_summary = Newsletter.create(
            'test4', '<summary></summary> <h1>test</h1> content of test4')

        db.session.add(self.draft_newsletter)
        db.session.add(self.draft_newsletter_with_image)
        db.session.add(self.published_newsletter)
        db.session.add(self.draft_newsletter_with_summary)

        db.session.commit()

        self.num_recipients = NewsletterRecipient.query.count()
        self.num_newsletter = Newsletter.query.count()
        self.num_email = Email.query.count()
        self.login()

    def test_make_summary_ok(self):
        titles = ['a first', 'a second']
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3>'.format(*titles)

        output_text = make_summary(input_text)
        soup = BeautifulSoup(output_text, 'html.parser')

        print(output_text)

        self.assertIsNone(soup.find('summary'))
        summary_list = soup.find('ul', class_='summary')
        self.assertIsNotNone(summary_list)

        a_tags = list(summary_list.find_all('a'))
        self.assertEqual(len(a_tags), len(titles))
        self.assertEqual([a.string for a in a_tags], titles)

    def test_make_summary_repetitive_title_ok(self):
        titles = ['repetitive', 'repetitive', 'repetitive']
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3><h3>{}</h3>'.format(*titles)

        output_text = make_summary(input_text)
        soup = BeautifulSoup(output_text, 'html.parser')
        summary_list = soup.find('ul', class_='summary')
        a_tags = list(summary_list.find_all('a'))

        links = [a['href'] for a in a_tags]
        for link in links:
            self.assertEqual(links.count(link), 1)

    def test_make_summary_page_link_ok(self):
        titles = ['a first', 'a second']
        link = 'test.html'
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3>'.format(*titles)

        output_text = make_summary(input_text, page_link=link)
        soup = BeautifulSoup(output_text, 'html.parser')
        summary_list = soup.find('ul', class_='summary')
        a_tags = list(summary_list.find_all('a'))

        self.assertTrue(all(link in a['href'] for a in a_tags))

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

    def test_view_draft_newsletter_with_summary_ok(self):
        # make summary
        titles = ['a first', 'a second']
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3>'.format(*titles)

        self.draft_newsletter.content = input_text
        self.db_session.add(self.draft_newsletter)
        self.db_session.commit()

        # visit (as admin)
        response = self.client.get(flask.url_for('admin.newsletter-view', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
        self.assertIsNone(soup.find('summary'))
        summary_list = soup.find('ul', class_='summary')
        self.assertIsNotNone(summary_list)

        a_tags = list(summary_list.find_all('a'))
        self.assertEqual(len(a_tags), len(titles))
        self.assertEqual([a.string for a in a_tags], titles)

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

    def test_view_newsletter_with_summary_ok(self):
        # make summary
        titles = ['a first', 'a second']
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3>'.format(*titles)

        self.published_newsletter.content = input_text
        self.db_session.add(self.published_newsletter)
        self.db_session.commit()

        # visit
        self.logout()
        response = self.client.get(flask.url_for(
            'visitor.newsletter-view', id=self.published_newsletter.id, slug=self.published_newsletter.slug))
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.get_data(as_text=True), 'html.parser')
        self.assertIsNone(soup.find('summary'))
        summary_list = soup.find('ul', class_='summary')
        self.assertIsNotNone(summary_list)

        a_tags = list(summary_list.find_all('a'))
        self.assertEqual(len(a_tags), len(titles))
        self.assertEqual([a.string for a in a_tags], titles)

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

        n = self.db_session.get(Newsletter, self.draft_newsletter.id)
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

        n = self.db_session.get(Newsletter, self.draft_newsletter.id)
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

        n = self.db_session.get(Newsletter, self.published_newsletter.id)
        self.assertEqual(n.title, title)
        self.assertEqual(n.content, content)
        self.assertEqual(n.slug, old_slug)  # slug does not change, as it is published

    def test_delete_newsletter_ok(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())

        response = self.client.delete(flask.url_for('admin.newsletter-delete', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_newsletter - 1, Newsletter.query.count())
        self.assertIsNone(self.db_session.get(Newsletter, self.draft_newsletter.id))

    def test_delete_newsletter_not_admin_ko(self):
        self.assertEqual(self.num_newsletter, Newsletter.query.count())
        self.logout()

        response = self.client.delete(flask.url_for('admin.newsletter-delete', id=self.draft_newsletter.id))
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_newsletter, Newsletter.query.count())
        self.assertIsNotNone(self.db_session.get(Newsletter, self.draft_newsletter.id))

    def test_publish_newsletter_ok(self):
        self.assertTrue(self.draft_newsletter.draft)

        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = self.db_session.get(Newsletter, self.draft_newsletter.id)
        self.assertFalse(n.draft)

        # check email
        self.assertEqual(self.num_email + 1, Email.query.count())
        e = Email.query.order_by(Email.id.desc()).first()
        self.assertEqual(e.recipient, self.subscribed)

        self.assertIn(n.title, e.content)
        self.assertIn(n.content, e.content)

    def test_publish_newsletter_with_image_ok(self):
        self.assertTrue(self.draft_newsletter_with_image.draft)

        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter_with_image.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = self.db_session.get(Newsletter, self.draft_newsletter_with_image.id)
        self.assertFalse(n.draft)

        # check email
        self.assertEqual(self.num_email + 1, Email.query.count())
        e = Email.query.order_by(Email.id.desc()).first()
        self.assertEqual(e.recipient, self.subscribed)

        # check attachment
        attachments = e.attachments()
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0].image.id, self.image.id)

        # check cid is actually used
        self.assertIn('cid:{}'.format(self.image.file_name), e.content)

    def test_publish_newsletter_summary_ok(self):
        # add summary
        self.assertTrue(self.draft_newsletter.draft)

        titles = ['a first', 'a second']
        input_text = '<summary></summary> <h3>{}</h3><h3>{}</h3>'.format(*titles)
        link = flask.url_for(
            'visitor.newsletter-view', id=self.draft_newsletter.id, slug=self.draft_newsletter.slug, _external=True)

        self.draft_newsletter.content = input_text
        self.db_session.add(self.draft_newsletter)
        self.db_session.commit()

        # publish
        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = self.db_session.get(Newsletter, self.draft_newsletter.id)
        self.assertFalse(n.draft)

        # check email
        self.assertEqual(self.num_email + 1, Email.query.count())
        e = Email.query.order_by(Email.id.desc()).first()

        soup = BeautifulSoup(e.content, 'html.parser')
        self.assertIsNone(soup.find('summary'))
        summary_list = soup.find('ul', class_='summary')
        self.assertIsNotNone(summary_list)

        a_tags = list(summary_list.find_all('a'))
        self.assertEqual(len(a_tags), len(titles))
        self.assertEqual([a.string for a in a_tags], titles)
        self.assertTrue(all(link in a['href'] for a in a_tags))

    def test_publish_newsletter_not_admin_ko(self):
        self.assertTrue(self.draft_newsletter.draft)
        self.logout()

        response = self.client.post(
            flask.url_for('admin.newsletter-publish', id=self.draft_newsletter.id), data={'confirm': True})

        self.assertEqual(response.status_code, 302)

        n = self.db_session.get(Newsletter, self.draft_newsletter.id)
        self.assertTrue(n.draft)
