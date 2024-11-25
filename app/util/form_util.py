from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, FloatField
from wtforms.validators import Optional, NumberRange


class RecommendationsForm(FlaskForm):
    track_seeds = StringField("Track Seeds", validators=[Optional()])
    artist_seeds = StringField("Artist Seeds", validators=[Optional()])
    limit = IntegerField("Limit", default=5, validators=[NumberRange(min=1, max=100)])

    min_popularity = IntegerField("Min Popularity", validators=[NumberRange(min=0, max=100)])
    max_popularity = IntegerField("Max Popularity", validators=[NumberRange(min=0, max=100)])

    min_energy = FloatField("Min Energy", validators=[NumberRange(min=0, max=1)])
    max_energy = FloatField("Max Energy", validators=[NumberRange(min=0, max=1)])

    min_instrumentalness = FloatField("Min Instrumentalness", validators=[NumberRange(min=0, max=1)])
    max_instrumentalness = FloatField("Max Instrumentalness", validators=[NumberRange(min=0, max=1)])

    min_tempo = FloatField("Min Tempo", validators=[NumberRange(min=24, max=208)])
    max_tempo = FloatField("Max Tempo", validators=[NumberRange(min=24, max=208)])

    min_danceability = FloatField("Min Danceability", validators=[NumberRange(min=0, max=1)])
    max_danceability = FloatField("Max Danceability", validators=[NumberRange(min=0, max=1)])

    min_valence = FloatField("Min Valence", validators=[NumberRange(min=0, max=1)])
    max_valence = FloatField("Max Valence", validators=[NumberRange(min=0, max=1)])

    submit = SubmitField("Get Recommendations")
