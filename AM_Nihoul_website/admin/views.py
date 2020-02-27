from flask import Blueprint

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Page

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blueprint.route('/test/<string:name>')
def tmp(name):
    p = Page.create(name, 'whatever')
    db.session.add(p)
    db.session.commit()

    return '{} created'.format(name)
