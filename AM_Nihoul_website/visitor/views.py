from flask import Blueprint

visitor_blueprint = Blueprint('visitor', __name__)


@visitor_blueprint.route('/test')
def tmp():
    return 'test2'
