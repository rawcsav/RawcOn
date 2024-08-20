from datetime import datetime, timedelta
from functools import wraps
import logging

from flask import session, redirect, url_for, request

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def require_spotify_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = datetime.now()
        tokens = session.get("tokens", {})
        expiry_time = datetime.fromisoformat(tokens.get("expiry_time", "2000-01-01"))
        if now >= expiry_time - timedelta(minutes=5):
            print("expired")
            return redirect(url_for("auth.refresh", next=request.url))

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
