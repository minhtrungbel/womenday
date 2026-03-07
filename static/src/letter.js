/* letter.js - logic hop qua + popup mat khau */
(function () {
  var giftBox   = document.getElementById('letter-gift-box');
  var overlay   = document.getElementById('letter-pwd-overlay');
  var closeBtn  = document.getElementById('letter-pwd-close');
  var input     = document.getElementById('letter-pwd-input');
  var submitBtn = document.getElementById('letter-pwd-submit');
  var errorMsg  = document.getElementById('letter-pwd-error');

  /* Mat khau lay tu data-password tren #letter-gift-box */
  /* Neu rong hoac khong co -> bo qua popup, mo thang nap */
  var CORRECT_PASSWORD = giftBox ? (giftBox.dataset.password || '') : '';
  var HAS_PASSWORD     = CORRECT_PASSWORD.trim() !== '';
  var giftState = 'closed'; /* closed | ajar | open */

  /* ---- Lockout config ---- */
  var MAX_ATTEMPTS   = 5;
  var LOCKOUT_SEC    = 30;
  var failCount      = 0;
  var lockoutTimer   = null;
  var isLockedOut    = false;

  /* ---- Bat / tat input + submit ---- */
  function setInputDisabled(disabled) {
    if (input)     input.disabled     = disabled;
    if (submitBtn) submitBtn.disabled = disabled;
  }

  /* ---- Bat dau lockout 30s ---- */
  function startLockout() {
    isLockedOut = true;
    setInputDisabled(true);
    var remaining = LOCKOUT_SEC;

    showError('Vui lòng chờ ' + remaining + 's...');

    lockoutTimer = setInterval(function () {
      remaining -= 1;
      if (remaining > 0) {
        showError('Vui lòng chờ ' + remaining + 's...');
      } else {
        clearInterval(lockoutTimer);
        lockoutTimer  = null;
        isLockedOut   = false;
        failCount     = 0;
        setInputDisabled(false);
        hideError();
        if (input) { input.value = ''; input.focus(); }
      }
    }, 1000);
  }

  /* ---- Helper hien / an error ---- */
  var attemptsSpan = document.getElementById('letter-pwd-attempts');

  function showError(attemptsText) {
    if (!errorMsg) return;
    if (attemptsSpan) attemptsSpan.textContent = attemptsText || '';
    errorMsg.classList.add('show');
  }
  function hideError() {
    if (errorMsg) errorMsg.classList.remove('show');
    if (attemptsSpan) attemptsSpan.textContent = '';
  }

  /* ---- Mo popup ---- */
  function openPopup() {
    if (!overlay) return;
    overlay.classList.add('active');
    hideError();
    if (input) {
      input.value = '';
      setTimeout(function () { input.focus(); }, 300);
    }
    if (isLockedOut) setInputDisabled(true);
  }

  /* ---- Dong popup ---- */
  function closePopup() {
    if (overlay) overlay.classList.remove('active');
  }

  /* ---- He nap hop qua ---- */
  function openLid() {
    giftState = 'ajar';
    if (giftBox) giftBox.classList.add('lid-ajar');
  }

  /* ---- Rung dien thoai ---- */
  function triggerVibrate() {
    if (navigator.vibrate) navigator.vibrate([40, 30, 40]);
  }

  /* ---- Am thanh rung cho may tinh (Web Audio API) ---- */
  function playRumble() {
    try {
      var ctx  = new (window.AudioContext || window.webkitAudioContext)();
      var osc  = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.setValueAtTime(60, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(30, ctx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.4, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.4);
    } catch (err) {}
  }

  /* ---- Xu ly submit mat khau ---- */
  function handleSubmit() {
    if (!input || isLockedOut) return;
    var val = input.value.trim();

    if (val === CORRECT_PASSWORD) {
      failCount   = 0;
      isLockedOut = false;
      if (lockoutTimer) { clearInterval(lockoutTimer); lockoutTimer = null; }
      setInputDisabled(false);
      closePopup();
      openLid();

    } else {
      failCount += 1;
      input.value = '';

      if (failCount >= MAX_ATTEMPTS) {
        startLockout();
      } else {
        var left = MAX_ATTEMPTS - failCount;
        showError('còn ' + left + ' lần thử.');
        if (input) input.focus();
      }
    }
  }

  /* ---- Click vao hop qua ---- */
  if (giftBox) {
    giftBox.addEventListener('click', function () {
      if (giftState === 'closed') {
        if (HAS_PASSWORD) {
          /* Co mat khau: hien popup binh thuong */
          openPopup();
        } else {
          /* Khong co mat khau (3 profile Hanh/KhanhAn/NhuHien):
             mo thang nap, khong hien popup */
          openLid();
        }
      } else if (giftState === 'ajar') {
        triggerVibrate();
        playRumble();
        giftState = 'open';
        giftBox.classList.remove('lid-ajar');
        giftBox.classList.add('lid-open');
      }
    });
  }

  /* ---- Nut X dong popup ---- */
  if (closeBtn) {
    closeBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      closePopup();
    });
  }

  /* ---- Nut mui ten submit ---- */
  if (submitBtn) {
    submitBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      handleSubmit();
    });
  }

  /* ---- Enter tren input ---- */
  if (input) {
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); }
    });
    input.addEventListener('input', function () {
      if (!isLockedOut) hideError();
    });
  }

  /* ---- Click backdrop de dong popup ---- */
  if (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closePopup();
    });
  }

})();
