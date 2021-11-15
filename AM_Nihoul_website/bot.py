from datetime import datetime
import logging
import os
import pathlib

from AM_Nihoul_website import settings, db
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email
from AM_Nihoul_website.admin.utils import Gmail, Message

logging.basicConfig(level=settings.LOGLEVEL, format='%(asctime)s (%(levelname)s) %(message)s')
logger = logging.getLogger(__name__)


BASE = pathlib.Path(__file__).parent.parent


class FakeMailClient:
    OUT = 'fake_mail_out.txt'

    def send(self, message, **kwargs):
        with open(os.path.join(settings.DATA_DIRECTORY, self.OUT), 'a') as f:
            f.write('====\nSUBJECT: {}\nTO: {}\nON: {}\n====\n{}\n'.format(
                message.subject, message.recipient, datetime.now(), message.msg_html))

            if message.html_attachments:
                f.write('\n'.join('+ Attachment: {}, {}'.format(
                    a.get_content_type(), a['Content-ID']) for a in message.html_attachments))


def bot_iteration():
    """The bot handles:

    1. Remove newsletter recipients that did not confirm their inscription after ``REMOVE_RECIPIENT_DELTA``
    2. Send emails
    """

    logger.debug('bot_iteration:: tick')

    # remove recipients
    with db.app.app_context():
        recipients = NewsletterRecipient.query\
            .filter(NewsletterRecipient.confirmed.is_(False))\
            .filter(
                NewsletterRecipient.date_created <= datetime.now() - settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA'])\
            .all()

        for r in recipients:
            logger.info('clean-recipients:: removed {} (id={})'.format(r.get_scrambled_email(), r.id))
            db.session.delete(r)

        # send emails
        emails = Email.query\
            .filter(Email.sent.is_(False))\
            .all()

        if len(emails) > 0:
            # get client
            if settings.APP_CONFIG['USE_FAKE_MAIL_SENDER']:
                client = FakeMailClient()
            else:
                client = Gmail()

            # go for it
            for e in emails:

                data = {
                    'sender': settings.APP_CONFIG['NEWSLETTER_SENDER_EMAIL'],
                    'recipient': e.recipient.email,
                    'subject': e.title,
                    'msg_html': e.content,
                }

                message = Message(**data)

                # attach logo
                message.add_html_attachment(
                    BASE / settings.APP_CONFIG['NEWSLETTER_LOGO'], cid='newsletter-logo')

                # attach others, if any
                for attachment in e.attachments():
                    f = attachment.image
                    message.add_html_attachment(pathlib.Path(f.path()), cid=f.file_name)

                # send
                client.send(message)
                logger.info('email:: sent `{}` to {} (id={}, recipient.id={})'.format(
                    e.title, e.recipient.get_scrambled_email(), e.id, e.recipient.id))

                e.sent = True
                db.session.add(e)

        if len(recipients) > 0 or len(emails) > 0:
            db.session.commit()
