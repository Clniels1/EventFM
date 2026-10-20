from . import db
from datetime import datetime, timezone
from flask_login import UserMixin

# List of genre choices (makes filtering possible)
GENRE_CHOICES = [
    ('pop', 'Pop'),
    ('hip-hop-rap', 'Hip-Hop & Rap'),
    ('rnb-soul', 'R&B & Soul'),
    ('alternative', 'Alternative'),
    ('indie-rock', 'Indie Rock'),
    ('electronic-dance', 'Electronic & Dance'),
    ('heavy-metal', 'Heavy Metal'),
    ('folk-acoustic', 'Folk & Acoustic'),
    ('punk-hardcore', 'Punk & Hardcore'),
    ('jazz-blues', 'Jazz & Blues'),
    ('edm', 'EDM'),
    ('country', 'Country'),
    ('post-grunge', 'Post-Grunge'),
    ('classical', 'Classical')
]

# Age restriction choices for events
AGE_LIMIT_CHOICES = [
    ('all-ages', 'All ages'),
    ('15-plus', '15+'),
    ('18-plus', '18+'),
    ('under-18', 'Under 18 only')
]

# Create user model 
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    emailid = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    street_address = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)

    # User has nested events and event related fields to link a UID to an event (makes it so other users can see their comments, made events, etc.)
    events = db.relationship('Event', backref='owner', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def __repr__(self):
        return '<NameL {}, id {}>'.format(self.name, self.id)

# Event model
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(30), nullable=False)
    age_limit = db.Column(db.String(20), nullable=False, default='all-ages')
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(200))
    status = db.Column(db.String(20), nullable=False, default='Open')
    acknowledgement_type = db.Column(db.String(20), nullable=False, default='none')
    acknowledgement_text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) #Links to user who created it (User.ID = Foreign Key)

    # Similar to user model, event has comments owned by it 
    comments = db.relationship('Comment', backref='event', lazy=True)
    orders = db.relationship('Order', backref='event', lazy=True)
    chunks = db.relationship('EventChunk', backref='event', lazy=True, cascade='all, delete-orphan')

    @property
    def tickets_sold(self):
        return sum(o.quantity for o in self.orders if o.booking_status != 'Cancelled')

    @property
    def tickets_remaining(self):
        return self.capacity - self.tickets_sold

    # Refreshes the status of the event based on the date and tickets remaining
    def refresh_status(self):
        if self.status == 'Cancelled':
            return
        if self.date < datetime.now().date():
            self.status = 'Inactive'
        elif self.tickets_remaining <= 0:
            self.status = 'Sold Out'
        else:
            self.status = 'Open'

# Text chunk of an event with its semantic-search embedding
class EventChunk(db.Model):
    __tablename__ = 'event_chunks'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.LargeBinary, nullable=False)

# Comment model, passed to user and event models to link comments to both users and events
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)

# Order model, passed to user and event models to link orders to both users and events
class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    booking_status = db.Column(db.String(20), nullable=False, default='Confirmed')