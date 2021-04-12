import flask
from flask import Blueprint, jsonify
from flask.views import View
import flask_login
from flask_login import login_required
from flask_uploads import UploadNotAllowed

from sqlalchemy import func

from werkzeug.datastructures import FileStorage

import base64
import io
from datetime import datetime
import re

from AM_Nihoul_website import settings, db, User, limiter
from AM_Nihoul_website.base_views import FormView, BaseMixin, RenderTemplateView, ObjectManagementMixin, \
    DeleteObjectView
from AM_Nihoul_website.admin.forms import LoginForm, PageEditForm, CategoryEditForm, UploadForm, NewsletterEditForm, \
    NewsletterPublishForm, MenuEditForm
from AM_Nihoul_website.visitor.models import Page, Category, UploadedFile, NewsletterRecipient, Newsletter, Email, \
    MenuEntry, EmailImageAttachment

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


class LoginView(BaseMixin, FormView):
    form_class = LoginForm
    template_name = 'admin/login.html'
    decorators = [limiter.limit(settings.LOGIN_LIMIT)]

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['next'] = flask.request.args.get('next', '')
        return ctx

    def dispatch_request(self, *args, **kwargs):

        if flask_login.current_user.is_authenticated:
            flask.flash('Vous êtes déjà connecté', category='error')
            return flask.redirect(flask.request.args.get('next', flask.url_for('visitor.index')))

        return super().dispatch_request(*args, **kwargs)

    def form_valid(self, form):

        if form.login.data != settings.APP_CONFIG['USERNAME'] or form.password.data != settings.APP_CONFIG['PASSWORD']:
            flask.flash('Utilisateur ou mot de passe incorrect', 'error')
            return self.form_invalid(form)

        flask_login.login_user(User(form.login.data))

        next = form.next.data
        self.success_url = flask.url_for('admin.index') if next == '' else next
        return super().form_valid(form)


admin_blueprint.add_url_rule('/login.html', view_func=LoginView.as_view(name='login'))


@login_required
@admin_blueprint.route('/logout', endpoint='logout')
def logout():
    flask_login.logout_user()
    flask.flash('Vous êtes déconnecté.')
    return flask.redirect(flask.url_for('visitor.index'))


# -- Index
class AdminBaseMixin(BaseMixin):
    decorators = [login_required]


