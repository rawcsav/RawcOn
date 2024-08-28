import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from flask import Blueprint, abort, redirect, render_template, request, session, url_for, current_app
from flask import make_response
from app import cache, limiter

from app.modules.auth.auth_util import generate_state, prepare_auth_payload, request_tokens
from app.util.wrappers import handle_errors

auth_bp = Blueprint("auth", __name__, template_folder="templates", static_folder="static", url_prefix="/")


@auth_bp.route("/")
@cache.cached(timeout=3600)  # Cache for 1 hour
@handle_errors
def index():
    return render_template("landing.html")


@auth_bp.route("/<loginout>")
@limiter.limit("10 per minute")
@handle_errors
def login(loginout):
    if loginout == "logout":
        session.clear()
        session["show_dialog"] = True
        session.pop("spotify_auth_state", None)

        return redirect(url_for("auth.index"))

    # If the path is login, handle the login logic.
    state = generate_state()
    time.sleep(1)
    scope = " ".join(
        [
            "user-read-private",
            "user-top-read",
            "user-read-recently-played",
            "playlist-read-private",
            "playlist-read-collaborative",
            "playlist-modify-private",
            "playlist-modify-public",
            "user-library-modify",
            "user-library-read",
            "ugc-image-upload",
        ]
    )

    # Check if we're supposed to show the dialog (this would be set upon logout).
    show_dialog = session.pop("show_dialog", False)
    payload = prepare_auth_payload(state, scope, show_dialog=show_dialog)
    # Redirect the user to Spotify's authorization URL.
    res = make_response(redirect(f'{current_app.config["AUTH_URL"]}/?{urlencode(payload)}'))
    session["spotify_auth_state"] = state

    return res


@auth_bp.route("/callback")
@limiter.limit("10 per minute")
@handle_errors
def callback():
    state = request.args.get("state")
    stored_state = session.get("spotify_auth_state")
    if state is None or state != stored_state:
        abort(400, description="State mismatch")
    print("passed")
    code = request.args.get("code")
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": current_app.config["REDIRECT_URI"],
        "client_id": current_app.config["CLIENT_ID"],
    }

    res_data, error = request_tokens(payload)
    if error:
        abort(400, description="Error obtaining tokens from Spotify")

    access_token = res_data.get("access_token")
    expires_in = res_data.get("expires_in")
    expiry_time = datetime.now() + timedelta(seconds=expires_in)

    session["tokens"] = {
        "access_token": access_token,
        "refresh_token": res_data.get("refresh_token"),
        "expiry_time": expiry_time.isoformat(),
    }
    time.sleep(1)
    return redirect(url_for("user.profile"))


@auth_bp.route("/refresh")
@limiter.limit("5 per minute")
def refresh():
    next_url = request.args.get("next") or url_for("user.profile")

    # Implement a cooldown to prevent rapid successive refreshes
    last_refresh = session.get("last_refresh_time")
    if last_refresh and datetime.now() - datetime.fromisoformat(last_refresh) < timedelta(seconds=30):
        current_app.logger.warning("Refresh attempt too soon after last refresh")
        return redirect(next_url)

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session["tokens"]["refresh_token"],
        "client_id": current_app.config["CLIENT_ID"],
        "client_secret": current_app.config["CLIENT_SECRET"],
    }

    res_data, error = request_tokens(payload)
    if error:
        current_app.logger.error(f"Token refresh failed: {error}")
        return redirect(url_for("auth.login"))

    # Update session with new token info
    session["tokens"] = {
        "access_token": res_data["access_token"],
        "refresh_token": res_data.get("refresh_token", session["tokens"]["refresh_token"]),
        "expiry_time": (datetime.now() + timedelta(seconds=res_data["expires_in"])).isoformat(),
    }
    session["last_refresh_time"] = datetime.now().isoformat()

    return redirect(next_url)


@auth_bp.route("/terms")
@cache.cached(timeout=3600)  # Cache for 1 hour
@handle_errors
def terms():
    return render_template("terms.html")
