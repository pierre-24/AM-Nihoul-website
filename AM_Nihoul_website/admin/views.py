import bs4
import flask
from flask import Blueprint, jsonify
from flask.views import View
import flask_login
from flask_login import login_required
from flask_uploads import UploadNotAllowed
from PIL import Image
from bs4 import BeautifulSoup

from sqlalchemy import func

from werkzeug.datastructures import FileStorage

import base64
import io
from datetime import datetime
import re

from AM_Nihoul_website import settings, db, User, limiter, pictures_set
from AM_Nihoul_website.admin.utils import Thumbnailer
from AM_Nihoul_website.base_views import FormView, BaseMixin, RenderTemplateView, ObjectManagementMixin, \
    DeleteObjectView
from AM_Nihoul_website.admin.forms import LoginForm, PageEditForm, CategoryEditForm, UploadForm, NewsletterEditForm, \
    NewsletterPublishForm, MenuEditForm, BlockEditForm, AlbumEditForm, PictureUploadForm
from AM_Nihoul_website.visitor.models import Page, Category, UploadedFile, NewsletterRecipient, Newsletter, Email, \
    MenuEntry, EmailImageAttachment, Block, Album, Picture

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
        ctx['content'] = db.session.get(Page, settings.APP_CONFIG['PAGES']['admin_index'])

        # few statistics
        sz_uploads = UploadedFile.query\
            .with_entities(func.sum(UploadedFile.file_size).label('total'))\
            .first()
        sz_pictures = Picture.query\
            .with_entities(func.sum(Picture.picture_size).label('total'))\
            .first()
        ctx['statistics'] = {
            "Nombre d'inscrits à l'infolettre": NewsletterRecipient.query.count(),
            "Nombre d'infolettres": '{} (dont {} publiées)'.format(
                Newsletter.query.count(), Newsletter.query.filter(Newsletter.draft.is_(False)).count()),
            'Nombre de pages': Page.query.count(),
            'Taille des fichiers': '{:.2f} Mio'.format(
                sz_uploads[0] / 1024 / 1024 if sz_uploads[0] is not None else 0),
            'Taille des photos': '{:.2f} Mio'.format(
                sz_pictures[0] / 1024 / 1024 if sz_pictures[0] is not None else 0)
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
        ctx['categories'] = Category.ordered_items()
        return ctx

    def form_valid(self, form):
        if form.is_create.data:
            c = Category.create(form.name.data)
            flask.flash('Catégorie "{}" créée.'.format(c.name))
        else:
            c = db.session.get(Category, form.id_category.data)
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


class BaseMoveView(AdminBaseMixin, ObjectManagementMixin, View):
    redirect_url = ''
    methods = ['GET']

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        action = kwargs.get('action')

        if action == 'up':
            self.object.up()
        elif action == 'down':
            self.object.down()
        else:
            flask.abort(403)

        return flask.redirect(flask.url_for(self.redirect_url))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


class CategoryMoveView(BaseMoveView):
    model = Category
    redirect_url = 'admin.categories'


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
        source_fp = io.BytesIO(im)

        # if image is larger than a given size, use jpg instead
        if len(im) > settings.APP_CONFIG['UPLOAD_CONVERT_TO_JPG']:
            image = Image.open(io.BytesIO(im))
            source_fp = io.BytesIO()
            image = image.convert('RGB')  # strip transparency
            image.save(source_fp, format='jpeg')
            ext = 'jpg'
            source_fp.seek(0)  # rewind

        data = FileStorage(
            stream=source_fp,
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

        ctx['recipients'] = NewsletterRecipient.query.order_by(NewsletterRecipient.date_created.desc()).all()
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


class NewsletterCleanupView(AdminBaseMixin, ObjectManagementMixin, View):
    model = Newsletter

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        soup = BeautifulSoup(self.object.content, 'html.parser')

        def clean_style(tag):
            # clean up style
            if type(tag) in [bs4.Tag, bs4.BeautifulSoup]:
                for c in tag.children:
                    clean_style(c)

                if 'style' in tag.attrs:
                    previous_styles = tag['style'].split(';')
                    final_styles = []

                    for style_def in previous_styles:
                        if style_def.strip() != '':
                            name, val = style_def.split(':')
                            name = name.strip()
                            if name == 'text-align' or (name == 'font-size' and '%' in val):
                                final_styles.append('{}: {}'.format(name, val.strip()))

                    if len(final_styles) > 0:
                        tag['style'] = ';'.join(final_styles)
                    else:
                        del tag.attrs['style']

                if 'align' in tag.attrs:
                    del tag.attrs['align']

        def clean_unwanted(tag):
            # clean up unwanted
            if type(tag) in [bs4.Tag, bs4.BeautifulSoup]:
                for c in tag.children:
                    clean_unwanted(c)
                if tag.name == 'font':
                    tag.unwrap()
                elif tag.name == 'span' and len(tag.attrs) == 0:
                    tag.unwrap()

        def clean_empty(tag):
            # clean empty
            if type(tag) in [bs4.Tag, bs4.BeautifulSoup]:
                for c in tag.children:
                    clean_empty(c)
                if tag.name in ['p', 'blockquote', 'h3', 'h4', 'strong', 'em', 'u', 'a']:
                    if len(tag.contents) == 0 or (len(tag.contents) == 1 and tag.contents[0].name == 'br'):
                        tag.unwrap()

        # do it:
        clean_style(soup)
        clean_unwanted(soup)
        clean_empty(soup)

        self.object.content = str(soup)
        db.session.add(self.object)
        db.session.commit()

        flask.flash('Le code a été nettoyé!')
        return flask.redirect(flask.url_for('admin.newsletters'))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule(
    '/infolettre-nettoyage-<int:id>.html', view_func=NewsletterCleanupView.as_view('newsletter-cleanup'))


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
            content = self.object.content_with_summary(
                link_page=flask.url_for(
                    'visitor.newsletter-view', id=self.object.id, slug=self.object.slug, _external=True))

            actual_attachments = set()
            content = image_regex.sub(
                lambda g: NewsletterPublishView.replace_image(g, possible_attachments, actual_attachments), content)

            db.session.add(self.object)
            db.session.commit()

            # schedule emailing
            recipients = NewsletterRecipient.query.filter(NewsletterRecipient.confirmed.is_(True)).all()
            emails = []
            for r in recipients:
                e = Email.create(
                    'Infolettre: {}'.format(self.object.title),
                    flask.render_template(
                        'newsletter/newsletter.html',
                        **{
                            'site_name': settings.WEBPAGE_INFO['site_name'],
                            'newsletter': self.object,
                            'transformed_content': content,
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

            flask.flash('Infolettre "{}" publiée.'.format(self.object.title))

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

    def form_valid(self, form):
        if form.is_create.data:
            c = MenuEntry.create(form.text.data, form.url.data)
            flask.flash('Entrée "{}" créé.'.format(c.text))
        else:
            c = db.session.get(MenuEntry, form.id_menu.data)
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


class MenuMoveView(BaseMoveView):
    model = MenuEntry
    redirect_url = 'admin.menus'


admin_blueprint.add_url_rule(
    '/menu-mouvement-<string:action>-<int:id>.html', view_func=MenuMoveView.as_view('menu-move'))


# -- Blocks
class BlocksView(AdminBaseMixin, RenderTemplateView):
    template_name = 'admin/blocks.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch blocks
        ctx['blocks'] = Block.ordered_items()

        return ctx


admin_blueprint.add_url_rule('/blocs.html', view_func=BlocksView.as_view(name='blocks'))


class BlockEditView(ObjectManagementMixin, AdminBaseMixin, FormView):
    template_name = 'admin/block-edit.html'
    form_class = BlockEditForm
    model = Block

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().post(*args, **kwargs)

    def get_form_kwargs(self):
        return {
            'content': self.object.text,
            'attributes': self.object.attributes
        }

    def form_valid(self, form):
        self.object.text = form.content.data
        self.object.attributes = form.attributes.data

        db.session.add(self.object)
        db.session.commit()

        flask.flash('Bloc modifié.')

        self.success_url = flask.url_for('admin.blocks')
        return super().form_valid(form)


admin_blueprint.add_url_rule(
    '/bloc-edition-<int:id>.html', view_func=BlockEditView.as_view(name='block-edit'))


class BlockCreateView(AdminBaseMixin, FormView):
    template_name = 'admin/block-edit.html'
    form_class = BlockEditForm

    def form_valid(self, form):
        block = Block.create(form.content.data, form.attributes.data)

        db.session.add(block)
        db.session.commit()

        flask.flash('Bloc créé.')

        self.success_url = flask.url_for('admin.blocks')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/bloc-nouveau.html', view_func=BlockCreateView.as_view(name='block-create'))


class BlockDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Block

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.blocks')
        flask.flash('Bloc supprimé.')


admin_blueprint.add_url_rule('/bloc-suppression-<int:id>.html', view_func=BlockDeleteView.as_view('block-delete'))


class BlockMoveView(BaseMoveView):
    model = Block
    redirect_url = 'admin.blocks'


admin_blueprint.add_url_rule(
    '/bloc-mouvement-<string:action>-<int:id>.html', view_func=BlockMoveView.as_view('block-move'))


# -- Albums
class AlbumsView(AdminBaseMixin, FormView):
    template_name = 'admin/albums.html'
    form_class = AlbumEditForm

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch albums
        ctx['albums'] = Album.ordered_items(desc=True)

        return ctx

    def form_valid(self, form):
        if form.is_create.data:
            a = Album.create(form.title.data, form.description.data)
            flask.flash('Album "{}" créé.'.format(a.title))
        else:
            a = db.session.get(Album, form.id_album.data)
            if a is None:
                flask.abort(403)

            a.title = form.title.data
            a.description = form.description.data
            flask.flash('Album "{}" modifié.'.format(a.title))

        db.session.add(a)
        db.session.commit()

        self.success_url = flask.url_for('admin.albums')
        return super().form_valid(form)


admin_blueprint.add_url_rule('/albums.html', view_func=AlbumsView.as_view(name='albums'))


class AlbumDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Album

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.albums')
        flask.flash('Album "{}" supprimé.'.format(obj.title))


admin_blueprint.add_url_rule('/album-suppression-<int:id>.html', view_func=AlbumDeleteView.as_view('album-delete'))


class AlbumMoveView(BaseMoveView):
    model = Album
    redirect_url = 'admin.albums'


admin_blueprint.add_url_rule(
    '/album-mouvement-<string:action>-<int:id>.html', view_func=AlbumMoveView.as_view('album-move'))


class AlbumView(AdminBaseMixin, ObjectManagementMixin, FormView):
    model = Album
    template_name = 'admin/album.html'
    form_class = PictureUploadForm

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().post(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx['album'] = self.object
        ctx['pictures'] = sorted(self.object.pictures, key=lambda k: k.date_taken)
        ctx['total_size'] = sum(f.picture_size for f in ctx['pictures'])

        return ctx

    def upload_picture(self, data):
        # take care of filename
        filename = data.filename

        if '.' in filename:
            fsplit = filename.split('.')
            basename = '.'.join(fsplit[:-1])
            ext = fsplit[-1]
        else:
            basename = filename
            ext = ''

        f = Picture.query.filter(Picture.picture_name == filename).all()

        if len(f) > 0:  # if this name already exists, adds its size
            basename = '{}_{}'.format(basename, len(f))

        filename = '{}.{}'.format(basename, ext)
        filename_thumb = '{}_thumb.{}'.format(basename, ext)

        # save image:
        r_filename = pictures_set.save(data, name=filename)

        # create thumbnail:
        image = Thumbnailer(*settings.APP_CONFIG['PICTURE_THUMB_SIZE'])\
            .transform(Image.open(pictures_set.path(r_filename)))

        thumb_fp = io.BytesIO()
        image.save(thumb_fp, format='jpeg', quality=85, optimize=True)
        thumb_fp.seek(0)  # rewind

        data_thumb = FileStorage(
            stream=thumb_fp,
            content_type='image/jpeg',
            name='thumbnail',
            filename=filename_thumb
        )

        r_filename_thumb = pictures_set.save(data_thumb, name=filename_thumb)

        # create object
        try:
            date_taken = datetime.strptime(image.getexif()[306], '%Y:%m:%d %H:%M:%S')
        except KeyError:
            date_taken = datetime.now()

        picture = Picture.create(
            filename=r_filename,
            filename_thumb=r_filename_thumb,
            album=self.object,
            date_taken=date_taken
        )

        return picture

    def form_valid(self, form):
        try:
            picture = self.upload_picture(form.file_uploaded.data)
        except UploadNotAllowed:
            flask.flash("Ce type de fichier n'est pas autorisé", category='error')
            return super().form_invalid(form)

        db.session.add(picture)
        db.session.commit()

        self.success_url = flask.url_for('admin.album', id=self.object.id)
        return super().form_valid(form)


admin_blueprint.add_url_rule('/album-<int:id>.html', view_func=AlbumView.as_view(name='album'))


class AlbumSetThumbnailView(AdminBaseMixin, ObjectManagementMixin, View):
    methods = ['GET']
    model = Album

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        picture_id = kwargs.get('picture')
        picture = db.session.get(Picture, picture_id)
        if picture is None:
            flask.abort(404)

        self.object.thumbnail = picture
        db.session.add(self.object)
        db.session.commit()

        flask.flash("Cette photo sera utilisée comme miniature de l'album.")

        return flask.redirect(flask.url_for('admin.album', id=self.object.id))

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


admin_blueprint.add_url_rule(
    '/album-<int:id>-miniature-<int:picture>.html', view_func=AlbumSetThumbnailView.as_view(name='album-set-thumbnail'))


class PictureDeleteView(AdminBaseMixin, DeleteObjectView):
    model = Picture

    def post_deletion(self, obj):
        self.success_url = flask.url_for('admin.album', id=obj.album_id)
        flask.flash('Photo supprimée.')


admin_blueprint.add_url_rule('/photo-suppression-<int:id>.html', view_func=PictureDeleteView.as_view('picture-delete'))
