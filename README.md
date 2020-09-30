# Code source du site web de l'association Anne-Marie Nihoul

Mise au gout du jour du site web [http://www.annemarienihoul.be/](http://www.annemarienihoul.be/).

# Installation

```bash
# create virtualenv
python3 -m venv venv
source venv/bin/activate

# install stuffs
make init
```

Et dans `settings_prod.py` (serveur <https://amn.pierrebeaujean.net/>):

```python
from AM_Nihoul_website import settings

settings.WEBPAGE_INFO['fa_kit'] = '*****'

settings.APP_CONFIG['LAUNCH_BOT'] = False
settings.APP_CONFIG['USE_FAKE_MAIL_SENDER'] = False

settings.APP_CONFIG['SECRET_KEY'] = '****'
settings.APP_CONFIG['PASSWORD'] = '*****'

del settings.APP_CONFIG['SERVER_NAME']
```