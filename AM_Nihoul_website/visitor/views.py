from flask import Blueprint

from AM_Nihoul_website.base_views import RenderTemplateView, BaseMixin

visitor_blueprint = Blueprint('visitor', __name__)


class IndexView(BaseMixin, RenderTemplateView):
    template_name = 'index.html'


visitor_blueprint.add_url_rule('/', view_func=IndexView.as_view(name='index'))
