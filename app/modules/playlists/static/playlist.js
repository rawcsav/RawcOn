const toastContainer = document.getElementById("toastContainer");

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  toast.addEventListener("click", () => {
    closeToast(toast);
  });

  toastContainer.appendChild(toast);

  toast.offsetHeight;

  toast.classList.add("show");

  setTimeout(() => {
    closeToast(toast);
  }, 3000);
}

function closeToast(toast) {
  if (toast.timeoutId) {
    clearTimeout(toast.timeoutId);
  }

  if (toast.parentNode === toastContainer) {
    toast.classList.remove("show");
    setTimeout(() => {
      if (toast.parentNode === toastContainer) {
        toastContainer.removeChild(toast);
      }
    }, 300);
  }
}

function getCsrfToken() {
  return document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
}

const util = {
  toggleDivVisibility: (selector) => {
    const el = document.querySelector(selector);
    el.style.display = el.style.display === "none" ? "block" : "none";
  },
};

const chartModule = (() => {
  let myPieChart;

  let myPopularityChart;

  let myAudioFeaturesChart;

  const initCharts = (
    yearCountData,
    popularityDistribution,
    featureStats,
    genreData,
    genreScores,
  ) => {
    initYearPieChart(yearCountData);
    initPopularityChart(popularityDistribution);
    initAudioFeaturesChart(featureStats);
    initGenreBubbleChart(genreData, genreScores);
  };

  const initYearPieChart = (temporalStats) => {
    const yearCountData = temporalStats.year_count;

    const canvas = document.getElementById("YrPieChart");
    if (!canvas) {
      console.error("Cannot find canvas element with id 'YrPieChart'");
      return;
    }

    const ctx = canvas.getContext("2d");
    const labels = Object.keys(yearCountData);
    const data = Object.values(yearCountData);

    myPieChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: data,
            backgroundColor: [
              "rgba(255, 99, 132, 0.5)",
              "rgba(54, 162, 235, 0.5)",
              "rgba(255, 206, 86, 0.5)",
              "rgba(75, 192, 192, 0.5)",
              "rgba(153, 102, 255, 0.5)",
              "rgba(255, 159, 64, 0.5)",
            ],
          },
        ],
      },
      options: {
        cutoutPercentage: 5,
        responsive: false,
        plugins: {
          title: {
            display: true,
            text: "Playlist Temporal Data",
            font: {
              size: 18,
              weight: "bold",
            },
            padding: {
              top: 10,
              bottom: 10,
            },
          },
          legend: {
            position: "bottom",
            labels: { boxWidth: 10, padding: 20 },
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label;
                const value = context.raw;
                return `${label}:\u00A0${value}\u00A0tracks`;
              },
            },
          },
        },
      },
    });
  };

  const initPopularityChart = (popularityData) => {
    const ctx = document.getElementById("popularityChart");

    const data = popularityData.distribution.filter(
      (item) => item.popularity > 0,
    );

    const bucketSize = 5;
    const buckets = Array.from({ length: 20 }, (_, i) => ({
      x: i * bucketSize + bucketSize / 2,
      y: 0,
      count: 0,
    }));

    data.forEach((item) => {
      const bucketIndex = Math.floor((item.popularity - 1) / bucketSize);
      if (bucketIndex >= 0 && bucketIndex < buckets.length) {
        buckets[bucketIndex].y += item.frequency;
        buckets[bucketIndex].count += item.count;
      }
    });

    new Chart(ctx, {
      type: "bar",
      data: {
        labels: buckets.map(
          (b) => `${b.x - bucketSize / 2 + 1}-${b.x + bucketSize / 2}`,
        ),
        datasets: [
          {
            label: "Track Distribution",
            data: buckets.map((b) => b.y),
            backgroundColor: [
              "rgba(255, 99, 132, 0.2)",
              "rgba(255, 159, 64, 0.2)",
              "rgba(255, 205, 86, 0.2)",
              "rgba(75, 192, 192, 0.2)",
              "rgba(54, 162, 235, 0.2)",
              "rgba(153, 102, 255, 0.2)",
              "rgba(201, 203, 207, 0.2)",
            ],
            borderColor: [
              "rgb(255, 99, 132)",
              "rgb(255, 159, 64)",
              "rgb(255, 205, 86)",
              "rgb(75, 192, 192)",
              "rgb(54, 162, 235)",
              "rgb(153, 102, 255)",
              "rgb(201, 203, 207)",
            ],
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 20,
            right: 25,
            bottom: 20,
            left: 25,
          },
        },
        scales: {
          x: {
            title: {
              display: true,
              text: "Popularity Score Range",
              font: { size: 16, weight: "bold" },
            },
            grid: {
              display: false,
            },
          },
          y: {
            title: {
              display: true,
              text: "Percentage of Tracks",
              font: { size: 16, weight: "bold" },
            },
            ticks: {
              callback: (value) => `${(value * 100).toFixed(1)}%`,
            },
            grid: {
              color: "rgba(0, 0, 0, 0.1)",
            },
          },
        },
        plugins: {
          title: {
            display: true,
            text: "Track Popularity Distribution",
            font: {
              size: 18,
              weight: "bold",
            },
            padding: {
              top: 10,
              bottom: 10,
            },
          },
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (tooltipItems) => {
                return `Popularity:\u00A0${tooltipItems[0].label}`;
              },
              label: (context) => {
                const bucketIndex = context.dataIndex;
                const bucket = buckets[bucketIndex];
                const percentage = (bucket.y * 100).toFixed(2);
                return [
                  `Tracks:\u00A0${bucket.count}`,
                  `Percentage:\u00A0${percentage}`,
                ];
              },
            },
          },
        },
      },
    });
  };

  const initAudioFeaturesChart = (featureStats) => {
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

    myAudioFeaturesChart = new Chart(ctx, {
      type: "radar",
      data: {
        labels: features,
        datasets: [
          {
            label: "Average",
            data: features.map((feature) =>
              normalizeFeature(feature, featureStats[feature].avg),
            ),
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
              normalizeFeature(feature, featureStats[feature].min[1]),
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
              normalizeFeature(feature, featureStats[feature].max[1]),
            ),
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            borderColor: "rgb(54, 162, 235)",
            pointBackgroundColor: "rgb(54, 162, 235)",
            pointBorderColor: "#fff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "rgb(54, 162, 235)",
          },
        ],
      },
      options: {
        responsive: true,
        showTooltips: true,
        scales: {
          r: {
            angleLines: { display: false },
            suggestedMin: 0,
            suggestedMax: 1,
            pointLabels: {
              font: {
                size: 12,
              },
            },
            ticks: {
              display: false,
            },
          },
        },
        plugins: {
          title: {
            display: true,
            text: "Playlist Audio Features",
            font: {
              size: 18,
              weight: "bold",
            },
            padding: {
              top: 10,
              bottom: 10,
            },
          },
          legend: {
            display: true,
            position: "bottom",
            labels: {
              font: {
                size: 12,
              },
              padding: 20,
            },
            align: "center",
          },
          tooltip: {
            enabled: true,
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
                return wrapText(explanation, 40);
              },
            },
          },
        },
        onHover: (event, activeElements) => {
          if (activeElements.length > 0) {
            const element = activeElements[0];
            const datasetIndex = element.datasetIndex;
            const index = element.index;
            const feature = features[index];

            const datasetLabel =
              datasetIndex === 0
                ? "Average"
                : datasetIndex === 1
                  ? "Min"
                  : datasetIndex === 2
                    ? "Max"
                    : null;

            let trackInfo;
            if (datasetLabel === "Min") {
              trackInfo = featureStats[feature].min;
            } else if (datasetLabel === "Max") {
              trackInfo = featureStats[feature].max;
            }

            if (trackInfo) {
              updateMinMaxTrack(
                feature,
                [
                  trackInfo[0],
                  trackInfo[1],
                  trackInfo[2],
                  trackInfo[3],
                  trackInfo[4],
                ],
                datasetLabel,
              );
            }
          }
        },
      },
    });
  };

  function updateMinMaxTrack(feature, trackInfo, datasetLabel) {
    const minMaxContainer = document.getElementById("minMaxTrack");
    const [trackName, value, trackUrl, artistName, albumArt] = trackInfo;
    const formattedValue = formatFeatureValue(feature, value);

    const titleClass =
      datasetLabel === "Min"
        ? "minmax-title-min"
        : datasetLabel === "Max"
          ? "minmax-title-max"
          : "minmax-title-avg";

    minMaxContainer.innerHTML = `
        <h4 id="minmax-title" class="${titleClass}">
            ${feature.charAt(0).toUpperCase() + feature.slice(1)}&nbsp;~&nbsp;${formattedValue}
        </h4>
        <div class="track-info">
            <img src="${albumArt || "/static/dist/img/default-album.svg"}" alt="${trackName}" class="album-art">
            <div class="track-details">
                <p class="minmax-track" title="${trackName}">${trackName}</p>
                <p class="minmax-artist artist-name" title="${artistName}">${artistName}</p>
                <div class="spotify-button" aria-label="Listen on Spotify">
                    <i class="rawcon-spotify" onclick="window.open('${trackUrl}', '_blank')"></i>
                    <span class="spotify-text">Listen on Spotify</span>
                </div>
            </div>
        </div>
    `;
  }

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

  const initGenreBubbleChart = (genreData, genreScores) => {
    const ctx = document.getElementById("genreBubbleChart").getContext("2d");

    const mainGenres = Object.entries(genreData).map(([genre, data]) => ({
      x: data.x,
      y: data.y,
      r: Math.sqrt(data.count) * 2,
      label: genre,
      count: data.count,
    }));

    const similarGenrePoints = genreScores.most_similar.map((genre) => ({
      x: genre.x,
      y: genre.y,
      r: 5,
      label: genre.genre,
      score: genre.similarity_score,
    }));

    const oppositeGenrePoints = genreScores.most_opposite.map((genre) => ({
      x: genre.x,
      y: genre.y,
      r: 5,
      label: genre.genre,
      score: genre.opposition_score,
    }));

    new Chart(ctx, {
      type: "bubble",
      data: {
        datasets: [
          {
            label: "Playlist Genres",
            data: mainGenres,
            backgroundColor: ["rgba(75, 192, 192, 0.5)"],
            borderColor: ["rgb(75, 192, 192)"],
          },
          {
            label: "Similar Genres",
            data: similarGenrePoints,
            backgroundColor: "rgba(54, 162, 235, 0.5)",
            borderColor: "rgb(54, 162, 235)",
          },
          {
            label: "Opposite Genres",
            data: oppositeGenrePoints,
            backgroundColor: "rgba(255, 99, 132, 0.5)",
            borderColor: "rgba(255, 99, 132, 1)",
          },
        ],
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        scales: {
          x: {
            title: {
              display: false,
              text: "Texture",
              font: {
                size: 14,
                weight: "bold",
              },
            },
            ticks: {
              align: "start",
              callback: function (value, index, values) {
                if (index === 0) return "Dense/Atmospheric";
                if (index === values.length - 1) return "Choppy/Bouncy/Sharp";
                return "";
              },
              crossAlign: "near",
              maxRotation: 0,
              autoSkip: false,
            },
          },
          y: {
            title: {
              display: false,
              text: "Production Style",
              font: {
                size: 14,
                weight: "bold",
              },
            },
            ticks: {
              align: "start",
              callback: function (value, index, values) {
                if (index === 0) return "Organic/Acoustic";
                if (index === values.length - 1) return "Synthetic/Mechanized";
                return "";
              },
            },
          },
        },
        plugins: {
          zoom: {
            zoom: {
              wheel: {
                enabled: true,
              },
              pinch: {
                enabled: true,
              },
              mode: "xy",
            },
            pan: {
              enabled: true,
            },
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const dataset = context.dataset.label;
                const label = context.raw.label;
                if (dataset === "Playlist Genres") {
                  return `${label}:\u00A0${context.raw.count}\u00A0tracks`;
                } else if (dataset === "Similar Genres") {
                  return `${label}`;
                } else {
                  return `${label}`;
                }
              },
            },
          },
          legend: {
            position: "bottom",
          },
          title: {
            display: true,
            text: "Distribution and Relationships",
            align: "center",
            font: {
              size: 18,
              weight: "bold",
            },
          },
        },
      },
    });
  };
  return { initCharts };
})();

