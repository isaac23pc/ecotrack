import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    WTF_CSRF_ENABLED = True

    # Use SQLite for easy demo; swap DATABASE_URL for MySQL
    USE_SQLITE = os.environ.get('USE_SQLITE', 'true').lower() == 'true'
    if USE_SQLITE:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'ecotrack.db'
        )
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get(
            'DATABASE_URL',
            'mysql+pymysql://root:password@localhost:3306/ecotrack_db'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
