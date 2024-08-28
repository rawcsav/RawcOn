import os
from flask import Flask, request, Response
from flask_assets import Environment
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer
from config import ProductionConfig, DevelopmentConfig
from flask_cors import CORS

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)


def country_flag(country_code):
    OFFSET = 127397
    return "".join(chr(ord(char) + OFFSET) for char in country_code.upper())


def create_app():
    app = Flask(__name__)
    flask_env = os.getenv("FLASK_ENV", "production").lower()
    app.jinja_env.filters["country_flag"] = country_flag

    if flask_env == "development":
        app.config.from_object(DevelopmentConfig)
        DevelopmentConfig.init_app(app)
    else:
        app.config.from_object(ProductionConfig)
        ProductionConfig.init_app(app)

    app.serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    assets = Environment(app)
    CORS(app)
    CSRFProtect(app)
    db.init_app(app)
    Migrate(app, db)
    bcrypt.init_app(app)
    assets.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        from app.modules.auth import auth
        from app.modules.user import user
        from app.modules.recs import recs
        from app.modules.playlists import playlist

        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(user.user_bp)
        app.register_blueprint(recs.recs_bp)
        app.register_blueprint(playlist.playlist_bp)

        from app.util.assets_util import compile_static_assets

        compile_static_assets(assets)

        @app.before_request
        def basic_authentication():
            if request.method.lower() == "options":
                return Response()

        @app.teardown_request
        def session_teardown(exception=None):
            if exception:
                db.session.rollback()
            db.session.remove()

        db.create_all()
        return app
