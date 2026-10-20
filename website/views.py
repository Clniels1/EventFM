import os
import calendar
from uuid import uuid4
from datetime import date
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash, session
from .models import Event, Order, Comment, GENRE_CHOICES, AGE_LIMIT_CHOICES
from .forms import EventForm, BookingForm, CommentForm, SearchForm
from . import db
from . import acknowledgement as aoc
from .semantic import index_event, semantic_search
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
main_bp = Blueprint('main', __name__)

SEARCH_RESULT_LIMIT = 10
SEARCH_CANDIDATE_LIMIT = 100  # semantic matches considered before filters and the result limit are applied
HOME_EVENT_LIMIT = 6
GENRE_LABELS = dict(GENRE_CHOICES)
AGE_LABELS = dict(AGE_LIMIT_CHOICES)

# (key, label, min price inclusive, max price exclusive)
PRICE_RANGES = [
    ('under-75', 'Under $75', 0, 75),
    ('75-100', '$75–$100', 75, 100),
    ('100-125', '$100–$125', 100, 125),
    ('125-plus', '$125+', 125, None),
]
PRICE_LABELS = {key: label for key, label, _, _ in PRICE_RANGES}

@main_bp.app_template_filter('genre_label')
def genre_label(slug):
    return GENRE_LABELS.get(slug, slug)

@main_bp.app_template_filter('age_label')
def age_label(slug):
    return AGE_LABELS.get(slug, slug)

def read_filters():
    """Read the filter bar's selections from the query string, dropping unknown values."""
    return {
        'genre': [g for g in request.args.getlist('genre') if g in GENRE_LABELS],
        'price': request.args.get('price') if request.args.get('price') in PRICE_LABELS else None,
        'age': [a for a in request.args.getlist('age') if a in AGE_LABELS],
    }

def apply_filters(query, filters):
    if filters['genre']:
        query = query.filter(Event.genre.in_(filters['genre']))
    if filters['price']:
        _, _, low, high = next(r for r in PRICE_RANGES if r[0] == filters['price'])
        query = query.filter(Event.price >= low)
        if high is not None:
            query = query.filter(Event.price < high)
    if filters['age']:
        query = query.filter(Event.age_limit.in_(filters['age']))
    return query

@main_bp.app_template_global()
def filter_url(endpoint, filters, query=None, drop=None):
    """URL for endpoint carrying the current filters; drop=('genre', 'pop') leaves one selection out."""
    def keep(key, value):
        return drop != (key, value)
    return url_for(
        endpoint,
        q=query or None,
        genre=[g for g in filters['genre'] if keep('genre', g)],
        price=filters['price'] if filters['price'] and keep('price', filters['price']) else None,
        age=[a for a in filters['age'] if keep('age', a)],
    )

def filter_context(filters):
    """Template variables shared by every page that shows the filter bar."""
    return {
        'filters': filters,
        'active_filter_count': len(filters['genre']) + len(filters['age']) + (1 if filters['price'] else 0),
        'genre_choices': GENRE_CHOICES,
        'price_ranges': PRICE_RANGES,
        'age_choices': AGE_LIMIT_CHOICES,
        'price_labels': PRICE_LABELS,
    }

def safe_index_event(event):
    try:
        index_event(event)
    except Exception:
        db.session.rollback()
        current_app.logger.exception('Failed to index event %s for semantic search', event.id)

def events_by_status(filters):
    """Return (upcoming, past, cancelled) events matching the filter bar's selections."""
    query = apply_filters(Event.query, filters).order_by(Event.date.asc(), Event.start_time.asc())
    events = query.all()
    for event in events:
        event.refresh_status()
    db.session.commit()
    upcoming_events = [event for event in events if event.status in ['Open', 'Sold Out']]
    recent_events = [event for event in reversed(events) if event.status == 'Inactive']
    cancelled_events = [event for event in events if event.status == 'Cancelled']
    return upcoming_events, recent_events, cancelled_events

@main_bp.route('/')
def index():
    filters = read_filters()
    upcoming_events, _, _ = events_by_status(filters)
    return render_template(
        'index.html',
        upcoming_events=upcoming_events[:HOME_EVENT_LIMIT],
        search_form=SearchForm(),
        **filter_context(filters),
    )

