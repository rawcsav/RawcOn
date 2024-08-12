import json
from collections import defaultdict
from datetime import datetime

from flask import session
from app import db
from app.models.user_models import PlaylistData
from app.modules.user.user_util import init_session_client
from app.util.database_util import get_or_fetch_audio_features, get_or_fetch_artist_info

import json
import random
from flask import jsonify
from app import db
from app.models.user_models import UserData, PlaylistData, GenreData
from app.modules.user.user_util import init_session_client, get_playlist_summary, format_track_info
from app.modules.recs.recs_util import get_recommendations


def get_playlist_data(playlist_id, spotify_user_id):
    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        sp, error = init_session_client()
        if error:
            return None
        playlist_data = fetch_and_create_playlist(sp, playlist_id)
    else:
        playlist_data = playlist.__dict__

    user_data_entry = UserData.query.filter_by(spotify_user_id=spotify_user_id).first()
    playlist_summary = get_playlist_summary(user_data_entry)

    genre_scores = calculate_genre_weights(playlist_data["genre_counts"], GenreData)

    return {
        "playlist_id": playlist_id,
        "playlist_url": f"https://open.spotify.com/playlist/{playlist_id}",
        "playlist_data": playlist_data,
        "top_10_genre_data": dict(
            sorted(playlist_data["genre_counts"].items(), key=lambda x: x[1]["count"], reverse=True)[:10]
        ),
        "year_count": json.dumps(playlist_data.get("temporal_stats", {}).get("year_count", {})),
        "owner_name": playlist_data["owner"],
        "total_tracks": playlist_data["total_tracks"],
        "is_collaborative": playlist_data["collaborative"],
        "is_public": playlist_data["public"],
        "genre_scores": genre_scores,
        "playlist_summary": playlist_summary,
    }


def fetch_and_create_playlist(sp, playlist_id):
    playlist_info, track_data, genre_counts, top_artists, feature_stats, temporal_stats = get_playlist_details(
        sp, playlist_id
    )

    new_playlist = PlaylistData(
        id=playlist_info["id"],
        name=playlist_info["name"],
        owner=playlist_info["owner"],
        cover_art=playlist_info["cover_art"],
        public=playlist_info["public"],
        collaborative=playlist_info["collaborative"],
        total_tracks=playlist_info["total_tracks"],
        snapshot_id=playlist_info["snapshot_id"],
        tracks=track_data,
        genre_counts=genre_counts,
        top_artists=top_artists,
        feature_stats=feature_stats,
        temporal_stats=temporal_stats,
    )

    db.session.merge(new_playlist)
    db.session.commit()

    return new_playlist.__dict__


def update_playlist_data(playlist_id):
    sp, error = init_session_client()
    if error:
        return error, 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return "Playlist not found", 404

    playlist_info, track_data, genre_counts, top_artists, feature_stats, temporal_stats = get_playlist_details(
        sp, playlist_id
    )

    playlist.name = playlist_info["name"]
    playlist.owner = playlist_info["owner"]
    playlist.cover_art = playlist_info["cover_art"]
    playlist.public = playlist_info["public"]
    playlist.collaborative = playlist_info["collaborative"]
    playlist.total_tracks = playlist_info["total_tracks"]
    playlist.snapshot_id = playlist_info["snapshot_id"]
    playlist.tracks = track_data
    playlist.genre_counts = genre_counts
    playlist.top_artists = top_artists
    playlist.feature_stats = feature_stats
    playlist.temporal_stats = temporal_stats

    db.session.commit()
    return "Playlist updated successfully"


def like_all_songs(playlist_id):
    sp, error = init_session_client()
    if error:
        return jsonify(error=error), 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return "Playlist not found", 404

    track_ids = [track["id"] for track in playlist.tracks if track.get("id")]
    if not track_ids:
        return "No valid tracks in the playlist", 400

    try:
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i : i + 50]
            sp.current_user_saved_tracks_add(batch)
    except Exception as e:
        return f"Error occurred while liking songs: {str(e)}", 500

    return "All songs liked!"


