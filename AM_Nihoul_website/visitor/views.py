import pathlib
import datetime

import flask
from flask import Blueprint, views, request, send_from_directory, current_app
from flask_login import current_user

import requests

import AM_Nihoul_website
from AM_Nihoul_website import db, limiter
from AM_Nihoul_website.base_views import RenderTemplateView, BaseMixin, ObjectManagementMixin, FormView
from AM_Nihoul_website.visitor.models import Page, UploadedFile, NewsletterRecipient, Newsletter, Email, Album, \
    Brief, Featured
from AM_Nihoul_website.visitor.forms import NewsletterForm

visitor_blueprint = Blueprint('visitor', __name__)


# -- Index
class IndexInfo:
    """Just a placeholder for brief/newsletter
    """

    def __init__(self, title: str, date: datetime.datetime, summary: str, link: str, type: str):
        self.title = title
        self.date = date
        self.summary = summary
        self.link = link
        self.type = type


class IndexView(BaseMixin, RenderTemplateView):
    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx['content'] = db.session.get(Page, current_app.config['PAGES']['visitor_index'])

        # fetch latest infos
        latest_info = []

        latest_briefs = Brief.query\
            .filter(Brief.visible.is_(True))\
            .order_by(Brief.id.desc())\
            .all()[:3]

        for brief in latest_briefs:
            latest_info.append(IndexInfo(
                title=brief.title,
                date=brief.date_created,
                summary=brief.summary,
                link=flask.url_for('visitor.brief-view', id=brief.id, slug=brief.slug),
                type='Brève'
            ))

        latest_newsletters = Newsletter.query\
            .filter(Newsletter.draft.is_(False))\
            .order_by(Newsletter.date_published.desc())\
            .all()[:3]

        for newsletter in latest_newsletters:
            latest_info.append(IndexInfo(
                title=newsletter.title,
                date=newsletter.date_published,
                summary=newsletter.summary,
                link=flask.url_for('visitor.newsletter-view', id=newsletter.id, slug=newsletter.slug),
                type='Infolettre'
            ))

        latest_info.sort(key=lambda x: x.date, reverse=True)

        ctx['latest_info'] = latest_info[:3]

        ctx['featureds'] = Featured.ordered_items()[:4]

        return ctx


visitor_blueprint.add_url_rule('/', view_func=IndexView.as_view(name='index'))


# -- Sitemap
class SitemapView(RenderTemplateView):
    template_name = 'sitemap.xml'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        urls = [
            {'location': flask.url_for('visitor.index', _external=True), 'changefreq': 'weekly', 'priority': 1},
            {
                'location': flask.url_for('visitor.newsletters', _external=True),
                'changefreq': 'monthly',
                'priority': 0.8
            },
            {'location': flask.url_for('visitor.briefs', _external=True), 'changefreq': 'weekly', 'priority': 0.8},
            {'location': flask.url_for('visitor.albums', _external=True), 'changefreq': 'weekly', 'priority': 0.8},
        ]

        # add pages
        for p in Page.query.filter(Page.visible.is_(True)).all():
            urls.append({
                'location': flask.url_for('visitor.page-view', id=p.id, slug=p.slug, _external=True),
                'changefreq': 'weekly',
                'modified': p.date_modified,
                'priority': 0.8
            })

        # add newsletters
        for n in Newsletter.query.filter(Newsletter.draft.is_(False)).all():
            urls.append({
                'location': flask.url_for('visitor.newsletter-view', id=n.id, slug=n.slug, _external=True),
                'changefreq': 'yearly',
                'modified': n.date_modified
            })

        # add briefs
        for n in Brief.query.filter(Brief.visible.is_(True)).all():
            urls.append({
                'location': flask.url_for('visitor.brief-view', id=n.id, slug=n.slug, _external=True),
                'changefreq': 'yearly',
                'modified': n.date_modified
            })

        # add albums
        for n in Album.query.all():
            urls.append({
                'location': flask.url_for('visitor.album', id=n.id, slug=n.slug, _external=True),
                'changefreq': 'yearly',
                'modified': n.date_modified
            })

        ctx['urls'] = urls
        return ctx

    def get(self, *args, **kwargs):
        response = flask.make_response(super().get(*args, **kwargs))
        response.headers['Content-type'] = 'application/xml'

        return response


visitor_blueprint.add_url_rule('/sitemap.xml', view_func=SitemapView.as_view(name='sitemap'))


