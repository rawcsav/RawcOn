import os
from datetime import timedelta
from urllib.parse import quote_plus

import cloudinary

basedir = os.path.abspath(os.path.dirname(__file__))
appdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "app"))


class Config(object):
    FLASK_ENV = os.getenv("FLASK_ENV")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY")
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REDIRECT_URI = os.getenv("REDIRECT_URI")
    ASSETS_DEBUG = False

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_RECYCLE = 299
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 299,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "pool_reset_on_return": "rollback",
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_DURATION = timedelta(days=14)

    SQL_HOSTNAME = os.getenv("SQL_HOSTNAME")
    SQL_USERNAME = os.getenv("SQL_USERNAME")
    SQL_PASSWORD = quote_plus(os.getenv("SQL_PASSWORD"))  # URL-encode the password
    SQL_DB_NAME = os.getenv("SQL_DB_NAME")

    CLOUD_NAME = os.getenv("CLOUD_NAME")
    CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUD_SECRET = os.getenv("CLOUDINARY_SECRET")

    GOOGLE_SITE_KEY = os.getenv("GOOGLE_SITE_KEY")
    GOOGLE_SECRET_KEY = os.getenv("GOOGLE_SECRET_KEY")

    SEARCH_ID = os.getenv("SEARCH_ID")
    SEARCH_SECRET = os.getenv("SEARCH_SECRET")

    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    ME_URL = "https://api.spotify.com/v1/me"

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

    REDIRECT_URL = os.getenv("REDIRECT_URL")

    MAX_RETRIES = 3
    RETRY_WAIT_SECONDS = 2

    @classmethod
    def init_app(cls, app):
        cloudinary.config(cloud_name=cls.CLOUD_NAME, api_key=cls.CLOUD_API_KEY, api_secret=cls.CLOUD_SECRET)


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
    FLASK_DEBUG = False
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
