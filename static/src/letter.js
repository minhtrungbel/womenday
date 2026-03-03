/* letter.js - logic hop qua + popup mat khau */
(function () {
  var giftBox   = document.getElementById('letter-gift-box');
  var overlay   = document.getElementById('letter-pwd-overlay');
  var closeBtn  = document.getElementById('letter-pwd-close');
  var input     = document.getElementById('letter-pwd-input');
  var submitBtn = document.getElementById('letter-pwd-submit');
  var errorMsg  = document.getElementById('letter-pwd-error');

  /* Mat khau lay tu data-password tren #letter-gift-box, fallback '0308' */
  var CORRECT_PASSWORD = giftBox ? (giftBox.dataset.password || '0308') : '0308';
  var giftState = 'closed'; /* closed | ajar | open */

  /* ---- Mo popup ---- */
  function openPopup() {
    if (!overlay) return;
    overlay.classList.add('active');
    if (errorMsg) errorMsg.classList.remove('show');
    if (input) {
      input.value = '';
      setTimeout(function () { input.focus(); }, 300);
    }
  }

  /* ---- Dong popup ---- */
  function closePopup() {
    if (overlay) overlay.classList.remove('active');
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
    if (!input) return;
    var val = input.value.trim();
    if (val === CORRECT_PASSWORD) {
      /* Dung: dong popup, he nap */
      closePopup();
      giftState = 'ajar';
      if (giftBox) giftBox.classList.add('lid-ajar');
    } else {
      /* Sai: hien loi, xoa input */
      if (errorMsg) errorMsg.classList.add('show');
      input.value = '';
      input.focus();
    }
  }

  /* ---- Click vao hop qua ---- */
  if (giftBox) {
    giftBox.addEventListener('click', function () {
      if (giftState === 'closed') {
        /* Lan 1: mo popup nhap mat khau */
        openPopup();
      } else if (giftState === 'ajar') {
        /* Lan 2: rung + am thanh + nap bay di */
        triggerVibrate();
        playRumble();
        giftState = 'open';
        giftBox.classList.remove('lid-ajar');
        giftBox.classList.add('lid-open');
      }
      /* Lan 3 tro di: khong lam gi them */
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
    /* An thong bao loi khi user bat dau go lai */
    input.addEventListener('input', function () {
      if (errorMsg) errorMsg.classList.remove('show');
    });
  }

  /* ---- Click backdrop de dong popup ---- */
  if (overlay) {
    overlay.addEventListener('click', function (e) {
      if (e.target === overlay) closePopup();
    });
  }

})();