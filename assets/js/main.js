/* FLYIFEI · 站点通用脚本：导航、滚动出现动画、数字动画、清单本地保存、标签切换 */
(function () {
  'use strict';

  /* ---------- 1. 移动端导航 ---------- */
  var nav = document.querySelector('.nav');
  var toggle = document.querySelector('.nav-toggle');
  if (nav && toggle) {
    toggle.addEventListener('click', function () {
      nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', nav.classList.contains('open') ? 'true' : 'false');
    });
    nav.querySelectorAll('.nav-links a').forEach(function (a) {
      a.addEventListener('click', function () { nav.classList.remove('open'); });
    });
  }

  /* ---------- 2. 当前页高亮 ---------- */
  var page = document.body.getAttribute('data-page');
  if (page) {
    document.querySelectorAll('.nav-links a').forEach(function (a) {
      if (a.getAttribute('data-nav') === page) { a.classList.add('active'); }
    });
  }

  /* ---------- 3. 滚动出现 ---------- */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    reveals.forEach(function (el, i) {
      el.style.transitionDelay = Math.min(i % 4, 3) * 70 + 'ms';
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- 4. 数字滚动 ---------- */
  function animateNumber(el) {
    var target = parseFloat(el.getAttribute('data-count'));
    if (isNaN(target)) { return; }
    var decimals = (el.getAttribute('data-decimals') || '0') | 0;
    var done = false;
    function settle() {
      if (done) { return; }
      done = true;
      el.textContent = target.toFixed(decimals);
    }
    if (reduced) { settle(); return; }
    var start = null, dur = 1100;
    function step(ts) {
      if (done) { return; }
      if (!start) { start = ts; }
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (target * eased).toFixed(decimals);
      if (p < 1) { requestAnimationFrame(step); } else { settle(); }
    }
    requestAnimationFrame(step);
    // 后台标签页或被节流时 rAF 不跑，用定时器兜底落到终值
    setTimeout(settle, dur + 900);
  }
  var counters = document.querySelectorAll('[data-count]');
  if ('IntersectionObserver' in window && !reduced) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { animateNumber(e.target); cio.unobserve(e.target); }
      });
    }, { threshold: 0.2, rootMargin: '0px 0px -4% 0px' });
    counters.forEach(function (el) { el.textContent = '0'; cio.observe(el); });
    // 兜底：若因布局原因始终未触发观察，2.4 秒后直接补上终值
    setTimeout(function () {
      counters.forEach(function (el) {
        if (el.textContent === '0') { animateNumber(el); cio.unobserve(el); }
      });
    }, 2400);
  } else {
    counters.forEach(animateNumber);
  }

  /* ---------- 5. 进度条 ---------- */
  document.querySelectorAll('[data-progress]').forEach(function (bar) {
    var v = Math.max(0, Math.min(100, parseFloat(bar.getAttribute('data-progress')) || 0));
    var fill = bar.querySelector('i');
    if (!fill) { return; }
    setTimeout(function () { fill.style.width = v + '%'; }, 260);
    var label = document.querySelector('[data-progress-label]');
    if (label) { label.textContent = v + '%'; }
  });

  /* ---------- 6. 申请清单：本地保存勾选状态 ---------- */
  var checks = document.querySelectorAll('.check-item input[type="checkbox"]');
  checks.forEach(function (box) {
    var key = 'flyifei.check.' + (box.getAttribute('data-key') || box.id);
    try { if (localStorage.getItem(key) === '1') { box.checked = true; } } catch (err) {}
    box.addEventListener('change', function () {
      try { localStorage.setItem(key, box.checked ? '1' : '0'); } catch (err) {}
      updateCheckProgress();
    });
  });
  function updateCheckProgress() {
    var total = checks.length;
    if (!total) { return; }
    var done = 0;
    checks.forEach(function (b) { if (b.checked) { done++; } });
    var txt = document.querySelector('[data-check-count]');
    if (txt) { txt.textContent = done + ' / ' + total; }
    var bar = document.querySelector('[data-check-bar]');
    if (bar) { bar.style.width = (done / total * 100) + '%'; }
  }
  if (checks.length) { updateCheckProgress(); }

  /* ---------- 7. 标签页 ---------- */
  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = group.querySelectorAll('.tab');
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        var name = tab.getAttribute('data-tab');
        tabs.forEach(function (t) { t.classList.toggle('active', t === tab); });
        group.querySelectorAll('.panel').forEach(function (p) {
          p.hidden = p.getAttribute('data-panel') !== name;
        });
      });
    });
  });

  /* ---------- 8. 年份 ---------- */
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();