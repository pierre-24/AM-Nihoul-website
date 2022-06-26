import os
from datetime import timedelta

DATA_DIRECTORY = 'data/'

LOGLEVEL = 'INFO'

APP_CONFIG = {
    # Flask secret key: generate a new one with
    # `python -c "import random; print(repr(''.join([chr(random.randrange(32, 126)) for _ in range(24)])))"`
    'SECRET_KEY': ';+b&#Yl] U$y7dzmW&IRh$GO',

    # change that in production
    'SERVER_NAME': '127.0.0.1:5000',
    'PREFERRED_URL_SCHEME': 'http',

    # username/password to access admin (change that in production)
    'USERNAME': 'admin',
    'PASSWORD': 'admin',

    # database
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(os.path.abspath(DATA_DIRECTORY), 'database.db'),

    # alembic
    'ALEMBIC_CONTEXT': {
        # useful since the database is sqlite (https://alembic.sqlalchemy.org/en/latest/batch.html)!
        'render_as_batch': True
    },

    # upload
    'UPLOADED_UPLOADS_DEST': os.path.join(DATA_DIRECTORY, 'uploads/'),
    'UPLOAD_CONVERT_TO_JPG': 250 * 1024,

    # newsletter
    'REMOVE_RECIPIENTS_DELTA': timedelta(days=1),
    'NEWSLETTER_SENDER_EMAIL': 'xyz@test.com',
    'USE_FAKE_MAIL_SENDER': False,
    'LAUNCH_BOT': True,
    'NEWSLETTER_LOGO': 'AM_Nihoul_website/assets/images/newsletter_logo.png',

    # scheduler
    'JOBS': [
        {
            'id': 'bot',
            'func': 'AM_Nihoul_website:bot.bot_iteration',
            'trigger': 'interval',
            'seconds': 60
        }
    ],

    'SCHEDULER_JOB_DEFAULTS': {
        'coalesce': False,
        'max_instances': 1
    },

    # important pages
    'PAGES': {
        'visitor_index': 1,
        'admin_index': 2
    },

    # recaptcha secret key
    'RECAPTCHA_SECRET_KEY': ''
}

WEBPAGE_INFO = {
    'author_url': 'https://pierrebeaujean.net/fr.html',
    'author_name': 'Pierre Beaujean',
    'repo_url': 'https://github.com/pierre-24/AM-Nihoul-website',
    'site_name': 'Association Anne-Marie Nihoul ASBL',
    'site_description': 'aide aux malades',
    'site_keywords': 'leucémie, aide au malades',
    'site_version': '0.6.4',

    # external services
    'fa_kit': '',  # FontAwesome
    'gtag': '',  # Google analytics
    'cookies_explain_page': '',  # if `gtag` is set, you MUST have a page that explains the cookies
    'recaptcha_public_key': ''
}

# limit over inscription at the newsletter
NEWSLETTER_LIMIT = '10/hour;1 per 5 second'
LOGIN_LIMIT = '10/hour;1 per 5 second'

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *  # noqa
except ImportError:
    pass
