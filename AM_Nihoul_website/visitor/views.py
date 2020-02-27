from flask import Blueprint, abort

from AM_Nihoul_website.visitor.models import Page

visitor_blueprint = Blueprint('visitor', __name__)


@visitor_blueprint.route('/test/<string:slug>')
def tmp(slug):
    pages = Page.query.filter(Page.slug == slug).all()
    if len(pages) == 0:
        abort(404)

    return pages[0].content
