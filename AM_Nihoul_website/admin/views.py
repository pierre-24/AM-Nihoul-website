import flask
from flask import Blueprint
from flask.views import View

from AM_Nihoul_website import settings, db
from AM_Nihoul_website.base_views import FormView, BaseMixin, LoginMixin, RenderTemplateView, ObjectManagementMixin, \
    DeleteObjectView
from AM_Nihoul_website.admin.forms import LoginForm, PageEditForm, CategoryEditForm, UploadForm
from AM_Nihoul_website.visitor.models import Page, Category, UploadedFile, NewsletterRecipient

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


class LoginView(BaseMixin, FormView):
    form_class = LoginForm
    template_name = 'admin/login.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['next'] = flask.request.args.get('next', '')
        return ctx

    def dispatch_request(self, *args, **kwargs):

        if LoginMixin.logged_in():
            flask.flash('Vous êtes déjà connecté', category='error')
            return flask.redirect(flask.request.args.get('next', flask.url_for('visitor.index')))

        return super().dispatch_request(*args, **kwargs)

    def form_valid(self, form):

        if form.login.data != settings.APP_CONFIG['USERNAME'] or form.password.data != settings.APP_CONFIG['PASSWORD']:
            flask.flash('Utilisateur ou mot de passe incorrect', 'error')
            return self.form_invalid(form)

        flask.session['logged_in'] = True

        next = form.next.data
        self.success_url = flask.url_for('admin.index') if next == '' else next
        return super().form_valid(form)


admin_blueprint.add_url_rule('/login.html', view_func=LoginView.as_view(name='login'))


@LoginMixin.login_required
@admin_blueprint.route('/logout', endpoint='logout')
def logout():
    flask.session['logged_in'] = False
    flask.flash('Vous êtes déconnecté.')
    return flask.redirect(flask.url_for('visitor.index'))


# -- Index
class AdminBaseMixin(BaseMixin):
    decorators = [LoginView.login_required]
    

class IndexView(AdminBaseMixin, RenderTemplateView):
    template_name = 'admin/index.html'
    decorators = [LoginView.login_required]


admin_blueprint.add_url_rule('/index.html', view_func=IndexView.as_view(name='index'))


# -- Pages
class PagesView(AdminBaseMixin, RenderTemplateView):
    template_name = 'admin/pages.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch list of pages
        ctx['pages'] = Page.query.order_by(Page.slug).all()
        ctx['categories'] = dict((c.id, c) for c in Category.query.all())

        return ctx


admin_blueprint.add_url_rule('/pages.html', view_func=PagesView.as_view(name='pages'))


class BasePageEditView(AdminBaseMixin, FormView):
    form_class = PageEditForm
    template_name = 'admin/page-edit.html'

    def get_form(self):
        form = super().get_form()

        # add choices
        choices = [(-1, '')]
        choices.extend((c.id, c.name) for c in Category.query.order_by(Category.name).all())
        form.category.choices = choices

        return form


