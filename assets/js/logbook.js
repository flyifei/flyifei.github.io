/* FLYIFEI · 飞行记录渲染：读取 assets/data/*.json，自动统计并生成表格 */
(function () {
  'use strict';

  var SOURCES = {
    msfs: 'assets/data/msfs.json',
    real: 'assets/data/real-flights.json'
  };

  function num(v, d) {
    var n = parseFloat(v);
    return isNaN(n) ? (0).toFixed(d) : n.toFixed(d);
  }

  function sum(list, key) {
    return list.reduce(function (acc, f) { return acc + (parseFloat(f[key]) || 0); }, 0);
  }

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c];
    });
  }

  function sortFlights(list) {
    return list.slice().sort(function (a, b) {
      return String(b.date).localeCompare(String(a.date));
    });
  }

  function renderRows(tbody, flights) {
    if (!tbody) { return; }
    if (!flights.length) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#8296ab">还没有记录，去 assets/data/ 里加第一条吧 ✈</td></tr>';
      return;
    }
    tbody.innerHTML = sortFlights(flights).map(function (f) {
      var route = esc(f.from || '—') + ' <span style="color:#5c7186">→</span> ' + esc(f.to || '—');
      var badge = f.example ? ' <span class="chip amber" style="margin-left:6px">示例</span>' : '';
      return '<tr>' +
        '<td class="num">' + esc(f.date || '') + '</td>' +
        '<td><strong>' + esc(f.type || '') + '</strong></td>' +
        '<td class="num">' + esc(f.reg || '—') + '</td>' +
        '<td>' + route + '</td>' +
        '<td class="num">' + num(f.hours, 1) + ' h</td>' +
        '<td class="num">' + (f.ldg || 0) + '</td>' +
        '<td><span class="chip">' + esc(f.cat || '—') + '</span></td>' +
        '<td>' + esc(f.remarks || '') + badge + '</td>' +
      '</tr>';
    }).join('');
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el) { el.textContent = value; }
  }

  function renderTypeSummary(target, allFlights) {
    if (!target) { return; }
    var map = {};
    allFlights.forEach(function (f) {
      var k = f.type || '未知机型';
      if (!map[k]) { map[k] = { hours: 0, sectors: 0 }; }
      map[k].hours += parseFloat(f.hours) || 0;
      map[k].sectors += 1;
    });
    var keys = Object.keys(map).sort(function (a, b) { return map[b].hours - map[a].hours; });
    var max = keys.length ? map[keys[0]].hours : 1;
    target.innerHTML = keys.map(function (k) {
      var pct = Math.max(3, Math.round(map[k].hours / max * 100));
      return '<div style="margin-bottom:14px">' +
        '<div style="display:flex;justify-content:space-between;font-size:13.5px;margin-bottom:6px">' +
          '<strong style="color:#e9f0f7">' + esc(k) + '</strong>' +
          '<span style="font-family:var(--mono);color:#8296ab">' + map[k].hours.toFixed(1) + ' h · ' + map[k].sectors + ' 段</span>' +
        '</div>' +
        '<div class="progress-bar" style="height:5px"><i style="width:' + pct + '%"></i></div>' +
      '</div>';
    }).join('');
  }

  function render(data) {
    var msfs = data.msfs.flights || [];
    var real = data.real.flights || [];
    var all = msfs.concat(real);

    var msfsHours = sum(msfs, 'hours');
    var realHours = sum(real, 'hours');
    var ldgs = msfs.reduce(function (a, f) { return a + (parseInt(f.ldg, 10) || 0); }, 0) +
               real.reduce(function (a, f) { return a + (parseInt(f.ldg, 10) || 0); }, 0);
    var types = {};
    all.forEach(function (f) { if (f.type) { types[f.type] = 1; } });
    var dates = all.map(function (f) { return f.date; }).filter(Boolean).sort();
    var last = dates.length ? dates[dates.length - 1] : '—';

    setText('st-msfs-hours', num(msfsHours, 1));
    setText('st-real-hours', num(realHours, 1));
    setText('st-total-hours', num(msfsHours + realHours, 1));
    setText('st-sectors', all.length);
    setText('st-landings', ldgs);
    setText('st-types', Object.keys(types).length);
    setText('st-last', last);
    setText('st-msfs-count', msfs.length);
    setText('st-real-count', real.length);

    renderRows(document.getElementById('tbody-msfs'), msfs);
    renderRows(document.getElementById('tbody-real'), real);
    renderTypeSummary(document.getElementById('type-summary'), all);
  }

  function fail(err) {
    console.warn('数据加载失败', err);
    ['tbody-msfs', 'tbody-real'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) {
        el.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#e2574c">' +
          '数据文件读取失败（用 file:// 直接打开时会这样）。请用本地服务器预览，或推送到 GitHub Pages 后查看。' +
          '</td></tr>';
      }
    });
  }

  function load() {
    if (!document.getElementById('tbody-msfs')) { return; }
    var jobs = Object.keys(SOURCES).map(function (key) {
      return fetch(SOURCES[key], { cache: 'no-cache' }).then(function (r) {
        if (!r.ok) { throw new Error(SOURCES[key] + ' ' + r.status); }
        return r.json();
      }).then(function (j) { return [key, j]; });
    });
    Promise.all(jobs).then(function (pairs) {
      var data = {};
      pairs.forEach(function (p) { data[p[0]] = p[1]; });
      render(data);
    }).catch(fail);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();