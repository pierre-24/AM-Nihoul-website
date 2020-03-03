from flask_wtf import FlaskForm
import wtforms as f


class LoginForm(FlaskForm):
    login = f.StringField('Login', validators=[f.validators.InputRequired()])
    password = f.PasswordField('Password', validators=[f.validators.InputRequired()])

    login_button = f.SubmitField('Login')
