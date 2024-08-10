from datetime import datetime
import logging
import os
import pathlib
import base64

from flask import current_app

import AM_Nihoul_website
from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email
from AM_Nihoul_website.admin.utils import Gmail, Message

logging.basicConfig(level=AM_Nihoul_website.LOGLEVEL, format='%(asctime)s (%(levelname)s) %(message)s')
logger = logging.getLogger(__name__)


BASE = pathlib.Path(__file__).parent.parent


class FakeMailClient:
    OUT = 'fake_mail_out.txt'

    def send(self, message: Message, **kwargs):
        with open(os.path.join(current_app.config['DATA_DIRECTORY'], self.OUT), 'a') as f:
            f.write('**********\nSUBJECT: {}\nTO: {}\nON: {}\n**********\n{}\n'.format(
                message.subject, message.recipient, datetime.now(), message.msg_html))

            if message.html_attachments:
                f.write('\n'.join('+ Attachment: {}, {}\n'.format(
                    a.get_content_type(), a['Content-ID']) for a in message.html_attachments))

            f.write('*********\n')
            f.write(base64.urlsafe_b64decode(message.prepare()['raw']).decode())
            f.write('*********\n')


def bot_iteration():
    """The bot handles:

    1. Remove newsletter recipients that did not confirm their inscription after ``REMOVE_RECIPIENT_DELTA``
    2. Send emails
    """

    logger.debug('bot_iteration:: tick')

    # remove recipients
    with current_app.app_context():
        recipients = NewsletterRecipient.query\
            .filter(NewsletterRecipient.confirmed.is_(False))\
            .filter(
                NewsletterRecipient.date_created <= datetime.now() - current_app.config['REMOVE_RECIPIENTS_DELTA'])\
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
            if current_app.config['USE_FAKE_MAIL_SENDER']:
                client = FakeMailClient()
            else:
                client = Gmail()

            # go for it
            for e in emails:

                data = {
                    'sender': current_app.config['NEWSLETTER_SENDER_EMAIL'],
                    'recipient': e.recipient.email,
                    'subject': e.title,
                    'msg_html': e.content,
                    'reply_to': current_app.config['NEWSLETTER_SENDER_EMAIL']
                }

                if 'NEWSLETTER_REPLY_TO_EMAIL' in current_app.config \
                        and current_app.config['NEWSLETTER_REPLY_TO_EMAIL'] is not None:
                    data['reply_to'] = current_app.config['NEWSLETTER_REPLY_TO_EMAIL']

                message = Message(**data)

                # attach logo
                message.add_html_attachment(
                    BASE / current_app.config['NEWSLETTER_LOGO'], cid='newsletter-logo')

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