class PageEditView(ObjectManagementMixin, BasePageEditView):
    model = Page

    def get_object_or_abort(self, *args, **kwargs):
        """Add slug check"""

        super().get_object_or_abort(*args, **kwargs)

        if self.object.slug != kwargs.get('slug', None):
            flask.abort(404)

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().post(*args, **kwargs)

    def get_form_kwargs(self):
        return {
            'title': self.object.title,
            'text': self.object.content,
            'category': -1 if self.object.category_id is None else self.object.category_id
        }

    def form_valid(self, form):
        self.object.title = form.title.data
        self.object.content = form.text.data
        self.object.category_id = form.category.data if form.category.data >= 0 else None

        db.session.add(self.object)
        db.session.commit()

        flask.flash('Page "{}" modifiée.'.format(self.object.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/page-edition-<int:id>-<string:slug>.html', view_func=PageEditView.as_view(name='page-edit'))


class PageCreateView(BasePageEditView):

    def form_valid(self, form):
        page = Page.create(form.title.data, form.text.data)

        if form.category.data >= 0:
            page.category_id = form.category.data

        db.session.add(page)
        db.session.commit()

        flask.flash('Page "{}" créée.'.format(page.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/page-nouveau.html', view_func=PageCreateView.as_view(name='page-create'))


class PageDeleteView(DeleteObjectView):
    model = Page

    def pre_deletion(self, obj):
        if obj.protected:
            return False

        return False

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.pages')
        flask.flash('Page "{}" supprimée.'.format(obj.title))


admin_blueprint.add_url_rule('/page-suppression-<int:id>.html', view_func=PageDeleteView.as_view('page-delete'))


# -- Categories
class CategoriesView(AdminBaseMixin, FormView):
    template_name = 'admin/categories.html'

    form_class = CategoryEditForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch list of category
        ctx['categories'] = Category.query.order_by(Category.order).all()
        return ctx

    def form_valid(self, form):
        if form.is_create.data:
            c = Category.create(form.name.data)
            flask.flash('Catégorie "{}" créée.'.format(c.name))
        else:
            c = Category.query.get(form.id_category.data)
            if c is None:
                flask.abort(403)

            c.name = form.name.data
            flask.flash('Catégorie "{}" modifiée.'.format(c.name))

        db.session.add(c)
        db.session.commit()

        self.success_url = flask.url_for('admin.categories')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/categories.html', view_func=CategoriesView.as_view('categories'))


class CategoryDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Category

    def pre_deletion(self, obj):
        """Set the page category to NULL"""

        pages = Page.query.filter(Page.category_id == obj.id).all()
        for p in pages:
            p.category_id = None
            db.session.add(p)

        return True  # keep going !

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.categories')
        flask.flash('Catégorie "{}" supprimée.'.format(obj.name))


admin_blueprint.add_url_rule(
    '/catégorie-suppression-<int:id>.html', view_func=CategoryDeleteView.as_view('category-delete'))


class CategoryMoveView(ObjectManagementMixin, View):
    methods = ['GET']
    model = Category

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        action = kwargs.get('action')

        if action == 'up':
            self.object.up()
        elif action == 'down':
            self.object.down()
        else:
            flask.abort(403)

        return flask.redirect(flask.url_for('admin.categories'))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule(
    '/catégorie-mouvement-<string:action>-<int:id>.html', view_func=CategoryMoveView.as_view('category-move'))


# -- Files
class FilesView(AdminBaseMixin, FormView):
    template_name = 'admin/files.html'

    form_class = UploadForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch list of pages
        files = UploadedFile.query.order_by(UploadedFile.file_name).all()

        ctx['files'] = files
        ctx['total_size'] = sum(f.file_size for f in files)

        return ctx

    def form_valid(self, form):
        filename = form.file_uploaded.data.filename

        f = UploadedFile.query.filter(UploadedFile.base_file_name == filename).all()
        if len(f) > 0:
            to_add = '_{}'.format(len(f))
            if filename.find('.') >= 0:
                fsplit = filename.split('.')
                fsplit[-2] += to_add
                filename = '.'.join(fsplit)
            else:
                filename += to_add

        u = UploadedFile.create(form.file_uploaded.data, description=form.description.data, filename=filename)
        db.session.add(u)
        db.session.commit()

        self.success_url = flask.url_for('admin.files')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/fichiers.html', view_func=FilesView.as_view('files'))


class FileDeleteView(DeleteObjectView):
    model = UploadedFile

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.files')
        flask.flash('Fichier "{}" supprimé.'.format(obj.file_name))


admin_blueprint.add_url_rule(
    '/fichier-suppression-<int:id>.html', view_func=FileDeleteView.as_view('file-delete'))


# -- Newsletter
class NewsletterRecipientsView(AdminBaseMixin, RenderTemplateView):
    template_name = 'admin/newsletter-recipients.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx['recipients'] = NewsletterRecipient.query.order_by(NewsletterRecipient.name).all()
        return ctx


admin_blueprint.add_url_rule(
    '/newsletter-inscrits.html', view_func=NewsletterRecipientsView.as_view('newsletter-recipients'))


class NewsletterRecipientDelete(DeleteObjectView):
    model = NewsletterRecipient

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.newsletter-recipients')
        flask.flash('Destinataire "{}" supprimé.'.format(obj.name))


admin_blueprint.add_url_rule(
    '/newsletter-inscit-suppression-<int:id>.html',
    view_func=NewsletterRecipientDelete.as_view('newsletter-recipient-delete'))
