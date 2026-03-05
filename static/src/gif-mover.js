
(function () {

  /* ==================== CẤU HÌNH ==================== */
  var CFG = {
    count:        3,    /* số gif con                              */
    gifSize:      80,   /* px — width mỗi gif (height auto)        */
    stripH:       80,   /* px — chiều cao dải (= gifSize)          */
    bottomOffset: 0,    /* px — khoảng cách từ dải đến đáy màn hình
   /*(sẽ tự cộng safe-area iOS ở runtime)   */
    speeds: [60, 85, 110], /* px/s — mỗi con 1 tốc độ khác nhau  */
    startDelayMs: 350,  /* ms — delay lệch giữa các con            */
  };

  /* ==================== LẤY SRC GIF ==================== */
  var layer = document.querySelector('.profile-gif-layer');
  if (!layer) return;

  var gifSrc = { up: null, down: null, left: null, right: null };
  ['up','down','left','right'].forEach(function (dir) {
    var el = layer.querySelector('.profile-gif--' + dir);
    if (el) { gifSrc[dir] = el.src || null; el.style.display = 'none'; }
  });

  var hasAny = ['up','down','left','right'].some(function(d){ return !!gifSrc[d]; });
  if (!hasAny) return;

  function srcFor(dir) {
    if (gifSrc[dir]) return gifSrc[dir];
    var order = ['right','left','up','down'];
    for (var i = 0; i < order.length; i++) {
      if (gifSrc[order[i]]) return gifSrc[order[i]];
    }
    return '';
  }
  function getSafeBottom() {
    /* Thử đọc CSS env() qua một div ẩn */
    try {
      var probe = document.createElement('div');
      probe.style.cssText =
        'position:fixed;bottom:env(safe-area-inset-bottom,0px);' +
        'height:0;width:0;pointer-events:none;visibility:hidden;';
      document.body.appendChild(probe);
      var rect = probe.getBoundingClientRect();
      var safeBottom = window.innerHeight - rect.bottom;
      document.body.removeChild(probe);
      return Math.max(0, Math.round(safeBottom));
    } catch(e) { return 0; }
  }

  /* Tính top của dải (Y cố định cho tất cả con) */
  function getStripTop() {
    var safeBottom = getSafeBottom();
    /* Đặt sao cho bottom của gif = bottom viewport - safeBottom - bottomOffset */
    return window.innerHeight - safeBottom - CFG.bottomOffset - CFG.stripH;
  }

  /* ==================== TẠO MỖI GIF CON ==================== */
  function createMover(index) {
    var img = document.createElement('img');
    img.style.cssText = [
      'position:fixed',
      'top:0',
      'left:0',
      'width:' + CFG.gifSize + 'px',
      'height:auto',
      'pointer-events:none',
      'will-change:transform',
      'image-rendering:auto',
      'z-index:' + (9990 + index),
    ].join(';');
    document.body.appendChild(img);

    var speed  = CFG.speeds[index % CFG.speeds.length]; /* px/s     */
    var stripY = getStripTop();                          /* Y cố định */

    /* X ban đầu: chia đều màn hình để 3 con không chồng ngay */
    var vw    = window.innerWidth;
    var maxX  = vw - CFG.gifSize;
    var x     = (maxX / (CFG.count + 1)) * (index + 1);
    var dir   = (index % 2 === 0) ? 1 : -1; /* 1=phải, -1=trái */
    var curSrcDir = '';

    function applyTransform() {
      img.style.transform = 'translate3d(' + Math.round(x) + 'px,' + Math.round(stripY) + 'px,0)';
    }

    function setImgDir(d) {
      /* d: 'right' hoặc 'left' */
      if (d === curSrcDir) return;
      curSrcDir = d;
      var s = srcFor(d);
      if (s && img.src !== s) img.src = s;
    }

    var lastTs = null;

    function tick(ts) {
      if (lastTs === null) { lastTs = ts; requestAnimationFrame(tick); return; }
      var dt = Math.min((ts - lastTs) / 1000, 0.05); /* giây, cap 50ms tránh lag spike */
      lastTs = ts;

      /* Cập nhật X */
      x += dir * speed * dt;

      /* Bounce tại cạnh */
      var curMaxX = window.innerWidth - CFG.gifSize;
      if (x >= curMaxX) { x = curMaxX; dir = -1; }
      if (x <= 0)       { x = 0;       dir =  1; }

      /* Cập nhật Y nếu resize */
      stripY = getStripTop();

      /* Đổi gif theo hướng */
      setImgDir(dir === 1 ? 'right' : 'left');

      applyTransform();
      requestAnimationFrame(tick);
    }

    function start() {
      img.src = srcFor(dir === 1 ? 'right' : 'left');
      applyTransform();
      setTimeout(function () {
        requestAnimationFrame(tick);
      }, index * CFG.startDelayMs + 200);
    }

    return { start: start };
  }

  /* ==================== PRELOAD & KHỞI ĐỘNG ==================== */
  var srcs = ['right','left','up','down']
    .map(function(d){ return gifSrc[d]; })
    .filter(Boolean);

  var loaded = 0;
  function onLoad() {
    loaded++;
    if (loaded >= srcs.length) {
      for (var i = 0; i < CFG.count; i++) createMover(i).start();
    }
  }

  if (srcs.length === 0) {
    for (var i = 0; i < CFG.count; i++) createMover(i).start();
  } else {
    srcs.forEach(function (src) {
      var tmp = new Image();
      tmp.onload = tmp.onerror = onLoad;
      tmp.src = src;
    });
  }

  /* Cập nhật stripY khi resize */
  window.addEventListener('resize', function () {
  });

})();