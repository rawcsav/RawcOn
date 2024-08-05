// DOM elements
document.addEventListener("DOMContentLoaded", function () {
  const timePeriodSelect = document.getElementById("timePeriod");
  const topArtistsList = document.getElementById("topArtists");
  const topTracksList = document.getElementById("topTracks");
  const topGenresList = document.getElementById("topGenres");
  const playlistsList = document.getElementById("playlists");

  // Pagination elements
  const prevArtistsBtn = document.getElementById("prevArtists");
  const nextArtistsBtn = document.getElementById("nextArtists");
  const prevTracksBtn = document.getElementById("prevTracks");
  const nextTracksBtn = document.getElementById("nextTracks");
  const artistsPageInfo = document.getElementById("artistsPageInfo");
  const tracksPageInfo = document.getElementById("tracksPageInfo");

  // Genre elements
  const genreDetails = document.getElementById("genre-details");
  const genreTitle = document.getElementById("genre-title");
  const genreArtistsList = document.getElementById("genre-artists-list");
  const genreTracksList = document.getElementById("genre-tracks-list");

  let audioFeaturesChart;
  const ITEMS_PER_PAGE = 10;
  let currentArtistsPage = 1;
  let currentTracksPage = 1;

  // Function to update the display based on the selected time period
  function updateDisplay(period) {
    console.log("Updating display for period:", period);
    updateTopArtists(period);
    updateTopTracks(period);
    updateTopGenres(period);
  }

  function updateTopArtists(period) {
    if (topArtistsSummary && topArtistsSummary[period]) {
      displayArtists(topArtistsSummary[period], currentArtistsPage);
      updatePagination(
        topArtistsSummary[period].length,
        currentArtistsPage,
        "artists",
      );
    } else {
      topArtistsList.innerHTML = "<p>No data available</p>";
      updatePagination(0, 1, "artists");
    }
  }

  function updateTopTracks(period) {
    if (topTracksSummary && topTracksSummary[period]) {
      displayTracks(topTracksSummary[period], currentTracksPage);
      updatePagination(
        topTracksSummary[period].length,
        currentTracksPage,
        "tracks",
      );
    } else {
      topTracksList.innerHTML = "<p>No data available</p>";
      updatePagination(0, 1, "tracks");
    }
  }

  function displayArtists(artists, page) {
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const artistsToDisplay = artists.slice(start, end);

    topArtistsList.innerHTML = artistsToDisplay
      .map(
        (artist) => `
    <div class="grid-item">
      <a href="${artist.spotify_url}" target="_blank">
        <img src="${artist.image_url || "/static/dist/img/default-artist.png"}" alt="${artist.name}" class="artist-image">
        <p>${artist.name}</p>
      </a>
    </div>
  `,
      )
      .join("");
  }

  function displayTracks(tracks, page) {
    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = start + ITEMS_PER_PAGE;
    const tracksToDisplay = tracks.slice(start, end);

    topTracksList.innerHTML = tracksToDisplay
      .map(
        (track) => `
    <div class="grid-item">
      <a href="${track.spotify_url}" target="_blank">
        <img src="${track.image_url || "/static/dist/img/default-album.png"}" alt="${track.name}" class="track-image">
        <p>${track.name}</p>
        <p class="artist-name">${track.artists.join(", ")}</p>
      </a>
    </div>
  `,
      )
      .join("");
  }

  function updatePagination(totalItems, currentPage, type) {
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);
    const pageInfo = type === "artists" ? artistsPageInfo : tracksPageInfo;
    pageInfo.innerHTML = `Page&nbsp;${currentPage}&nbsp;of&nbsp;${totalPages}`;
    const prevBtn = type === "artists" ? prevArtistsBtn : prevTracksBtn;
    const nextBtn = type === "artists" ? nextArtistsBtn : nextTracksBtn;

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
  }

  function updateTopGenres(period) {
    if (topGenres && topGenres[period]) {
      topGenresList.innerHTML = topGenres[period]
        .map(
          (genre) => `
          <a href="#" class="genre-link" data-period="${period}" data-genre="${genre[0]}">
            ${genre[0]}
          </a>
        `,
        )
        .join(" ");
      addGenreEventListeners();
    } else {
      topGenresList.innerHTML = "No data available";
    }
  }

  function addGenreEventListeners() {
    const genreLinks = document.querySelectorAll(".genre-link");
    genreLinks.forEach((link) => {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        const period = this.dataset.period;
        const genre = this.dataset.genre;
        fetchGenreData(period, genre);
      });
    });
  }

  function fetchGenreData(period, genre) {
    fetch(`/user/genre_data/${period}/${encodeURIComponent(genre)}`)
      .then((response) => response.json())
      .then((data) => {
        displayGenreData(genre, period, data);
      })
      .catch((error) => console.error("Error:", error));
  }

  function displayGenreData(genre, period, data) {
    genreTitle.textContent = `${genre}`;

    genreArtistsList.innerHTML = data.top_artists
      .map(
        (artist) => `
        <li class="grid-item">
          <img src="${
            artist.images && artist.images.length > 0
              ? artist.images[0].url
              : "/static/dist/img/default-artist.png"
          }" alt="${artist.name}" class="artist-image">
          <p>${artist.name}</p>
        </li>
      `,
      )
      .join("");

    genreTracksList.innerHTML = data.top_tracks
      .map(
        (track) => `
        <li class="grid-item">
          <img src="${
            track.album && track.album.images && track.album.images.length > 0
              ? track.album.images[0].url
              : "/static/dist/img/default-album.png"
          }" alt="${track.name}" class="track-image">
          <p>${track.name}</p>
          <p class="artist-name">${track.artists[0].name}</p>
        </li>
      `,
      )
      .join("");

    genreDetails.style.display = "block";
  }
  function createEnhancedAudioFeaturesChart(audioFeaturesSummary, periodData) {
    const ctx = document.getElementById("audioFeaturesChart").getContext("2d");
    const features = [
      "acousticness",
      "danceability",
      "energy",
      "instrumentalness",
      "liveness",
      "speechiness",
      "valence",
      "loudness",
      "tempo",
    ];
    let currentPeriod = "short_term";
    let showMinMax = false;

    const featureRanges = {
      acousticness: [0, 1],
      danceability: [0, 1],
      energy: [0, 1],
      instrumentalness: [0, 1],
      liveness: [0, 1],
      speechiness: [0, 1],
      valence: [0, 1],
      loudness: [-60, 0],
      tempo: [0, 250],
    };

    const featureExplanations = {
      acousticness:
        "A confidence measure from 0.0 to 1.0 of whether the track is acoustic.",
      danceability:
        "Describes how suitable a track is for dancing based on a combination of musical elements including tempo, rhythm stability, beat strength, and overall regularity. 0.0 is least danceable and 1.0 is most danceable.",
      energy:
        "Represents a perceptual measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy. Scale of 0.0 to 1.0.",
      instrumentalness:
        "Predicts whether a track contains no vocals. The closer the instrumentalness value is to 1.0, the greater likelihood the track contains no vocal content.",
      liveness:
        "Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live. Scale of 0.0 to 1.0.",
      speechiness:
        "Detects the presence of spoken words in a track. Values above 0.66 describe tracks that are probably made entirely of spoken words, values between 0.33 and 0.66 describe tracks that may contain both music and speech, and values below 0.33 most likely represent music and other non-speech-like tracks.",
      valence:
        "A measure describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive (e.g. happy, cheerful, euphoric), while tracks with low valence sound more negative (e.g. sad, depressed, angry). Scale of 0.0 to 1.0.",
      loudness:
        "The overall loudness of a track in decibels (dB). Loudness values are averaged across the entire track. Values typically range between -60 and 0 db.",
      tempo:
        "The overall estimated tempo of a track in beats per minute (BPM).",
    };

    function normalizeFeature(feature, value) {
      const [min, max] = featureRanges[feature];
      return (value - min) / (max - min);
    }

    function denormalizeFeature(feature, value) {
      const [min, max] = featureRanges[feature];
      return value * (max - min) + min;
    }

    let chart = new Chart(ctx, {
      type: "radar",
      data: {
        labels: features,
        datasets: [
          {
            label: "Audio Features",
            data: features.map((feature) =>
              normalizeFeature(
                feature,
                audioFeaturesSummary[currentPeriod][feature],
              ),
            ),
            backgroundColor: "rgba(29, 185, 84, 0.2)",
            borderColor: "rgb(29, 185, 84)",
            pointBackgroundColor: "rgb(29, 185, 84)",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgb(29, 185, 84)",
          },
        ],
      },
      options: {
        scales: {
          r: {
            angleLines: { display: false },
            suggestedMin: 0,
            suggestedMax: 1,
          },
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                const feature = context.label.toLowerCase();
                const value = denormalizeFeature(feature, context.raw);
                const unit =
                  feature === "loudness"
                    ? "dB"
                    : feature === "tempo"
                      ? "BPM"
                      : "";
                return `${context.label}: ${value.toFixed(2)}${unit ? " " + unit : ""}`;
              },
              afterLabel: function (context) {
                const feature = context.label.toLowerCase();
                return featureExplanations[feature];
              },
            },
          },
        },
        onHover: (event, activeElements) => {
          if (activeElements.length > 0) {
            const datasetIndex = activeElements[0].datasetIndex;
            const index = activeElements[0].index;
            const feature = features[index];
            let trackInfo;

            if (datasetIndex === 1) {
              // Min dataset
              trackInfo = periodData[currentPeriod].min_track[feature];
            } else if (datasetIndex === 2) {
              // Max dataset
              trackInfo = periodData[currentPeriod].max_track[feature];
            }

            if (trackInfo) {
              updateMinMaxTrack(feature, trackInfo);
            } else {
              clearMinMaxTrack();
            }
          } else {
            clearMinMaxTrack();
          }
        },
      },
    });

    function updateChart() {
      const avgData = features.map((feature) =>
        normalizeFeature(feature, audioFeaturesSummary[currentPeriod][feature]),
      );

      chart.data.datasets = [
        {
          label: "Average",
          data: avgData,
          backgroundColor: "rgba(29, 185, 84, 0.2)",
          borderColor: "rgb(29, 185, 84)",
          pointBackgroundColor: "rgb(29, 185, 84)",
          pointBorderColor: "#fff",
          pointHoverBackgroundColor: "#fff",
          pointHoverBorderColor: "rgb(29, 185, 84)",
        },
      ];

      if (showMinMax) {
        chart.data.datasets.push(
          {
            label: "Min",
            data: features.map((feature) =>
              normalizeFeature(
                feature,
                periodData[currentPeriod].min_values[feature],
              ),
            ),
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            borderColor: "rgb(255, 99, 132)",
            pointBackgroundColor: "rgb(255, 99, 132)",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgb(255, 99, 132)",
          },
          {
            label: "Max",
            data: features.map((feature) =>
              normalizeFeature(
                feature,
                periodData[currentPeriod].max_values[feature],
              ),
            ),
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgb(54, 162, 235)",
            pointBackgroundColor: "rgb(54, 162, 235)",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgb(54, 162, 235)",
          },
        );
      }

      chart.update();
      clearMinMaxTrack();
    }

    function updateMinMaxTrack(feature, trackInfo) {
      const minMaxContainer = document.getElementById("minMaxTrack");
      minMaxContainer.innerHTML = `
      <h4>${feature}</h4>
      <p>${trackInfo.name}&nbsp;by&nbsp;${trackInfo.artists[0].name}</p>
    `;
    }

    function clearMinMaxTrack() {
      const minMaxContainer = document.getElementById("minMaxTrack");
      minMaxContainer.innerHTML = "";
    }

    // Add controls
    const controlsContainer = document.createElement("div");
    controlsContainer.className = "audio-features-controls";
    controlsContainer.innerHTML = `
    <button id="toggleMinMaxBtn">Toggle Min/Max</button>
  `;
    document
      .getElementById("audioFeaturesChart")
      .parentNode.insertBefore(
        controlsContainer,
        document.getElementById("audioFeaturesChart"),
      );

    // Add min/max track container
    const minMaxContainer = document.createElement("div");
    minMaxContainer.id = "minMaxTrack";
    document
      .getElementById("audioFeaturesChart")
      .parentNode.appendChild(minMaxContainer);

    // Event listeners
    timePeriodSelect.addEventListener("change", function (e) {
      currentPeriod = e.target.value;
      updateChart();
    });

    document
      .getElementById("toggleMinMaxBtn")
      .addEventListener("click", function () {
        showMinMax = !showMinMax;
        updateChart();
      });

    // Initial update
    updateChart();
  }

  function displayPlaylists() {
    if (playlistSummary && playlistSummary.length > 0) {
      playlistsList.innerHTML = playlistSummary
        .map(
          (playlist) =>
            `<li>${playlist.name} (${
              playlist.public ? "Public" : "Private"
            })</li>`,
        )
        .join("");
    } else {
      playlistsList.innerHTML = "<li>No playlists available</li>";
    }
  }

  // Event listeners for pagination
  prevArtistsBtn.addEventListener("click", () => {
    if (currentArtistsPage > 1) {
      currentArtistsPage--;
      updateTopArtists(timePeriodSelect.value);
    }
  });

  nextArtistsBtn.addEventListener("click", () => {
    const totalArtists = topArtistsSummary[timePeriodSelect.value].length;
    if (currentArtistsPage < Math.ceil(totalArtists / ITEMS_PER_PAGE)) {
      currentArtistsPage++;
      updateTopArtists(timePeriodSelect.value);
    }
  });

  prevTracksBtn.addEventListener("click", () => {
    if (currentTracksPage > 1) {
      currentTracksPage--;
      updateTopTracks(timePeriodSelect.value);
    }
  });

  nextTracksBtn.addEventListener("click", () => {
    const totalTracks = topTracksSummary[timePeriodSelect.value].length;
    if (currentTracksPage < Math.ceil(totalTracks / ITEMS_PER_PAGE)) {
      currentTracksPage++;
      updateTopTracks(timePeriodSelect.value);
    }
  });

  // Event listener for time period changes
  timePeriodSelect.addEventListener("change", (event) => {
    console.log("Time period changed to:", event.target.value);
    currentArtistsPage = 1;
    currentTracksPage = 1;
    updateDisplay(event.target.value);
  });

  // Initial display
  updateDisplay("short_term");
  displayPlaylists();
  createEnhancedAudioFeaturesChart(audioFeaturesSummary, periodData);
});
