from flask import Blueprint, render_template, jsonify, session

from app.models.user_models import UserData
from modules.auth.auth_util import fetch_user_data
from util.wrappers import require_spotify_auth
from app.modules.user.user_util import calculate_averages_for_period
from app.modules.auth.auth_util import verify_session

stats_bp = Blueprint("stats", __name__, template_folder="templates", static_folder="static", url_prefix="/stats")


@stats_bp.route("/stats")
@require_spotify_auth
def stats():
    spotify_user_id = session["USER_ID"]
    access_token = verify_session(session)
    res_data = fetch_user_data(access_token)

    user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()

    if not user_data_entry:
        return jsonify(error="User data not found"), 404
    time_periods = ["short_term", "medium_term", "long_term"]

    top_tracks = {period: user_data_entry.top_tracks.get(period, {}) for period in time_periods}
    top_artists = {period: user_data_entry.top_artists.get(period, {}) for period in time_periods}
    sorted_genres_by_period = {
        period: user_data_entry.sorted_genres_by_period.get(period, {}) for period in time_periods
    }
    genre_specific_data = {period: user_data_entry.genre_specific_data.get(period, {}) for period in time_periods}

    audio_features = user_data_entry.audio_features

    period_data = {}
    time_periods = ["short_term", "medium_term", "long_term", "overall"]

    for period in time_periods:
        period_tracks = (
            top_tracks[period]
            if period != "overall"
            else {"items": [track for sublist in top_tracks.values() for track in sublist["items"]]}
        )
        period_data[period] = {}
        (
            period_data[period]["averages"],
            period_data[period]["min_track"],
            period_data[period]["max_track"],
            period_data[period]["min_values"],
            period_data[period]["max_values"],
        ) = calculate_averages_for_period(period_tracks, audio_features)
    return render_template(
        "stats.html",
        data=res_data,
        top_tracks=top_tracks,
        top_artists=top_artists,
        sorted_genres=sorted_genres_by_period,
        genre_specific_data=genre_specific_data,
        user_data=user_data_entry,
        period_data=period_data,
    )
