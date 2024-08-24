# app/modules/user/user_util.py

import json
from collections import defaultdict, deque
from datetime import datetime, timedelta

from spotipy import Spotify
from flask import current_app, session, redirect
from app.models.user_models import UserData, GenreData
from app import db
from app.modules.auth.auth import refresh
from app.util.database_util import get_or_fetch_artist_info, get_or_fetch_audio_features
from app.modules.auth.auth_util import verify_session, fetch_user_data

FEATURES = [
    "acousticness",
    "danceability",
    "energy",
    "instrumentalness",
    "liveness",
    "loudness",
    "speechiness",
    "tempo",
    "valence",
    "popularity",
]


def init_session_client():
    tokens = session.get("tokens", {})
    access_token = tokens.get("access_token")
    expiry_time_str = tokens.get("expiry_time")

    if expiry_time_str:
        expiry_time = datetime.fromisoformat(expiry_time_str)
        if datetime.now() >= expiry_time:
            access_token = None

    if not access_token:
        refresh_response = refresh()
        if refresh_response.status_code == 200:
            access_token = refresh_response.json.get("access_token")
        else:
            return None, redirect(current_app.config["REDIRECT_URL"])

    return Spotify(auth=access_token), None


def clean_spotify_data(data, keys_to_remove):
    for key in keys_to_remove:
        data.pop(key, None)
    return data


def clean_track_data(track):
    track_keys_to_remove = [
        "available_markets",
        "disc_number",
        "external_ids",
        "href",
        "linked_from",
        "restrictions",
        "preview_url",
        "track_number",
        "uri",
        "is_playable",
    ]
    album_keys_to_remove = [
        "album_type",
        "available_markets",
        "external_urls",
        "href",
        "total_tracks",
        "restrictions",
        "type",
        "uri",
        "artists",
    ]
    artist_keys_to_remove = ["href", "uri"]

    clean_spotify_data(track, track_keys_to_remove)

    if "album" in track:
        clean_spotify_data(track["album"], album_keys_to_remove)
        if "images" in track["album"]:
            track["album"]["images"] = track["album"]["images"][:1]

    if "artists" in track:
        for artist in track["artists"]:
            clean_spotify_data(artist, artist_keys_to_remove)

    return track


def get_top_items(sp, item_type, period):
    method = sp.current_user_top_tracks if item_type == "tracks" else sp.current_user_top_artists
    all_items = method(time_range=period, limit=50)

    global_keys_to_remove = ["href", "next", "previous", "total"]
    clean_spotify_data(all_items, global_keys_to_remove)

    if "items" in all_items:
        all_items["items"] = [clean_track_data(item) for item in all_items["items"]]

    return all_items


def get_recently_played_tracks(sp, limit=50):
    recent_tracks = sp.current_user_recently_played(limit=limit)
    clean_spotify_data(recent_tracks, ["href"])

    if "items" in recent_tracks:
        for item in recent_tracks["items"]:
            if "track" in item:
                item["track"] = clean_track_data(item["track"])

    return recent_tracks


def get_user_playlists(sp):
    playlist_info = []
    offset = 0
    while True:
        playlists = sp.current_user_playlists(limit=50, offset=offset)
        if not playlists["items"]:
            break
        for playlist in playlists["items"]:
            info = {
                "id": playlist["id"],
                "name": playlist["name"],
                "owner": playlist["owner"]["display_name"],
                "cover_art": playlist["images"][0]["url"] if playlist["images"] else None,
                "public": playlist["public"],
                "collaborative": playlist["collaborative"],
            }
            playlist_info.append(info)
        offset += 50
    return playlist_info


def get_genre_counts(top_artists, top_tracks, all_artists_info):
    genre_counts = defaultdict(int)

    for artist in top_artists["items"]:
        for genre in artist["genres"]:
            genre_counts[genre] += 1

    for track in top_tracks["items"]:
        for artist in track["artists"]:
            artist_info = all_artists_info.get(artist["id"])
            if artist_info:
                for genre in artist_info["genres"]:
                    genre_counts[genre] += 1

    return sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:20]


def get_artists_for_genre(all_artists_info, genre, artist_ids):
    return [
        artist
        for artist_id, artist in all_artists_info.items()
        if genre in artist["genres"] and artist_id in artist_ids
    ]


def get_tracks_for_artists(tracks, artist_ids):
    return [track for track in tracks if any(artist["id"] in artist_ids for artist in track["artists"])]


