// static/js/profile.js
document.addEventListener("DOMContentLoaded", function () {
  const audio = document.getElementById("profile-audio");
  const audioTrigger = document.getElementById("audio-trigger");
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
        saveAudioState();
      })
      .catch((err) => {
        console.warn("Autoplay bị chặn:", err);
        // Không hiện UI gì, cơ chế unlock qua audio-trigger sẽ xử lý
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
  }

  // === DỰ PHÒNG: CHẠM / CLICK ĐẦU TIÊN BẤT KỲ ĐÂU ===
  const unlockAudio = () => {
    playAudio();
    sessionStorage.setItem("audio_allowed", "true");
  };
  document.body.addEventListener("click", unlockAudio, { once: true });
  document.body.addEventListener("touchstart", unlockAudio, { once: true });

  // === AUDIO TRIGGER: element vô hình, gán thêm listener nếu cần ===
  if (audioTrigger) {
    audioTrigger.addEventListener("click", () => {
      playAudio();
      sessionStorage.setItem("audio_allowed", "true");
    });
  }

  // === MUSIC BAR ===
  const bar    = document.getElementById('music-bar');
  const barBtn = document.getElementById('music-bar-btn');

  function syncBarState() {
    if (!bar) return;
    if (audio.paused) {
      bar.classList.remove('playing');
      bar.classList.add('paused');
    } else {
      bar.classList.add('playing');
      bar.classList.remove('paused');
    }
  }

  if (barBtn && audio) {
    barBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (audio.paused) {
        audio.play().then(() => {
          isPlaying = true;
          fadeIn();
          saveAudioState();
        }).catch(() => {});
      } else {
        fadeOut();
        isPlaying = false;
        saveAudioState();
      }
    });

    audio.addEventListener('play',  syncBarState);
    audio.addEventListener('pause', syncBarState);
    // sync ngay khi load
    syncBarState();
  }
// === GIFT BAR — chuyển sang /letter?name=... ===
const giftBarBtn = document.getElementById('gift-bar-btn');
if (giftBarBtn) {
  giftBarBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name') || '';
    const url = new URL('/letter', window.location.origin);
    if (name) url.searchParams.set('name', name);
    sessionStorage.setItem('audio_allowed', 'true');
    location.href = url.toString();
  });
}
const giftBar = document.getElementById('gift-bar');
if (giftBar) {
  giftBar.addEventListener('click', function (e) {
    e.stopPropagation();
    const params = new URLSearchParams(window.location.search);
    const name = params.get('name') || '';
    const url = new URL('/letter', window.location.origin);
    if (name) url.searchParams.set('name', name);
    sessionStorage.setItem('audio_allowed', 'true');
    location.href = url.toString();
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