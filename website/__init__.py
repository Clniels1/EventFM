import os
# import flask - from 'package' import 'Class'
from flask import Flask 
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

# create a function that creates a web application
# a web server will run this web application
def create_app():
  
    app = Flask(__name__)  # this is the name of the module/package that is calling this app
    # Should be set to false in a production environment
    app.debug = True
    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.secret_key = '{=i?D@bc3L&lF(=T'
    # set the app configuration data 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sitedata.sqlite'
    # initialise db with flask app
    db.init_app(app)

    # enable CSRF protection
    csrf.init_app(app)

    Bootstrap5(app)
    
    # initialise the login manager
    login_manager = LoginManager()
    
    # set the name of the login function that lets user login
    # in our case it is auth.login (blueprintname.viewfunction name)
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    # create a user loader function takes userid and returns User
    # Importing inside the create_app function avoids circular references
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
       return db.session.scalar(db.select(User).where(User.id==user_id))

    from . import views
    app.register_blueprint(views.main_bp)

    from . import auth
    app.register_blueprint(auth.auth_bp)

    from . import errors
    app.register_blueprint(errors.errors_bp)

    with app.app_context():
        db.create_all()

        # preload the semantic search model and embeddings; skipped in the reloader's
        # parent process, which never serves requests
        if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            from .semantic import warm_up
            try:
                warm_up()
            except Exception:
                app.logger.exception('Semantic search warm-up failed')

    return app