// static/js/profile.js
document.addEventListener("DOMContentLoaded", function () {

  // ==================== TOUCH HOVER EFFECT (1-2s rồi về bình thường) ====================
  function addTouchHover(el, duration = 1200) {
    if (!el) return;
    el.addEventListener("touchstart", () => {
      el.classList.add("touch-hover");
    }, { passive: true });
    el.addEventListener("touchend", () => {
      setTimeout(() => el.classList.remove("touch-hover"), duration);
    }, { passive: true });
    el.addEventListener("touchcancel", () => {
      el.classList.remove("touch-hover");
    }, { passive: true });
  }

  addTouchHover(document.getElementById("music-bar-btn"), 1200);
  addTouchHover(document.getElementById("gift-bar-btn"), 1200);
  addTouchHover(document.querySelector(".gift-bar__pill"), 1200);

  // ==================== IOS SAFARI: fix toàn bộ layout dùng bottom thay top ====================
  // Safari mobile có thanh địa chỉ ở dưới + 100vh không chính xác
  // → dùng bottom thay top cho mọi element cần canh vị trí trên mobile iOS
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

  if (isIOS) {
    const musicBarEl    = document.getElementById('music-bar');
    const giftBarEl     = document.getElementById('gift-bar');

    // Tính navbar height thực tế
    function getNavbarHeight() {
      const navbar = document.querySelector('.navbar');
      return navbar ? navbar.offsetHeight : 58;
    }

    function applyIOSLayout() {
      const vw = window.innerWidth;
      const navH = getNavbarHeight();

      // Chỉ can thiệp trên mobile (< 796px)
      if (vw >= 796) {
        // Reset về CSS gốc cho tablet/desktop
        if (musicBarEl) {
          musicBarEl.style.cssText = '';
        }
        if (giftBarEl) {
          giftBarEl.style.cssText = '';
        }
        return;
      }

      // === MUSIC BAR: dùng bottom thay top để tránh thanh Safari che ===
      if (musicBarEl) {
        // Tính width theo breakpoint
        let barWidth, barLeft;
        if (vw <= 359) {
          barWidth = Math.min(Math.max(vw * 0.46, 148), 175) + 'px';
          barLeft = '28%';
        } else if (vw <= 414) {
          barWidth = Math.min(Math.max(vw * 0.50, 175), 210) + 'px';
          barLeft = '32%';
        } else if (vw <= 576) {
          barWidth = Math.min(Math.max(vw * 0.54, 183), 222) + 'px';
          barLeft = '34%';
        } else {
          barWidth = Math.min(Math.max(vw * 0.56, 190), 240) + 'px';
          barLeft = '40%';
        }
        musicBarEl.style.top       = '';
        musicBarEl.style.bottom    = '180px'; // trên thanh Safari + gift bar
        musicBarEl.style.left      = barLeft;
        musicBarEl.style.transform = 'translateX(-50%)';
        musicBarEl.style.width     = barWidth;
      }

      // === GIFT BAR: đã dùng bottom trong CSS nên chỉ cần đảm bảo an toàn với Safari ===
      if (giftBarEl) {
        // Safari bottom bar cao ~83px, ta thêm buffer
        giftBarEl.style.bottom = '20px';
        giftBarEl.style.left   = '50%';
        giftBarEl.style.transform = 'translateX(-50%)';
      }
    }

    applyIOSLayout();
    window.addEventListener('resize', applyIOSLayout);
    // Safari thay đổi viewport khi scroll → recalc
    window.addEventListener('scroll', applyIOSLayout, { passive: true });
  }

  // ==================== AUDIO ====================
  const audio        = document.getElementById("profile-audio");
  const audioTrigger = document.getElementById("audio-trigger");
  const backButton   = document.getElementById("back-button");

  if (!audio) return;

  let isPlaying     = false;
  let fadeInInterval = null;
  const SESSION_KEY  = "profile_audio_state";

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
      });
  }

  function stopAudio() {
    if (!isPlaying) return;
    fadeOut();
    isPlaying = false;
    saveAudioState();
  }

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

  const unlockAudio = () => {
    playAudio();
    sessionStorage.setItem("audio_allowed", "true");
  };
  document.body.addEventListener("click",      unlockAudio, { once: true });
  document.body.addEventListener("touchstart", unlockAudio, { once: true });

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
    syncBarState();
  }

  // === GIFT BAR → chuyển sang trang letter ===
  const giftBarBtn = document.getElementById('gift-bar-btn');
  if (giftBarBtn) {
    giftBarBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const params = new URLSearchParams(window.location.search);
      const name = params.get('name');
      if (name) {
        const url = new URL('/letter', window.location.origin);
        url.searchParams.set('name', name);
        location.href = url.toString();
      }
    });
  }

  const giftBarpill = document.querySelector('.gift-bar__pill');
  if (giftBarpill) {
    giftBarpill.addEventListener('click', (e) => {
      e.stopPropagation();
      const params = new URLSearchParams(window.location.search);
      const name = params.get('name');
      if (name) {
        const url = new URL('/letter', window.location.origin);
        url.searchParams.set('name', name);
        location.href = url.toString();
      }
    });
  }

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

  const cleanup = () => {
    stopAudio();
    sessionStorage.removeItem(SESSION_KEY);
  };
  window.addEventListener("pagehide",      cleanup);
  window.addEventListener("beforeunload",  cleanup);
});
