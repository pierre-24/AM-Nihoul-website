from flask import Blueprint

from AM_Nihoul_website import db
from AM_Nihoul_website.pages.models import Page

pages_blueprint = Blueprint('pages', __name__, url_prefix='/pages')


@pages_blueprint.route('/test')
def tmp():
    return 'test2'
