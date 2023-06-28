from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FileField
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Done")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class AddForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    img_url_1 = FileField("URL", validators=[DataRequired()])
    img_url_2 = FileField("URL", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    blurb = StringField("Blurb", validators=[DataRequired()])
    submit = SubmitField("Submit")