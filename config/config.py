import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }


class DevelopmentConfig(Config):
    DEBUG = True
    # SQLite — zero setup, perfect for local dev
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'ecotrack.db'
    )


class ProductionConfig(Config):
    DEBUG = False
    # Vercel is serverless — SQLite won't persist.
    # Set DATABASE_URL in Vercel Environment Variables to a hosted DB:
    #   MySQL:      mysql+pymysql://user:pass@host:3306/ecotrack_db
    #   PostgreSQL: postgresql://user:pass@host:5432/ecotrack_db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '')


config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
