from flask_wtf import FlaskForm
import wtforms as f


class NewsletterForm(FlaskForm):
    name = f.StringField(
        'Nom',
        validators=[
            f.validators.input_required(message='Ce champ est requis'),
            f.validators.Length(min=4, max=100, message='La valeur doit être comprise entre 4 et 100 caractères')
        ])
    email = f.StringField(
        'Adresse e-mail',
        validators=[
            f.validators.input_required(message='Ce champ est requis'),
            f.validators.email(message='Ceci n\'est pas une adresse email valide')]
    )
    opt_in = f.BooleanField(
        "J'accepte que les informations saisies soient utilisées pour m'envoyer des informations sur l'ASBL",
        validators=[f.validators.input_required(message='Vous devez accepter afin de recevoir la newsletter')]
    )

    submit_button = f.SubmitField('S\'inscrire')
