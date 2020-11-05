![](./AM_Nihoul_website/assets/images/logo.svg)

# Code source du site web de l'association Anne-Marie Nihoul

Mise au gout du jour du site web [http://annemarienihoul.be/](http://annemarienihoul.be/).

# Installation

```bash
# create virtualenv
python3 -m venv venv
source venv/bin/activate

# install stuffs
make init
```

Et dans `settings_prod.py`,

```python
from AM_Nihoul_website import settings

settings.WEBPAGE_INFO['fa_kit'] = '*****'

settings.WEBPAGE_INFO['gtag'] = '*****'
settings.WEBPAGE_INFO['cookies_explain_page'] = 'cookies.html'  # mandatory if gtag is set

settings.APP_CONFIG['LAUNCH_BOT'] = False
settings.APP_CONFIG['USE_FAKE_MAIL_SENDER'] = False
settings.APP_CONFIG['NEWSLETTER_SENDER_EMAIL'] = '*****'

settings.APP_CONFIG['SECRET_KEY'] = '****'
settings.APP_CONFIG['PASSWORD'] = '*****'

del settings.APP_CONFIG['SERVER_NAME'] # messed up with stuffs
```

N'oubliez pas d'utiliser un service type [gunicorn](https://gunicorn.org/).