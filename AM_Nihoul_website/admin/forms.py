from flask_wtf import FlaskForm
import wtforms as f


class LoginForm(FlaskForm):
    login = f.StringField('Login', validators=[f.validators.InputRequired()])
    password = f.PasswordField('Mot de passe', validators=[f.validators.InputRequired()])

    login_button = f.SubmitField('Login')


class TrumbowygTextarea(f.widgets.TextArea):
    """Add a custom class"""

    def __call__(self, field, **kwargs):
        kwargs['class'] = 'trumbowyg-textarea'
        return super(TrumbowygTextarea, self).__call__(field, **kwargs)


class PageEditForm(FlaskForm):
    title = f.StringField(
        'Titre', validators=[f.validators.InputRequired()], render_kw={'placeholder': 'Titre de la page'})
    text = f.TextAreaField('Texte', widget=TrumbowygTextarea())

    submit_button = f.SubmitField('Enregistrer')
