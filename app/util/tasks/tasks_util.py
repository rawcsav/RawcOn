import json
from datetime import datetime, timedelta
from typing import Tuple, Optional

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
        playlist_info,
    ) = fetch_and_process_data(sp, time_periods)

    user_data_entry.top_tracks = top_tracks
    user_data_entry.top_artists = top_artists
    user_data_entry.all_artists_info = all_artists_info
    user_data_entry.audio_features = audio_features
    user_data_entry.genre_specific_data = genre_specific_data
    user_data_entry.sorted_genres_by_period = sorted_genres_by_period
    user_data_entry.playlist_info = playlist_info
    session.merge(user_data_entry)
    session.commit()

    return "User updated successfully"


def init_session_client_for_celery(user_id: str) -> Tuple[Optional[Spotify], Optional[str]]:
    db_session = make_session()
    try:
        # Get user data
        user = db_session.query(UserData).filter_by(spotify_user_id=user_id).first()
        if not user:
            logger.error(f"User {user_id} not found in database")
            return None, "User not found"

        access_token = user.access_token
        refresh_token = user.refresh_token
        token_expiry = user.token_expiry

        # Check if token needs refresh
        if not access_token or (token_expiry and datetime.utcnow() >= token_expiry):
            token_info, error = refresh(refresh_token)

            if error:
                logger.error(f"Failed to refresh token for user {user_id}: {error}")
                return None, f"Failed to refresh token: {error}"

            if not token_info:
                logger.error(f"No token info returned for user {user_id}")
                return None, "Token refresh failed - no token info returned"

            # Update user tokens
            try:
                user.access_token = token_info["access_token"]
                user.refresh_token = token_info.get("refresh_token", user.refresh_token)
                user.token_expiry = datetime.utcnow() + timedelta(seconds=token_info.get("expires_in", 3600))
                db_session.commit()
                access_token = user.access_token
            except KeyError as e:
                logger.error(f"Missing key in token info for user {user_id}: {e}")
                return None, f"Invalid token info returned: {e}"

        # Initialize Spotify client
        try:
            spotify_client = Spotify(auth=access_token)
            # Verify client is working with a simple API call
            spotify_client.current_user()  # This will raise an exception if token is invalid
            return spotify_client, None
        except Exception as e:
            logger.error(f"Failed to initialize Spotify client for user {user_id}: {e}")
            return None, f"Failed to initialize Spotify client: {e}"

    except Exception as e:
        logger.error(f"Error in session client initialization for user {user_id}: {str(e)}")
        return None, str(e)
    finally:
        db_session.remove()
