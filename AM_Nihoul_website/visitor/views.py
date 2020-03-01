from flask import Blueprint

from AM_Nihoul_website import settings
from AM_Nihoul_website.base_views import RenderTemplateView

visitor_blueprint = Blueprint('visitor', __name__)


class BaseTemplateView(RenderTemplateView):
    def get_context_data(self, *args, **kwargs):
        """Add webpage infos"""
        data = super().get_context_data(*args, **kwargs)

        data.update(**settings.WEBPAGE_INFO)
        return data


class IndexView(BaseTemplateView):
    template_name = 'index.html'


visitor_blueprint.add_url_rule('/', view_func=IndexView.as_view(name='index'))
