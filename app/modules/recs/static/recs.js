const toastContainer = document.getElementById("toastContainer");

function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  toast.addEventListener("click", () => {
    closeToast(toast);
  });

  toastContainer.appendChild(toast);

  // Trigger reflow
  toast.offsetHeight;

  toast.classList.add("show");

  // Auto close after 3 seconds
  setTimeout(() => {
    closeToast(toast);
  }, 3000);
}

function closeToast(toast) {
  // Clear the timeout to prevent multiple close attempts
  if (toast.timeoutId) {
    clearTimeout(toast.timeoutId);
  }

  // Only proceed if the toast is still in the DOM
  if (toast.parentNode === toastContainer) {
    toast.classList.remove("show");
    setTimeout(() => {
      // Check again before removing, in case it was removed during the transition
      if (toast.parentNode === toastContainer) {
        toastContainer.removeChild(toast);
      }
    }, 300); // Wait for the transition to finish
  }
}

function getCsrfToken() {
  return document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");
}

const util = {
  debounce: (func, delay) => {
    let debounceTimer;
    return function (...args) {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => func.apply(this, args), delay);
    };
  },
  createElement: (tag, className, innerHTML) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (innerHTML) element.innerHTML = innerHTML;
    return element;
  },
};

// DOM elements
const elements = {
  searchInput: document.getElementById("universal-input"),
  searchButton: document.getElementById("universal-search"),
  searchDropdown: document.getElementById("search-dropdown"),
  seedsContainer: document.getElementById("universal-seeds-container"),
  trackSeedsInput: document.getElementById("track_seeds"),
  artistSeedsInput: document.getElementById("artist_seeds"),
  recommendationForm: document.querySelector("form"),
  resultsContainer: document.getElementById("results"),
  seedStep: document.getElementById("seed-step"),
  playlistModal: document.getElementById("playlistModal"),
  playlistOptions: document.getElementById("playlistOptions"),
  toast: document.getElementById("toast"),
};

// Search module
const searchModule = (() => {
  const performSearch = async (query) => {
    if (!query.trim()) {
      uiModule.hideDropdown();
      return;
    }

    try {
      const response = await fetch("/recs/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ query, type: "track,artist" }),
      });

      if (!response.ok) throw new Error("Network response was not ok");

      const data = await response.json();
      uiModule.displaySearchResults(data);
    } catch (error) {
      console.error("Search error:", error);
      showToast(
        "An error occurred while searching. Please try again.",
        "error",
      );
    }
  };

  return { performSearch };
})();

// Seeds module
const seedsModule = (() => {
  // Add this to the elements object at the beginning of the file
  elements.submitButton = document.querySelector('form button[type="submit"]');

  // Add this function to the seedsModule
  const updateSubmitButton = () => {
    const seedCount = elements.seedsContainer.children.length;
    elements.seedStep.visible = seedCount >= 1;
    elements.submitButton.disabled = seedCount === 0;
    elements.submitButton.classList.toggle("disabled", seedCount === 0);
    elements.seedStep.classList.toggle("hidden", seedCount >= 1);
  };
  const addToSeeds = (item, type) => {
    if (elements.seedsContainer.children.length >= 5) {
      showToast("You can select no more than 5 combined seeds.", "warning");
      return;
    }

    const seedElement = util.createElement("div", `seed-item ${type}`);
    seedElement.dataset.id = item.id;
    seedElement.dataset.type = type;

    const spotifyUrl = item.external_urls.spotify;
    seedElement.innerHTML = `
      <div class="seed-info">
        <a href="${spotifyUrl}" target="_blank" rel="noopener noreferrer" class="seed-name" title="${item.name}">${item.name}</a>
        <div class="seed-subtext">${type === "track" ? item.artists[0].name : "Artist"}</div>
      </div>
      <button class="remove-seed" aria-label="Remove seed">×</button>
    `;

    seedElement
      .querySelector(".remove-seed")
      .addEventListener("click", () => removeSeed(seedElement));

    elements.seedsContainer.appendChild(seedElement);
    updateSeedsInput();
    updateSeedCounter();
    updateSubmitButton(); // Add this line
  };
  const removeSeed = (seedElement) => {
    seedElement.remove();
    updateSeedsInput();
    updateSeedCounter(); // Update counter when a seed is added
    updateSubmitButton(); // Add this line
  };

  const updateSeedsInput = () => {
    const trackSeeds = [];
    const artistSeeds = [];

    elements.seedsContainer.querySelectorAll(".seed-item").forEach((seed) => {
      if (seed.dataset.type === "track") {
        trackSeeds.push(seed.dataset.id);
      } else if (seed.dataset.type === "artist") {
        artistSeeds.push(seed.dataset.id);
      }
    });

    elements.trackSeedsInput.value = trackSeeds.join(",");
    elements.artistSeedsInput.value = artistSeeds.join(",");
  };

  function updateSeedCounter() {
    const seedContainer = document.getElementById("universal-seeds-container");
    const seedCounter = document.getElementById("seed-counter");
    const seedCount = seedContainer.children.length;
    seedCounter.textContent = `${seedCount}/5`;
  }

  return {
    addToSeeds,
    removeSeed,
    updateSeedsInput,
    updateSeedCounter,
    updateSubmitButton, // Add this line
  };
})();

