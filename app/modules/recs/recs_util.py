from spotipy import SpotifyException


def spotify_search(sp, query, type, limit=6):
    try:
        results = sp.search(q=query, type=type, limit=limit)
        return results
    except SpotifyException as e:
        return {"error": str(e)}


def get_recommendations(sp, limit, market, **kwargs):
    seed_tracks = kwargs.get("track", None)
    seed_artists = kwargs.get("artist", None)
    seed_genres = kwargs.get("genre", None)
    try:
        return sp.recommendations(
            seed_tracks=seed_tracks, seed_artists=seed_artists, seed_genres=seed_genres, limit=limit, **kwargs
        )
    except Exception as e:
        return {"error": str(e)}
