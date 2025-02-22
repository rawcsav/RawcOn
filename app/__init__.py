import os

from flask import Flask, request, Response, jsonify
from flask_assets import Environment
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.errors import RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer

from app.celery_app import celery
from app.util.logging_util import get_logger, notify_error
from config import ProductionConfig, DevelopmentConfig

logger = get_logger(__name__)

db = SQLAlchemy()
bcrypt = Bcrypt()
cors = CORS()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
sess = Session()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    flask_env = os.getenv("FLASK_ENV", "production").lower()

    if flask_env == "development":
        app.config.from_object(DevelopmentConfig)
        DevelopmentConfig.init_app(app)
    else:
        app.config.from_object(ProductionConfig)
        ProductionConfig.init_app(app)

    app.serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

    assets = Environment(app)
    CORS(app)
    csrf.init_app(app)
    db.init_app(app)
    Migrate(app, db)
    bcrypt.init_app(app)
    assets.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    sess.init_app(app)

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

        if os.getenv("FLASK_ENV") == "development":

            @app.route("/trigger/update-stale-users", methods=["POST"])
            @csrf.exempt
            def trigger_update_stale_user_data():
                celery.send_task("tasks.update_stale_user_data")
                return jsonify({"message": "Task update_stale_user_data triggered successfully"}), 202

            @app.route("/trigger/delete-inactive-users", methods=["POST"])
            @csrf.exempt
            def trigger_delete_inactive_users():
                celery.send_task("tasks.delete_inactive_users")
                return jsonify({"message": "Task delete_inactive_users triggered successfully"}), 202

            @app.route("/trigger/clear-cache")
            @csrf.exempt
            def clear_caches_route():
                cache.clear()
                redis_client = cache.cache._read_client
                redis_client.flushall()
                return "All caches cleared"

            @app.route("/trigger/test-logging")
            @csrf.exempt
            def test_logging():
                logger.info("Flask route logging test - info message")
                logger.error("Flask route logging test - error message")
                notify_error("Flask Test", "This is a test error from Flask route")
                celery.send_task("tasks.test_logging")
                return "Logging tests initiated. Check your logs and email."

        db.create_all()

        def register_error_handlers(app):
            @app.errorhandler(RateLimitExceeded)
            def handle_rate_limit_error(error):
                return jsonify({"message": str(error.description), "type": "warning"})

        register_error_handlers(app)

        return app
