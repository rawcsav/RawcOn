import secrets
import string
from datetime import datetime, timedelta

import requests
from flask import abort, session, current_app


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
