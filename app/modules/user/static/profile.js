document.addEventListener("DOMContentLoaded", function () {
  let showMinMax = true; // Set this to true by default
  const timeSelector = document.querySelector(".time-selector");
  const timeOptions = document.querySelectorAll(".time-option");
  timeOptions.forEach((option) => {
    option.addEventListener("click", () => {
      timeOptions.forEach((opt) => opt.classList.remove("selected"));
      option.classList.add("selected");
      const selectedValue = option.getAttribute("data-value");
      updateDisplay(selectedValue);

      // Update the chart
      currentPeriod = selectedValue;
      if (typeof updateChart === "function") {
        updateChart();
      }

      // Reset scroll positions when changing time periods
      artistsContainer.scrollLeft = 0;
      tracksContainer.scrollLeft = 0;
    });
  });
  const topArtistsList = document.getElementById("topArtists");
  const topTracksList = document.getElementById("topTracks");
  const topGenresList = document.getElementById("topGenres");
  const playlistsList = document.getElementById("playlists");

  const artistsPageInfo = document.getElementById("artistsPageInfo");
  const tracksPageInfo = document.getElementById("tracksPageInfo");

  // Genre elements
  const genreDetails = document.getElementById("genre-details");
  const genreTitle = document.getElementById("genre-title");
  const genreArtistsList = document.getElementById("genre-artists-list");
  const genreTracksList = document.getElementById("genre-tracks-list");

  let artistsOffset = 0;
  let tracksOffset = 0;
  const ITEMS_PER_LOAD = 20;
  // Add this function to get the currently selected time period
  function getCurrentTimePeriod() {
    const selectedOption = document.querySelector(".time-option.selected");
    return selectedOption
      ? selectedOption.getAttribute("data-value")
      : "short_term";
  }

  function handleScroll(container, loadMoreFunction) {
    if (
      container.scrollLeft + container.clientWidth >=
      container.scrollWidth - 20
    ) {
      loadMoreFunction(getCurrentTimePeriod());
    }
  }

  // Update the event listeners for scrolling
  const artistsContainer = topArtistsList.parentElement;
  const tracksContainer = topTracksList.parentElement;

  artistsContainer.addEventListener("scroll", () =>
    handleScroll(artistsContainer, loadMoreArtists),
  );
  tracksContainer.addEventListener("scroll", () =>
    handleScroll(tracksContainer, loadMoreTracks),
  );

  function updateDisplay(period) {
    artistsOffset = 0;
    tracksOffset = 0;
    topArtistsList.innerHTML = "";
    topTracksList.innerHTML = "";
    loadMoreArtists(period);
    loadMoreTracks(period);
    updateTopGenres(period); // Add this line
  }

  function loadMoreArtists(period) {
    if (topArtistsSummary && topArtistsSummary[period]) {
      const artists = topArtistsSummary[period].slice(
        artistsOffset,
        artistsOffset + ITEMS_PER_LOAD,
      );
      displayArtists(artists);
      artistsOffset += ITEMS_PER_LOAD;
    }
  }

  function loadMoreTracks(period) {
    if (topTracksSummary && topTracksSummary[period]) {
      const tracks = topTracksSummary[period].slice(
        tracksOffset,
        tracksOffset + ITEMS_PER_LOAD,
      );
      displayTracks(tracks);
      tracksOffset += ITEMS_PER_LOAD;
    }
  }

  function displayArtists(artists) {
    const fragment = document.createDocumentFragment();
    artists.forEach((artist) => {
      const div = document.createElement("div");
      div.className = "grid-item";
      div.innerHTML = `
        <a href="${artist.spotify_url}" target="_blank" rel="noopener noreferrer">
          <img src="${artist.image_url || "/static/dist/img/default-artist.png"}" alt="${artist.name}" class="artist-image" loading="lazy">
          <p>${artist.name}</p>
        </a>
      `;
      addInteractions(div);
      fragment.appendChild(div);
    });
    topArtistsList.appendChild(fragment);
  }

  function displayTracks(tracks) {
    const fragment = document.createDocumentFragment();
    tracks.forEach((track) => {
      const div = document.createElement("div");
      div.className = "grid-item";
      div.innerHTML = `
        <a href="${track.spotify_url}" target="_blank" rel="noopener noreferrer">
          <img src="${track.image_url || "/static/dist/img/default-album.png"}" alt="${track.name}" class="track-image" loading="lazy">
          <p>${track.name}</p>
          <p class="artist-name">${track.artists.join(", ")}</p>
        </a>
      `;
      addInteractions(div);
      fragment.appendChild(div);
    });
    topTracksList.appendChild(fragment);
  }

  function addInteractions(element) {
    element.addEventListener("mouseenter", () => {
      element.style.transform = "scale(1.05)";
      element.style.transition = "transform 0.3s ease";
    });
    element.addEventListener("mouseleave", () => {
      element.style.transform = "scale(1)";
    });
  }

  function handleScroll(container, loadMoreFunction) {
    if (
      container.scrollLeft + container.clientWidth >=
      container.scrollWidth - 20
    ) {
      loadMoreFunction(timePeriodSelect.value);
    }
  }

  artistsContainer.addEventListener("scroll", () =>
    handleScroll(artistsContainer, loadMoreArtists),
  );
  tracksContainer.addEventListener("scroll", () =>
    handleScroll(tracksContainer, loadMoreTracks),
  );

  timeOptions.forEach((option) => {
    option.addEventListener("click", () => {
      timeOptions.forEach((opt) => opt.classList.remove("selected"));
      option.classList.add("selected");
      const selectedValue = option.getAttribute("data-value");
      updateDisplay(selectedValue);

      // Update the chart if it exists
      if (typeof updateChart === "function") {
        currentPeriod = selectedValue;
        updateChart();
      }
    });
  });

  // Initial display
  updateDisplay("short_term");

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
    const overlay = document.getElementById("genreOverlay");
    const genreTitle = document.getElementById("genre-title");
    const genreArtistsList = document.getElementById("genre-artists-list");
    const genreTracksList = document.getElementById("genre-tracks-list");

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

    overlay.style.display = "block";
  }

  // Add this function to close the overlay
  function closeGenreOverlay() {
    document.getElementById("genreOverlay").style.display = "none";
  }

  // Add event listener for the close button
  document
    .querySelector(".close-btn")
    .addEventListener("click", closeGenreOverlay);

  // Close the overlay if the user clicks outside of the content
  window.addEventListener("click", function (event) {
    if (event.target == document.getElementById("genreOverlay")) {
      closeGenreOverlay();
    }
  });

  // Modify the addGenreEventListeners function
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
            pointLabels: {
              font: 12,
            },
            ticks: {
              display: false, // Add this line to remove the numbers
            },
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
                return ` ${value.toFixed(2)}${unit ? " " + unit : ""}`;
              },
              afterLabel: function (context) {
                const feature = context.label.toLowerCase();
                const explanation = featureExplanations[feature];
                return wrapText(explanation, 40); // Wrap explanation text
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

    function wrapText(text, maxLength) {
      const words = text.split(" ");
      let lines = [];
      let currentLine = "";

      words.forEach((word) => {
        if ((currentLine + word).length <= maxLength) {
          currentLine += (currentLine ? " " : "") + word;
        } else {
          lines.push(currentLine);
          currentLine = word;
        }
      });
      lines.push(currentLine);

      return lines;
    }

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
      ];

      chart.update();
      clearMinMaxTrack();
    }

    function updateMinMaxTrack(feature, trackInfo, datasetLabel) {
      const minMaxContainer = document.getElementById("minMaxTrack");
      const value =
        datasetLabel === "Min"
          ? periodData[currentPeriod].min_values[feature]
          : periodData[currentPeriod].max_values[feature];
      const formattedValue = formatFeatureValue(feature, value);

      minMaxContainer.innerHTML = `
        <h4>${feature.charAt(0).toUpperCase() + feature.slice(1)}</h4>
        <p><strong>Track:</strong> ${trackInfo.name}</p>
        <p><strong>Artist:</strong> ${trackInfo.artists[0].name}</p>
        <p><strong>Value:</strong> ${formattedValue}</p>
      `;
    }

    function formatFeatureValue(feature, value) {
      switch (feature) {
        case "loudness":
          return `${value.toFixed(2)} dB`;
        case "tempo":
          return `${value.toFixed(2)} BPM`;
        case "popularity":
          return `${Math.round(value)}`;
        default:
          return value.toFixed(2);
      }
    }

    function clearMinMaxTrack() {
      const minMaxContainer = document.getElementById("minMaxTrack");
      minMaxContainer.innerHTML = "";
    }

    // Add controls
    const controlsContainer = document.createElement("div");
    controlsContainer.className = "audio-features-controls";
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

    // Initial update
    updateChart();
  }
  function displayPlaylists() {
    const playlistsList = document.getElementById("playlists");
    if (playlistSummary && playlistSummary.length > 0) {
      playlistsList.innerHTML = playlistSummary
        .map(
          (playlist) => `
      <li>
        <a href="https://open.spotify.com/playlist/${playlist.id}" target="_blank" rel="noopener noreferrer" class="playlist-item">
          <img src="${playlist.image_url || "/static/dist/img/default-playlist.png"}" alt="${playlist.name}" class="playlist-image">
          <div class="playlist-info">
            <span class="playlist-name">${playlist.name}</span>
            <span class="playlist-visibility">${playlist.public ? "Public" : "Private"}</span>
          </div>
        </a>
      </li>
      `,
        )
        .join("");
    } else {
      playlistsList.innerHTML = "<li>No playlists available</li>";
    }
  }

  function setupPlaylistToggle() {
    const playlistHeader = document.querySelector(".playlist-header");
    const playlistsList = document.getElementById("playlists");
    const toggleArrow = document.querySelector(".toggle-arrow");

    playlistHeader.addEventListener("click", () => {
      playlistsList.classList.toggle("hidden");
      toggleArrow.classList.toggle("open");
    });
  }

  // Initial display
  updateDisplay("short_term");
  displayPlaylists();
  setupPlaylistToggle();
  createEnhancedAudioFeaturesChart(audioFeaturesSummary, periodData);
});
