import csv
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.spatial import distance_matrix

from app import db
from app.models.artgen_models import artgen_sql, artgenurl_sql
from app.models.user_models import artist_sql, features_sql


def get_today_date():
    return datetime.utcnow().date()


def validate_artist_data(data):
    required_keys = ["id", "name", "external_urls", "followers", "genres", "images", "popularity"]
    return all(key in data for key in required_keys)


def validate_audio_data(data):
    required_keys = [
        "id",
        "danceability",
        "energy",
        "key",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "time_signature",
    ]
    return all(key in data for key in required_keys)


def add_artist_to_db(artist_data):
    new_artist = artist_sql(
        id=artist_data["id"],
        name=artist_data["name"],
        external_url=json.dumps(artist_data["external_urls"]),
        followers=artist_data.get("followers", {"total": 0})["total"],
        genres=json.dumps(artist_data["genres"]),
        images=json.dumps(artist_data["images"]),
        popularity=artist_data["popularity"],
    )
    db.session.merge(new_artist)


def get_or_fetch_artist_info(sp, artist_ids):
    if isinstance(artist_ids, str):
        artist_ids = [artist_ids]
    existing_artists = artist_sql.query.filter(artist_sql.id.in_(artist_ids)).all()
    existing_artist_ids = {artist.id: artist for artist in existing_artists}

    to_fetch = [artist_id for artist_id in artist_ids if artist_id not in existing_artist_ids]

    batch_size = 50

    for i in range(0, len(to_fetch), batch_size):
        batch = [x for x in to_fetch[i : i + batch_size] if x is not None]
        fetched_artists = sp.artists(batch)["artists"]

        for artist in fetched_artists:
            new_artist = artist_sql(
                id=artist["id"],
                name=artist["name"],
                external_url=json.dumps(artist["external_urls"]),
                followers=artist["followers"]["total"],
                genres=json.dumps(artist["genres"]),
                images=json.dumps(artist["images"]),
                popularity=artist["popularity"],
            )
            existing_artist_ids[new_artist.id] = new_artist
            db.session.merge(new_artist)
    db.session.commit()

    final_artists = {}
    for artist_id in artist_ids:
        artist = existing_artist_ids.get(artist_id)
        if artist:
            final_artists[artist_id] = {
                "id": artist.id,
                "name": artist.name,
                "external_url": json.loads(artist.external_url),
                "followers": artist.followers,
                "genres": json.loads(artist.genres or "[]"),
                "images": json.loads(artist.images),
                "popularity": artist.popularity,
            }
    return final_artists


def get_or_fetch_audio_features(sp, track_ids):
    existing_features = features_sql.query.filter(features_sql.id.in_(track_ids)).all()
    existing_feature_ids = {feature.id: feature for feature in existing_features}

    to_fetch = [track_id for track_id in track_ids if track_id not in existing_feature_ids]

    batch_size = 100

    if to_fetch:
        for i in range(0, len(to_fetch), batch_size):
            batch = to_fetch[i : i + batch_size]
            fetched_features = sp.audio_features(batch)

            for feature in fetched_features:
                if feature:
                    new_feature = features_sql(
                        id=feature["id"],
                        danceability=feature["danceability"],
                        energy=feature["energy"],
                        key=feature["key"],
                        loudness=feature["loudness"],
                        mode=feature["mode"],
                        speechiness=feature["speechiness"],
                        acousticness=feature["acousticness"],
                        instrumentalness=feature["instrumentalness"],
                        liveness=feature["liveness"],
                        valence=feature["valence"],
                        tempo=feature["tempo"],
                        time_signature=feature["time_signature"],
                    )
                    try:
                        db.session.merge(new_feature)
                        existing_feature_ids[feature["id"]] = new_feature
                        db.session.commit()
                    except:
                        db.session.rollback()
                        raise

    final_features = {
        track_id: {
            "id": feature.id,
            "danceability": feature.danceability,
            "energy": feature.energy,
            "key": feature.key,
            "loudness": feature.loudness,
            "mode": feature.mode,
            "speechiness": feature.speechiness,
            "acousticness": feature.acousticness,
            "instrumentalness": feature.instrumentalness,
            "liveness": feature.liveness,
            "valence": feature.valence,
            "tempo": feature.tempo,
            "time_signature": feature.time_signature,
        }
        for track_id, feature in existing_feature_ids.items()
    }

    return final_features


def delete_expired_images_for_playlist(playlist_id):
    expiry_threshold = datetime.utcnow() - timedelta(hours=1)

    expired_images = artgenurl_sql.query.filter(
        artgenurl_sql.playlist_id == playlist_id, artgenurl_sql.timestamp <= expiry_threshold
    ).all()

    for image in expired_images:
        db.session.delete(image)

    db.session.commit()
    db.session.close()
