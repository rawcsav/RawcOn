from flask import Blueprint, render_template, session, redirect, url_for, request

from app import limiter
from app.models.user_models import UserData
from app.modules.auth.auth_util import fetch_user_data, verify_session
from app.modules.playlists.playlist_util import (
    get_playlist_data,
    update_playlist_data,
    like_all_songs,
    unlike_all_songs,
    remove_duplicates,
    reorder_playlist,
    get_playlist_recommendations,
)
from app.util.wrappers import require_spotify_auth

playlist_bp = Blueprint(
    "playlist", __name__, template_folder="templates", static_folder="static", url_prefix="/playlist"
)


@playlist_bp.route("/playlist/<string:playlist_id>")
@limiter.limit("30 per minute")
# @cache.cached(timeout=300)  # Cache for 5 minutes
@require_spotify_auth
def show_playlist(playlist_id):
    access_token = verify_session(session)
    spotify_user_id = session["USER_ID"]
    user_data = fetch_user_data(access_token)
    user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()

    playlist_data = get_playlist_data(playlist_id, spotify_user_id)
    if not playlist_data:
        return "Playlist not found", 404

    return render_template("playlist.html", **playlist_data, user_data=user_data)


@playlist_bp.route("/playlist/<string:playlist_id>/refresh", methods=["POST"])
@limiter.limit("2 per minute")
@require_spotify_auth
def refresh_playlist(playlist_id):
    spotify_user_id = session["USER_ID"]
    result = update_playlist_data(playlist_id, spotify_user_id)
    if isinstance(result, tuple):
        return result
    return redirect(url_for("playlist.show_playlist", playlist_id=playlist_id))


@playlist_bp.route("/like_all_songs/<playlist_id>")
@limiter.limit("5 per minute")
@require_spotify_auth
def route_like_all_songs(playlist_id):
    return like_all_songs(playlist_id)


@playlist_bp.route("/unlike_all_songs/<playlist_id>")
@limiter.limit("5 per minute")
@require_spotify_auth
def route_unlike_all_songs(playlist_id):
    return unlike_all_songs(playlist_id)


@playlist_bp.route("/remove_duplicates/<playlist_id>")
@limiter.limit("5 per minute")
@require_spotify_auth
def route_remove_duplicates(playlist_id):
    result = remove_duplicates(playlist_id)
    if isinstance(result, tuple):
        return result
    return redirect(url_for("playlist.show_playlist", playlist_id=playlist_id))


@playlist_bp.route("/playlist/<string:playlist_id>/reorder", methods=["POST"])
@limiter.limit("3 per minute")
@require_spotify_auth
def route_reorder_playlist(playlist_id):
    sorting_criterion = request.json.get("sorting_criterion")
    return reorder_playlist(playlist_id, sorting_criterion)


@playlist_bp.route("/get_pl_recommendations/<string:playlist_id>/recommendations", methods=["POST"])
@limiter.limit("3 per minute")
@require_spotify_auth
def route_get_pl_recommendations(playlist_id):
    return get_playlist_recommendations(playlist_id)