@main_bp.route('/search')
def search():
    search_form = SearchForm(formdata=request.args)
    query = (search_form.q.data or '').strip()
    filters = read_filters()
    results = []
    ai_available = True

    if query:
        search_filter = db.or_(
            Event.title.ilike(f'%{query}%'),
            Event.location.ilike(f'%{query}%'),
            Event.genre.ilike(f'%{query}%'),
            Event.description.ilike(f'%{query}%')
        )
        keyword_ids = {e.id for e in apply_filters(Event.query.filter(search_filter), filters).all()}

        # score each event by semantic similarity
        semantic_scores = {}
        try:
            semantic_scores = dict(semantic_search(query, limit=SEARCH_CANDIDATE_LIMIT))
        except Exception:
            ai_available = False
            current_app.logger.exception('Semantic search failed, using keyword results only')

        # only events passing the filters are ranked, so the result limit is applied after filtering
        events_by_id = {e.id: e for e in apply_filters(
            Event.query.filter(Event.id.in_(set(semantic_scores) | keyword_ids)), filters).all()}
        scores = {event_id: score for event_id, score in semantic_scores.items() if event_id in events_by_id}
        for event_id in keyword_ids:
            boost = 1.0 if query.lower() in events_by_id[event_id].title.lower() else 0.5
            scores[event_id] = scores.get(event_id, 0) + boost

        ranked_ids = sorted(scores, key=scores.get, reverse=True)[:SEARCH_RESULT_LIMIT]
        for event_id in ranked_ids:
            if event_id not in events_by_id:
                continue
            event = events_by_id[event_id]
            event.refresh_status()
            semantic_score = semantic_scores.get(event_id)
            results.append({
                'event': event,
                'match_percent': round(semantic_score * 100) if semantic_score is not None else None,
                'keyword_match': event_id in keyword_ids,
            })
        db.session.commit()

        return render_template('search-results.html', search_form=search_form, query=query,
                               results=results, ai_available=ai_available,
                               **filter_context(filters))

    # an empty search lists every festival matching the filters
    upcoming_events, recent_events, cancelled_events = events_by_status(filters)
    return render_template('search-results.html', search_form=search_form, query=query,
                           upcoming_events=upcoming_events,
                           recent_events=recent_events,
                           cancelled_events=cancelled_events,
                           **filter_context(filters))

# Where the event page's back button goes: the page the visitor came from.
# It's kept in the session so it survives commenting, booking or editing, which
# all redirect back to the event page and would otherwise replace the referrer.
def event_back_url(event_id):
    referrer = urlparse(request.referrer or '')
    event_path = f'/event/{event_id}'
    from_this_event = referrer.path == event_path or referrer.path.startswith(event_path + '/')
    from_form = referrer.path in ('/create-event', '/login', '/register')
    if referrer.netloc == request.host and not from_this_event and not from_form:
        url = referrer.path + (f'?{referrer.query}' if referrer.query else '')
        session['event_back'] = {'event_id': event_id, 'url': url}
        return url

    saved = session.get('event_back')
    if saved and saved.get('event_id') == event_id:
        return saved['url']
    return url_for('main.index')

@main_bp.route('/event/<int:event_id>')
def event_details(event_id):
    event = Event.query.get_or_404(event_id)
    event.refresh_status()
    db.session.commit()
    booking_form = BookingForm()
    comment_form = CommentForm()
    order_id = request.args.get('order_id')
    booking_error = request.args.get('booking_error')

    return render_template(
        'event-details.html',
        event=event,
        back_url=event_back_url(event.id),
        capital_cities=aoc.CAPITAL_CITIES,
        source_labels=aoc.SOURCE_LABELS,
        booking_form=booking_form,
        comment_form=comment_form,
        order_id=order_id,
        booking_error=booking_error
    )

@main_bp.route('/my-events')
@login_required
def my_events():
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.date.desc()).all()
    for event in events:
        event.refresh_status()
    db.session.commit()

    return render_template('my-events.html', events=events)

@main_bp.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image = form.image.data
            image_filename = f"{uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(current_app.root_path, 'static', 'img', image_filename)
            image.save(image_path)
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            location=form.location.data,
            genre=form.genre.data,
            age_limit=form.age_limit.data,
            price=float(form.price.data),
            capacity=form.capacity.data,
            image_filename=image_filename,
            user_id=current_user.id
        )
        aoc.apply_to_event(form, event)

        db.session.add(event)
        db.session.commit()
        safe_index_event(event)
        flash('Event created successfully!', 'success')
        return redirect(url_for('main.event_details', event_id=event.id))

    return render_event_form(form)

@main_bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return redirect(url_for('main.event_details', event_id=event.id))
    event.refresh_status()
    db.session.commit()
    if event.status in ['Cancelled', 'Inactive']:
        flash('Cancelled or past events cannot be edited.', 'danger')
        return redirect(url_for('main.event_details', event_id=event.id))
    form = EventForm(obj=event)
    if not form.is_submitted():
        aoc.load_into_form(form, event)
    if form.validate_on_submit():
        # capacity above sold
        if form.capacity.data < event.tickets_sold:
            flash(f'Capacity cannot be less than the {event.tickets_sold} tickets already sold', 'danger')
            return render_event_form(form, editing=True)
        existing_image = event.image_filename
        form.populate_obj(event)
        event.image_filename = existing_image
        aoc.apply_to_event(form, event)
        if form.image.data:
            image = form.image.data
            image_filename = f"{uuid4().hex}_{secure_filename(image.filename)}"
            image_path = os.path.join(current_app.root_path, 'static', 'img', image_filename)
            image.save(image_path)
            event.image_filename = image_filename
        db.session.commit()
        safe_index_event(event)
        flash('Event updated successfully!', 'success')
        return redirect(url_for('main.event_details', event_id=event.id))

    return render_event_form(form, editing=True)