def unlike_all_songs(playlist_id):
    sp, error = init_session_client()
    if error:
        return jsonify(error=error), 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return "Playlist not found", 404

    track_ids = [track["id"] for track in playlist.tracks if track.get("id")]
    if not track_ids:
        return "No valid tracks in the playlist", 400

    try:
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i : i + 50]
            sp.current_user_saved_tracks_delete(batch)
    except Exception as e:
        return f"Error occurred while unliking songs: {str(e)}", 500

    return "All songs unliked!"


def remove_duplicates(playlist_id):
    sp, error = init_session_client()
    if error:
        return error, 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return "Playlist not found", 404

    snapshot_id = playlist.snapshot_id
    track_ids = [track["id"] for track in playlist.tracks if track["id"] is not None]
    all_track_ids = [track["id"] for track in playlist.tracks]

    track_count = {track: track_ids.count(track) for track in set(track_ids)}
    positions_to_remove = [
        pos
        for track_id, count in track_count.items()
        for pos in [i for i, x in enumerate(all_track_ids) if x == track_id][1:]
        if count > 1
    ]

    for i in range(0, len(positions_to_remove), 100):
        batch = [
            {"uri": f"spotify:track:{all_track_ids[pos]}", "positions": [pos]}
            for pos in positions_to_remove[i : i + 100]
        ]
        sp.playlist_remove_specific_occurrences_of_items(playlist_id, batch, snapshot_id)

    update_playlist_data(playlist_id)
    return "Duplicates removed successfully"


def reorder_playlist(playlist_id, sorting_criterion):
    sp, error = init_session_client()
    if error:
        return jsonify(error=error), 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return jsonify(error="Playlist not found"), 404

    non_local_files = [track for track in playlist.tracks if track["id"] is not None]
    combined = [(track["id"], track["added_at"], track["release_date"]) for track in non_local_files]

    if sorting_criterion == "Date Added - Ascending":
        sorted_tracks = sorted(combined, key=lambda x: x[1])
    elif sorting_criterion == "Date Added - Descending":
        sorted_tracks = sorted(combined, key=lambda x: x[1], reverse=True)
    elif sorting_criterion == "Release Date - Ascending":
        sorted_tracks = sorted(combined, key=lambda x: (x[2] is None, x[2]))
    elif sorting_criterion == "Release Date - Descending":
        sorted_tracks = sorted(combined, key=lambda x: (x[2] is None, x[2]), reverse=True)
    elif sorting_criterion == "Shuffle":
        random.shuffle(combined)
        sorted_tracks = combined
    else:
        return jsonify(error="Invalid sorting criterion"), 400

    sorted_track_ids = [item[0] for item in sorted_tracks]
    new_playlist_name = f"Sorted {playlist.name}"
    new_playlist = sp.user_playlist_create(sp.me()["id"], new_playlist_name)
    new_playlist_id = new_playlist["id"]

    track_uris = [f"spotify:track:{track_id}" for track_id in sorted_track_ids if track_id is not None]
    for i in range(0, len(track_uris), 100):
        batch = track_uris[i : i + 100]
        sp.user_playlist_add_tracks(sp.me()["id"], new_playlist_id, batch)

    return jsonify(status="Playlist reordered successfully"), 200


def get_playlist_recommendations(playlist_id):
    sp, error = init_session_client()
    if error:
        return jsonify(error=error), 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return jsonify(error="Playlist not found"), 404

    genre_info = playlist.genre_counts
    top_artists = playlist.top_artists

    artist_counts = {artist[0]: artist[1] for artist in top_artists}
    artist_ids = {artist[0]: artist[4] for artist in top_artists}

    top_artist_ids = get_artists_seeds(artist_counts, artist_ids)
    top_genres = get_genres_seeds(sp, genre_info)

    num_artist_seeds = 5 - len(top_genres)
    seeds = {"track": None, "artist": top_artist_ids[:num_artist_seeds], "genre": top_genres}

    recommendations_data = get_recommendations(sp, limit=10, market="US", **seeds)

    if "error" in recommendations_data:
        return jsonify(error=recommendations_data["error"]), 400

    track_info_list = [format_track_info(track) for track in recommendations_data["tracks"]]
    return jsonify({"recommendations": track_info_list})


def get_playlist_info(sp, playlist_id):
    playlist = sp.playlist(playlist_id)

    playlist_info = {
        "id": playlist["id"],
        "name": playlist["name"],
        "owner": playlist["owner"]["display_name"],
        "cover_art": playlist["images"][0]["url"] if playlist["images"] else None,
        "public": playlist["public"],
        "collaborative": playlist["collaborative"],
        "total_tracks": playlist["tracks"]["total"],
        "snapshot_id": playlist["snapshot_id"],
    }

    return playlist_info


