import functools

import flask
from flask.views import View

from AM_Nihoul_website import settings


class RenderTemplateView(View):
    methods = ['GET']
    template_name = None

    url_args = []
    url_kwargs = {}

    def get_context_data(self, *args, **kwargs):
        return {}

    def get(self, *args, **kwargs):
        """Handle GET: render template"""

        if not self.template_name:
            raise ValueError('template_name')

        context_data = self.get_context_data(*args, **kwargs)
        return flask.render_template(self.template_name, **context_data)

    def dispatch_request(self, *args, **kwargs):
        self.url_args = args
        self.url_kwargs = kwargs

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

    def get_form_kwargs(self):
        return {}

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


class LoginMixin(object):
    """Maintain the logged_in information in context"""

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        if LoginMixin.logged_in():
            context['logged_in'] = True

        return context

    @staticmethod
    def logged_in():
        """Check if the admin is logged in"""
        if 'logged_in' in flask.session and flask.session['logged_in']:
            return True

        return False

    @staticmethod
    def login_required(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'logged_in' not in flask.session or not flask.session['logged_in']:
                return flask.redirect(flask.url_for('login', next=flask.request.url))
            return f(*args, **kwargs)

        return decorated_function


class BaseMixin(LoginMixin):
    """Add a few variables to the page context"""

    def get_context_data(self, *args, **kwargs):
        """Add webpage infos"""
        ctx = super().get_context_data(*args, **kwargs)
        ctx.update(**settings.WEBPAGE_INFO)
        return ctx