def fetch_and_process_data(sp, time_periods):
    try:
        top_tracks = {period: get_top_items(sp, "tracks", period) for period in time_periods}
        top_artists = {period: get_top_items(sp, "artists", period) for period in time_periods}

        all_artist_ids = set()
        all_track_ids = set()
        for period in time_periods:
            all_artist_ids.update(artist["id"] for artist in top_artists[period]["items"])
            all_artist_ids.update(artist["id"] for track in top_tracks[period]["items"] for artist in track["artists"])
            all_track_ids.update(track["id"] for track in top_tracks[period]["items"])

        all_artists_info = get_or_fetch_artist_info(sp, list(all_artist_ids))
        audio_features = get_or_fetch_audio_features(sp, list(all_track_ids))

        genre_specific_data = {period: {} for period in time_periods}
        sorted_genres_by_period = {}

        for period in time_periods:
            sorted_genres = get_genre_counts(top_artists[period], top_tracks[period], all_artists_info)
            sorted_genres_by_period[period] = sorted_genres

            artist_ids_for_period = {artist["id"] for artist in top_artists[period]["items"]} | {
                artist["id"] for track in top_tracks[period]["items"] for artist in track["artists"]
            }

            for genre, _ in sorted_genres:
                top_genre_artists = get_artists_for_genre(all_artists_info, genre, artist_ids_for_period)
                top_genre_tracks = get_tracks_for_artists(
                    top_tracks[period]["items"], [artist["id"] for artist in top_genre_artists]
                )
                genre_specific_data[period][genre] = {"top_artists": top_genre_artists, "top_tracks": top_genre_tracks}

        recent_tracks = get_recently_played_tracks(sp)["items"]
        playlist_info = get_user_playlists(sp)

        return (
            top_tracks,
            top_artists,
            all_artists_info,
            audio_features,
            genre_specific_data,
            sorted_genres_by_period,
            recent_tracks,
            playlist_info,
        )
    except Exception as e:
        print("Exception:", str(e))
        return (None,) * 8


def calculate_averages_for_period(tracks, audio_features):
    feature_sums = defaultdict(float)
    track_counts = defaultdict(int)
    min_track = {feature: None for feature in FEATURES}
    max_track = {feature: None for feature in FEATURES}
    min_values = {feature: float("inf") for feature in FEATURES}
    max_values = {feature: float("-inf") for feature in FEATURES}

    for track in tracks["items"]:
        track_id = track["id"]
        for feature in FEATURES:
            value = track.get(feature, 0) if feature == "popularity" else audio_features[track_id].get(feature, 0)

            feature_sums[feature] += value
            track_counts[feature] += 1

            if value < min_values[feature]:
                min_values[feature] = value
                min_track[feature] = track
            if value > max_values[feature]:
                max_values[feature] = value
                max_track[feature] = track

    averaged_features = {
        feature: feature_sums[feature] / track_counts[feature] if track_counts[feature] else 0 for feature in FEATURES
    }
    return averaged_features, min_track, max_track, min_values, max_values


def update_user_data(user_data_entry):
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401

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
    user_data_entry.last_active = datetime.utcnow()

    db.session.merge(user_data_entry)
    db.session.commit()

    return "User updated successfully"


def check_and_refresh_user_data(user_data_entry):
    if user_data_entry:
        delta_since_last_active = datetime.utcnow() - user_data_entry.last_active
        if timedelta(days=7) < delta_since_last_active < timedelta(days=30):
            update_user_data(user_data_entry)
        return True
    return False


def delete_old_user_data():
    threshold_date = datetime.utcnow() - timedelta(days=30)
    old_users = UserData.query.filter(UserData.last_active < threshold_date).all()
    for user in old_users:
        db.session.delete(user)
    db.session.commit()


def get_top_genres(user_data, time_range):
    """
    Get the top genres for a specific time range.
    """
    return user_data.sorted_genres_by_period.get(time_range, [])[:10]


def get_audio_features_summary(user_data, time_range):
    """
    Calculate the average audio features for a specific time range.
    """
    tracks = user_data.top_tracks.get(time_range, {}).get("items", [])
    audio_features = user_data.audio_features

    feature_sums = defaultdict(float)
    feature_counts = defaultdict(int)

    for track in tracks:
        track_id = track["id"]
        if track_id in audio_features:
            for feature in FEATURES:
                value = audio_features[track_id].get(feature, 0)
                feature_sums[feature] += value
                feature_counts[feature] += 1

    return {
        feature: feature_sums[feature] / feature_counts[feature] if feature_counts[feature] > 0 else 0
        for feature in FEATURES
    }


