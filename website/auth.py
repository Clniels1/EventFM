from flask import Blueprint, flash, render_template, request, url_for, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user
from .models import User
from .forms import LoginForm, RegisterForm
from . import db


# Create a blueprint - make sure all BPs have unique names
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])

# view function
def login():
    login_form = LoginForm()
    error = None
    if login_form.validate_on_submit():
        user_name = login_form.user_name.data
        password = login_form.password.data
        user = db.session.scalar(db.select(User).where(User.name==user_name))
        if user is None:
            error = 'Incorrect user name'
        elif not check_password_hash(user.password_hash, password): # takes the hash and cleartext password
            error = 'Incorrect password'
        if error is None:
            login_user(user)
            nextp = request.args.get('next') # this gives the url from where the login page was accessed
            if nextp is None or not nextp.startswith('/') or nextp.startswith(('//', '/\\')):
                return redirect(url_for('main.index'))
            return redirect(nextp)
        else:
            flash(error)
    return render_template('account.html', form=login_form, heading='Login')

# registration view function
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        user_name = register_form.user_name.data
        first_name = register_form.first_name.data
        surname = register_form.surname.data
        email = register_form.email.data.strip().lower()
        contact_number = register_form.contact_number.data
        street_address = register_form.street_address.data
        password = register_form.password.data
        user_type = register_form.user_type.data

        existing_user = db.session.scalar(db.select(User).where(db.or_(User.name==user_name, db.func.lower(User.emailid)==email)))
        if existing_user is not None:
            flash('That user name or email is already registered')
            return render_template('account.html', form=register_form, heading='Register')

        password_hash = generate_password_hash(password)
        new_user = User(name=user_name, first_name=first_name, surname=surname, emailid=email,
                         contact_number=contact_number, street_address=street_address,
                         password_hash=password_hash, user_type=user_type)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('Registration successful, welcome!')
        return redirect(url_for('main.index'))
    return render_template('account.html', form=register_form, heading='Register')

# logout view function
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('main.index'))
