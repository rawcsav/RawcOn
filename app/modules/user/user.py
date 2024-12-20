from datetime import datetime

from flask import Blueprint, render_template, session, jsonify
from pytz import timezone

from app import db, limiter
from app.models.user_models import UserData
from app.modules.auth.auth_util import verify_session
from app.util.logging_util import get_logger
from app.util.wrappers import require_spotify_auth, handle_errors
from .user_util import (
    init_session_client,
    fetch_and_process_data,
    get_top_genres,
    get_audio_features_summary,
    get_top_artists_summary,
    get_top_tracks_summary,
    get_playlist_summary,
    calculate_averages_for_period,
    get_user_data,
    get_genre_bubble_chart_data,
    get_audio_features_evolution,
    generate_stats_blurbs,
)
from ..auth.auth_util import fetch_user_data

logger = get_logger(__name__)

user_bp = Blueprint("user", __name__, template_folder="templates", static_folder="static", url_prefix="/user")

eastern = timezone("US/Eastern")


@user_bp.route("/profile")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def profile():
    try:
        access_token = verify_session(session)
        res_data = fetch_user_data(access_token)
        spotify_user_id = session["USER_ID"]

        user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()

        if not user_data_entry or user_data_entry.new_account:
            sp, error = init_session_client()
            if error:
                logger.error(f"Failed to initialize Spotify client for user {spotify_user_id}: {error}")
                return error
            time_periods = ["short_term", "medium_term", "long_term"]
            (
                top_tracks,
                top_artists,
                all_artists_info,
                audio_features,
                genre_specific_data,
                sorted_genres_by_period,
                playlist_info,
            ) = fetch_and_process_data(sp, time_periods)

            if not user_data_entry:
                logger.info(f"Creating new user data entry for {spotify_user_id}")
                user_data_entry = UserData(spotify_user_id=spotify_user_id)
                db.session.add(user_data_entry)

            user_data_entry.top_tracks = top_tracks
            user_data_entry.top_artists = top_artists
            user_data_entry.all_artists_info = all_artists_info
            user_data_entry.audio_features = audio_features
            user_data_entry.genre_specific_data = genre_specific_data
            user_data_entry.sorted_genres_by_period = sorted_genres_by_period
            user_data_entry.playlist_info = playlist_info
            user_data_entry.last_active = datetime.utcnow()
            user_data_entry.new_account = False

            db.session.commit()

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

        top_genres = {period: get_top_genres(user_data_entry, period) for period in time_periods[:3]}
        audio_features_summary = {
            period: get_audio_features_summary(user_data_entry, period) for period in time_periods[:3]
        }
        top_artists_summary = {period: get_top_artists_summary(user_data_entry, period) for period in time_periods[:3]}
        top_tracks_summary = {period: get_top_tracks_summary(user_data_entry, period) for period in time_periods[:3]}
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
            playlist_summary=playlist_summary,
            stats_blurbs=stats_blurbs,
        )

    except Exception as e:
        logger.error(f"An error occurred while loading a user's profile: {e}")
        db.session.rollback()
        return str(e), 500


@user_bp.route("/top_genres/<time_range>")
@handle_errors
@require_spotify_auth
def top_genres(time_range):
    try:
        user_data = get_user_data()
        genres = get_top_genres(user_data, time_range)
        return jsonify(genres)
    except Exception as e:
        logger.error(f"An error ocurred while gathering a user's top genres: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/genre_data/<period>/<genre>")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def genre_data(period, genre):
    user_data = get_user_data()
    genre_data = user_data.genre_specific_data.get(period, {}).get(genre, {})
    return jsonify(genre_data)


@user_bp.route("/audio_features/<time_range>")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def audio_features(time_range):
    try:
        user_data = get_user_data()
        features = get_audio_features_summary(user_data, time_range)
        return jsonify(features)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@user_bp.route("/top_artists/<time_range>")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def top_artists(time_range):
    try:
        user_data = get_user_data()
        artists = get_top_artists_summary(user_data, time_range)
        return jsonify(artists)
    except Exception as e:
        logger.error(f"An error ocurred while fetching a user's top artists: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/top_tracks/<time_range>")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def top_tracks(time_range):
    try:
        user_data = get_user_data()
        tracks = get_top_tracks_summary(user_data, time_range)
        return jsonify(tracks)
    except Exception as e:
        logger.error(f"An error occurred while fetching a user's top tracks: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/playlists")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def playlists():
    try:
        user_data = get_user_data()
        playlist_summary = get_playlist_summary(user_data)
        return jsonify(playlist_summary)
    except Exception as e:
        logger.error(f"An error occurred while fetching a user's playlists: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/genre_bubble_chart")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def genre_bubble_chart():
    try:
        user_data = get_user_data()
        bubble_chart_data = get_genre_bubble_chart_data(user_data)
        return jsonify(bubble_chart_data)
    except Exception as e:
        logger.error(f"An error occurred while generating a user's genre chart: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/audio_features_evolution")
@limiter.limit("30 per minute")
@handle_errors
@require_spotify_auth
def audio_features_evolution():
    try:
        user_data = get_user_data()
        evolution_data = get_audio_features_evolution(user_data)
        return jsonify(evolution_data)
    except Exception as e:
        logger.error(f"An error occurred while fetching a user's audio features chart: {e}")
        return jsonify({"error": str(e)}), 500


@user_bp.route("/stats_blurbs")
@limiter.limit("30 per minute")
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