def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results["items"]
    next_page = results["next"]

    while next_page:
        results = sp.next(results)
        tracks.extend(results["items"])
        next_page = results["next"]

    return tracks


def get_track_info_list(sp, tracks):
    track_ids = [
        track_data["track"]["id"]
        for track_data in tracks
        if track_data and track_data.get("track") and track_data["track"].get("id")
    ]
    track_features_dict = get_or_fetch_audio_features(sp, track_ids)
    track_info_list = []

    unique_artist_ids = list(
        set(
            artist["id"]
            for track_data in tracks
            if track_data and track_data.get("track") and track_data["track"].get("artists")
            for artist in track_data["track"]["artists"]
            if artist.get("id")
        )
    )
    all_artist_info = get_or_fetch_artist_info(sp, unique_artist_ids)

    for track_data in tracks:
        if not track_data or not track_data.get("track"):
            continue  # Skip this track if it's None or doesn't have 'track' key

        track = track_data["track"]

        track.pop("available_markets", None)
        track.pop("disc_number", None)
        track.pop("external_ids", None)
        track.pop("href", None)
        track.pop("linked_from", None)
        track.pop("restrictions", None)

        artists = track.get("artists", [])
        image = track.get("album", {}).get("images", [])
        cover_art = image[0].get("url") if image else None

        artist_info = []
        for artist in artists:
            artist_id = artist.get("id")
            if artist_id and artist_id in all_artist_info:
                artist_info.append(all_artist_info[artist_id])

        audio_features = track_features_dict.get(track.get("id"), {})
        is_local = track.get("is_local", False)

        track_info = {
            "id": track.get("id"),
            "name": track.get("name"),
            "is_local": is_local,
            "added_at": track_data.get("added_at"),
            "album": track.get("album", {}).get("name"),
            "release_date": track.get("album", {}).get("release_date"),
            "explicit": track.get("explicit"),
            "popularity": None if is_local else track.get("popularity"),
            "cover_art": cover_art,
            "artists": artist_info,
            "audio_features": audio_features,
        }

        track_info_list.append(track_info)

    return track_info_list


def get_genre_artists_count(track_info_list, top_n=10):
    genre_info = {}
    artist_counts = {}
    artist_images = {}
    artist_urls = {}
    artist_ids = {}

    for track_info in track_info_list:
        for artist_dict in track_info["artists"]:
            artist_id = artist_dict.get("id")
            artist_name = artist_dict.get("name")
            artist_genres = artist_dict.get("genres", [])
            spotify_url = f"https://open.spotify.com/artist/{artist_id}"

            try:
                artist_image_url = artist_dict.get("images", [{}])[0].get("url")
            except IndexError:
                artist_image_url = None

            for genre in artist_genres:
                if genre not in genre_info:
                    genre_info[genre] = {"count": 0, "artists": set()}

                genre_info[genre]["count"] += 1
                genre_info[genre]["artists"].add(artist_name)

            artist_counts[artist_name] = artist_counts.get(artist_name, 0) + 1
            artist_ids[artist_name] = artist_id

            if artist_image_url:
                artist_images[artist_name] = artist_image_url

            artist_urls[artist_name] = spotify_url

    sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
    top_artists = [
        (name, count, artist_images.get(name, None), artist_urls.get(name), artist_ids.get(name))
        for name, count in sorted_artists[:top_n]
    ]

    for genre, info in genre_info.items():
        info["artists"] = list(info["artists"])

    return genre_info, top_artists


