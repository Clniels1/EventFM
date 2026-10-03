import os
import calendar
from datetime import date
from flask import Blueprint, render_template, redirect, url_for, current_app, request, flash
from .models import Event, Order, Comment
from .forms import EventForm, BookingForm, CommentForm
from . import db
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    selected_genre = request.args.get('genre')
    if selected_genre:
        events = Event.query.filter_by(genre=selected_genre).all()
    else:
        events = Event.query.all()
    for event in events:
        event.refresh_status()
    db.session.commit()
    upcoming_events = [event for event in events if event.status in ['Open', 'Sold Out']]
    recent_events = [event for event in events if event.status == 'Inactive']
    cancelled_events = [event for event in events if event.status == 'Cancelled']
    return render_template(
        'index.html',
        upcoming_events=upcoming_events,
        recent_events=recent_events,
        cancelled_events=cancelled_events,
        selected_genre=selected_genre,
    )

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
        booking_form=booking_form,
        comment_form=comment_form,
        order_id=order_id,
        booking_error=booking_error
    )

@main_bp.route('/create-event', methods=['GET', 'POST'])
@login_required
def create_event():
    # organisers only
    if current_user.user_type != 'organiser':
        flash('Only organiser accounts can create events')
        return redirect(url_for('main.index'))
    form = EventForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image = form.image.data
            image_filename = secure_filename(image.filename)
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
            price=float(form.price.data),
            capacity=form.capacity.data,
            image_filename=image_filename,
            acknowledgement_type=form.acknowledgement_type.data,
            acknowledgement_text=form.acknowledgement_text.data,
            user_id=current_user.id
        )

        db.session.add(event)
        db.session.commit()
        return redirect(url_for('main.event_details', event_id=event.id))

    return render_template('create-event.html', form=form)

@main_bp.route('/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.user_id != current_user.id:
        return redirect(url_for('main.event_details', event_id=event.id))
    form = EventForm(obj=event)
    if form.validate_on_submit():
        # capacity above sold
        if form.capacity.data < event.tickets_sold:
            flash(f'Capacity cannot be less than the {event.tickets_sold} tickets already sold')
            return render_template('create-event.html', form=form, editing=True)
        existing_image = event.image_filename
        form.populate_obj(event)
        event.image_filename = existing_image
        if form.image.data:
            image = form.image.data
            image_filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.root_path, 'static', 'img', image_filename)
            image.save(image_path)
            event.image_filename = image_filename
        db.session.commit()
        return redirect(url_for('main.event_details', event_id=event.id))
    
    return render_template('create-event.html', form=form, editing=True)

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

    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/event/<int:event_id>/book', methods=['POST'])
@login_required
def book_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = BookingForm()
    event.refresh_status()
    if event.status != 'Open':
        db.session.commit()
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

    return redirect(url_for('main.event_details', event_id=event.id))

@main_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main_bp.route('/event/<int:event_id>/payment')
@login_required
def payment(event_id):
    event = Event.query.get_or_404(event_id)
    quantity = request.args.get('quantity', 1, type=int)
    if quantity < 1:
        quantity = 1
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
    if event.status != 'Open' or quantity < 1 or quantity > event.tickets_remaining:
        db.session.commit()
        return redirect(url_for(
            'main.event_details',
            event_id=event.id,
            booking_error='not_enough_tickets'
        ))
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