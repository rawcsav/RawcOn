# Genre Data

## Data Source

All genre data used in this project is scraped from [Every Noise At Once](https://everynoise.com/), a comprehensive resource for music genre classification and exploration.

## Data Collection Method

The data was collected using a custom Go-based web scraper, [ENAOScrape](https://github.com/rawcsav/ENAOScrape). This scraper was developed to efficiently and responsibly gather detailed information about music genres from the Every Noise at Once website.

## Data Format

The genre data is stored in a CSV file with the following columns:

- `genre`: The name of the music genre
- `sim_genres`: Similar genres, separated by '|'
- `sim_weights`: Weights of similarity for each similar genre, separated by '|'
- `opp_genres`: Opposite genres, separated by '|'
- `opp_weights`: Weights of opposition for each opposite genre, separated by '|'
- `spotify_url`: URL to the genre's Spotify playlist
- `color_hex`: Hexadecimal color code associated with the genre
- `color_rgb`: RGB color values associated with the genre
- `x`: X-coordinate for genre visualization (if applicable)
- `y`: Y-coordinate for genre visualization (if applicable)

## Data Usage

This data is used within the project to provide comprehensive information about music genres, their relationships, and associated visual attributes. It forms the basis for various features such as genre recommendations, visualizations, and playlist generation.