const playlistActionsModule = (() => {
  const likeAllSongs = (playlistId) => {
    fetch(`/playlist/like_all_songs/${playlistId}`)
      .then((response) => response.text())
      .then((message) => showToast(message, "success"))
      .catch((error) =>
        showToast("An error occurred while liking all songs.", "error"),
      );
  };

  const unlikeAllSongs = (playlistId) => {
    fetch(`/playlist/unlike_all_songs/${playlistId}`)
      .then((response) => response.text())
      .then((message) => showToast(message, "success"))
      .catch((error) =>
        showToast(
          `An error occurred while unliking all songs: ${error}`,
          "error",
        ),
      );
  };

  const removeDuplicates = (playlistId) => {
    fetch(`/playlist/remove_duplicates/${playlistId}`)
      .then(() => showToast("Successfully removed duplicates.", "success"))
      .catch((error) =>
        showToast(
          `An error occurred while removing duplicates: ${error}`,
          "error",
        ),
      );
  };

  const reorderPlaylist = (playlistId, criterion) => {
    fetch(`/playlist/playlist/${playlistId}/reorder`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
        "X-Long-Running": "true",
      },
      body: JSON.stringify({ sorting_criterion: criterion }),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((data) => Promise.reject(data));
        }
        return response.json();
      })
      .then((data) => {
        showToast(
          data.message || "Playlist reordered successfully.",
          data.type || "success",
        );
      })
      .catch((error) => {
        if (error && error.message) {
          showToast(error.message, error.type || "error");
        } else {
          showToast(
            `An error occurred while reordering the playlist: ${error}`,
            "error",
          );
        }
      });
  };

  return { likeAllSongs, unlikeAllSongs, removeDuplicates, reorderPlaylist };
})();

