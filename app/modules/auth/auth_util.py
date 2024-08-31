import secrets
import string

import requests
from flask import abort, current_app


def verify_session(session):
    if "tokens" not in session:
        abort(400)
    return session["tokens"].get("access_token")


def generate_state():
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))


def prepare_auth_payload(state, scope, show_dialog=False):
    payload = {
        "client_id": current_app.config["CLIENT_ID"],
        "response_type": "code",
        "redirect_uri": current_app.config["REDIRECT_URI"],
        "state": state,
        "scope": scope,
    }
    if show_dialog:
        payload["show_dialog"] = True
    return payload


def request_tokens(payload):
    res = requests.post(
        current_app.config["TOKEN_URL"],
        auth=(current_app.config["CLIENT_ID"], current_app.config["CLIENT_SECRET"]),
        data=payload,
    )
    res_data = res.json()
    if res_data.get("error") or res.status_code != 200:
        return None, res.status_code
    return res_data, None


def fetch_user_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(current_app.config["ME_URL"], headers=headers)
    if res.status_code != 200:
        abort(res.status_code)

    return res.json()


def get_spotify_user_id(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)

    if response.status_code == 200:
        user_data = response.json()
        return user_data["id"]
    else:
        current_app.logger.error(f"Failed to fetch Spotify user ID. Status code: {response.status_code}")
        return None
