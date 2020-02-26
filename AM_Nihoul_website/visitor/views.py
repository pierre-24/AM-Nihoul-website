from flask import Blueprint

from AM_Nihoul_website import db
from AM_Nihoul_website.visitor.models import Page

visitor_blueprint = Blueprint('visitor', __name__)


@visitor_blueprint.route('/test')
def tmp():
    return 'test2'