def get_audio_features_stats(track_info_list):
    audio_feature_stats = {
        feature: {"min": None, "max": None, "total": 0}
        for feature in track_info_list[0]["audio_features"].keys()
        if feature != "id"
    }
    audio_feature_stats["popularity"] = {"min": None, "max": None, "total": 0}

    for idx, track_info in enumerate(track_info_list):
        if track_info["is_local"] or track_info["popularity"] is None:
            continue

        for feature, value in track_info["audio_features"].items():
            if feature != "id":
                try:
                    if audio_feature_stats[feature]["min"] is None or value < audio_feature_stats[feature]["min"][1]:
                        audio_feature_stats[feature]["min"] = (track_info["name"], value)
                    if audio_feature_stats[feature]["max"] is None or value > audio_feature_stats[feature]["max"][1]:
                        audio_feature_stats[feature]["max"] = (track_info["name"], value)
                    audio_feature_stats[feature]["total"] += value
                except KeyError:
                    print(
                        f"KeyError at track index {idx}, track name: {track_info['name']}, missing feature: {feature}"
                    )
                    continue

        pop = track_info["popularity"]
        if audio_feature_stats["popularity"]["min"] is None or pop < audio_feature_stats["popularity"]["min"][1]:
            audio_feature_stats["popularity"]["min"] = (track_info["name"], pop)
        if audio_feature_stats["popularity"]["max"] is None or pop > audio_feature_stats["popularity"]["max"][1]:
            audio_feature_stats["popularity"]["max"] = (track_info["name"], pop)
        audio_feature_stats["popularity"]["total"] += pop

    for feature, stats in audio_feature_stats.items():
        stats["avg"] = stats["total"] / len(
            [track for track in track_info_list if not track["is_local"] and track["popularity"] is not None]
        )

    return audio_feature_stats


def get_temporal_stats(track_info_list, playlist_id):
    if not track_info_list:
        return {}

    def parse_date_or_default(track, default):
        release_date = track["release_date"]

        if release_date:
            try:
                # Handle year-only format
                if len(release_date) == 4 and int(release_date) > 0:
                    return datetime.strptime(release_date, "%Y")
                # Handle year-month-day format
                elif len(release_date) == 10:
                    return datetime.strptime(release_date, "%Y-%m-%d")
            except ValueError:
                # If parsing fails, return the default
                pass

        return default

    valid_tracks = [track for track in track_info_list if track.get("id") and not track.get("is_local")]

    if not valid_tracks:
        return {}  # return empty dict if no valid tracks

    oldest_track = min(valid_tracks, key=lambda x: parse_date_or_default(x, datetime.min))
    newest_track = max(valid_tracks, key=lambda x: parse_date_or_default(x, datetime.max))

    year_count = defaultdict(int)

    for track in track_info_list:
        if track["release_date"]:
            year = track["release_date"].split("-")[0]
            decade = year[:-1] + "0s"  # truncate the last digit and append "0s" for the decade representation
            year_count[decade] += 1

    temporal_stats = {
        "oldest_track": oldest_track["name"],
        "newest_track": newest_track["name"],
        "oldest_track_date": oldest_track["release_date"],
        "newest_track_date": newest_track["release_date"],
        "oldest_track_image": oldest_track["cover_art"],
        "newest_track_image": newest_track["cover_art"],
        "oldest_track_artist": oldest_track["artists"][0]["name"] if oldest_track["artists"] else "Unknown",
        "newest_track_artist": newest_track["artists"][0]["name"] if newest_track["artists"] else "Unknown",
        "year_count": year_count,
    }
    return temporal_stats


def compute_scores_for_playlist(genre_info, genre_sql):
    results = []

    # Fetch all relevant genres from the genre_sql table
    genres = genre_sql.query.filter(genre_sql.sim_genres.isnot(None), genre_sql.opp_genres.isnot(None)).all()

    for genre_entry in genres:
        # Skip genres that are already in the playlist
        if genre_entry.genre in genre_info:
            continue

        sim_genres = genre_entry.sim_genres.split(", ")
        sim_weights = list(map(int, genre_entry.sim_weights.split(", ")))

        opp_genres = genre_entry.opp_genres.split(", ")
        opp_weights = list(map(int, genre_entry.opp_weights.split(", ")))

        # Compute similarity score
        sim_score = sum([genre_info.get(genre, 0) * weight for genre, weight in zip(sim_genres, sim_weights)])

        # Compute opposition score
        opp_score = sum([genre_info.get(genre, 0) * weight for genre, weight in zip(opp_genres, opp_weights)])

        results.append(
            {
                "genre": genre_entry.genre,
                "similarity_score": sim_score,
                "opposition_score": opp_score,
                "spotify_url": genre_entry.spotify_url,  # Including the spotify_url attribute
            }
        )

    # Sort the results based on similarity_score and opposition_score
    most_similar = sorted(results, key=lambda x: x["similarity_score"], reverse=True)[:10]
    most_opposite = sorted(results, key=lambda x: x["opposition_score"], reverse=True)[:10]

    return {"most_similar": most_similar, "most_opposite": most_opposite}


