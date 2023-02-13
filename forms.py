from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class RegisterForm(FlaskForm):
    name = StringField("Namn", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    submit = SubmitField("Registrera")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Lösenord", validators=[DataRequired()])
    submit = SubmitField("Logga in")


class PostForm(FlaskForm):
    title = StringField("Rubrik", validators=[DataRequired()])
    subtitle = StringField("Underrubrik", validators=[DataRequired()])
    img_url = StringField("Länk till bild", validators=[DataRequired(), URL()])
    body = CKEditorField("Innehåll", validators=[DataRequired()])
    submit = SubmitField("Publicera")


class CommentForm(FlaskForm):
    text = CKEditorField("Kommentar", validators=[DataRequired()])
    submit = SubmitField("Publicera")

