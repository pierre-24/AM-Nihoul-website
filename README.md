![](./AM_Nihoul_website/assets/images/logo.svg)

# Code source du site web de l'association Anne-Marie Nihoul ASBL

Mise au gout du jour du site web [http://annemarienihoul.be/](http://annemarienihoul.be/).

Version: 0.8.3

# Installation

```bash
# create virtualenv
python3 -m venv venv
source venv/bin/activate

# install stuffs
make init
```

Si nécessaire, configurez `instance/settings.py`.

N'oubliez pas d'utiliser un service type [gunicorn](https://gunicorn.org/).

Pour l'envoi des emails, le code utilise [`simplegmail`](https://github.com/jeremyephron/simplegmail), il faut donc le configurer (voir les instructions dans le [README](https://github.com/jeremyephron/simplegmail#getting-started)).

# Mise a jour

```bash
make sync # mettre à jour les dépendances du back
make front  # reconstruire front

 # mettre à jour la BDD
export FLASK_APP=AM_Nihoul_website
flask db upgrade 
```