def render_event_form(form, editing=False):
    # check custom wording for common mistakes
    review = []
    if form.acknowledgement_type.data == 'enhanced' and form.acknowledgement_text.data:
        review = aoc.review_statement(form.acknowledgement_text.data, form.aoc_custodians.data or '')
    return render_template(
        'create-event.html',
        form=form,
        editing=editing,
        aoc_preview=aoc.preview_statement(form),
        aoc_review=review,
        generic_statement=aoc.GENERIC_STATEMENT,
        capital_cities=aoc.CAPITAL_CITIES,
    )

@main_bp.route('/acknowledgement-of-country')
def acknowledgement_guide():
    return render_template(
        'acknowledgement-of-country.html',
        capital_cities=aoc.CAPITAL_CITIES,
        resources=aoc.RESOURCES,
        mistakes=aoc.MISTAKES,
        contested=aoc.CONTESTED,
        generic_statement=aoc.GENERIC_STATEMENT,
    )

@main_bp.route('/event/<int:event_id>/cancel', methods=['POST'])
@login_required
def cancel_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return redirect(url_for('main.event_details', event_id=event.id))
    event.refresh_status()
    if event.status not in ('Open', 'Sold Out'):
        db.session.commit()
        return redirect(url_for('main.event_details', event_id=event.id))
    event.status = 'Cancelled'
    db.session.commit()
    flash('Event cancelled successfully.', 'success')

    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/event/<int:event_id>/book', methods=['POST'])
@login_required
def book_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = BookingForm()
    event.refresh_status()
    if event.status != 'Open':
        db.session.commit()
        flash('This event is not available for booking.', 'danger')
        return redirect(url_for('main.event_details', event_id=event.id))
    if form.validate_on_submit():
        quantity = form.quantity.data
        if quantity > event.tickets_remaining:
            return redirect(url_for(
                'main.event_details',
                event_id=event.id,
                booking_error='not_enough_tickets'
            ))
        return redirect(url_for(
            'main.payment',
            event_id=event.id,
            quantity=quantity
            ))
    flash('Invalid booking quantity. Please select between 1 and 10 tickets.', 'danger')
    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/booking-history')
@login_required
def booking_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.booking_date.desc()).all()
    upcoming_orders = [
        order for order in orders
        if order.event.date >= date.today()
    ]
    past_orders = [
        order for order in orders
        if order.event.date < date.today()
    ]

    return render_template(
        'booking-history.html',
        upcoming_orders=upcoming_orders,
        past_orders=past_orders
    )

@main_bp.route('/event/<int:event_id>/comment', methods=['POST'])
@login_required
def add_comment(event_id):
    event = Event.query.get_or_404(event_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user_id=current_user.id,
            event_id=event.id
        )
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted successfully.', 'success')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, 'danger')

    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main_bp.route('/event/<int:event_id>/payment')
@login_required
def payment(event_id):
    event = Event.query.get_or_404(event_id)
    quantity = request.args.get('quantity', type=int)
    event.refresh_status()
    if event.status != 'Open' or quantity is None or not 1 <= quantity <= 10 or quantity > event.tickets_remaining:
         db.session.commit()
         flash('This event is unavailable or the ticket quantity is invalid.', 'danger')
         return redirect(url_for('main.event_details', event_id=event.id))
    total_price = event.price * quantity
    return render_template(
        'payment.html',
        event=event,
        quantity=quantity,
        total_price=total_price
    )

@main_bp.route('/event/<int:event_id>/payment/confirm', methods=['POST'])
@login_required
def confirm_payment(event_id):
    event = Event.query.get_or_404(event_id)
    quantity = request.form.get('quantity', 1, type=int)
    event.refresh_status()
    if event.status != 'Open' or quantity < 1 or quantity > 10 or quantity > event.tickets_remaining:
        db.session.commit()
        flash('Payment could not be completed. The event is unavailable or the ticket quantity is invalid.', 'danger')
        return redirect(url_for('main.event_details', event_id=event.id))
    card_name = request.form.get('card_name', '').strip()
    billing_address = request.form.get('billing_address', '').strip()
    if not 2 <= len(card_name) <= 100 or not 5 <= len(billing_address) <= 200:
        flash('Please enter valid demo payment details.', 'danger')
        return redirect(url_for('main.payment', event_id=event.id, quantity=quantity))
    order = Order(
        user_id=current_user.id,
        event_id=event.id,
        quantity=quantity,
        total_price=event.price * quantity
    )
    db.session.add(order)
    db.session.commit()
    event.refresh_status()
    db.session.commit()

    return redirect(url_for(
        'main.event_details',
        event_id=event.id,
        order_id=order.id
    ))

@main_bp.route('/calendar')
def festival_calendar():
    events = Event.query.order_by(Event.date.asc()).all()
    for event in events:
        event.refresh_status()
    db.session.commit()
    months = {}
    for event in events:
        month_key = (event.date.year, event.date.month)
        if month_key not in months:
            months[month_key] = {
                'name': calendar.month_name[event.date.month],
                'year': event.date.year,
                'weeks': calendar.monthcalendar(
                    event.date.year,
                    event.date.month
                ),
                'events': []
            }
        months[month_key]['events'].append(event)

    return render_template(
        'festival-calendar.html',
        months=months
    )