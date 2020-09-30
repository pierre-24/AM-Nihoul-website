import flask
from flask.views import View

from AM_Nihoul_website import settings, db
from AM_Nihoul_website.visitor.forms import NewsletterForm


class RenderTemplateView(View):
    methods = ['GET']
    template_name = None

    def get_context_data(self, *args, **kwargs):
        return {}

    def get(self, *args, **kwargs):
        """Handle GET: render template"""

        if not self.template_name:
            raise ValueError('template_name')

        context_data = self.get_context_data(*args, **kwargs)
        return flask.render_template(self.template_name, **context_data)

    def dispatch_request(self, *args, **kwargs):
        if flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


class FormView(RenderTemplateView):

    methods = ['GET', 'POST']
    form_class = None
    success_url = '/'
    failure_url = '/'
    modal_form = False

    DEBUG = False

    form_kwargs = {}

    def get_form_kwargs(self):
        return self.form_kwargs

    def get_form(self):
        """Return an instance of the form"""
        return self.form_class(**self.get_form_kwargs())

    def get_context_data(self, *args, **kwargs):
        """Insert form in context data"""

        context = super().get_context_data(*args, **kwargs)

        if 'form' not in context:
            context['form'] = kwargs.pop('form', self.get_form())

        return context

    def post(self, *args, **kwargs):
        """Handle POST: validate form."""

        self.url_args = args
        self.url_kwargs = kwargs
        if not self.form_class:
            raise ValueError('form_class')

        form = self.get_form()

        if form.validate_on_submit():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        """If the form is valid, go to the success url"""
        return flask.redirect(self.success_url)

    def form_invalid(self, form):
        """If the form is invalid, go back to the same page with an error"""

        if self.DEBUG:
            print('form is invalid ::')
            for i in form:
                if len(i.errors) != 0:
                    print('-', i, '→', i.errors, '(value is=', i.data, ')')

        if not self.modal_form:
            return self.get(form=form, *self.url_args, **self.url_kwargs)
        else:
            return flask.redirect(self.failure_url)

    def dispatch_request(self, *args, **kwargs):

        if flask.request.method == 'POST':
            return self.post(*args, **kwargs)
        elif flask.request.method == 'GET':
            return self.get(*args, **kwargs)
        else:
            flask.abort(403)


class DeleteView(View):

    methods = ['POST', 'DELETE']
    success_url = '/'

    def get_object_to_delete(self, *args, **kwargs):
        raise NotImplementedError()

    def pre_deletion(self, obj):
        """Performs an action before deletion from database. Note: if return `False`, deletion is not performed"""
        return True

    def post_deletion(self, obj):
        """Performs an action after deletion from database"""
        pass

    def delete(self, *args, **kwargs):
        """Handle delete"""

        obj = self.get_object_to_delete(*args, **kwargs)

        if not self.pre_deletion(obj):
            return flask.abort(403)

        db.session.delete(obj)
        db.session.commit()

        self.post_deletion(obj)

        return flask.redirect(self.success_url)

    def dispatch_request(self, *args, **kwargs):

        if flask.request.method == 'POST':
            return self.delete(*args, **kwargs)
        elif flask.request.method == 'DELETE':
            return self.delete(*args, **kwargs)
        else:
            flask.abort(403)


# --- Object management
class ObjectManagementMixin:
    model = None
    url_parameter_id = 'id'
    object = None

    def get_object_or_abort(self, error_code=404, *args, **kwargs):
        if self.object is None:
            self.object = self._get_object(*args, **kwargs)

            if self.object is None:
                flask.abort(error_code)

    def get_object(self, *args, **kwargs):
        if self.object is None:
            self.object = self._get_object(*args, **kwargs)

    def _get_object(self, *args, **kwargs):
        return self.model.query.get(kwargs.get(self.url_parameter_id))


class DeleteObjectView(ObjectManagementMixin, DeleteView):

    def get_object_to_delete(self, *args, **kwargs):
        return self._get_object(*args, **kwargs)


# --- Other mixins
class BaseMixin:
    """Add a few variables to the page context"""

    def get_context_data(self, *args, **kwargs):
        """Add some info into context"""

        # webpage info
        ctx = super().get_context_data(*args, **kwargs)
        ctx.update(**settings.WEBPAGE_INFO)

        from AM_Nihoul_website.visitor.models import Page, Category, MenuEntry

        # top menus
        menus = MenuEntry.query.order_by(MenuEntry.order).all()
        ctx['top_menu_small'] = list(filter(lambda x: x.position == MenuEntry.MENU_SMALL, menus))
        ctx['top_menu_big'] = list(filter(lambda x: x.position == MenuEntry.MENU_BIG, menus))

        # bottom menu
        categories = Category.query.order_by(Category.order).all()
        pages = Page.query.filter(Page.category_id.isnot(None)).all()

        cats = {}

        for p in pages:
            cid = p.category_id
            if cid is not None:
                if cid not in cats:
                    cats[cid] = []
                cats[cid].append(p)

        bottom_menu = {}
        for c in categories:
            if c.id in cats:
                bottom_menu[c.name] = cats[c.id]

        ctx['bottom_menu'] = bottom_menu

        # newsletter form
        ctx['newsletter_form'] = NewsletterForm()

        return ctx
