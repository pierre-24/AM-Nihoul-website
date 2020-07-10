from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Page, Category


def bootstrap():
    """Create the minimum set of stuffs"""

    # categories
    c = Category.create('Site web')
    db.session.add(c)
    db.session.commit()

    # pages
    pages = [
        Page.create('Accueil', "<i>Placez un petit message d'accueil</i>", protected=True),
        Page.create('À propos de', '<i>Indiquez ici des détails sur le site web</i>', protected=True, category_id=c.id),
        Page.create('Contact', '<i>Donnez vos informations de contact ici</i>', protected=True, category_id=c.id)
    ]

    for o in pages:
        db.session.add(o)

    db.session.commit()