// UI module
const uiModule = (() => {
  const displaySearchResults = (data) => {
    elements.searchDropdown.innerHTML = "";

    const createResultElement = (item, type) => {
      const element = util.createElement("div", "dropdown-item");
      element.dataset.id = item.id;
      element.dataset.type = type;

      const imageUrl =
        type === "track" ? item.album.images[0]?.url : item.images[0]?.url;
      const spotifyUrl =
        type === "track"
          ? item.external_urls.spotify
          : item.external_urls.spotify;

      element.innerHTML = `
    <img src="${imageUrl || "/static/dist/img/default-track.svg"}" alt="${item.name}" class="result-image">
    <div class="result-info">
      <div class="result-name" title="${item.name}">${item.name}</div>
      <div class="result-subtext">${type === "track" ? item.artists[0].name : "Artist"}</div>
                    <div class="spotify-button" aria-label="Listen on Spotify">
          <i class="rawcon-spotify" onclick="window.open('${spotifyUrl}', '_blank')"></i>
          <span class="spotify-text">Listen on Spotify</span>
        </div>
    </div>
    <div class="result-actions">
      <button class="add-to-seeds" data-id="${item.id}" data-type="${type}" data-tooltip="Add to seeds">+</button>
    </div>
  `;

      element.querySelector(".add-to-seeds").addEventListener("click", (e) => {
        e.stopPropagation();
        seedsModule.addToSeeds(item, type);
        seedsModule.updateSeedCounter();
      });

      return element;
    };

    (data.tracks?.items || []).forEach((track) =>
      elements.searchDropdown.appendChild(createResultElement(track, "track")),
    );
    (data.artists?.items || []).forEach((artist) =>
      elements.searchDropdown.appendChild(
        createResultElement(artist, "artist"),
      ),
    );

    showDropdown();
  };

  const showDropdown = () => {
    elements.searchDropdown.style.display = "block";
    elements.searchInput.style.borderBottomLeftRadius = "0";
  };

  const hideDropdown = () => {
    elements.searchDropdown.style.display = "none";
    elements.searchInput.style.borderBottomLeftRadius = "4px";
  };

  const displayErrorMessage = (message) => {
    elements.searchDropdown.innerHTML = `<div class="error-message">${message}</div>`;
    showDropdown();
  };

  const displayRecommendations = (recommendations) => {
    elements.resultsContainer.innerHTML = "";

    recommendations.forEach((trackInfo) => {
      const trackElement = util.createElement("div", "result-item");
      trackElement.innerHTML = `
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
        <a href="#" class="add-to-saved" data-trackid="${trackInfo.trackid}" data-tooltip-liked="Remove from Liked Songs" data-tooltip-unliked="Add to Liked Songs">
          <i class="heart-icon rawcon-heart"></i>
        </a>
        <a href="#" class="add-to-playlist" data-trackid="${trackInfo.trackid}" data-tooltip="Add to Playlist">
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

      elements.resultsContainer.appendChild(trackElement);
      if (trackInfo.preview) {
        audioModule.setupPlayToggle(trackInfo.trackid);
      }
    });
  };
  return {
    displaySearchResults,
    showDropdown,
    hideDropdown,
    displayErrorMessage,
    displayRecommendations,
  };
})();

// Slider module
const sliderModule = (() => {
  const initMinMaxSlider = (sliderId, minInputId, maxInputId, config) => {
    const container = document.getElementById(sliderId);
    const minSlider = container.querySelector(".min-slider");
    const maxSlider = container.querySelector(".max-slider");
    const range = container.querySelector(".slider-range");
    const minValue = container.querySelector(".min-value");
    const maxValue = container.querySelector(".max-value");
    const minInput = document.getElementById(minInputId);
    const maxInput = document.getElementById(maxInputId);

    // Set initial values based on config
    minSlider.min = config.min;
    minSlider.max = config.max;
    maxSlider.min = config.min;
    maxSlider.max = config.max;
    minSlider.value = config.defaultMin;
    maxSlider.value = config.defaultMax;

    function updateSlider() {
      const minVal = parseInt(minSlider.value);
      const maxVal = parseInt(maxSlider.value);

      if (minVal > maxVal) {
        minSlider.value = maxVal;
      }

      const minPercent =
        ((minSlider.value - config.min) / (config.max - config.min)) * 100;
      const maxPercent =
        ((maxSlider.value - config.min) / (config.max - config.min)) * 100;

      range.style.left = minPercent + "%";
      range.style.width = maxPercent - minPercent + "%";

      if (config.isInteger) {
        minValue.textContent = minSlider.value;
        maxValue.textContent = maxSlider.value;
        minInput.value = minSlider.value;
        maxInput.value = maxSlider.value;
      } else {
        const minDisplayValue = (minSlider.value / 100).toFixed(2);
        const maxDisplayValue = (maxSlider.value / 100).toFixed(2);
        minValue.textContent = minDisplayValue;
        maxValue.textContent = maxDisplayValue;
        minInput.value = minDisplayValue;
        maxInput.value = maxDisplayValue;
      }
    }

    minSlider.addEventListener("input", updateSlider);
    maxSlider.addEventListener("input", updateSlider);

    updateSlider(); // Initial update
  };

  const initializeAllSliders = () => {
    const sliderConfigs = {
      popularity: {
        min: 0,
        max: 100,
        defaultMin: 0,
        defaultMax: 100,
        isInteger: true,
      },
      energy: {
        min: 0,
        max: 100,
        defaultMin: 0,
        defaultMax: 100,
        isInteger: false,
      },
      instrumentalness: {
        min: 0,
        max: 100,
        defaultMin: 0,
        defaultMax: 100,
        isInteger: false,
      },
      tempo: {
        min: 24,
        max: 208,
        defaultMin: 24,
        defaultMax: 208,
        isInteger: true,
      },
      danceability: {
        min: 0,
        max: 100,
        defaultMin: 0,
        defaultMax: 100,
        isInteger: false,
      },
      valence: {
        min: 0,
        max: 100,
        defaultMin: 0,
        defaultMax: 100,
        isInteger: false,
      },
    };

    Object.entries(sliderConfigs).forEach(([key, config]) => {
      initMinMaxSlider(`${key}_slider`, `min_${key}`, `max_${key}`, config);
    });
  };

  return { initializeAllSliders };
})();
// Recommendation module
const recommendationModule = (() => {
  const getRecommendations = async () => {
    const formData = new FormData(elements.recommendationForm);
    const data = Object.fromEntries(formData.entries());

    // Prepare the data object
    const requestData = {
      artist_seeds: data.artist_seeds || "",
      track_seeds: data.track_seeds || "",
      limit: data.limit || 10,
      min_popularity: data.min_popularity,
      max_popularity: data.max_popularity,
      min_energy: data.min_energy,
      max_energy: data.max_energy,
      min_instrumentalness: data.min_instrumentalness,
      max_instrumentalness: data.max_instrumentalness,
      min_tempo: data.min_tempo,
      max_tempo: data.max_tempo,
      min_danceability: data.min_danceability,
      max_danceability: data.max_danceability,
      min_valence: data.min_valence,
      max_valence: data.max_valence,
    };

    try {
      const response = await fetch("/recs/get_recommendations", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      uiModule.displayRecommendations(data.recommendations);
    } catch (error) {
      console.error("Error:", error);
      showToast(
        "An error occurred while getting recommendations. Please try again.",
        "error",
      );
    }
  };

  return { getRecommendations };
})();
// Audio playback module
const audioModule = (() => {
  let currentPlayingAudio = null;
  let currentPlayingButton = null;

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

    const updatePlayState = (isPlaying, button, icon) => {
      icon.className = isPlaying ? "rawcon-pause" : "rawcon-play";
      button.classList.toggle("playing", isPlaying);
    };

    const resetPreviousPlayer = () => {
      if (currentPlayingAudio && currentPlayingAudio !== audioPlayer) {
        currentPlayingAudio.pause();
        currentPlayingAudio.currentTime = 0;

        if (currentPlayingButton) {
          const previousIcon = currentPlayingButton.querySelector("i");
          updatePlayState(false, currentPlayingButton, previousIcon);
        }
      }
    };

    playButton.addEventListener("click", () => {
      resetPreviousPlayer();

      if (audioPlayer.paused) {
        audioPlayer.play();
        updatePlayState(true, playButton, playIcon);
        currentPlayingAudio = audioPlayer;
        currentPlayingButton = playButton;
      } else {
        audioPlayer.pause();
        updatePlayState(false, playButton, playIcon);
        currentPlayingAudio = null;
        currentPlayingButton = null;
      }
    });

    // Add ended event listener to reset the play button
    audioPlayer.addEventListener("ended", () => {
      updatePlayState(false, playButton, playIcon);
      currentPlayingAudio = null;
      currentPlayingButton = null;
    });
  };

  return { setupPlayToggle };
})();
// Playlist module
const playlistModule = (() => {
  const addToPlaylist = async (trackId, playlistId) => {
    try {
      const response = await fetch("/recs/add_to_playlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ track_id: trackId, playlist_id: playlistId }),
      });
      const data = await response.json();
      if (data.error) {
        throw new Error(data.error);
      }
      const plusIcon = document.querySelector(
        `.add-to-playlist[data-trackid="${trackId}"] .plus-icon`,
      );

      if (plusIcon) {
        plusIcon.classList.add("added");
      } else {
        console.log("Plus icon not found");
      }

      elements.playlistModal.style.display = "none";
      showToast("Track added to playlist successfully.", "success");
    } catch (error) {
      showToast("Error adding track to playlist. Please try again.", "error");
    }
  };
  const loadUserPlaylists = async () => {
    try {
      const response = await fetch("/recs/get-user-playlists");
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const playlists = await response.json();
      if (playlists.error) {
        throw new Error(playlists.error);
      } else {
        const playlistsHtml = playlists
          .map(
            (playlist) => `
            <div class="playlist-choice" data-playlistid="${playlist.id}">
              <div class="playlist-div">
                <img src="${playlist.cover_art}" alt="${playlist.name}" class="playlist-art">
                <h3 class="playlist-title" title="${playlist.name}">${playlist.name}</h3>
              </div>
            </div>
          `,
          )
          .join("");
        elements.playlistOptions.innerHTML = playlistsHtml;
      }
    } catch (error) {
      console.error(error);
      showToast("Failed to load playlists.", "error");
    }
  };

  return { addToPlaylist, loadUserPlaylists };
})();

// Track management module
const trackModule = (() => {
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
        heartIcon.classList.add("liked");
        // Update tooltip text through the parent anchor
        showToast("Added to Liked Songs.", "success");
      } else {
        throw new Error("Error liking the track");
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
        heartIcon.classList.remove("liked");
        // Update tooltip text through the parent anchor
      } else {
        throw new Error("Error unsaving the track");
      }
    } catch (error) {
      showToast("Error unliking track. Please try again.", "error");
      console.error("Error:", error);
    }
  };

  return { saveTrack, unsaveTrack };
})();
// Event listeners
document.addEventListener("DOMContentLoaded", () => {
  const debouncedSearch = util.debounce(searchModule.performSearch, 300);
  seedsModule.updateSubmitButton();

  elements.searchInput.addEventListener("input", (e) =>
    debouncedSearch(e.target.value),
  );
  elements.searchButton.addEventListener("click", () =>
    searchModule.performSearch(elements.searchInput.value),
  );

  elements.searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      searchModule.performSearch(elements.searchInput.value);
    }
  });

  document.addEventListener("click", (e) => {
    if (
      !elements.searchInput.contains(e.target) &&
      !elements.searchDropdown.contains(e.target)
    ) {
      uiModule.hideDropdown();
    }
  });

  elements.searchDropdown.addEventListener("click", (e) => {
    e.stopPropagation();
  });

  elements.recommendationForm.addEventListener("submit", (e) => {
    e.preventDefault();
    recommendationModule.getRecommendations();
  });

  // Event listener for saving/unsaving tracks
  document.addEventListener("click", function (event) {
    if (event.target.closest(".add-to-saved")) {
      event.preventDefault();
      const heartIcon = event.target
        .closest(".add-to-saved")
        .querySelector(".heart-icon");
      const trackId = event.target.closest(".add-to-saved").dataset.trackid;

      if (heartIcon.classList.contains("liked")) {
        trackModule.unsaveTrack(trackId, heartIcon);
      } else {
        trackModule.saveTrack(trackId, heartIcon);
      }
    }
  });

  // Event listener for adding tracks to playlist
  document.addEventListener("click", function (event) {
    if (event.target.closest(".add-to-playlist")) {
      event.preventDefault();
      const button = event.target.closest(".add-to-playlist");
      const trackId = button.dataset.trackid;
      elements.playlistModal.dataset.trackid = trackId;
      elements.playlistModal.dataset.button = button;
      elements.playlistModal.style.display = "block";
      playlistModule.loadUserPlaylists();
    }
  });

  // Event listener for selecting a playlist
  elements.playlistOptions.addEventListener("click", function (event) {
    if (event.target.closest(".playlist-choice")) {
      event.preventDefault();
      const playlistId =
        event.target.closest(".playlist-choice").dataset.playlistid;
      const trackId = elements.playlistModal.dataset.trackid;
      playlistModule.addToPlaylist(trackId, playlistId);
    }
  });

  // Close modal event listeners
  document.querySelectorAll(".close").forEach((closeButton) => {
    closeButton.addEventListener("click", function () {
      elements.playlistModal.style.display = "none";
    });
  });

  window.addEventListener("click", function (event) {
    if (event.target === elements.playlistModal) {
      elements.playlistModal.style.display = "none";
    }
  });
  sliderModule.initializeAllSliders();
});
