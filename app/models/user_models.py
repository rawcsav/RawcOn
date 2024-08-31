from datetime import datetime
from typing import Optional

from sqlalchemy import BLOB
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from cryptography.fernet import Fernet
from flask import current_app


def encrypt_token(token: str) -> str:
    key = current_app.config["ENCRYPTION_KEY"]
    f = Fernet(key)
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    key = current_app.config["ENCRYPTION_KEY"]
    f = Fernet(key)
    return f.decrypt(encrypted_token.encode()).decode()


class UserData(db.Model):
    spotify_user_id = db.Column(db.VARCHAR(255), primary_key=True, index=True)
    top_tracks = db.Column(db.JSON, nullable=True)
    top_artists = db.Column(db.JSON, nullable=True)
    all_artists_info = db.Column(db.JSON, nullable=True)
    audio_features = db.Column(db.JSON, nullable=True)
    genre_specific_data = db.Column(db.JSON, nullable=True)
    sorted_genres_by_period = db.Column(db.JSON, nullable=True)
    recent_tracks = db.Column(db.JSON, nullable=True)
    playlist_info = db.Column(db.JSON, nullable=True)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    isDarkMode = db.Column(db.Boolean, nullable=True)
    last_stale_update = db.Column(db.DateTime, nullable=True)
    _access_token = db.Column(db.VARCHAR(1000), nullable=True)  # Encrypted access token
    _refresh_token = db.Column(db.VARCHAR(1000), nullable=True)  # Encrypted refresh token
    token_expiry = db.Column(db.DateTime, nullable=True)

    playlists = db.relationship("PlaylistData", back_populates="user", lazy="dynamic")

    @hybrid_property
    def access_token(self) -> Optional[str]:
        return decrypt_token(self._access_token) if self._access_token else None

    @access_token.setter
    def access_token(self, value: Optional[str]):
        self._access_token = encrypt_token(value) if value else None

    @hybrid_property
    def refresh_token(self) -> Optional[str]:
        return decrypt_token(self._refresh_token) if self._refresh_token else None

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]):
        self._refresh_token = encrypt_token(value) if value else None

    def __repr__(self):
        return f"<UserData {self.spotify_user_id}>"


class ArtistData(db.Model):
    id = db.Column(db.String(100), primary_key=True, index=True)
    name = db.Column(db.VARCHAR(255), index=True)
    external_url = db.Column(db.VARCHAR(255))
    followers = db.Column(db.Integer)
    genres = db.Column(db.VARCHAR(255))
    images = db.Column(db.JSON)
    popularity = db.Column(db.Integer)

    features = db.relationship("FeatureData", back_populates="artist")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class FeatureData(db.Model):
    id = db.Column(db.VARCHAR(255), primary_key=True, index=True)
    artist_id = db.Column(db.String(100), db.ForeignKey("artist_data.id"), index=True)
    danceability = db.Column(db.Float)
    energy = db.Column(db.Float)
    key = db.Column(db.Integer)
    loudness = db.Column(db.Float)
    mode = db.Column(db.Integer)
    speechiness = db.Column(db.Float)
    acousticness = db.Column(db.Float)
    instrumentalness = db.Column(db.Float)
    liveness = db.Column(db.Float)
    valence = db.Column(db.Float)
    tempo = db.Column(db.Float)
    time_signature = db.Column(db.Integer)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PlaylistData(db.Model):
    id = db.Column(db.VARCHAR(255), primary_key=True, index=True)
    user_id = db.Column(db.VARCHAR(255), db.ForeignKey("user_data.spotify_user_id"), index=True)
    name = db.Column(db.VARCHAR(255), index=True)
    owner = db.Column(db.VARCHAR(255))
    cover_art = db.Column(db.VARCHAR(255))
    public = db.Column(db.Boolean)
    collaborative = db.Column(db.Boolean)
    total_tracks = db.Column(db.Integer)
    snapshot_id = db.Column(db.VARCHAR(255))
    followers = db.Column(db.VARCHAR(255))
    total_duration = db.Column(db.VARCHAR(255))
    last_updated = db.Column(db.DateTime)
    tracks = db.Column(db.JSON)
    genre_counts = db.Column(db.JSON)
    top_artists = db.Column(db.JSON)
    local_tracks_count = db.Column(db.Integer)
    feature_stats = db.Column(db.JSON)
    temporal_stats = db.Column(db.JSON)

    user = db.relationship("UserData", back_populates="playlists")


class GenreData(db.Model):
    genre = db.Column(db.VARCHAR(50), primary_key=True)
    sim_genres = db.Column(db.TEXT, nullable=True)
    sim_weights = db.Column(db.TEXT, nullable=True)
    opp_genres = db.Column(db.TEXT, nullable=True)
    opp_weights = db.Column(db.TEXT, nullable=True)
    spotify_url = db.Column(db.TEXT, nullable=True)
    color_hex = db.Column(db.TEXT, nullable=True)
    color_rgb = db.Column(db.TEXT, nullable=True)
    x = db.Column(db.Float, nullable=True)
    y = db.Column(db.Float, nullable=True)
