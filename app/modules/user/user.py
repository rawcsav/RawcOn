from datetime import datetime

from flask import Blueprint, render_template, session, request, jsonify
from pytz import timezone

from app import db
from app.models.user_models import UserData
from ..auth.auth_util import fetch_user_data
from app.util.wrappers import require_spotify_auth, handle_errors
from app.modules.auth.auth_util import verify_session
from .user_util import (
    init_session_client,
    check_and_refresh_user_data,
    fetch_and_process_data,
    delete_old_user_data,
    update_user_data,
    get_top_genres,
    get_audio_features_summary,
    get_top_artists_summary,
    get_top_tracks_summary,
    get_recent_tracks_summary,
    get_playlist_summary,
    calculate_averages_for_period,
    get_user_data,
    get_genre_bubble_chart_data,
    get_audio_features_evolution,
    generate_stats_blurbs,
)

user_bp = Blueprint("user", __name__, template_folder="templates", static_folder="static", url_prefix="/user")

eastern = timezone("US/Eastern")


@user_bp.route("/profile")
@handle_errors
@require_spotify_auth
def profile():
    try:
        access_token = verify_session(session)
        res_data = fetch_user_data(access_token)
        spotify_user_id = res_data.get("id")
        spotify_user_display_name = res_data.get("display_name")
        user_market = res_data.get("country")
        session["DISPLAY_NAME"] = spotify_user_display_name
        session["USER_ID"] = spotify_user_id
        session["MARKET"] = user_market

        user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()

        if not user_data_entry or not check_and_refresh_user_data(user_data_entry):
            sp, error = init_session_client()
            if error:
                return error
            time_periods = ["short_term", "medium_term", "long_term"]
            (
                top_tracks,
                top_artists,
                all_artists_info,
                audio_features,
                genre_specific_data,
                sorted_genres_by_period,
                recent_tracks,
                playlist_info,
            ) = fetch_and_process_data(sp, time_periods)

            user_data_entry = UserData(
                spotify_user_id=spotify_user_id,
                top_tracks=top_tracks,
                top_artists=top_artists,
                all_artists_info=all_artists_info,
                audio_features=audio_features,
                genre_specific_data=genre_specific_data,
                sorted_genres_by_period=sorted_genres_by_period,
                recent_tracks=recent_tracks,
                playlist_info=playlist_info,
                last_active=datetime.utcnow(),
            )
            db.session.add(user_data_entry)
            db.session.commit()

        delete_old_user_data()

        # Calculate period data for stats
        time_periods = ["short_term", "medium_term", "long_term", "overall"]
        period_data = {}

        for period in time_periods:
            period_tracks = (
                user_data_entry.top_tracks[period]
                if period != "overall"
                else {"items": [track for sublist in user_data_entry.top_tracks.values() for track in sublist["items"]]}
            )
            period_data[period] = {}
            (
                period_data[period]["averages"],
                period_data[period]["min_track"],
                period_data[period]["max_track"],
                period_data[period]["min_values"],
                period_data[period]["max_values"],
            ) = calculate_averages_for_period(period_tracks, user_data_entry.audio_features)

        # Prepare additional data for the profile page
        top_genres = {period: get_top_genres(user_data_entry, period) for period in time_periods[:3]}
        audio_features_summary = {
            period: get_audio_features_summary(user_data_entry, period) for period in time_periods[:3]
        }
        top_artists_summary = {period: get_top_artists_summary(user_data_entry, period) for period in time_periods[:3]}
        top_tracks_summary = {period: get_top_tracks_summary(user_data_entry, period) for period in time_periods[:3]}
        recent_tracks_summary = get_recent_tracks_summary(user_data_entry)
        playlist_summary = get_playlist_summary(user_data_entry)
        stats_blurbs = generate_stats_blurbs(audio_features_summary, top_genres)

        return render_template(
            "profile.html",
            user_data=res_data,
            tokens=session.get("tokens"),
            period_data=period_data,
            top_genres=top_genres,
            genre_specific_data=user_data_entry.genre_specific_data,
            audio_features_summary=audio_features_summary,
            top_artists_summary=top_artists_summary,
            top_tracks_summary=top_tracks_summary,
            recent_tracks_summary=recent_tracks_summary,
            playlist_summary=playlist_summary,
            stats_blurbs=stats_blurbs,
        )

    except Exception as e:
        print(f"An error occurred: {e}")
        return str(e), 500


