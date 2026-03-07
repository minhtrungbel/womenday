/* profile_guard.js
   Hien popup ngay khi vao profile co profile_password.
   Nhap dung -> an overlay, hien noi dung.
   Sai / dong / backdrop / ESC -> quay ve trang chu.
*/
(function () {
  var overlay = document.getElementById('profile-guard-overlay');
  if (!overlay) return;

  var CORRECT_PASSWORD = overlay.dataset.password || '';
  if (!CORRECT_PASSWORD) return;

  var closeBtn     = document.getElementById('profile-guard-close');
  var input        = document.getElementById('profile-guard-input');
  var submitBtn    = document.getElementById('profile-guard-submit');
  var errorMsg     = document.getElementById('profile-guard-error');
  var attemptsSpan = document.getElementById('profile-guard-attempts');

  var MAX_ATTEMPTS = 5;
  var LOCKOUT_SEC  = 30;
  var failCount    = 0;
  var lockoutTimer = null;
  var isLockedOut  = false;

  /* Hien popup ngay khi load */
  overlay.classList.add('active');
  if (input) setTimeout(function () { input.focus(); }, 300);

  function setInputDisabled(disabled) {
    if (input)     input.disabled     = disabled;
    if (submitBtn) submitBtn.disabled = disabled;
  }

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
        lockoutTimer = null;
        isLockedOut  = false;
        failCount    = 0;
        setInputDisabled(false);
        hideError();
        if (input) { input.value = ''; input.focus(); }
      }
    }, 1000);
  }

  function showError(text) {
    if (!errorMsg) return;
    if (attemptsSpan) attemptsSpan.textContent = text || '';
    errorMsg.classList.add('show');
  }
  function hideError() {
    if (errorMsg) errorMsg.classList.remove('show');
    if (attemptsSpan) attemptsSpan.textContent = '';
  }

  function goHome() { window.location.href = '/'; }

  function handleSubmit() {
    if (!input || isLockedOut) return;
    var val = input.value.trim();
    if (val === CORRECT_PASSWORD) {
      failCount = 0;
      isLockedOut = false;
      if (lockoutTimer) { clearInterval(lockoutTimer); lockoutTimer = null; }
      overlay.classList.remove('active');
    } else {
      failCount += 1;
      input.value = '';
      if (failCount >= MAX_ATTEMPTS) {
        startLockout();
      } else {
        showError('còn ' + (MAX_ATTEMPTS - failCount) + ' lần thử.');
        if (input) input.focus();
      }
    }
  }

  if (closeBtn)  closeBtn.addEventListener('click', function (e) { e.stopPropagation(); goHome(); });
  if (submitBtn) submitBtn.addEventListener('click', function (e) { e.stopPropagation(); handleSubmit(); });
  if (input) {
    input.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); } });
    input.addEventListener('input',   function ()  { if (!isLockedOut) hideError(); });
  }
  overlay.addEventListener('click', function (e) { if (e.target === overlay) goHome(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && overlay.classList.contains('active')) goHome(); });
})();