# -- Robots.txt
ROBOTS_TXT = """
# www.robotstxt.org
Sitemap: {}

User-agent: *
Disallow: /admin/
Disallow: /fichier/
"""


class RobotsView(views.MethodView):
    methods = ['GET']

    def get(self, *args, **kwargs):
        response = flask.make_response(ROBOTS_TXT.format(flask.url_for('visitor.sitemap', _external=True)))
        response.headers['Content-type'] = 'text/plain'

        return response


visitor_blueprint.add_url_rule('/robots.txt', view_func=RobotsView.as_view(name='robots'))


# -- Pages
class PageView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'page.html'
    model = Page

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if self.object.slug != kwargs.get('slug'):
            flask.abort(error_code)

        if not self.object.visible and not current_user.is_authenticated:
            flask.abort(error_code)  # cannot access directly a non-visible page if not connected

        if self.object.next_id:
            self.object.next = db.session.get(Page, self.object.next_id)  # load object

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['page'] = self.object
        return ctx


visitor_blueprint.add_url_rule('/page/<int:id>-<string:slug>.html', view_func=PageView.as_view(name='page-view'))


# -- Uploads
class UploadView(ObjectManagementMixin, views.MethodView):
    methods = ['GET']
    model = UploadedFile

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if kwargs.get('filename') != self.object.file_name:
            flask.abort(error_code)

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)

        with open(self.object.path(), 'rb') as fx:
            response = flask.make_response(fx.read())

        response.headers['Content-Disposition'] = 'attachment; filename={}'.format(self.object.file_name)
        response.headers['Cache-Control'] = 'must-revalidate'
        response.headers['Pragma'] = 'must-revalidate'
        response.headers['Content-type'] = self.object.possible_mime

        return response


visitor_blueprint.add_url_rule('/fichier/<int:id>/<string:filename>', view_func=UploadView.as_view(name='upload-view'))


@visitor_blueprint.route('/photos/<string:filename>')
def get_picture(filename):
    return send_from_directory(pathlib.Path('..') / current_app.config['UPLOADED_PICTURES_DEST'], filename)


# -- Newsletter
class NewsletterRegisterView(BaseMixin, FormView):
    form_class = NewsletterForm
    template_name = 'newsletter-in.html'
    decorators = [limiter.limit(AM_Nihoul_website.NEWSLETTER_LIMIT)]

    def form_valid(self, form):

        # check captcha, if any
        if AM_Nihoul_website.WEBPAGE_INFO['recaptcha_public_key'] != '':
            if 'g-recaptcha-response' not in request.form:
                return self.form_invalid(form)

            payload = {
                'response': request.form['g-recaptcha-response'],
                'secret': current_app.config['RECAPTCHA_SECRET_KEY']
            }
            response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload).json()

            if not response['success']:
                msg = 'Google reCAPTCHA ne vous a pas accepté'
                if 'error-codes' in response:
                    msg += ' (raisons données: {})'.format(', '.join(response['error-codes']))
                flask.flash(msg, 'error')

                return self.form_invalid(form)

        if NewsletterRecipient.query.filter(NewsletterRecipient.email == form.email.data).count() == 0:
            r = NewsletterRecipient.create(form.name.data, form.email.data)

            db.session.add(r)
            db.session.commit()

            e = Email.create(
                'Inscription aux infolettres',
                flask.render_template(
                    'newsletter/newsletter-in.html',
                    **{
                        'name': form.name.data,
                        'site_name': AM_Nihoul_website.WEBPAGE_INFO['site_name'],
                        'recipient': r,
                        'ndays': current_app.config['REMOVE_RECIPIENTS_DELTA'].days
                    }
                ),
                r.id)
            db.session.add(e)
            db.session.commit()

        # done on purpose, so that nobody knows if a given address has subscribed or not:
        flask.flash(
            'Veuillez consulter le mail que nous venons de vous envoyer. '
            "Vous devez y cliquer sur le lien de confirmation d'ici {} jours !!".format(
                current_app.config['REMOVE_RECIPIENTS_DELTA'].days)
        )
        self.success_url = flask.url_for('visitor.index')

        return super().form_valid(form)


visitor_blueprint.add_url_rule(
    '/infolettres-inscription.html', view_func=NewsletterRegisterView.as_view(name='newsletter-subscribe'))


class BaseNewsletterMixin(BaseMixin, ObjectManagementMixin, views.MethodView):
    model = NewsletterRecipient

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if self.object.hash != kwargs.get('hash'):
            flask.abort(error_code)

    def get(self, *args, **kwargs):
        raise NotImplementedError()