@user_bp.route("/refresh-data", methods=["POST"])
@handle_errors
@require_spotify_auth
def refresh_data():
    try:
        access_token = verify_session(session)
        res_data = fetch_user_data(access_token)
        spotify_user_id = res_data.get("id")
        session["USER_ID"] = spotify_user_id

        user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()
        if user_data_entry:
            update_user_data(user_data_entry)
            return jsonify({"message": "User Refreshed Successfully!"}), 200
        else:
            return jsonify({"error": "User data not found"}), 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/get_mode", methods=["GET"])
@require_spotify_auth
def get_mode():
    try:
        user_data = get_user_data()
        mode = "dark" if user_data.isDarkMode else "light"
        return jsonify({"mode": mode})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/update_mode", methods=["POST"])
@handle_errors
@require_spotify_auth
def update_mode():
    try:
        mode = request.json.get("mode")
        user_data = get_user_data()
        user_data.isDarkMode = mode == "dark"
        db.session.commit()
        return jsonify({"message": "Mode updated successfully!"}), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/top_genres/<time_range>")
@handle_errors
@require_spotify_auth
def top_genres(time_range):
    try:
        user_data = get_user_data()
        genres = get_top_genres(user_data, time_range)
        return jsonify(genres)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/genre_data/<period>/<genre>")
@handle_errors
@require_spotify_auth
def genre_data(period, genre):
    user_data = get_user_data()
    genre_data = user_data.genre_specific_data.get(period, {}).get(genre, {})
    return jsonify(genre_data)


@user_bp.route("/audio_features/<time_range>")
@handle_errors
@require_spotify_auth
def audio_features(time_range):
    try:
        user_data = get_user_data()
        features = get_audio_features_summary(user_data, time_range)
        return jsonify(features)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/top_artists/<time_range>")
@handle_errors
@require_spotify_auth
def top_artists(time_range):
    try:
        user_data = get_user_data()
        artists = get_top_artists_summary(user_data, time_range)
        return jsonify(artists)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/top_tracks/<time_range>")
@handle_errors
@require_spotify_auth
def top_tracks(time_range):
    try:
        user_data = get_user_data()
        tracks = get_top_tracks_summary(user_data, time_range)
        return jsonify(tracks)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/recent_tracks")
@handle_errors
@require_spotify_auth
def recent_tracks():
    try:
        user_data = get_user_data()
        tracks = get_recent_tracks_summary(user_data)
        return jsonify(tracks)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/playlists")
@handle_errors
@require_spotify_auth
def playlists():
    try:
        user_data = get_user_data()
        playlist_summary = get_playlist_summary(user_data)
        return jsonify(playlist_summary)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/genre_bubble_chart")
@handle_errors
@require_spotify_auth
def genre_bubble_chart():
    try:
        user_data = get_user_data()
        bubble_chart_data = get_genre_bubble_chart_data(user_data)
        return jsonify(bubble_chart_data)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/audio_features_evolution")
@handle_errors
@require_spotify_auth
def audio_features_evolution():
    try:
        user_data = get_user_data()
        evolution_data = get_audio_features_evolution(user_data)
        return jsonify(evolution_data)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/stats_blurbs")
@handle_errors
@require_spotify_auth
def get_stats_blurbs():
    user_data = get_user_data()
    audio_features_summary = {
        period: get_audio_features_summary(user_data, period) for period in ["short_term", "medium_term", "long_term"]
    }

    top_genres = {period: get_top_genres(user_data, period) for period in ["short_term", "medium_term", "long_term"]}

    stats_blurbs = generate_stats_blurbs(audio_features_summary, top_genres)

    return jsonify({"blurbs": stats_blurbs})
