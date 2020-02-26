import os

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
}

WEBPAGE_INFO = {
    'repo_url': 'https://git.pierrebeaujean.net/pierre/AM-Nihoul-website',
    'author_url': 'https://pierrebeaujean.net',
    'author_name': 'Pierre Beaujean',
    'site_description': 'Association Anne-Marie Nihoul - Aide aux malades'
}

# Load the production settings, overwrite the existing ones if needed
try:
    from settings_prod import *  # noqa
except ImportError:
    pass
