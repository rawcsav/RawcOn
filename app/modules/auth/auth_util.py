import base64
import hashlib
import os
import re
import secrets
import string
from datetime import timezone, timedelta, datetime
import requests
from flask import abort, session, current_app


def verify_session(session):
    if "tokens" not in session:
        abort(400)
    return session["tokens"].get("access_token")


def generate_state():
    return "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(16))


def prepare_auth_payload(state, scope, code_challenge, show_dialog=False):
    payload = {
        "client_id": current_app.config["CLIENT_ID"],
        "response_type": "code",
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "redirect_uri": current_app.config["REDIRECT_URI"],
        "state": state,
        "scope": scope,
    }
    if show_dialog:
        payload["show_dialog"] = True
    return payload


def request_tokens(payload):
    res = requests.post(current_app.config["TOKEN_URL"], data=payload)
    res_data = res.json()
    if res_data.get("error") or res.status_code != 200:
        return None, res.status_code
    return res_data, None


def fetch_user_data(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    res = requests.get(current_app.config["ME_URL"], headers=headers)
    if res.status_code != 200:
        abort(res.status_code)

    print(res.json())
    return res.json()


def generate_code_verifier():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).decode("utf-8")
    code_verifier = re.sub("[^a-zA-Z0-9]+", "", code_verifier)
    return code_verifier


def generate_code_challenge(code_verifier):
    code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
    code_challenge = code_challenge.replace("=", "")
    return code_challenge
