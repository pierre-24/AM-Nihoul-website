import flask

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Page, Category, MenuEntry


def bootstrap():
    """Create the minimum set of stuffs"""

    # categories
    c = Category.create('Site web')
    db.session.add(c)
    db.session.commit()

    # pages
    pages = [
        Page.create('Accueil', "<i>Placez un petit message d'accueil</i>", protected=True, visible=False),
        Page.create("Accueil de l'administration", '<i>Vous savez quoi faire !</i>', protected=True, visible=False),
        Page.create('Contact', '<i>Donnez vos informations de contact ici</i>', protected=True, category_id=c.id),
        Page.create('À propos de', '<i>Indiquez ici des détails sur le site web</i>', protected=True, category_id=c.id)
    ]

    for o in pages:
        db.session.add(o)

    db.session.commit()

    # menu entries
    links = [
        MenuEntry.create(pages[2].title, flask.url_for('visitor.page-view', id=pages[2].id, slug=pages[2].slug)),
        MenuEntry.create(pages[3].title, flask.url_for('visitor.page-view', id=pages[3].id, slug=pages[3].slug)),
        MenuEntry.create('Albums photo', flask.url_for('visitor.albums'))
    ]

    links[0].order, links[1].order, links[2].order = 2, 0, 1

    for o in links:
        db.session.add(o)

    db.session.commit()