class NewsletterSubscribeConfirmView(BaseNewsletterMixin):

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)
        if self.object.confirmed:
            flask.abort(error_code)

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)

        self.object.confirmed = True
        db.session.add(self.object)
        db.session.commit()

        flask.flash('Votre inscription aux infolettres est bien confirmée, merci !')
        return flask.redirect(flask.url_for('visitor.index'))


visitor_blueprint.add_url_rule(
    '/infolettres-confirmation-<int:id>-<string:hash>.html',
    view_func=NewsletterSubscribeConfirmView.as_view(name='newsletter-confirm'))


class NewsletterUnsubscribeView(BaseNewsletterMixin):

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)

        db.session.delete(self.object)
        db.session.commit()

        flask.flash('Vous êtes bien désinscrit, vous ne recevrez plus de message de notre part.')
        return flask.redirect(flask.url_for('visitor.index'))


visitor_blueprint.add_url_rule(
    '/infolettres-désinscription-<int:id>-<string:hash>.html',
    view_func=NewsletterUnsubscribeView.as_view(name='newsletter-unsubscribe'))


class NewsletterView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'newsletter.html'
    model = Newsletter

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if self.object.draft:
            flask.abort(error_code)

        if self.object.slug != kwargs.get('slug'):
            flask.abort(error_code)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['newsletter'] = self.object

        # next?
        next_newsletter = Newsletter.query\
            .filter(Newsletter.draft.is_(False))\
            .filter(Newsletter.date_published < self.object.date_published)\
            .filter(Newsletter.id.isnot(self.object.id))\
            .order_by(Newsletter.date_published.desc())\
            .first()

        if next_newsletter is not None:
            ctx['next_newsletter'] = next_newsletter

        return ctx


visitor_blueprint.add_url_rule(
    '/infolettre/<int:id>-<string:slug>.html', view_func=NewsletterView.as_view(name='newsletter-view'))


class NewslettersView(BaseMixin, RenderTemplateView):
    template_name = 'newsletters.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['newsletters'] = Newsletter.query\
            .filter(Newsletter.draft.is_(False))\
            .order_by(Newsletter.date_published.desc())\
            .all()

        return ctx


visitor_blueprint.add_url_rule('/infolettres.html', view_func=NewslettersView.as_view(name='newsletters'))


# -- ALBUMS
class AlbumsView(BaseMixin, RenderTemplateView):
    template_name = 'albums.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        # fetch albums
        ctx['albums'] = Album.ordered_items(desc=True)

        return ctx


visitor_blueprint.add_url_rule('/albums.html', view_func=AlbumsView.as_view(name='albums'))


class AlbumView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    model = Album
    template_name = 'album.html'

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if self.object.slug != kwargs.get('slug'):
            flask.abort(error_code)

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)

        ctx['album'] = self.object
        ctx['pictures'] = sorted(self.object.pictures, key=lambda k: k.date_taken)

        return ctx


visitor_blueprint.add_url_rule('/album-<int:id>-<string:slug>.html', view_func=AlbumView.as_view(name='album'))


# -- Brief
class BriefsView(BaseMixin, RenderTemplateView):
    template_name = 'briefs.html'

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['briefs'] = Brief.query.filter(Brief.visible.is_(True)).order_by(Brief.id.desc()).all()
        return ctx


visitor_blueprint.add_url_rule('/brèves.html', view_func=BriefsView.as_view(name='briefs'))


class BriefView(BaseMixin, ObjectManagementMixin, RenderTemplateView):
    template_name = 'brief.html'
    model = Brief

    def get(self, *args, **kwargs):
        self.get_object_or_abort(*args, **kwargs)
        return super().get(*args, **kwargs)

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        super().get_object_or_abort(error_code, *args, **kwargs)

        if self.object.slug != kwargs.get('slug'):
            flask.abort(error_code)

        if not self.object.visible and not current_user.is_authenticated:
            flask.abort(error_code)  # cannot access directly a non-visible page if not connected

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['brief'] = self.object

        # next?
        next_brief = Brief.query\
            .filter(Brief.visible.is_(True))\
            .order_by(Brief.id.desc())\
            .filter(Brief.id < self.object.id)\
            .first()

        if next_brief is not None:
            ctx['next_brief'] = next_brief

        return ctx


visitor_blueprint.add_url_rule(
    '/brève/<int:id>-<string:slug>.html', view_func=BriefView.as_view(name='brief-view'))
