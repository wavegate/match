import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
#from elasticsearch import Elasticsearch
from config import Config
from flask_wtf.csrf import CSRFProtect
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView

db = SQLAlchemy()
migrate = Migrate(render_as_batch=True)
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    csrf.init_app(app)
    admin = Admin()
    admin.init_app(app)
    admin.add_view(AdminView(models.User, db.session))
    admin.add_view(AdminView(models.Specialty, db.session))
    admin.add_view(AdminView(models.Program, db.session))
    admin.add_view(AdminView(models.Interview, db.session))
    admin.add_view(AdminView(models.Interview_Date, db.session))
    admin.add_view(AdminView(models.Notification, db.session))
    admin.add_view(AdminView(models.Message, db.session))
    admin.add_view(AdminView(models.Post, db.session))

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.cognition import bp as cognition_bp
    app.register_blueprint(cognition_bp, url_prefix='/cognition')

    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Match Failure',
                credentials=auth, secure=secure)
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/match.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('Match startup')

        with app.app_context():
            if db.engine.url.drivername == 'sqlite':
                migrate.init_app(app, db, render_as_batch=True)
            else:
                migrate.init_app(app, db)

    return app


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])

class AdminView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return current_user.admin
        else:
            return False

from app import models