import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (TextAreaField, SubmitField, StringField, PasswordField,
                             SelectField, DateField, TimeField, FloatField, IntegerField)
from wtforms.validators import InputRequired, Length, Email, EqualTo, NumberRange, ValidationError
from .models import GENRE_CHOICES

CONTACT_NUMBER_RE = re.compile(r'^(?:\+?61|0)[2-478]\d{8}$')

STREET_ADDRESS_RE = re.compile(r'^\d+[a-zA-Z]?(?:[\/-]\d+[a-zA-Z]?)?\s+[a-zA-Z].{2,}$')


def validate_contact_number(form, field):
    digits_only = re.sub(r'[^\d+]', '', field.data or '')
    if not CONTACT_NUMBER_RE.match(digits_only):
        raise ValidationError('Enter a valid Australian contact number, e.g. 0412 345 678')


def validate_street_address(form, field):
    value = (field.data or '').strip()
    if not STREET_ADDRESS_RE.match(value):
        raise ValidationError('Enter a full street address with a street number and name, e.g. 12 Example Street')


# Login form
class LoginForm(FlaskForm):
    user_name=StringField("User Name", validators=[InputRequired('Enter user name')])
    password=PasswordField("Password", validators=[InputRequired('Enter user password')])
    submit = SubmitField("Login")

# Registration form
class RegisterForm(FlaskForm):
    user_name=StringField("User Name", validators=[InputRequired()])
    first_name = StringField("First Name", validators=[InputRequired()])
    surname = StringField("Surname", validators=[InputRequired()])
    email = StringField("Email Address", validators=[InputRequired(), Email("Please enter a valid email")])
    contact_number = StringField("Contact Number", validators=[InputRequired(), validate_contact_number])
    street_address = StringField("Street Address", validators=[InputRequired(), validate_street_address])
    user_type = SelectField("Account Type", choices=[('attendee', 'Attendee'), ('organiser', 'Organiser')], validators=[InputRequired()])
    password=PasswordField("Password", validators=[InputRequired(), Length(min=6, message="Password must be at least 6 characters"),
                  EqualTo('confirm', message="Passwords should match")]) # Password hashed and stored in database, not stored in plaintext + check for length and matching below
    confirm = PasswordField("Confirm Password")
    submit = SubmitField("Register")

# Acknowledgement of Country selector shown on event creation
AOC_CHOICES = [('none', 'No Acknowledgement of Country'),
               ('generic', 'Acknowledgement of Country: generic'),
               ('enhanced', 'Acknowledgement of Country: enhanced')]

# Event form 
class EventForm(FlaskForm):
    title = StringField("Event Name", validators=[InputRequired(), Length(max=200)])
    description = TextAreaField("Event Description", validators=[InputRequired()])
    date = DateField("Event Date", validators=[InputRequired()])
    start_time = TimeField("Start Time", validators=[InputRequired()])
    end_time = TimeField("End Time", validators=[InputRequired()])
    location = StringField("Location", validators=[InputRequired(), Length(max=200)])
    price = FloatField("Ticket Price ($)", validators=[InputRequired(), NumberRange(min=0)])
    capacity = IntegerField("Number of Tickets Available", validators=[InputRequired(), NumberRange(min=1)])
    image = FileField("Event Image", validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')])
    genre = SelectField("Music Genre", choices=GENRE_CHOICES, validators=[InputRequired()])
    acknowledgement_type = SelectField("Acknowledgement of Country", choices=AOC_CHOICES,
                                        default='none', validators=[InputRequired()])
    acknowledgement_text = TextAreaField("Acknowledgement Text")
    submit = SubmitField("Create Event")

class CommentForm(FlaskForm):
    content = TextAreaField("Your Comment", validators=[InputRequired(), Length(max=2000)])
    submit = SubmitField("Post Comment")

class BookingForm(FlaskForm):
    quantity = IntegerField("Number of Tickets", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField("Book Event")