from flask_wtf import FlaskForm, file as wtf_file
import wtforms as f


class LoginForm(FlaskForm):
    login = f.StringField('Login', validators=[f.validators.InputRequired()])
    password = f.PasswordField('Mot de passe', validators=[f.validators.InputRequired()])
    next = f.HiddenField(default='')

    login_button = f.SubmitField('Login')


class TrumbowygTextarea(f.widgets.TextArea):
    """Add a custom class"""

    def __call__(self, field, **kwargs):
        kwargs['class'] = 'trumbowyg-textarea'
        return super(TrumbowygTextarea, self).__call__(field, **kwargs)


class PageEditForm(FlaskForm):
    title = f.StringField(
        'Titre', validators=[f.validators.InputRequired(), f.validators.Length(max=150)])
    text = f.TextAreaField('Texte', widget=TrumbowygTextarea())
    category = f.SelectField('Catégorie', coerce=int)

    submit_button = f.SubmitField('Enregistrer')


class CategoryEditForm(FlaskForm):

    name = f.StringField('Nom', validators=[f.validators.InputRequired(), f.validators.Length(max=150)])
    is_create = f.BooleanField(widget=f.widgets.HiddenInput(), default=False)
    id_category = f.IntegerField(widget=f.widgets.HiddenInput(), default=-1)

    submit_button = f.SubmitField('Enregistrer')


class UploadForm(FlaskForm):
    file_uploaded = wtf_file.FileField('Fichier', validators=[wtf_file.FileRequired()])
    description = f.StringField('Description')

    submit_button = f.SubmitField('Envoyer')


class NewsletterEditForm(FlaskForm):
    title = f.StringField(
        'Titre', validators=[f.validators.InputRequired(), f.validators.Length(max=150)])
    text = f.TextAreaField('Texte', widget=TrumbowygTextarea())

    submit_button = f.SubmitField('Enregistrer')
    submit_button_2 = f.SubmitField('Enregistrer et prévisualiser')


class NewsletterPublishForm(FlaskForm):
    confirm = f.BooleanField(widget=f.widgets.HiddenInput(), default=False)

    submit_button = f.SubmitField('Publier')
