from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlencode
from flask import Blueprint, abort, redirect, render_template, request, session, url_for, jsonify, current_app
from flask import make_response


from app.modules.auth.auth_util import generate_state, prepare_auth_payload, request_tokens, fetch_user_data

auth_bp = Blueprint("auth", __name__, template_folder="templates", static_folder="static", url_prefix="/")


@auth_bp.route("/")
def index():
    return render_template("landing.html")


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


@auth_bp.route("/<loginout>")
def login(loginout):
    # If the path is logout, clear the session and return to the index page.
    if loginout == "logout":
        session.clear()
        # Optionally, if you want to force re-authentication on Spotify's side next time,
        # you could set `show_dialog=True` for the next login attempt.
        session["show_dialog"] = True
        # You also might want to clear the spotify_auth_state cookie if it's not needed anymore.
        response = make_response(redirect(url_for("auth.index")))
        response.set_cookie("spotify_auth_state", "", expires=0, path="/")
        return response

    # If the path is login, handle the login logic.
    state = generate_state()
    scope = " ".join(
        [
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

    # Prepare the payload for authentication.
    payload = prepare_auth_payload(state, scope, show_dialog=show_dialog)

    # Redirect the user to Spotify's authorization URL.
    res = make_response(redirect(f'{current_app.config["AUTH_URL"]}/?{urlencode(payload)}'))
    res.set_cookie("spotify_auth_state", state)

    return res


@auth_bp.route("/callback")
def callback():
    state = request.args.get("state")
    stored_state = request.cookies.get("spotify_auth_state")

    if state is None or state != stored_state:
        abort(400, description="State mismatch")

    code = request.args.get("code")
    payload = {"grant_type": "authorization_code", "code": code, "redirect_uri": current_app.config["REDIRECT_URI"]}

    res_data, error = request_tokens(payload, current_app.config["CLIENT_ID"], current_app.config["CLIENT_SECRET"])
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

    return redirect(url_for("user.profile"))


@auth_bp.route("/refresh")
def refresh():
    payload = {"grant_type": "refresh_token", "refresh_token": session.get("tokens").get("refresh_token")}

    res_data, error = request_tokens(payload, current_app.config["CLIENT_ID"], current_app.config["CLIENT_SECRET"])
    if error:
        return redirect(url_for("auth.index"))

    new_access_token = res_data.get("access_token")
    new_refresh_token = res_data.get("refresh_token", session["tokens"]["refresh_token"])
    expires_in = res_data.get("expires_in")
    new_expiry_time = datetime.now() + timedelta(seconds=expires_in)

    session["tokens"].update(
        {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expiry_time": new_expiry_time.isoformat(),
        }
    )

    return redirect(session.pop("original_request_url", url_for("user.profile")))
