import flask
from flask import Blueprint, views

from AM_Nihoul_website.base_views import RenderTemplateView, BaseMixin, ObjectManagementMixin
from AM_Nihoul_website.visitor.models import Page, UploadedFile

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


class UploadView(views.View):
    methods = ['GET']

    def get(self, *args, **kwargs):
        f = UploadedFile.query\
            .filter(UploadedFile.file_name == kwargs.get('filename'))\
            .filter(UploadedFile.id == kwargs.get('id'))\
            .all()

        if len(f) < 1:
            flask.abort(404)

        f = f[0]

        with open(f.path(), 'rb') as fx:
            response = flask.make_response(fx.read())

        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(f.file_name)
        response.headers['Cache-Control'] = 'must-revalidate'
        response.headers['Pragma'] = 'must-revalidate'
        response.headers['Content-type'] = f.possible_mime

        return response

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


visitor_blueprint.add_url_rule('/fichier/<int:id>/<string:filename>', view_func=UploadView.as_view(name='upload-view'))
