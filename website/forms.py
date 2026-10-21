import re
from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (TextAreaField, SubmitField, StringField, PasswordField, SelectField,
                             RadioField, BooleanField, DateField, TimeField, FloatField, IntegerField)
from wtforms.validators import InputRequired, DataRequired, Length, Email, EqualTo, NumberRange, ValidationError
from .models import GENRE_CHOICES, AGE_LIMIT_CHOICES
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


def strip_whitespace(value):
    return value.strip() if isinstance(value, str) else value


# Login form
class LoginForm(FlaskForm):
    user_name=StringField("Username", filters=[strip_whitespace],
                          validators=[DataRequired('Enter your username'), Length(max=100)],
                          render_kw={'placeholder': 'Enter your username', 'autocomplete': 'username'})
    password=PasswordField("Password", validators=[InputRequired('Enter your password')],
                           render_kw={'placeholder': 'Enter your password', 'autocomplete': 'current-password'})
    submit = SubmitField("Log In")

# Registration form
class RegisterForm(FlaskForm):
    user_name=StringField("Username", filters=[strip_whitespace],
                          validators=[DataRequired('Choose a username'),
                                      Length(min=3, max=30, message='Username must be between 3 and 30 characters')],
                          render_kw={'placeholder': 'e.g. festivalfan99', 'autocomplete': 'username'})
    first_name = StringField("First Name", filters=[strip_whitespace],
                             validators=[DataRequired('Enter your first name'),
                                         Length(max=50, message='First name must be 50 characters or fewer')],
                             render_kw={'placeholder': 'e.g. Alex', 'autocomplete': 'given-name'})
    surname = StringField("Surname", filters=[strip_whitespace],
                          validators=[DataRequired('Enter your surname'),
                                      Length(max=50, message='Surname must be 50 characters or fewer')],
                          render_kw={'placeholder': 'e.g. Smith', 'autocomplete': 'family-name'})
    email = StringField("Email Address", filters=[strip_whitespace],
                        validators=[DataRequired('Enter your email address'), Email("Please enter a valid email"),
                                    Length(max=100, message='Email must be 100 characters or fewer')],
                        render_kw={'placeholder': 'e.g. alex@example.com', 'autocomplete': 'email'})
    contact_number = StringField("Contact Number", filters=[strip_whitespace],
                                 validators=[DataRequired('Enter your contact number'), Length(max=20), validate_contact_number],
                                 render_kw={'placeholder': 'e.g. 0412 345 678', 'autocomplete': 'tel'})
    street_address = StringField("Street Address", filters=[strip_whitespace],
                                 validators=[DataRequired('Enter your street address'),
                                             Length(max=200, message='Street address must be 200 characters or fewer'),
                                             validate_street_address],
                                 render_kw={'placeholder': 'e.g. 12 Example Street, Brisbane QLD 4000', 'autocomplete': 'street-address'})
    user_type = SelectField("Account Type", choices=[('attendee', 'Attendee'), ('organiser', 'Organiser')], validators=[InputRequired()])
    password=PasswordField("Password", validators=[InputRequired('Enter a password'),
                  Length(min=6, max=128, message="Password must be between 6 and 128 characters"),
                  EqualTo('confirm', message="Passwords should match")],
                  render_kw={'placeholder': 'At least 6 characters', 'autocomplete': 'new-password'}) # Password hashed and stored in database, not stored in plaintext + check for length and matching below
    confirm = PasswordField("Confirm Password", validators=[InputRequired('Confirm your password')],
                            render_kw={'placeholder': 'Re-enter your password', 'autocomplete': 'new-password'})
    submit = SubmitField("Create Account")

# Acknowledgement of Country selector shown on event creation
AOC_CHOICES = [('none', 'No Acknowledgement of Country'),
               ('generic', 'Acknowledgement of Country: generic'),
               ('enhanced', 'Acknowledgement of Country: enhanced')]

# Event form
class EventForm(FlaskForm):
    title = StringField(
        "Event Name",
        validators=[InputRequired(), Length(max=200)]
    )
    description = TextAreaField(
        "Event Description",
        validators=[
            InputRequired(),
            Length(max=5000, message="Description cannot exceed 5000 characters.")
        ]
    )
    date = DateField("Event Date", validators=[InputRequired()])
    start_time = TimeField("Start Time", validators=[InputRequired()])
    end_time = TimeField("End Time", validators=[InputRequired()])
    location = StringField(
        "Location",
        validators=[InputRequired(), Length(max=200)]
    )
    price = FloatField(
        "Ticket Price ($)",
        validators=[
            NumberRange(min=0, max=10000,
                        message="Ticket price must be between $0 and $10,000.")
        ]
    )
    capacity = IntegerField(
        "Number of Tickets Available",
        validators=[
            InputRequired(),
            NumberRange(min=1, max=100000,
                        message="Capacity must be between 1 and 100,000.")
        ]
    )
    image = FileField(
        "Event Image",
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only')]
    )
    genre = SelectField(
        "Music Genre",
        choices=GENRE_CHOICES,
        validators=[InputRequired()]
    )
    age_limit = SelectField(
        "Age Restriction",
        choices=AGE_LIMIT_CHOICES,
        default='all-ages',
        validators=[InputRequired()]
    )
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
    def validate_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError("Event date cannot be in the past.")

    def validate_end_time(self, field):
        if self.start_time.data and field.data:
            if field.data <= self.start_time.data:
                raise ValidationError("End time must be later than start time.")

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
    content = TextAreaField(
        "Your Comment",
        validators=[
            InputRequired(message="Please enter a comment before submitting."),
            Length(max=2000, message="Your comment cannot exceed 2,000 characters.")
        ]
    )
    submit = SubmitField("Post Comment")

class BookingForm(FlaskForm):
    quantity = IntegerField(
        "Number of Tickets",
        validators=[
            InputRequired(),
            NumberRange(
                min=1,
                max=10,
                message="You can book between 1 and 10 tickets per order."
            )
        ]
    )
    submit = SubmitField("Book Event")
# Search form, submitted with GET so results pages can be linked to
class SearchForm(FlaskForm):
    class Meta:
        csrf = False

    q = StringField("Search")