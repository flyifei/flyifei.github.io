/* Pan / zoom for the inline SVG route map. No dependencies.
   Mouse: wheel to zoom, drag to pan. Touch: two-finger pinch / drag.
   The +, - and Reset buttons work everywhere. */
(function () {
  'use strict';
  var svg = document.querySelector('.map-box svg');
  if (!svg || !svg.viewBox || !svg.viewBox.baseVal) { return; }
  var vb = svg.viewBox.baseVal;
  var home = { x: vb.x, y: vb.y, w: vb.width, h: vb.height };
  var cur = { x: home.x, y: home.y, w: home.w, h: home.h };
  var MIN_W = home.w / 16;

  function apply() {
    svg.setAttribute('viewBox',
      cur.x.toFixed(2) + ' ' + cur.y.toFixed(2) + ' ' + cur.w.toFixed(2) + ' ' + cur.h.toFixed(2));
  }

  function clamp() {
    if (cur.w > home.w) { var a = home.w / cur.w; cur.w *= a; cur.h *= a; }
    if (cur.w < MIN_W) { var b = MIN_W / cur.w; cur.w *= b; cur.h *= b; }
    var minX = home.x - cur.w * 0.5, maxX = home.x + home.w - cur.w * 0.5;
    var minY = home.y - cur.h * 0.5, maxY = home.y + home.h - cur.h * 0.5;
    cur.x = Math.min(maxX, Math.max(minX, cur.x));
    cur.y = Math.min(maxY, Math.max(minY, cur.y));
  }

  function zoomAt(factor, cx, cy) {
    cur.x = cx - (cx - cur.x) * factor;
    cur.y = cy - (cy - cur.y) * factor;
    cur.w *= factor;
    cur.h *= factor;
    clamp();
    apply();
  }

  function toSvg(clientX, clientY) {
    var m = svg.getScreenCTM();
    if (!m) { return null; }
    var pt = svg.createSVGPoint();
    pt.x = clientX;
    pt.y = clientY;
    var q = pt.matrixTransform(m.inverse());
    return { x: q.x, y: q.y };
  }

  function center() { return { x: cur.x + cur.w / 2, y: cur.y + cur.h / 2 }; }

  svg.addEventListener('wheel', function (e) {
    e.preventDefault();
    var p = toSvg(e.clientX, e.clientY);
    if (p) { zoomAt(e.deltaY < 0 ? 0.85 : 1.18, p.x, p.y); }
  }, { passive: false });

  svg.addEventListener('dblclick', function (e) {
    e.preventDefault();
    var p = toSvg(e.clientX, e.clientY);
    if (p) { zoomAt(0.6, p.x, p.y); }
  });

  var pointers = {};
  var dragging = false;
  var last = null;
  var pinchDist = 0;

  function count() { return Object.keys(pointers).length; }
  function firstTwo() {
    var ids = Object.keys(pointers);
    return [pointers[ids[0]], pointers[ids[1]]];
  }

  svg.addEventListener('pointerdown', function (e) {
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };
    if (e.pointerType === 'mouse') {
      dragging = true;
      last = { x: e.clientX, y: e.clientY };
      svg.style.cursor = 'grabbing';
      try { svg.setPointerCapture(e.pointerId); } catch (err) {}
    }
    if (count() === 2) {
      var t = firstTwo();
      pinchDist = Math.hypot(t[0].x - t[1].x, t[0].y - t[1].y);
      dragging = false;
    }
  });

  svg.addEventListener('pointermove', function (e) {
    if (!pointers[e.pointerId]) { return; }
    pointers[e.pointerId] = { x: e.clientX, y: e.clientY };

    if (count() === 2) {
      var t = firstTwo();
      var d = Math.hypot(t[0].x - t[1].x, t[0].y - t[1].y);
      if (pinchDist > 0 && d > 0) {
        var mid = toSvg((t[0].x + t[1].x) / 2, (t[0].y + t[1].y) / 2);
        if (mid) { zoomAt(pinchDist / d, mid.x, mid.y); }
      }
      pinchDist = d;
      return;
    }

    if (dragging && last) {
      var rect = svg.getBoundingClientRect();
      cur.x -= (e.clientX - last.x) / rect.width * cur.w;
      cur.y -= (e.clientY - last.y) / rect.height * cur.h;
      last = { x: e.clientX, y: e.clientY };
      clamp();
      apply();
    }
  });

  function endPointer(e) {
    delete pointers[e.pointerId];
    if (count() < 2) { pinchDist = 0; }
    if (count() === 0) {
      dragging = false;
      last = null;
      svg.style.cursor = 'grab';
    }
  }
  svg.addEventListener('pointerup', endPointer);
  svg.addEventListener('pointercancel', endPointer);

  var box = svg.parentNode;
  box.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('[data-zoom]') : null;
    if (!btn) { return; }
    var mode = btn.getAttribute('data-zoom');
    if (mode === 'reset') {
      cur.x = home.x; cur.y = home.y; cur.w = home.w; cur.h = home.h;
      apply();
      return;
    }
    var c = center();
    zoomAt(mode === 'in' ? 0.72 : 1.4, c.x, c.y);
  });

  svg.style.cursor = 'grab';
  apply();
})();