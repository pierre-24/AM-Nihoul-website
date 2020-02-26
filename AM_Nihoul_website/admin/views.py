from flask import Blueprint

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blueprint.route('/test')
def tmp():
    return 'test3'
