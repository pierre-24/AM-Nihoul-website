![](./AM_Nihoul_website/assets/images/logo.svg)

# Code source du site web de l'association Anne-Marie Nihoul ASBL

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

# config interne
settings.APP_CONFIG.update({
    # Pour utiliser le bot (ici comme un service externe):
    'LAUNCH_BOT': False,  # `True` pour l'utiliser en même temps 
    'USE_FAKE_MAIL_SENDER': False,
    
    # Personne indiquée comme envoyant le mail
    'NEWSLETTER_SENDER_EMAIL': '****',
    
    # Clé secrète pour Flask
    'SECRET_KEY': '****',
    
    # Mot de passe d'administration
    'PASSWORD': '****',
    
    # Clé secrète reCAPTCHA (si utilisé)
    'RECAPTCHA_SECRET_KEY': '***'
})

settings.WEBPAGE_INFO.update({
    'site_keywords': 'leucémie, leucemie, nihoul, anne-marie, fondation, cancer, moelle osseuse, hla, malades, aide, aides',
    'fa_kit': '***',
    'gtag': '****',
    'cookies_explain_page': '****',
    
    # clé publique recaptcha
    'recaptcha_public_key': '****'
})

# ça peut poser des problèmes:
del settings.APP_CONFIG['SERVER_NAME']
```

N'oubliez pas d'utiliser un service type [gunicorn](https://gunicorn.org/).

Pour l'envoi des emails, le code utilise [`simplegmail`](https://github.com/jeremyephron/simplegmail), il faut donc le configurer (voir les instructions dans le [README](https://github.com/jeremyephron/simplegmail#getting-started)).

# Mise a jour

```bash
make sync # mettre à jour les dépendances du back
flask db upgrade  # mettre à jour la BDD
make front # mettre à jour et reconstruire le front
```
