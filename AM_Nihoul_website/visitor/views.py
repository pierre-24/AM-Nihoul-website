import flask
from flask import Blueprint, views

from AM_Nihoul_website import db, settings
from AM_Nihoul_website.base_views import RenderTemplateView, BaseMixin, ObjectManagementMixin, FormView
from AM_Nihoul_website.visitor.models import Page, UploadedFile, NewsletterRecipient
from AM_Nihoul_website.visitor.forms import NewsletterForm

visitor_blueprint = Blueprint('visitor', __name__)


# -- Index
class IndexView(BaseMixin, RenderTemplateView):
    template_name = 'index.html'


visitor_blueprint.add_url_rule('/', view_func=IndexView.as_view(name='index'))


# -- Pages
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


# -- Uploads
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


# -- Newsletter
class NewsletterRegisterView(BaseMixin, FormView):
    form_class = NewsletterForm
    template_name = 'newsletter.html'

    DEBUG = True

    def form_valid(self, form):

        if NewsletterRecipient.query.filter(NewsletterRecipient.email == form.email.data).count() == 0:
            r = NewsletterRecipient.create(form.name.data, form.email.data)

            db.session.add(r)
            db.session.commit()

            t = flask.render_template(
                'newsletter/newsletter-in.html',
                **{
                    'name': form.name.data,
                    'site_name': settings.WEBPAGE_INFO['site_name'],
                    'rid': r.id,
                    'rhash': r.hash
                }
            )

            print(t)

        flask.flash('Vous êtes bien inscrit à la newsletter')
        self.success_url = flask.url_for('visitor.index')

        return super().form_valid(form)


visitor_blueprint.add_url_rule('/newsletter.html', view_func=NewsletterRegisterView.as_view(name='newsletter-subscribe'))


class NewsletterUnregisterView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'newsletter-out.html'
    model = NewsletterRecipient

    def _fetch_object(self, *args, **kwargs):
        super()._fetch_object(*args, **kwargs)

        if self.object.hash != kwargs.get('hash'):
            flask.abort(404)

    def get_context_data(self, *args, **kwargs):
        # fetch and delete
        self._fetch_object(*args, **kwargs)

        db.session.delete(self.object)
        db.session.commit()

        # and go
        return super().get_context_data(*args, **kwargs)


visitor_blueprint.add_url_rule(
    '/newsletter-out-<int:id>-<string:hash>.html',
    view_func=NewsletterUnregisterView.as_view(name='newsletter-unsubscribe'))
