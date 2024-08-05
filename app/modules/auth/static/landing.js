// eslint-disable-next-line no-unused-vars
function handleAuthClick() {
  window.isArtGenerationRequest = true;
  window.showLoading(20000);
  window.onload = function () {
    if (window.isArtGenerationRequest) {
      window.hideLoading();

      window.isArtGenerationRequest = false;
    }
  };
}