def get_top_artists_summary(user_data, time_range):
    """
    Get a summary of top artists for a specific time range.
    """
    artists = user_data.top_artists.get(time_range, {}).get("items", [])
    return [
        {
            "name": artist["name"],
            "id": artist["id"],
            "image_url": artist["images"][0]["url"] if artist["images"] else None,
            "spotify_url": artist["external_urls"]["spotify"],
        }
        for artist in artists[:50]
    ]


def get_top_tracks_summary(user_data, time_range):
    """
    Get a summary of top tracks for a specific time range.
    """
    tracks = user_data.top_tracks.get(time_range, {}).get("items", [])
    return [
        {
            "name": track["name"],
            "id": track["id"],
            "artists": [artist["name"] for artist in track["artists"]],
            "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
            "spotify_url": track["external_urls"]["spotify"],
        }
        for track in tracks[:50]
    ]


def get_recent_tracks_summary(user_data):
    """
    Get a summary of the most recently played track.
    """
    if user_data.recent_tracks and len(user_data.recent_tracks) > 0:
        most_recent = user_data.recent_tracks[0]
        return {
            "name": most_recent["track"]["name"],
            "id": most_recent["track"]["id"],
            "artists": [artist["name"] for artist in most_recent["track"]["artists"]],
            "album": most_recent["track"]["album"]["name"],
            "played_at": most_recent["played_at"],
            "image_url": most_recent["track"]["album"]["images"][0]["url"]
            if most_recent["track"]["album"]["images"]
            else None,
        }
    return None  # Return None if no recent tracks are available


def get_playlist_summary(user_data):
    """
    Get a summary of user's playlists.
    """
    playlists = user_data.playlist_info
    return [
        {
            "name": playlist["name"],
            "id": playlist["id"],
            "owner": playlist["owner"],
            "public": playlist["public"],
            "collaborative": playlist["collaborative"],
            "image_url": playlist["cover_art"],
        }
        for playlist in playlists[:20]
    ]


def format_track_info(track):
    return {
        "trackid": track["id"],
        "artistid": track["artists"][0]["id"] if track["artists"] else None,
        "preview": track["preview_url"],
        "cover_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
        "artist": track["artists"][0]["name"],
        "trackName": track["name"],
        "trackUrl": track["external_urls"]["spotify"],
        "albumName": track["album"]["name"],
    }


def get_user_data():
    access_token = verify_session(session)
    res_data = fetch_user_data(access_token)
    spotify_user_id = res_data.get("id")
    return UserData.query.filter_by(spotify_user_id=spotify_user_id).first()


def get_genre_bubble_chart_data(user_data):
    time_periods = ["short_term", "medium_term", "long_term"]
    genre_data = {period: {} for period in time_periods}

    for period in time_periods:
        period_genres = user_data.sorted_genres_by_period.get(period, [])
        for genre, count in period_genres:
            genre_info = GenreData.query.filter_by(genre=genre).first()
            if genre_info:
                genre_data[period][genre] = {"x": genre_info.x, "y": genre_info.y, "count": count}

    result = [
        {
            "period": period,
            "data": [
                {"genre": genre, "x": data["x"], "y": data["y"], "r": data["count"]}  # Use count for bubble size
                for genre, data in period_data.items()
            ],
        }
        for period, period_data in genre_data.items()
    ]

    return result


def get_audio_features_evolution(user_data):
    features = [
        "acousticness",
        "danceability",
        "energy",
        "instrumentalness",
        "liveness",
        "loudness",
        "speechiness",
        "tempo",
        "valence",
        "popularity",
    ]
    periods = ["long_term", "medium_term", "short_term"]  # Ordered from oldest to most recent

    evolution_data = {feature: [] for feature in features}
    labels = []

    window_size = 10  # Size of the moving average window
    windows = {feature: deque(maxlen=window_size) for feature in features}

    for period in periods:
        tracks = user_data.top_tracks.get(period, {}).get("items", [])
        for track in tracks:
            track_id = track["id"]
            if track_id in user_data.audio_features:
                labels.append(f"{period}")  # You could make this more descriptive if needed
                for feature in features:
                    if feature == "popularity":
                        value = track.get("popularity", 0) / 100  # Normalize popularity
                    elif feature == "loudness":
                        value = (
                            user_data.audio_features[track_id].get("loudness", -60) + 60
                        ) / 60  # Normalize loudness
                    elif feature == "tempo":
                        value = user_data.audio_features[track_id].get("tempo", 0) / 250  # Normalize tempo
                    else:
                        value = user_data.audio_features[track_id].get(feature, 0)

                    windows[feature].append(value)
                    evolution_data[feature].append(sum(windows[feature]) / len(windows[feature]))

    return {
        "labels": labels,
        "datasets": [{"label": feature.capitalize(), "data": evolution_data[feature]} for feature in features],
    }
