import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (TextAreaField, SubmitField, StringField, PasswordField, SelectField,
                             RadioField, BooleanField, DateField, TimeField, FloatField, IntegerField)
from wtforms.validators import InputRequired, Length, Email, EqualTo, NumberRange, ValidationError
from .models import GENRE_CHOICES
from .acknowledgement import CAPITAL_CITIES, REGION_CHOICES, SOURCE_CHOICES

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
    acknowledgement_type = RadioField("Acknowledgement of Country", choices=AOC_CHOICES,
                                       default='none', validators=[InputRequired()])
    acknowledgement_text = TextAreaField("Write your own wording (optional)", validators=[Length(max=2000)])

    # Enhanced acknowledgement builder - only required when 'enhanced' is selected
    aoc_region = SelectField("Where is the event held?", choices=REGION_CHOICES, default='')
    aoc_custodians = StringField("Traditional Custodians", validators=[Length(max=200)])
    aoc_place_name = StringField("Place name in local language (optional)", validators=[Length(max=100)])
    aoc_source = SelectField("How did you confirm the Traditional Custodians?", choices=SOURCE_CHOICES, default='')
    aoc_connection = TextAreaField("Why does this Country matter to your event?", validators=[Length(max=1000)])
    aoc_commitment = TextAreaField("What is your event doing to support First Nations communities? (optional)", validators=[Length(max=1000)])
    aoc_welcome = BooleanField("A Welcome to Country will be delivered by a Traditional Owner")
    aoc_check_names = BooleanField("I have checked the custodians' names and spelling with a reliable local source")
    aoc_check_genuine = BooleanField("Everything in my acknowledgement is true of this event (nothing tokenistic or overclaimed)")
    aoc_check_difference = BooleanField("I understand this is an Acknowledgement, not a Welcome to Country")

    submit = SubmitField("Create Event")

    def _enhanced(self):
        return self.acknowledgement_type.data == 'enhanced'

    def validate_aoc_region(self, field):
        if self._enhanced() and not field.data:
            raise ValidationError('Select where the event is held')

    def validate_aoc_custodians(self, field):
        if not self._enhanced() or (field.data or '').strip():
            return
        # capital cities can be filled in from the reference data
        city = CAPITAL_CITIES.get(self.aoc_region.data)
        if not city:
            raise ValidationError('Name the Traditional Custodians of the place where the event is held')
        field.data = city['custodians']

    def validate_aoc_source(self, field):
        if self._enhanced() and not field.data:
            raise ValidationError('Select the source you used to identify the Traditional Custodians')

    def validate_aoc_connection(self, field):
        if self._enhanced() and len((field.data or '').strip()) < 20:
            raise ValidationError('Write at least a sentence about why this Country matters to your event')

    def _require_checked(self, field):
        if self._enhanced() and not field.data:
            raise ValidationError('Please confirm before publishing an enhanced acknowledgement')

    validate_aoc_check_names = validate_aoc_check_genuine = validate_aoc_check_difference = _require_checked

class CommentForm(FlaskForm):
    content = TextAreaField("Your Comment", validators=[InputRequired(), Length(max=2000)])
    submit = SubmitField("Post Comment")

class BookingForm(FlaskForm):
    quantity = IntegerField("Number of Tickets", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField("Book Event")

# Search form, submitted with GET so results pages can be linked to
class SearchForm(FlaskForm):
    class Meta:
        csrf = False

    q = StringField("Search")
