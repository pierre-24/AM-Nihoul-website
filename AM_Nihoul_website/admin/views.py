import flask
from flask import Blueprint

from AM_Nihoul_website import settings, db
from AM_Nihoul_website.base_views import FormView, BaseMixin, LoginMixin, RenderTemplateView, ObjectManagementMixin, \
    DeleteView
from AM_Nihoul_website.admin.forms import LoginForm, PageEditForm
from AM_Nihoul_website.visitor.models import Page

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


class LoginView(BaseMixin, FormView):
    form_class = LoginForm
    template_name = 'admin/login.html'

    def dispatch_request(self, *args, **kwargs):

        if LoginMixin.logged_in():
            flask.flash('Vous êtes déjà connecté', category='error')
            return flask.redirect(flask.url_for('visitor.index'))

        return super().dispatch_request(*args, **kwargs)

    def form_valid(self, form):

        if form.login.data != settings.APP_CONFIG['USERNAME'] or form.password.data != settings.APP_CONFIG['PASSWORD']:
            flask.flash('Utilisateur ou mot de passe incorrect', 'error')
            return self.form_invalid(form)

        flask.session['logged_in'] = True

        self.success_url = flask.url_for('admin.index')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/login.html', view_func=LoginView.as_view(name='login'))


@LoginMixin.login_required
@admin_blueprint.route('/logout', endpoint='logout')
def logout():
    flask.session['logged_in'] = False
    flask.flash('Vous êtes déconnecté.')
    return flask.redirect(flask.url_for('visitor.index'))


class IndexView(BaseMixin, RenderTemplateView):
    template_name = 'admin/index.html'
    decorators = [LoginView.login_required]


admin_blueprint.add_url_rule('/index.html', view_func=IndexView.as_view(name='index'))


# -- Pages
class PagesView(BaseMixin, RenderTemplateView):
    template_name = 'admin/pages.html'
    decorators = [LoginView.login_required]

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch list of pages
        ctx['pages'] = Page.query.order_by(Page.slug).all()

        return ctx


admin_blueprint.add_url_rule('/pages.html', view_func=PagesView.as_view(name='pages'))


class PageEditView(BaseMixin, ObjectManagementMixin, FormView):
    template_name = 'admin/page-modify.html'
    form_class = PageEditForm
    decorators = [LoginView.login_required]

    model = Page

    def _fetch_object(self, *args, **kwargs):
        """Add slug check"""

        super()._fetch_object(*args, **kwargs)

        if self.object.slug != kwargs.get('slug', None):
            flask.abort(404)

    def get(self, *args, **kwargs):
        self._fetch_object(*args, **kwargs)
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._fetch_object(*args, **kwargs)
        return super().post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):

        self.form_kwargs = {
            'title': self.object.title,
            'text': self.object.content
        }

        return super().get_context_data(*args, **kwargs)

    def form_valid(self, form):
        self.object.title = form.title.data
        self.object.content = form.text.data

        db.session.add(self.object)
        db.session.commit()

        flask.flash('Page "{}" modifiée.'.format(self.object.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/page-edition-<int:id>-<string:slug>.html', view_func=PageEditView.as_view(name='page-edit'))


class PageCreateView(BaseMixin, FormView):
    template_name = 'admin/page-modify.html'
    form_class = PageEditForm
    decorators = [LoginView.login_required]

    def form_valid(self, form):
        page = Page.create(form.title.data, form.text.data)

        db.session.add(page)
        db.session.commit()

        flask.flash('Page "{}" créée.'.format(page.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/page-nouveau.html', view_func=PageCreateView.as_view(name='page-create'))


class PageDeleteView(BaseMixin, ObjectManagementMixin, DeleteView):
    model = Page
    decorators = [LoginView.login_required]

    def delete(self, *args, **kwargs):
        self._fetch_object(*args, **kwargs)
        self.success_url = flask.url_for('admin.pages')
        return super().delete(*args, **kwargs)

    def get_object(self):
        return self.object

    def post_deletion(self, obj):
        flask.flash('Page "{}" supprimée.'.format(obj.title))


admin_blueprint.add_url_rule('/page-suppression-<int:id>.html', view_func=PageDeleteView.as_view('page-delete'))
