import json

from flask import Blueprint, jsonify, render_template, request, session, json

from app import db, limiter
from app.models.user_models import UserData
from app.modules.auth.auth_util import fetch_user_data
from app.modules.auth.auth_util import verify_session
from app.modules.recs.recs_util import spotify_search, get_recommendations
from app.modules.user.user_util import init_session_client, format_track_info, get_playlist_summary
from app.util.database_util import add_artist_to_db
from app.util.logging_util import get_logger
from app.util.wrappers import require_spotify_auth

logger = get_logger(__name__)

recs_bp = Blueprint("recs", __name__, template_folder="templates", static_folder="static", url_prefix="/recs")


def parse_seeds(key):
    return [item.strip() for item in request.form.get(f"{key}_seeds", "").split(",") if item.strip()] or None


@recs_bp.route("/recommendations", methods=["GET"])
@limiter.limit("5 per minute")
# @cache.cached(timeout=300)  # Cache for 5 minutes
@require_spotify_auth
def recommendations():
    spotify_user_id = session["USER_ID"]
    access_token = verify_session(session)
    res_data = fetch_user_data(access_token)

    user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()
    playlist_summary = get_playlist_summary(user_data_entry)

    if not user_data_entry:
        return jsonify(error="User data not found"), 404

    return render_template(
        "recommendations.html", user_data=res_data, data=user_data_entry, playlist_summary=playlist_summary
    )


@recs_bp.route("/get_recommendations", methods=["POST"])
@limiter.limit("5 per minute")
@require_spotify_auth
def get_recommendations_route():
    sp, error = init_session_client()
    if error:
        return jsonify(error), 401

    data = request.get_json()

    seeds = {
        key: [item.strip() for item in data.get(f"{key}_seeds", "").split(",") if item.strip()] or None
        for key in ["track", "artist"]
    }

    limit = data.get("limit", 10)

    sliders = {}
    for key in ["popularity", "energy", "instrumentalness", "tempo", "danceability", "valence"]:
        min_key = f"min_{key}"
        max_key = f"max_{key}"
        if min_key in data and max_key in data:
            if key == "popularity":
                sliders[f"min_{key}"] = int(float(data[min_key]))
                sliders[f"max_{key}"] = int(float(data[max_key]))
            elif key == "tempo":
                sliders[f"min_{key}"] = float(data[min_key])
                sliders[f"max_{key}"] = float(data[max_key])
            else:
                sliders[f"min_{key}"] = float(data[min_key])
                sliders[f"max_{key}"] = float(data[max_key])
    user_market = session.get("MARKET", "US")  # Default to "US" if not set

    recommendations_data = get_recommendations(sp, **seeds, limit=limit, **sliders, market=user_market)

    if "error" in recommendations_data:
        logger.error(recommendations_data["error"])
        return jsonify(recommendations_data), 400

    track_info_list = [format_track_info(track) for track in recommendations_data["tracks"]]
    return jsonify({"recommendations": track_info_list})


@recs_bp.route("/save_track", methods=["POST"])
@limiter.limit("5 per minute")
@require_spotify_auth
def save_track():
    sp, error = init_session_client()
    if error:
        logger.error()
        return json.dumps(error), 401

    track_id = request.json["track_id"]

    sp.current_user_saved_tracks_add([track_id])
    return jsonify({"status": "success"})


@recs_bp.route("/add_to_playlist", methods=["POST"])
@limiter.limit("25 per minute")
@require_spotify_auth
def add_to_playlist():
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401

    track_id = request.json["track_id"]
    playlist_id = request.json["playlist_id"]
    sp.playlist_add_items(playlist_id, [track_id])
    return jsonify({"status": "success"})


@recs_bp.route("/unsave_track", methods=["POST"])
@limiter.limit("25 per minute")
@require_spotify_auth
def unsave_track():
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401

    track_id = request.json["track_id"]

    sp.current_user_saved_tracks_delete([track_id])
    return jsonify({"status": "success"})


@recs_bp.route("/remove_from_playlist", methods=["POST"])
@limiter.limit("25 per minute")
@require_spotify_auth
def remove_from_playlist():
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401

    track_id = request.json["track_id"]
    playlist_id = request.json["playlist_id"]

    sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_id])
    return jsonify({"status": "success"})


@recs_bp.route("/search", methods=["POST"])
@limiter.limit("15 per minute")
@require_spotify_auth
def search():
    query = request.json.get("query")
    type = request.json.get("type")
    if not query:
        return json.dumps({"error": "No search query provided"}), 400
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401
    results = spotify_search(sp, query, type)
    if results.get("artists", {}).get("items"):
        for artist_data in results["artists"]["items"]:
            try:
                add_artist_to_db(artist_data)
                db.session.commit()
            except:
                db.session.rollback()
                raise
    return json.dumps(results)


@recs_bp.route("/get-user-playlists")
@limiter.limit("15 per minute")
def get_user_playlists():
    spotify_user_id = session.get("USER_ID")
    if not spotify_user_id:
        return jsonify(error="Session not initialized"), 403

    user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()
    if not user_data_entry:
        return jsonify(error="User data not found"), 404

    owner_name = session.get("DISPLAY_NAME")
    playlists_data = [playlist for playlist in user_data_entry.playlist_info if playlist.get("owner") == owner_name]

    return jsonify(playlists_data)
