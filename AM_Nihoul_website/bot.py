from datetime import datetime
import logging

from AM_Nihoul_website import db, settings
from AM_Nihoul_website.visitor.models import NewsletterRecipient, Email

logging.basicConfig(level=settings.LOGLEVEL, format='%(asctime)s (%(levelname)s) %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def bot_iteration():
    """The bot handles:

    1. Remove newsletter recipients that did not confirm their inscription after ``REMOVE_RECIPIENT_DELTA``
    2. Send emails
    """

    # remove recipients
    recipients = NewsletterRecipient.query\
        .filter(NewsletterRecipient.confirmed.is_(False))\
        .filter(NewsletterRecipient.date_created <= datetime.now() - settings.APP_CONFIG['REMOVE_RECIPIENTS_DELTA'])\
        .all()

    for r in recipients:
        logger.info('clean-recipients:: removed {} (id={})'.format(r.get_scrambled_email(), r.id))
        db.session.delete(r)

    # send emails
    emails = Email.query\
        .filter(Email.sent.is_(False))\
        .all()

    for e in emails:
        e.sent = True
        # TODO: actually send something
        logger.info('email:: sent `{}` to {} (id={}, recipient.id={})'.format(
            e.title, e.recipient.get_scrambled_email(), e.id, e.recipient.id))
        db.session.add(e)

    if len(recipients) > 0 or len(emails) > 0:
        db.session.commit()