def calculate_genre_weights(genre_counts, genre_sql):
    genre_info = {genre: data["count"] for genre, data in genre_counts.items()}
    genre_scores = compute_scores_for_playlist(genre_info, genre_sql)

    total_tracks = sum(genre_info.values())
    genre_prevalence = {genre: count / total_tracks for genre, count in genre_info.items()}

    sorted_genres = sorted(genre_prevalence.items(), key=lambda x: x[1], reverse=True)[:10]

    # Create a dictionary to store the mapping of genre to closest_genre_stat
    genre_to_stat_mapping = {}

    for genre, _ in sorted_genres:
        genre_entry = genre_sql.query.filter_by(genre=genre).first()
        if genre_entry:
            genre_to_stat_mapping[genre] = genre_entry.closest_stat_genres

    return genre_to_stat_mapping, genre_scores


def get_playlist_details(sp, playlist_id):
    playlist_info = get_playlist_info(sp, playlist_id)
    tracks = get_playlist_tracks(sp, playlist_id)
    track_info_list = get_track_info_list(sp, tracks)
    genre_counts, top_artists = get_genre_artists_count(track_info_list)
    audio_feature_stats = get_audio_features_stats(track_info_list)
    temporal_stats = get_temporal_stats(track_info_list, playlist_id)
    return playlist_info, track_info_list, genre_counts, top_artists, audio_feature_stats, temporal_stats


def update_playlist_data(playlist_id):
    sp, error = init_session_client()
    if error:
        return json.dumps(error), 401

    playlist = PlaylistData.query.get(playlist_id)
    if not playlist:
        return "Playlist not found", 404

    # Fetch the new data
    (
        pl_playlist_info,
        pl_track_data,
        pl_genre_counts,
        pl_top_artists,
        pl_feature_stats,
        pl_temporal_stats,
    ) = get_playlist_details(sp, playlist_id)

    # Update the playlist object
    playlist.name = pl_playlist_info["name"]
    playlist.owner = pl_playlist_info["owner"]
    playlist.cover_art = pl_playlist_info["cover_art"]
    playlist.public = pl_playlist_info["public"]
    playlist.collaborative = pl_playlist_info["collaborative"]
    playlist.total_tracks = pl_playlist_info["total_tracks"]
    playlist.snapshot_id = pl_playlist_info["snapshot_id"]
    playlist.tracks = pl_track_data
    playlist.genre_counts = pl_genre_counts
    playlist.top_artists = pl_top_artists
    playlist.feature_stats = pl_feature_stats
    playlist.temporal_stats = pl_temporal_stats

    try:
        db.session.merge(playlist)
        db.session.commit()
    except:
        db.session.rollback()
        raise

    return "Playlist updated successfully"


def get_sp_genre_seeds(sp):
    global genre_seeds
    if "genre_seeds" not in globals():
        genre_seeds = sp.recommendation_genre_seeds()  # Assuming sp is your Spotipy client
    return genre_seeds


def get_artists_seeds(artist_counts, artist_ids, top_n=5):
    sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
    return [artist_ids[artist[0]] for artist in sorted_artists[: min(top_n, len(sorted_artists))]]


def get_genres_seeds(sp, genre_info, top_n=10):
    genre_seeds_dict = get_sp_genre_seeds(sp)
    genre_seeds = genre_seeds_dict["genres"]

    valid_genres = []
    for genre, count in sorted(genre_info.items(), key=lambda x: x[1]["count"], reverse=True)[:top_n]:
        sanitized_genre = genre.strip().lower()

        # Check for direct match
        if sanitized_genre in genre_seeds:
            valid_genres.append(sanitized_genre)
            continue

        hyphenated_genre = sanitized_genre.replace(" ", "-")
        if hyphenated_genre in genre_seeds:
            valid_genres.append(hyphenated_genre)
            continue

        spaced_genre = sanitized_genre.replace("-", " ")
        if spaced_genre in genre_seeds:
            valid_genres.append(spaced_genre)

    print(valid_genres)
    return valid_genres[:2]
