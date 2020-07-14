import os
from datetime import timedelta

DATA_DIRECTORY = 'data/'

APP_CONFIG = {
    # Flask secret key: generate a new one with
    # `python -c "import random; print(repr(''.join([chr(random.randrange(32, 126)) for _ in range(24)])))"`
    'SECRET_KEY': ';+b&#Yl] U$y7dzmW&IRh$GO',

    'USERNAME': 'admin',
    'PASSWORD': 'admin',

    # database
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + os.path.join(os.path.abspath(DATA_DIRECTORY), 'database.db'),

    # upload
    'UPLOADED_UPLOADS_DEST': os.path.join(DATA_DIRECTORY, 'uploads/'),

    # newsletter
    'REMOVE_RECIPIENTS_DELTA': timedelta(days=1)
}

WEBPAGE_INFO = {
    'author_url': 'https://pierrebeaujean.net/fr.html',
    'author_name': 'Pierre Beaujean',
    'repo_url': 'https://git.pierrebeaujean.net/pierre/AM-Nihoul-website',
    'site_name': 'Association Anne-Marie Nihoul',
    'site_description': 'aide aux malades',
    'site_version': '0.1a0',
    'fa_kit': ''
}

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *  # noqa
except ImportError:
    pass
