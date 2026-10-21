import os
from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()
csrf = CSRFProtect()

def create_app():
  
    app = Flask(__name__)
    app.secret_key = '{=i?D@bc3L&lF(=T'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
    db.init_app(app)

    csrf.init_app(app)

    Bootstrap5(app)
    
    login_manager = LoginManager()
    
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # Importing inside the create_app function avoids circular references
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
       # treat the user as logged out if the database is unavailable, so error pages can still render
       try:
          return db.session.scalar(db.select(User).where(User.id==user_id))
       except SQLAlchemyError:
          db.session.rollback()
          return None

    from . import views
    app.register_blueprint(views.main_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    with app.app_context():
        db.create_all()

        # create_all never adds columns to existing tables, so add age_limit to older databases here
        event_columns = [row[1] for row in db.session.execute(db.text('PRAGMA table_info(events)'))]
        if 'age_limit' not in event_columns:
            db.session.execute(db.text(
                "ALTER TABLE events ADD COLUMN age_limit VARCHAR(20) NOT NULL DEFAULT 'all-ages'"))
            db.session.commit()

        # preload the semantic search model and embeddings; skipped in the reloader's
        # parent process, which never serves requests
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from .semantic import warm_up
            try:
                warm_up()
            except Exception:
                app.logger.exception('Semantic search warm-up failed')

    return app