// static/js/profile.js
document.addEventListener("DOMContentLoaded", function () {
  const audio = document.getElementById("profile-audio");
  const audioPrompt = document.getElementById("audio-prompt");
  const playButton = document.getElementById("play-audio");
  const backButton = document.getElementById("back-button");

  if (!audio) return;

  let isPlaying = false;
  let fadeInInterval = null;
  const SESSION_KEY = "profile_audio_state";

  // Lưu trạng thái để khôi phục khi quay lại tab
  function saveAudioState() {
    sessionStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        src: audio.src,
        currentTime: audio.currentTime,
        loop: audio.loop,
      })
    );
  }

  function restoreAudioState() {
    const saved = sessionStorage.getItem(SESSION_KEY);
    if (!saved) return false;
    const state = JSON.parse(saved);
    if (state.src !== audio.src) return false;
    audio.currentTime = state.currentTime;
    return true;
  }

  function fadeIn() {
    audio.volume = 0;
    let vol = 0;
    fadeInInterval = setInterval(() => {
      vol = Math.min(vol + 0.1, 1);
      audio.volume = vol;
      if (vol >= 1) clearInterval(fadeInInterval);
    }, 100);
  }

  function fadeOut() {
    clearInterval(fadeInInterval);
    let vol = audio.volume;
    const interval = setInterval(() => {
      vol = Math.max(vol - 0.1, 0);
      audio.volume = vol;
      if (vol <= 0) {
        audio.pause();
        clearInterval(interval);
      }
    }, 50);
  }

  function playAudio() {
    if (isPlaying) return;
    audio
      .play()
      .then(() => {
        isPlaying = true;
        fadeIn();
        if (audioPrompt) audioPrompt.style.display = "none";
        saveAudioState();
      })
      .catch((err) => {
        console.warn("Autoplay bị chặn:", err);
        if (audioPrompt) audioPrompt.style.display = "block";
      });
  }

  function stopAudio() {
    if (!isPlaying) return;
    fadeOut();
    isPlaying = false;
    saveAudioState();
  }

  // === TỰ ĐỘNG PHÁT KHI VÀO TRANG (nếu đã tương tác) ===
  if (sessionStorage.getItem("audio_allowed") === "true") {
    setTimeout(() => {
      if (restoreAudioState()) {
        playAudio();
      } else {
        audio.currentTime = 0;
        playAudio();
      }
    }, 0);
  } else {
    if (audioPrompt) audioPrompt.style.display = "block";
  }

  // === DỰ PHÒNG: CHẠM ĐẦU TIÊN ===
  const unlockAudio = () => {
    playAudio();
    sessionStorage.setItem("audio_allowed", "true");
    document.body.removeEventListener("click", unlockAudio);
    document.body.removeEventListener("touchstart", unlockAudio);
  };
  document.body.addEventListener("click", unlockAudio, { once: true });
  document.body.addEventListener("touchstart", unlockAudio, {
    once: true,
  });

  // Nút phát
  if (playButton) {
    playButton.addEventListener("click", () => {
      playAudio();
      sessionStorage.setItem("audio_allowed", "true");
    });
  }

  // Nút quay lại
  if (backButton) {
    backButton.addEventListener("click", function (e) {
      e.preventDefault();
      this.classList.add("tapped");
      stopAudio();
      sessionStorage.removeItem("audio_allowed");
      sessionStorage.removeItem(SESSION_KEY);
      setTimeout(() => (location.href = this.href), 150);
    });
  }

  // === XỬ LÝ RA / VÀO TAB (iOS & Android) ===
  let wasHidden = false;
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      wasHidden = true;
      stopAudio();
    } else if (
      wasHidden &&
      sessionStorage.getItem("audio_allowed") === "true"
    ) {
      // Khôi phục vị trí nhạc trước khi tắt
      if (restoreAudioState()) {
        playAudio();
      }
      wasHidden = false;
    }
  });

  // === DỌN DẸP KHI RỜI TRANG ===
  const cleanup = () => {
    stopAudio();
    sessionStorage.removeItem(SESSION_KEY);
  };
  window.addEventListener("pagehide", cleanup);
  window.addEventListener("beforeunload", cleanup);
});
