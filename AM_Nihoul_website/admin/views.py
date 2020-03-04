import flask
from flask import Blueprint

from AM_Nihoul_website import settings
from AM_Nihoul_website.base_views import FormView, BaseMixin, LoginMixin, RenderTemplateView
from AM_Nihoul_website.admin.forms import LoginForm

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


admin_blueprint.add_url_rule('/index.html', view_func=IndexView.as_view(name='index'))
