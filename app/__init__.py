from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from config import config_map

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
migrate = Migrate()


def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'warning'

    # Register blueprints
    from app.controllers import auth_bp, admin_bp, resident_bp, collector_bp, main_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(resident_bp)
    app.register_blueprint(collector_bp)

    # Jinja2 helpers
    from datetime import datetime
    import builtins as _builtins

    @app.template_filter('datefmt')
    def datefmt(value, fmt='%b %d, %Y'):
        if not value:
            return '—'
        if isinstance(value, str):
            try:
                value = datetime.strptime(value, '%Y-%m-%d').date()
            except Exception:
                return value
        return value.strftime(fmt)

    @app.template_filter('timefmt')
    def timefmt(value):
        if not value:
            return '—'
        return str(value).replace('-', ' – ')

    app.jinja_env.globals['enumerate'] = _builtins.enumerate

    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Create tables and seed static data only
    with app.app_context():
        db.create_all()
        _seed_waste_types()

    return app


def _seed_waste_types():
    """Seed the four waste categories if they don't exist yet.
    No user accounts are pre-seeded — the admin creates their own on first run.
    """
    from app.models import WasteType

    if WasteType.query.first() is not None:
        return  # already seeded

    waste_types = [
        WasteType(name='Household',  description='General domestic waste',
                  icon='trash-2',        color_class='waste-household'),
        WasteType(name='Recyclable', description='Plastic, paper, glass, metal',
                  icon='recycle',        color_class='waste-recyclable'),
        WasteType(name='Organic',    description='Food and garden waste',
                  icon='leaf',           color_class='waste-organic'),
        WasteType(name='Hazardous',  description='Chemicals, batteries, e-waste',
                  icon='alert-triangle', color_class='waste-hazardous',
                  requires_special_handling=True),
    ]
    for wt in waste_types:
        db.session.add(wt)
    db.session.commit()
