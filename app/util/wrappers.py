from datetime import datetime
from functools import wraps
import logging

from flask import session, redirect, url_for, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def require_spotify_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tokens = session.get("tokens")
        expiry_time = datetime.fromisoformat(tokens.get("expiry_time")) if tokens else None

        if not tokens:
            return redirect(url_for("auth.index"))

        if expiry_time and expiry_time < datetime.now():
            session["original_request_url"] = request.url
            return redirect(url_for("auth.refresh"))

        return f(*args, **kwargs)

    return decorated_function


from functools import wraps
from flask import jsonify


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Log the full exception with traceback
            logging.exception(f"An error occurred in {f.__name__}:")
            # Return a JSON response with the error message
            return jsonify({"error": str(e)}), 500

    return decorated_function


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "tokens" not in session:
            return redirect(url_for("auth.index"))

        expiry_time = datetime.fromisoformat(session["tokens"]["expiry_time"])
        if datetime.now() > expiry_time:
            return redirect(url_for("auth.refresh"))

        return f(*args, **kwargs)

    return decorated
