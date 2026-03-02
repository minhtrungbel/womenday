// static/js/profile.js
document.addEventListener("DOMContentLoaded", function () {

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
        musicBarEl.style.bottom    = 'calc(180px + 11vh)'; // xích xuống 3% so với trước (14vh → 11vh)
        musicBarEl.style.left      = barLeft;
        musicBarEl.style.transform = 'translateX(-50%)';
        musicBarEl.style.width     = barWidth;
      }

      // === GIFT BAR: xích xuống 3% so với trước ===
      if (giftBarEl) {
        giftBarEl.style.bottom    = 'calc(20px - 3vh)'; // xích xuống 3vh
        giftBarEl.style.left      = '50%';
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

  const isIOS_audio = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;

  // Hàm unlock + play audio sau gesture
  function unlockAndPlay() {
    sessionStorage.setItem("audio_allowed", "true");
    if (restoreAudioState()) {
      playAudio();
    } else {
      audio.currentTime = 0;
      playAudio();
    }
  }

  // iOS: hiện overlay "chạm để vào" để lấy gesture → unlock audio
  function showIOSOverlay() {
    if (document.getElementById("ios-audio-overlay")) return;

    const overlay = document.createElement("div");
    overlay.id = "ios-audio-overlay";
    overlay.innerHTML = `
      <div class="ios-overlay__inner">
        <div class="ios-overlay__icon">♪</div>
        <div class="ios-overlay__text">Chạm để vào</div>
        <div class="ios-overlay__sub">Trang có nhạc nền dành cho bạn 🌸</div>
      </div>
    `;
    overlay.style.cssText = [
      "position:fixed", "inset:0", "z-index:99999",
      "display:flex", "align-items:center", "justify-content:center",
      "background:linear-gradient(135deg,rgba(103,13,38,0.93) 0%,rgba(43,0,19,0.96) 100%)",
      "backdrop-filter:blur(10px)", "-webkit-backdrop-filter:blur(10px)",
      "cursor:pointer", "touch-action:manipulation",
      "transition:opacity 0.35s ease"
    ].join(";");

    overlay.querySelector(".ios-overlay__inner").style.cssText = [
      "display:flex", "flex-direction:column", "align-items:center", "gap:14px",
      "animation:ios-pulse 1.3s ease-in-out infinite alternate"
    ].join(";");

    overlay.querySelector(".ios-overlay__icon").style.cssText = [
      "font-size:3.8rem",
      "background:linear-gradient(to bottom,#FFDBE9,#FE94B2)",
      "-webkit-background-clip:text", "-webkit-text-fill-color:transparent",
      "background-clip:text",
      "filter:drop-shadow(0 0 20px rgba(254,148,178,0.8))"
    ].join(";");

    overlay.querySelector(".ios-overlay__text").style.cssText = [
      "font-family:'Bebas Neue','Samsung Sharp Bold',sans-serif",
      "font-size:2.6rem", "letter-spacing:4px",
      "background:linear-gradient(to right,#FFDBE9,#FE94B2)",
      "-webkit-background-clip:text", "-webkit-text-fill-color:transparent",
      "background-clip:text"
    ].join(";");

    overlay.querySelector(".ios-overlay__sub").style.cssText = [
      "font-family:'Samsung Sharp Bold',sans-serif",
      "font-size:0.88rem", "color:rgba(255,219,233,0.72)",
      "letter-spacing:0.4px"
    ].join(";");

    if (!document.getElementById("ios-overlay-style")) {
      const s = document.createElement("style");
      s.id = "ios-overlay-style";
      s.textContent = "@keyframes ios-pulse{from{transform:scale(0.96);opacity:0.82}to{transform:scale(1.04);opacity:1}}";
      document.head.appendChild(s);
    }

    function dismiss(e) {
      e.stopPropagation();
      overlay.style.opacity = "0";
      setTimeout(() => overlay.remove(), 380);
      unlockAndPlay();
    }
    overlay.addEventListener("touchstart", dismiss, { once: true, passive: false });
    overlay.addEventListener("click",      dismiss, { once: true });

    document.body.appendChild(overlay);
  }

  if (isIOS_audio) {
    // iOS: luôn hiện overlay vì autoplay bị chặn hoàn toàn
    showIOSOverlay();
  } else {
    // Non-iOS: thử autoplay, nếu fail thì tap bất kỳ đâu
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
    const unlockAudio = () => unlockAndPlay();
    document.body.addEventListener("click",      unlockAudio, { once: true });
    document.body.addEventListener("touchstart", unlockAudio, { once: true });
  }

  if (audioTrigger) {
    audioTrigger.addEventListener("click", () => unlockAndPlay());
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