class IndexView(AdminBaseMixin, RenderTemplateView):
    template_name = 'admin/index.html'
    decorators = [login_required]

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['content'] = Page.query.get(settings.APP_CONFIG['PAGES']['admin_index'])

        # few statistics
        sz = UploadedFile.query\
            .with_entities(func.sum(UploadedFile.file_size).label('total'))\
            .first()
        ctx['statistics'] = {
            "Nombre d'inscrits à l'infolettre": NewsletterRecipient.query.count(),
            "Nombre d'infolettres": '{} (dont {} publiées)'.format(
                Newsletter.query.count(), Newsletter.query.filter(Newsletter.draft.is_(False)).count()),
            'Nombre de pages': Page.query.count(),
            'Taille des fichiers': '{:.2f} Mio'.format(
                sz[0] / 1024 / 1024 if sz[0] is not None else 0)
        }

        return ctx


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

        # add choices for categories
        choices = [(-1, '')]
        choices.extend((c.id, c.name) for c in Category.query.order_by(Category.name).all())
        form.category.choices = choices

        # add choices for next
        choices = [(-1, '')]
        q = Page.query.order_by(Page.title)

        if isinstance(self, PageEditView):  # avoid getting the page looping to itself
            q = q.filter(Page.id.isnot(self.object.id))

        choices.extend((c.id, c.title) for c in q.all())
        form.next.choices = choices

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
            'content': self.object.content,
            'category': -1 if self.object.category_id is None else self.object.category_id,
            'next': -1 if self.object.next_id is None else self.object.next_id
        }

    def form_valid(self, form):
        self.object.title = form.title.data
        self.object.content = form.content.data
        self.object.category_id = form.category.data if form.category.data >= 0 else None
        self.object.next_id = form.next.data if form.next.data >= 0 else None

        db.session.add(self.object)
        db.session.commit()

        flask.flash('Page "{}" modifiée.'.format(self.object.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/page-edition-<int:id>-<string:slug>.html', view_func=PageEditView.as_view(name='page-edit'))


class PageCreateView(BasePageEditView):

    def form_valid(self, form):
        page = Page.create(form.title.data, form.content.data)

        if form.category.data >= 0:
            page.category_id = form.category.data

        if form.next.data >= 0:
            page.next_id = form.next.data

        db.session.add(page)
        db.session.commit()

        flask.flash('Page "{}" créée.'.format(page.title))

        self.success_url = flask.url_for('admin.pages')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/page-nouveau.html', view_func=PageCreateView.as_view(name='page-create'))


class PageDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Page

    def pre_deletion(self, obj):
        if obj.protected:
            return False

        return True

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.pages')
        flask.flash('Page "{}" supprimée.'.format(obj.title))


admin_blueprint.add_url_rule('/page-suppression-<int:id>.html', view_func=PageDeleteView.as_view('page-delete'))


class PageToggleVisibility(AdminBaseMixin, ObjectManagementMixin, View):
    methods = ['GET']
    model = Page

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        self.object.visible = not self.object.visible

        db.session.add(self.object)
        db.session.commit()

        return flask.redirect(flask.url_for('admin.pages'))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule(
    '/page-visible-<int:id>.html', view_func=PageToggleVisibility.as_view('page-toggle-visibility'))


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


admin_blueprint.add_url_rule('/catégories.html', view_func=CategoriesView.as_view('categories'))


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


class CategoryMoveView(AdminBaseMixin, ObjectManagementMixin, View):
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

    @staticmethod
    def upload_file(data, description=''):
        filename = data.filename
        f = UploadedFile.query.filter(UploadedFile.base_file_name == filename).all()

        # if this name already exists, adds its size
        if len(f) > 0:
            to_add = '_{}'.format(len(f))
            if filename.find('.') >= 0:
                fsplit = filename.split('.')
                fsplit[-2] += to_add
                filename = '.'.join(fsplit)
            else:
                filename += to_add

        u = UploadedFile.create(data, description=description, filename=filename)
        return u

    def form_valid(self, form):
        try:
            u = FilesView.upload_file(form.file_uploaded.data, form.description.data)
        except UploadNotAllowed:
            flask.flash("Ce type de fichier n'est pas autorisé", category='error')
            return super().form_invalid(form)

        db.session.add(u)
        db.session.commit()

        self.success_url = flask.url_for('admin.files')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/fichiers.html', view_func=FilesView.as_view('files'))


class UploadBase64(AdminBaseMixin, View):
    """Upload an image as base64 encoded string"""

    methods = ['POST']

    def post(self, *args, **kwargs):

        context = flask.request.args.get('context', 'textarea')

        if 'image' not in flask.request.form:
            return jsonify(success=False, reason='missing `image` field'), 400

        content = flask.request.form['image']

        if content[0:5] == 'data:':
            pos = content.find(',')
            info = content[5:pos].split(';')

            if info[1] != 'base64':
                return jsonify(success=False, reason='not base64'), 400
            if 'image/' not in info[0]:
                return jsonify(success=False, reason='mime does not starts with `image/'), 400
            mime = info[0]
            ext = mime[mime.find('/') + 1:]
            content = content[pos + 1:]
        else:
            return jsonify(success=False, reason='no data information'), 400

        im = base64.b64decode(content)
        data = FileStorage(
            stream=io.BytesIO(im),
            content_type=mime,
            name='image',
            filename='{}_{}.{}'.format(context, datetime.now().strftime('%Y_%m_%d-%H-%M-%S'), ext)
        )

        try:
            u = FilesView.upload_file(data, 'Uploadé pour une infolettre')
        except UploadNotAllowed:
            return jsonify(success=False, reason='invalid file'), 400

        db.session.add(u)
        db.session.commit()

        return jsonify(
            success=True, url=flask.url_for('visitor.upload-view', id=u.id, filename=u.file_name, _external=True))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'POST':
            return self.post(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule('/api/image-base64', view_func=UploadBase64.as_view('image-base64'))


class FileDeleteView(AdminBaseMixin, DeleteObjectView):
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
    '/infolettres-inscrits.html', view_func=NewsletterRecipientsView.as_view('newsletter-recipients'))


class NewsletterRecipientDelete(AdminBaseMixin, DeleteObjectView):
    model = NewsletterRecipient

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.newsletter-recipients')
        flask.flash('Destinataire "{}" supprimé.'.format(obj.name))


admin_blueprint.add_url_rule(
    '/infolettre-inscit-suppression-<int:id>.html',
    view_func=NewsletterRecipientDelete.as_view('newsletter-recipient-delete'))


class NewslettersView(AdminBaseMixin, FormView):
    template_name = 'admin/newsletters.html'
    form_class = NewsletterPublishForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx['newsletters'] = Newsletter.query.order_by(Newsletter.id.desc()).all()
        return ctx

    def form_valid(self, form):
        flask.abort(403)


admin_blueprint.add_url_rule(
    '/infolettres.html', view_func=NewslettersView.as_view('newsletters'))


class BaseNewsletterEditView(AdminBaseMixin, FormView):
    form_class = NewsletterEditForm
    template_name = 'admin/newsletter-edit.html'


class NewsletterEditView(ObjectManagementMixin, BaseNewsletterEditView):
    model = Newsletter

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
            'content': self.object.content,
        }

    def form_valid(self, form):
        self.object.title = form.title.data
        self.object.content = form.content.data

        db.session.add(self.object)
        db.session.commit()

        flask.flash('Newsletter "{}" modifiée.'.format(self.object.title))

        if form.submit_button_2.data:
            self.success_url = flask.url_for('admin.newsletter-view', id=self.object.id)
        else:
            self.success_url = flask.url_for('admin.newsletters')

        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/infolettre-edition-<int:id>-<string:slug>.html', view_func=NewsletterEditView.as_view(name='newsletter-edit'))


class NewsletterCreateView(BaseNewsletterEditView):

    def form_valid(self, form):
        newsletter = Newsletter.create(form.title.data, form.content.data)

        db.session.add(newsletter)
        db.session.commit()

        flask.flash('Infolettre "{}" créée.'.format(newsletter.title))

        if form.submit_button_2.data:
            self.success_url = flask.url_for('admin.newsletter-view', id=newsletter.id)
        else:
            self.success_url = flask.url_for('admin.newsletters')

        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/infolettre-nouvelle.html', view_func=NewsletterCreateView.as_view(name='newsletter-create'))


class NewsletterDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Newsletter

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.newsletters')
        flask.flash('Newsletter "{}" supprimée.'.format(obj.title))


admin_blueprint.add_url_rule(
    '/infolettre-suppression-<int:id>.html', view_func=NewsletterDeleteView.as_view('newsletter-delete'))


class NewsletterPublishView(AdminBaseMixin, ObjectManagementMixin, FormView):
    form_class = NewsletterPublishForm
    model = Newsletter

    def get(self, *args, **kwargs):
        flask.abort(403)

    def post(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().post(*args, **kwargs)

    @staticmethod
    def replace_image(g, possible, actual):
        path = g.group('path')
        if path in possible:
            actual.add(possible[path])
            return g.group('begin') + 'src="cid:{}"'.format(possible[path].file_name) + g.group('end')
        else:
            return g.group('begin') + 'src="{}"'.format(g.group('path')) + g.group('end')

    def form_valid(self, form):
        self.success_url = flask.url_for('admin.newsletters')
        if not self.object.draft:
            flask.flash('La newsletter "{}" est déjà publiée'.format(self.object.title))
            return super().form_valid(form)
        else:
            self.object.draft = False
            self.object.date_published = db.func.current_timestamp()

            # get attachments
            possible_attachments = dict(
                (flask.url_for(
                    'visitor.upload-view',
                    id=u.id,
                    filename=u.file_name,
                    _external=True),
                 u) for u in UploadedFile.query.all()
            )

            image_regex = re.compile('(?P<begin><img .*?)src="(?P<path>.*?)"(?P<end>.*?>)')
            content = self.object.content

            actual_attachments = set()
            content = image_regex.sub(
                lambda g: NewsletterPublishView.replace_image(g, possible_attachments, actual_attachments), content)

            self.object.content = content
            db.session.add(self.object)
            db.session.commit()

            # schedule emailing
            recipients = NewsletterRecipient.query.filter(NewsletterRecipient.confirmed.is_(True)).all()
            emails = []
            for r in recipients:
                e = Email.create(
                    'Newsletter: {}'.format(self.object.title),
                    flask.render_template(
                        'newsletter/newsletter.html',
                        **{
                            'site_name': settings.WEBPAGE_INFO['site_name'],
                            'newsletter': self.object,
                            'recipient': r,
                        }
                    ),
                    r.id)
                emails.append(e)
                db.session.add(e)

            db.session.commit()

            # add attachments
            if len(actual_attachments) > 0:
                for e in emails:
                    for a in actual_attachments:
                        db.session.add(EmailImageAttachment.create(e.id, a.id))

                db.session.commit()

            flask.flash('Newsletter "{}" publiée.'.format(self.object.title))

        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/infolettre-publie-<int:id>.html', view_func=NewsletterPublishView.as_view('newsletter-publish'))


class NewsletterView(AdminBaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'admin/newsletter.html'
    model = Newsletter

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['newsletter'] = self.object
        return ctx


admin_blueprint.add_url_rule(
    '/infolettre-voir-<int:id>.html', view_func=NewsletterView.as_view(name='newsletter-view'))


# --- Menu
class MenuEditView(AdminBaseMixin, FormView, RenderTemplateView):
    template_name = 'admin/menus.html'
    form_class = MenuEditForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        return ctx

    def form_valid(self, form):
        if form.is_create.data:
            c = MenuEntry.create(form.text.data, form.url.data)
            flask.flash('Entrée "{}" créé.'.format(c.text))
        else:
            c = MenuEntry.query.get(form.id_menu.data)
            if c is None:
                flask.abort(403)

            c.text = form.text.data
            c.url = form.url.data
            flask.flash('Entrée "{}" modifié.'.format(c.text))

        db.session.add(c)
        db.session.commit()

        self.success_url = flask.url_for('admin.menus')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/menus.html', view_func=MenuEditView.as_view(name='menus'))


class MenuDeleteView(AdminBaseMixin, DeleteObjectView):
    model = MenuEntry

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.menus')
        flask.flash('Entrée "{}" supprimée.'.format(obj.text))


admin_blueprint.add_url_rule(
    '/menu-suppression-<int:id>.html', view_func=MenuDeleteView.as_view('menu-delete'))


class MenuMoveView(AdminBaseMixin, ObjectManagementMixin, View):
    methods = ['GET']
    model = MenuEntry

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        action = kwargs.get('action')

        if action == 'up':
            self.object.up()
        elif action == 'down':
            self.object.down()
        else:
            flask.abort(403)

        return flask.redirect(flask.url_for('admin.menus'))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule(
    '/menu-mouvement-<string:action>-<int:id>.html', view_func=MenuMoveView.as_view('menu-move'))
