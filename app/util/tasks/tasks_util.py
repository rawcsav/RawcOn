import json
from datetime import datetime, timedelta

import requests
from flask import current_app
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool
from spotipy import Spotify
from app.models.user_models import UserData
from app.modules.user.user_util import fetch_and_process_data
from app.util.logging_util import configure_logging

logger = configure_logging()


def make_engine_with_pool_options():
    database_url = current_app.config["SQLALCHEMY_DATABASE_URI"]
    engine = create_engine(
        database_url, poolclass=QueuePool, pool_recycle=299, pool_pre_ping=True, pool_size=10, max_overflow=20
    )
    return engine


def make_session():
    engine = make_engine_with_pool_options()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return scoped_session(SessionLocal)


def refresh(refresh_token):
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": current_app.config["CLIENT_ID"],
        "client_secret": current_app.config["CLIENT_SECRET"],
    }

    try:
        response = requests.post(current_app.config["TOKEN_URL"], data=payload)
        response.raise_for_status()
        new_token_info = response.json()

        return new_token_info, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Token refresh failed: {str(e)}")
        return None, str(e)


def update_user_data(user_data_entry, sp, session):
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

    user_data_entry.top_tracks = top_tracks
    user_data_entry.top_artists = top_artists
    user_data_entry.all_artists_info = all_artists_info
    user_data_entry.audio_features = audio_features
    user_data_entry.genre_specific_data = genre_specific_data
    user_data_entry.sorted_genres_by_period = sorted_genres_by_period
    user_data_entry.recent_tracks = recent_tracks
    user_data_entry.playlist_info = playlist_info
    print(recent_tracks)
    session.merge(user_data_entry)
    session.commit()

    return "User updated successfully"


def init_session_client_for_celery(user_id):
    db_session = make_session()
    try:
        user = db_session.query(UserData).filter_by(spotify_user_id=user_id).first()
        if not user:
            logger.error(f"User {user_id} not found in database")
            return None, "User not found"

        access_token = user.access_token
        refresh_token = user.refresh_token
        token_expiry = user.token_expiry

        if not access_token or (token_expiry and datetime.utcnow() >= token_expiry):
            refresh_response = refresh(refresh_token)
            if refresh_response.status_code == 200:
                token_info = refresh_response.json()
                user.access_token = token_info.get("access_token")
                user.refresh_token = token_info.get("refresh_token", user.refresh_token)
                user.token_expiry = datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 3600))
                db_session.commit()
                access_token = user.access_token
            else:
                logger.error(f"Failed to refresh token for user {user_id}")
                return None, "Failed to refresh token"

        return Spotify(auth=access_token), None
    except Exception as e:
        logger.error(f"Error initializing Spotify client for user {user_id}: {str(e)}")
        return None, str(e)
    finally:
        db_session.remove()