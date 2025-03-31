import time
from datetime import datetime, timedelta
from urllib.parse import urlencode

from flask import Blueprint, redirect, render_template, request, session, url_for, current_app, jsonify, flash
from flask import make_response

from app import limiter
from app.modules.auth.auth_util import (
    generate_state,
    prepare_auth_payload,
    request_tokens,
    get_spotify_user_id,
    fetch_user_data,
)
from app.util.database_util import save_tokens_to_db
from app.util.wrappers import handle_errors

auth_bp = Blueprint("auth", __name__, template_folder="templates", static_folder="static", url_prefix="/")


@auth_bp.route("/")
# @cache.cached(timeout=3600)  # Cache for 1 hour
@handle_errors
def index():
    show_eula_modal = not session.get("eula_agreed", False)
    return render_template("landing.html", show_eula_modal=show_eula_modal)


@auth_bp.route("/accept_eula", methods=["POST"])
@handle_errors
def accept_eula():
    session["eula_agreed"] = True
    return jsonify({"success": True})


@auth_bp.route("/<loginout>")
@limiter.limit("10 per minute")
@handle_errors
def login(loginout):
    if loginout == "logout":
        session.clear()
        session["show_dialog"] = True
        session.pop("spotify_auth_state", None)
        return redirect(url_for("auth.index"))

    state = generate_state()
    time.sleep(1)
    scope = " ".join(
        [
            "user-read-private",
            "user-top-read",
            "playlist-read-private",
            "playlist-read-collaborative",
            "playlist-modify-private",
            "playlist-modify-public",
            "user-library-modify",
            "user-library-read",
        ]
    )

    show_dialog = session.pop("show_dialog", False)
    payload = prepare_auth_payload(state, scope, show_dialog=show_dialog)
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
        session.pop("spotify_auth_state", None)
        session["show_dialog"] = True
        current_app.logger.error("State mismatch in Spotify callback")
        flash("Authentication error. Please try again.", "error")
        return redirect(url_for("auth.index"))

    # Check for Spotify's error response
    error = request.args.get("error")
    if error:
        session["show_dialog"] = True
        current_app.logger.error(f"Spotify authentication error: {error}")
        flash(f"Spotify authentication failed: {error}", "error")
        return redirect(url_for("auth.index"))

    code = request.args.get("code")
    if not code:
        session["show_dialog"] = True
        current_app.logger.error("No authorization code received from Spotify")
        flash("Authentication failed. No authorization code received.", "error")
        return redirect(url_for("auth.index"))

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": current_app.config["REDIRECT_URI"],
        "client_id": current_app.config["CLIENT_ID"],
    }
    try:
        res_data, error = request_tokens(payload)
        if error:
            session["show_dialog"] = True
            current_app.logger.error(f"Token request error: {error}")
            flash(f"Failed to obtain tokens: {error}", "error")
            return redirect(url_for("auth.index"))

        # Validate token response
        if not res_data.get("access_token"):
            session["show_dialog"] = True
            current_app.logger.error("No access token in Spotify response")
            flash("Authentication failed. No access token received.", "error")
            return redirect(url_for("auth.index"))

        access_token = res_data.get("access_token")
        expires_in = res_data.get("expires_in")
        expiry_time = datetime.now() + timedelta(seconds=expires_in)
        refresh_token = res_data.get("refresh_token")

        # Validate refresh token
        if not refresh_token:
            current_app.logger.warning("No refresh token received. Using existing or generating new.")
            refresh_token = session.get("tokens", {}).get("refresh_token")

        session["tokens"] = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expiry_time": expiry_time.isoformat(),
        }

        try:
            user_data = fetch_user_data(access_token)
            spotify_user_id = user_data.get("id")
            spotify_user_display_name = user_data.get("display_name")
            user_market = user_data.get("country")
            session["DISPLAY_NAME"] = spotify_user_display_name
            session["USER_ID"] = spotify_user_id
            session["MARKET"] = user_market
            save_tokens_to_db(spotify_user_id, access_token, refresh_token, expiry_time.isoformat())
        except Exception as user_id_error:
            current_app.logger.error(f"Failed to fetch or save user ID: {user_id_error}")
            flash("Unable to complete authentication. Please try again.", "error")
            return redirect(url_for("auth.index"))

        # Clear the stored state
        session.pop("spotify_auth_state", None)

        return redirect(url_for("user.profile"))

    except Exception as e:
        session["show_dialog"] = True
        current_app.logger.error(f"Unexpected authentication error: {e}")
        flash("An unexpected error occurred during authentication.", "error")
        return redirect(url_for("auth.index"))


@auth_bp.route("/refresh")
@limiter.limit("20 per minute")
@handle_errors
def refresh():
    next_url = request.args.get("next") or url_for("user.profile")

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

    session["tokens"] = {
        "access_token": res_data["access_token"],
        "refresh_token": res_data.get("refresh_token", session["tokens"]["refresh_token"]),
        "expiry_time": (datetime.now() + timedelta(seconds=res_data["expires_in"])).isoformat(),
    }
    session["last_refresh_time"] = datetime.now().isoformat()
    user_id = get_spotify_user_id(access_token=res_data["access_token"])
    save_tokens_to_db(
        user_id,
        access_token=res_data["access_token"],
        refresh_token=res_data.get("refresh_token", session["tokens"]["refresh_token"]),
        expiry_time=(datetime.now() + timedelta(seconds=res_data["expires_in"])).isoformat(),
    )
    return redirect(next_url)


@auth_bp.route("/terms")
# @cache.cached(timeout=3600)  # Cache for 1 hour
@handle_errors
def terms():
    is_logged_in = "tokens" in session and session["tokens"].get("access_token")
    show_eula_modal = not session.get("eula_agreed", False)
    return render_template("terms.html", logged_in=is_logged_in, show_eula_modal=show_eula_modal)
