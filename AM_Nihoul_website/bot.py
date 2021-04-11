from datetime import datetime
import logging
import os
import simplegmail

from AM_Nihoul_website import settings, db
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email

logging.basicConfig(level=settings.LOGLEVEL, format='%(asctime)s (%(levelname)s) %(message)s')
logger = logging.getLogger(__name__)


class FakeMailClient:
    OUT = 'fake_mail_out.txt'

    def send_message(self, to, sender, subject, msg_html, **kwargs):
        with open(os.path.join(settings.DATA_DIRECTORY, self.OUT), 'a') as f:
            f.write('====\nSUBJECT: {}\nTO: {}\nON: {}\n====\n{}'.format(subject, to, datetime.now(), msg_html))


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
                client = simplegmail.Gmail()

            # go for it
            for e in emails:
                e.sent = True

                data = {
                    'to': e.recipient.email,
                    'sender': settings.APP_CONFIG['NEWSLETTER_SENDER_EMAIL'],
                    'subject': e.title,
                    'msg_html': e.content,
                    'attachments': ['AM_Nihoul_website/assets/images/logo.svg'],
                }

                client.send_message(**data)

                logger.info('email:: sent `{}` to {} (id={}, recipient.id={})'.format(
                    e.title, e.recipient.get_scrambled_email(), e.id, e.recipient.id))
                db.session.add(e)

        if len(recipients) > 0 or len(emails) > 0:
            db.session.commit()
