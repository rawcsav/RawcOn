import os
from datetime import timedelta
from urllib.parse import quote_plus

import redis
from celery.schedules import crontab

basedir = os.path.abspath(os.path.dirname(__file__))
appdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))


class Config(object):

    # Flask Config
    FLASK_ENV = os.getenv("FLASK_ENV")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    ENCRYPTION_KEY = os.getenv("CRYPT_KEY")
    # Spotify Config
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    ME_URL = "https://api.spotify.com/v1/me"

    # Assets Config
    ASSETS_DEBUG = False

    # SQLAlchemy Config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 299,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "pool_reset_on_return": "rollback",
    }

    # SQL General Config
    SQL_HOSTNAME = os.getenv("SQL_HOSTNAME")
    SQL_USERNAME = os.getenv("SQL_USERNAME")
    SQL_PASSWORD = quote_plus(os.getenv("SQL_PASSWORD"))  # URL-encode the password
    SQL_DB_NAME = os.getenv("SQL_DB_NAME")

    # Cloudinary Config
    CLOUD_NAME = os.getenv("CLOUD_NAME")
    CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUD_SECRET = os.getenv("CLOUDINARY_SECRET")

    # Cors
    CORS_ORIGINS = "*"
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    AUDIO_FEATURES = [
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "tempo",
        "valence",
        "popularity",
    ]

    # Cache Config
    CACHE_TYPE = "redis"
    CACHE_REDIS_HOST = os.getenv("REDIS_HOST")
    CACHE_REDIS_PORT = os.getenv("REDIS_PORT")
    CACHE_REDIS_DB = os.getenv("CACHE_REDIS_DB")
    CACHE_REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # if applicable
    CACHE_DEFAULT_TIMEOUT = 300

    # Rate Limit Config
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_REDIS_URI")
    RATELIMIT_STORAGE_OPTIONS = {"password": os.getenv("REDIS_PASSWORD")}
    RATELIMIT_HEADERS_ENABLED = True

    # Flask-Session
    REDIS_URI = os.getenv("SESSION_REDIS_URI")
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.from_url(REDIS_URI)

    # Celery Config
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_IMPORTS = ("app.util.tasks.celery_tasks",)

    CELERY_BEAT_SCHEDULE = {
        "update-stale-user-data": {
            "task": "tasks.update_stale_user_data",
            "schedule": crontab(minute=0, hour="*/6"),  # Run every 6 hours
        },
        "delete-inactive-users": {
            "task": "tasks.delete_inactive_users",
            "schedule": crontab(hour=0, minute=0),  # Run daily at midnight
        },
    }

    @classmethod
    def init_app(cls, app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    @classmethod
    def init_app(cls, app):
        super().init_app(app)  # Call the parent init_app
        app.tunnel = None
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{os.getenv('SQL_USERNAME')}:"
            f"{quote_plus(os.getenv('SQL_PASSWORD'))}@{os.getenv('SQL_HOSTNAME')}:"
            f"3306/{os.getenv('SQL_DB_NAME')}"
        )


class ProductionConfig(Config):
    FLASK_DEBUG = True
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        super().init_app(app)  # Call the parent init_app
        app.tunnel = None
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+pymysql://{os.getenv('SQL_USERNAME')}:"
            f"{quote_plus(os.getenv('SQL_PASSWORD'))}@{os.getenv('SQL_HOSTNAME')}:"
            f"3306/{os.getenv('SQL_DB_NAME')}"
        )
