import traceback
from datetime import datetime, timedelta
from flask import session, redirect, url_for, request, current_app, flash
from app.util.logging_util import get_logger
from functools import wraps
from flask import jsonify

logger = get_logger(__name__)


def require_spotify_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "tokens" not in session or not session.get("tokens", {}).get("access_token"):
            flash("Please authenticate and try again.", "error")
            return redirect(url_for("auth.index"))

        now = datetime.now()
        tokens = session.get("tokens", {})
        try:
            expiry_time = datetime.fromisoformat(tokens.get("expiry_time", "2000-01-01"))
            if now >= expiry_time - timedelta(minutes=5):
                return redirect(url_for("auth.refresh", next=request.url))
        except (TypeError, ValueError):
            flash("Please authenticate and try again.", "error")
            return redirect(url_for("auth.index"))

        return f(*args, **kwargs)

    return decorated_function


def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            app_trace = next((t for t in tb if "site-packages" not in t.filename), None)
            if app_trace:
                filename = app_trace.filename
                line_number = app_trace.lineno
                function_name = app_trace.name
                line_content = app_trace.line
            else:
                filename = "Unknown"
                line_number = "Unknown"
                function_name = "Unknown"
                line_content = "Unknown"

            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file": filename,
                "line": line_number,
                "function": function_name,
                "code": line_content,
            }

            # Log the error
            current_app.logger.error(f"Error in {function_name} ({filename}:{line_number}): {str(e)}")
            current_app.logger.error(f"Problematic code: {line_content}")

            if current_app.debug:
                error_details["full_traceback"] = traceback.format_exc()

            return jsonify(error_details), 500

    return decorated_function
