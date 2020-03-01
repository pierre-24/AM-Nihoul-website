import flask
from flask.views import View


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
