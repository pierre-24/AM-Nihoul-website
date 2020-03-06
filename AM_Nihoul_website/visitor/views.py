import flask
from flask import Blueprint

from AM_Nihoul_website.base_views import RenderTemplateView, BaseMixin, ObjectManagementMixin
from AM_Nihoul_website.visitor.models import Page

visitor_blueprint = Blueprint('visitor', __name__)


class IndexView(BaseMixin, RenderTemplateView):
    template_name = 'index.html'


visitor_blueprint.add_url_rule('/', view_func=IndexView.as_view(name='index'))


class PageView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'page.html'
    model = Page

    def _fetch_object(self, *args, **kwargs):
        super()._fetch_object(*args, **kwargs)

        if self.object.slug != kwargs.get('slug'):
            flask.abort(404)

    def get_context_data(self, *args, **kwargs):
        self._fetch_object(*args, **kwargs)

        ctx = super().get_context_data(*args, **kwargs)
        ctx['page'] = self.object
        return ctx


visitor_blueprint.add_url_rule('/page/<int:id>-<string:slug>.html', view_func=PageView.as_view(name='page-view'))