const recommendationModule = (() => {
  let recommendationsFetched = false;
  let eventListenersAttached = false;

  const getPLRecommendations = async (playlistId) => {
    try {
      const response = await fetch(
        `/playlist/get_pl_recommendations/${playlistId}/recommendations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
        },
      );
      const data = await response.json();
      util.toggleDivVisibility(".results-title-spot");
      displayRecommendations(data.recommendations);

      if (!eventListenersAttached) {
        attachEventListeners(playlistId);
        eventListenersAttached = true;
      }

      recommendationsFetched = true;
    } catch (error) {
      console.error("Error:", error);
      showToast("An error occurred while fetching recommendations.", "error");
    }
  };

  const attachEventListeners = (playlistId) => {
    const resultsContainer = document.getElementById("results");
    resultsContainer.addEventListener("click", (event) => {
      const target = event.target.closest(".add-to-playlist, .add-to-saved");
      if (!target) return;

      event.preventDefault();
      const trackId = target.dataset.trackid;

      if (target.classList.contains("add-to-playlist")) {
        const plusIcon = target.querySelector("i");
        if (plusIcon.classList.contains("rawcon-circle-minus")) {
          trackActionsModule.removeFromPlaylist(playlistId, trackId, plusIcon);
        } else {
          trackActionsModule.addToPlaylist(playlistId, trackId, plusIcon);
        }
      } else if (target.classList.contains("add-to-saved")) {
        const heartIcon = target.querySelector("i");
        if (heartIcon.classList.contains("rawcon-spotify-liked")) {
          trackActionsModule.unsaveTrack(trackId, heartIcon);
        } else {
          trackActionsModule.saveTrack(trackId, heartIcon);
        }
      }
    });
  };

  const createTrackElement = (trackInfo) => {
    const div = document.createElement("div");
    div.className = "result-item";
    div.innerHTML = `
      <div class="result-cover-art-container">
        <div class="cover-art-container">
          <img src="${trackInfo.cover_art}" alt="Cover Art" class="result-cover-art">
        </div>
        <div class="caption">
          <h2 title="${trackInfo.trackName}"><i class="rawcon-music"></i>${trackInfo.trackName}</h2>
          <p title="${trackInfo.artist}"><i class="rawcon-user-music"></i>${trackInfo.artist}</p>
          <a href="${trackInfo.trackUrl}" target="_blank" rel="noopener noreferrer">
            <i class="rawcon-spotify"></i>Play on Spotify
          </a>
        </div>
        ${
          trackInfo.preview
            ? `<div class="preview play-button noselect" id="play_${trackInfo.trackid}" 
                data-tooltip-play="Play Preview" 
                data-tooltip-pause="Pause Preview">
                <i class="rawcon-play"></i>
               </div>`
            : `<div class="no-preview">Preview N/A</div>`
        }
      </div>
      <div class="dropdown-content">
      <a href="#" class="add-to-saved" data-trackid="${trackInfo.trackid}" 
         data-tooltip-liked="Remove from Liked Songs" 
         data-tooltip-unliked="Add to Liked Songs">
        <i class="heart-icon ${
          trackInfo.is_saved ? "rawcon-spotify-liked" : "rawcon-spotify-like"
        }"></i>
      </a>
        <a href="#" class="add-to-playlist" data-trackid="${trackInfo.trackid}" 
           data-tooltip="Add to Playlist" 
           data-tooltip-added="Remove from Playlist" 
           data-tooltip-unadded="Add to Playlist">
          <i class="plus-icon rawcon-album-plus"></i>
        </a>
      </div>
      ${
        trackInfo.preview
          ? `<audio class="audio-player" id="audio_${trackInfo.trackid}">
               <source src="${trackInfo.preview}" type="audio/mpeg">
               Your browser does not support the audio element.
             </audio>`
          : ""
      }
    `;
    return div;
  };

  const displayRecommendations = (recommendations) => {
    const resultsContainer = document.getElementById("results");
    resultsContainer.innerHTML = "";
    recommendations.forEach((trackInfo) => {
      const trackElement = createTrackElement(trackInfo);
      resultsContainer.appendChild(trackElement);
      audioModule.setupPlayToggle(trackInfo.trackid);
    });
  };

  return {
    getPLRecommendations,
    recommendationsFetched,
  };
})();

const audioModule = (() => {
  let currentPlayingAudio = null;

  const setupPlayToggle = (trackId) => {
    const playButton = document.getElementById(`play_${trackId}`);
    const audioPlayer = document.getElementById(`audio_${trackId}`);
    if (!playButton || !audioPlayer) {
      console.warn(
        `Play button or audio player not found for track ${trackId}`,
      );
      return;
    }
    const playIcon = playButton.querySelector("i");

    playButton.addEventListener("click", () => {
      if (currentPlayingAudio && currentPlayingAudio !== audioPlayer) {
        currentPlayingAudio.pause();
        currentPlayingAudio.currentTime = 0;
        const playingId = currentPlayingAudio
          .getAttribute("id")
          .replace("audio_", "");
        document
          .getElementById(`play_${playingId}`)
          .querySelector("i").className = "rawcon-play";
      }

      if (audioPlayer.paused) {
        audioPlayer.play();
        playIcon.className = "rawcon-pause";
        currentPlayingAudio = audioPlayer;
      } else {
        audioPlayer.pause();
        playIcon.className = "rawcon-play";
        currentPlayingAudio = null;
      }
    });
  };

  return { setupPlayToggle };
})();

const trackActionsModule = (() => {
  const addToPlaylist = (playlistId, trackId, plusIcon) => {
    fetch("/recs/add_to_playlist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ playlist_id: playlistId, track_id: trackId }),
    })
      .then(() => {
        showToast("Track added to playlist successfully!", "success");
        plusIcon.classList.remove("rawcon-album-plus");
        plusIcon.classList.add("rawcon-circle-minus", "added");
      })
      .catch((error) => {
        showToast(
          "An error occurred while adding the track to the playlist.",
          "error",
        );
        console.error("Error:", error);
      });
  };

  const removeFromPlaylist = (playlistId, trackId, plusIcon) => {
    fetch("/recs/remove_from_playlist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ playlist_id: playlistId, track_id: trackId }),
    })
      .then(() => {
        showToast("Track removed from playlist successfully!", "success");
        plusIcon.classList.remove("rawcon-circle-minus", "added");
        plusIcon.classList.add("rawcon-album-plus");
      })
      .catch((error) => {
        showToast(
          "An error occurred while removing the track from the playlist.",
          "error",
        );
        console.error("Error:", error);
      });
  };

  const saveTrack = async (trackId, heartIcon) => {
    try {
      const response = await fetch("/recs/save_track", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ track_id: trackId }),
      });

      if (response.ok) {
        showToast("Added to Liked Songs.", "success");

        heartIcon.classList.remove("rawcon-spotify-like");

        heartIcon.classList.add("rawcon-spotify-liked");
      } else {
        throw new Error("Failed to save track");
      }
    } catch (error) {
      showToast("Error liking track. Please try again.", "error");
      console.error("Error:", error);
    }
  };

  const unsaveTrack = async (trackId, heartIcon) => {
    try {
      const response = await fetch("/recs/unsave_track", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ track_id: trackId }),
      });

      if (response.ok) {
        showToast("Removed from Liked Songs.", "success");

        heartIcon.classList.remove("rawcon-spotify-liked");

        heartIcon.classList.add("rawcon-spotify-like");
      } else {
        throw new Error("Failed to unsave track");
      }
    } catch (error) {
      showToast("Error unliking track. Please try again.", "error");
      console.error("Error:", error);
    }
  };

  return { addToPlaylist, removeFromPlaylist, saveTrack, unsaveTrack };
})();

const uiModule = (() => {
  const setupEventListeners = (playlistId) => {
    document.querySelectorAll(".data-view-btn").forEach((btn) => {
      btn.addEventListener("click", function () {
        document
          .querySelectorAll(".data-view-btn")
          .forEach((b) => b.classList.remove("active"));
        this.classList.add("active");
        const dataViewToShow = this.id.replace("-btn", "");
        document
          .querySelectorAll(".data-view")
          .forEach((view) => (view.style.display = "none"));
        document.getElementById(dataViewToShow).style.display = "block";
      });
    });

    document
      .getElementById("like-all-songs-btn")
      .addEventListener("click", () =>
        playlistActionsModule.likeAllSongs(playlistId),
      );
    document
      .getElementById("unlike-all-songs-btn")
      .addEventListener("click", () =>
        playlistActionsModule.unlikeAllSongs(playlistId),
      );

    document
      .getElementById("recommendations-btn")
      .addEventListener("click", (event) => {
        event.preventDefault();
        if (!recommendationModule.recommendationsFetched) {
          recommendationModule.getPLRecommendations(playlistId);
        } else {
          util.toggleDivVisibility(".results-title-spot");
        }
      });
    const reorderButtons = [
      { id: "order-desc-btn", criterion: "Date Added - Descending" },
      { id: "order-asc-btn", criterion: "Date Added - Ascending" },
      { id: "rd-asc-btn", criterion: "Release Date - Ascending" },
      { id: "rd-desc-btn", criterion: "Release Date - Descending" },
      { id: "shuffle-btn", criterion: "Shuffle" },
    ];

    reorderButtons.forEach((button) => {
      document
        .getElementById(button.id)
        .addEventListener("click", () =>
          playlistActionsModule.reorderPlaylist(playlistId, button.criterion),
        );
    });

    document.querySelectorAll("#genre-counts > ul > li").forEach((item) => {
      item.addEventListener("click", function () {
        const artistList = this.querySelector(".artist-genre-list");
        artistList.style.display =
          artistList.style.display === "none" || artistList.style.display === ""
            ? "block"
            : "none";
      });
    });
  };

  const setupIntersectionObserver = () => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate");
        } else {
          entry.target.classList.remove("animate");
        }
      });
    });

    document.querySelectorAll(".data-view").forEach((element) => {
      observer.observe(element);
    });
  };

  return { setupEventListeners, setupIntersectionObserver };
})();

document.addEventListener("DOMContentLoaded", function () {
  const dataContainer = document.getElementById("data-container");
  let yearCountData = dataContainer.dataset.yearCount;
  const playlistId = dataContainer.dataset.playlistId;
  let popDistribution = dataContainer.dataset.popularityDistribution;
  let featureStats = dataContainer.dataset.featureStats;
  let genreData = dataContainer.dataset.genreData;
  let genreScores = dataContainer.dataset.genreScores;

  try {
    yearCountData = JSON.parse(yearCountData);
    popDistribution = JSON.parse(popDistribution);
    featureStats = JSON.parse(featureStats);
    genreData = JSON.parse(genreData);
    genreScores = JSON.parse(genreScores);
  } catch (error) {
    console.error("Error parsing data:", error);
  }

  chartModule.initCharts(
    yearCountData,
    popDistribution,
    featureStats,
    genreData,
    genreScores,
  );

  uiModule.setupEventListeners(playlistId);

  uiModule.setupIntersectionObserver();
});
