# blueprints/legal/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

class ContactForm(FlaskForm):
    full_name = StringField("Nom complet", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    phone = StringField("Téléphone")  # optionnel
    subject = SelectField("Sujet", choices=[
        ("bug", "Signaler un bug"),
        ("improvement", "Proposer une amélioration"),
        ("partnership", "Demande de partenariat"),
        ("other", "Autre demande")
    ], validators=[DataRequired()])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])