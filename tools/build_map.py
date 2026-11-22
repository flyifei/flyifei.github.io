"""Build map.html: world map with great-circle routes drawn as inline SVG.

Usage:
  python build_map.py --routes routes.csv --airports airports.json --land land.geojson

  routes.csv  : from,to,count
  airports.json: mwgg/Airports style dict keyed by ICAO (needs lat/lon/name)
  land.geojson : Natural Earth 110m land, FeatureCollection of Polygon/MultiPolygon
"""
import argparse, csv, json, math, os

W = 1000.0
LAT_MAX, LAT_MIN = 82.0, -58.0
H = W * (LAT_MAX - LAT_MIN) / 360.0


def xy(lon, lat):
    x = (lon + 180.0) / 360.0 * W
    y = (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * H
    return x, y


def load_airports(path, wanted):
    raw = json.load(open(path, encoding='utf-8'))
    out = {}
    for code in wanted:
        a = raw.get(code)
        if a is None:
            # some files key by iata or use extra keys
            for k, v in raw.items():
                if v.get('icao') == code:
                    a = v
                    break
        if a and a.get('lat') is not None and a.get('lon') is not None:
            out[code] = {
                'lat': float(a['lat']),
                'lon': float(a['lon']),
                'name': a.get('name') or code,
                'city': a.get('city') or '',
                'country': a.get('country') or '',
            }
    return out


def load_land(path):
    gj = json.load(open(path, encoding='utf-8'))
    paths = []
    for feat in gj['features']:
        geom = feat['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        for poly in polys:
            for ring in poly:  # outer + holes, simplified: draw all
                d = []
                for i, (lon, lat) in enumerate(ring):
                    x, y = xy(lon, max(LAT_MIN, min(LAT_MAX, lat)))
                    d.append(('M' if i == 0 else 'L') + '%.1f,%.1f' % (x, y))
                paths.append(''.join(d) + 'Z')
    return paths


def great_circle(a, b, steps=72):
    """Return list of (lon, lat) along the great circle from a to b."""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    d = 2 * math.asin(math.sqrt(
        math.sin((lat2 - lat1) / 2) ** 2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    if d == 0:
        return [(a[1], a[0]), (b[1], b[0])]
    pts = []
    for i in range(steps + 1):
        f = i / steps
        A = math.sin((1 - f) * d) / math.sin(d)
        B = math.sin(f * d) / math.sin(d)
        x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
        y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
        z = A * math.sin(lat1) + B * math.sin(lat2)
        pts.append((math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, math.hypot(x, y)))))
    return pts


def arc_path(a, b):
    pts = great_circle(a, b)
    segs, cur, prev = [], [], None
    for lon, lat in pts:
        if prev is not None and abs(lon - prev) > 180:
            segs.append(cur)
            cur = []
        cur.append(xy(lon, lat))
        prev = lon
    segs.append(cur)
    out = []
    for seg in segs:
        if len(seg) < 2:
            continue
        out.append('M' + ' L'.join('%.1f,%.1f' % p for p in seg))
    return ' '.join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--routes', required=True)
    ap.add_argument('--airports', required=True)
    ap.add_argument('--land', required=True)
    ap.add_argument('--out', default='map.html')
    args = ap.parse_args()

    routes = []
    with open(args.routes, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            routes.append((row['from'].strip(), row['to'].strip(), int(row['count'])))

    codes = sorted({c for r in routes for c in r[:2]})
    airports = load_airports(args.airports, codes)
    missing = [c for c in codes if c not in airports]

    land_paths = load_land(args.land)

    drawn, skipped = [], []
    for a, b, n in routes:
        if a in airports and b in airports:
            drawn.append((a, b, n))
        else:
            skipped.append((a, b, n, [c for c in (a, b) if c not in airports]))

    max_n = max([n for _, _, n in drawn], default=1)

    # graticule
    grat = []
    for lon in range(-180, 181, 30):
        x, _ = xy(lon, 0)
        grat.append('M%.1f,0 L%.1f,%.1f' % (x, x, H))
    for lat in range(-60, 81, 20):
        _, y = xy(0, lat)
        grat.append('M0,%.1f L%.1f,%.1f' % (y, W, y))

    svg = []
    svg.append('<svg viewBox="0 0 %.0f %.0f" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of simulator routes">' % (W, H))
    svg.append('<rect width="%.0f" height="%.0f" fill="#f7fbfe"/>' % (W, H))
    svg.append('<g stroke="#dbe9f5" stroke-width="0.6" fill="none">')
    svg.append('<path d="%s"/>' % ' '.join(grat))
    svg.append('</g>')
    svg.append('<g fill="#e6eff8" stroke="#c3d8ea" stroke-width="0.7" stroke-linejoin="round">')
    for d in land_paths:
        svg.append('<path d="%s"/>' % d)
    svg.append('</g>')

    # routes, weak first so strong ones sit on top
    svg.append('<g fill="none" stroke-linecap="round">')
    for a, b, n in sorted(drawn, key=lambda r: r[2]):
        p = arc_path((airports[a]['lat'], airports[a]['lon']), (airports[b]['lat'], airports[b]['lon']))
        width = 0.8 + 2.2 * (n / max_n)
        opacity = 0.30 + 0.55 * (n / max_n)
        dash = ' stroke-dasharray="3 3"' if n == 1 else ''
        svg.append('<path class="route" data-from="%s" data-to="%s" data-n="%d" d="%s" stroke="#1a6fb5" stroke-width="%.2f" stroke-opacity="%.2f"%s><title>%s → %s (%d)</title></path>'
                   % (a, b, n, p, width, opacity, dash, a, b, n))
    svg.append('</g>')

    # airports
    busiest = {c: 0 for c in airports}
    for a, b, n in drawn:
        busiest[a] += n
        busiest[b] += n
    svg.append('<g>')
    for code, a in airports.items():
        x, y = xy(a['lon'], a['lat'])
        r = 2.4 if code != 'VHHH' else 3.6
        fill = '#08446f' if code == 'VHHH' else '#1a6fb5'
        svg.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#fff" stroke-width="*.6"><title>%s — %s</title></circle>'
                   % (x, y, r, fill, code, a['name']))
    svg.append('</g>')

    # labels for the busiest airports
    svg.append('<g font-family="-apple-system, Segoe UI, sans-serif" font-size="8.5" fill="#08446f">')
    for code, a in airports.items():
        if code != 'VHHH' and busiest.get(code, 0) < 4:
            continue
        x, y = xy(a['lon'], a['lat'])
        anchor = 'start' if a['lon'] > -30 else 'end'
        dx = 5 if anchor == 'start' else -5
        svg.append('<text x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (x + dx, y + 2.5, anchor, code))
    svg.append('</g>')
    svg.append('</svg>')
    svg_body = '\n'.join(svg).replace('stroke-width="*.6"', 'stroke-width="0.6"')

    rows = []
    for a, b, n in sorted(drawn, key=lambda r: (-r[2], r[0], r[1])):
        na = airports[a]['name']
        nb = airports[b]['name']
        cls = ' class="weak"' if n == 1 else ''
        rows.append('      <tr%s><td><strong>%s</strong> → <strong>%s</strong></td><td>%s → %s</td><td>%d</td></tr>'
                    % (cls, a, b, na, nb, n))

    page = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Route Map — Jeff Li</title>
<meta name="description" content="World map of every leg flown in Microsoft Flight Simulator, extracted from the simulator logbook.">
<link rel="stylesheet" href="assets/css/style.css">
<style>
.map-box {{ border:1px solid var(--blue-line); background:#fff; padding:8px; margin:1rem 0; }}
.map-box svg {{ width:100%; height:auto; display:block; }}
.legend {{ display:flex; flex-wrap:wrap; gap:1.1rem; font-size:.88rem; color:var(--ink-soft); margin:.6rem 0 0; }}
.legend span {{ display:inline-flex; align-items:center; gap:.4rem; }}
.legend i {{ display:inline-block; width:22px; height:0; border-top:2px solid #1a6fb5; }}
.legend i.weak {{ border-top-style:dashed; opacity:.5; }}
.legend i.dot {{ width:9px; height:9px; border:0; border-radius:50%; background:#1a6fb5; }}
tr.weak td {{ color:var(--ink-soft); }}
@media (max-width: 720px) {{
  .map-box {{ overflow-x:auto; }}
  .map-box svg {{ min-width:640px; }}
}}
</style>
</head>
<body>

<header class="site-header">
  <div class="wrap">
    <a class="brand" href="index.html">Jeff Li <span>/ Cadet Pilot Notes</span></a>
    <nav class="site-nav">
      <a href="index.html">Home</a>
      <a href="about.html">About</a>
      <a href="application.html">Application</a>
      <a href="cathay.html">Cathay</a>
      <a href="resources.html">Resources</a>
      <a href="logbook.html">Flight Log</a>
      <a class="active" href="map.html">Route Map</a>
    </nav>
  </div>
</header>

<main>

<h1>Route map</h1>

<p class="lead">
Every leg in my Microsoft Flight Simulator logbook, drawn as great-circle arcs between the airports
actually departed and arrived.
</p>

<div class="map-box">
__SVG__
<div class="legend">
  <span><i></i> leg flown more than once</span>
  <span><i class="weak"></i> leg recorded once</span>
  <span><i class="dot"></i> airport (dark = Hong Kong, home base)</span>
</div>
</div>

<p class="muted">
__NLEGS__ legs between __NAPT__ airports. Labels are shown for the most frequently used fields.
Hover a line or a dot for details.
</p>

<h2>Legs</h2>

<div class="table-scroll">
<table>
  <thead><tr><th style="width:26%">Leg</th><th>Airports</th><th style="width:12%">Times</th></tr></thead>
  <tbody>
__ROWS__
  </tbody>
</table>
</div>

__SKIPPED__

<div class="note">
  <p><strong>Where this comes from.</strong> Parsed from the simulator's own logbook file
  (<code>sr_logbook</code>, MSFS 2024 on Steam), which stores airport codes in a binary stream.
  Duplicated entries are collapsed and neighbouring airports counted as legs, so a leg marked
  “recorded once” may be an artefact of two sessions being adjacent in the file rather than a flight
  you actually made. Times show how often that leg appears in the log.</p>
  <p>Dates, block times and landing counts are not stored as plain values in that file — they exist
  only in the simulator's logbook screen. If they matter, install a recorder such as Volanta or
  Little Navmap and the numbers become exportable.</p>
</div>

</main>

<footer class="site-footer">
  <div class="wrap">
    <p>Personal study notes on the Cathay Pacific Cadet Pilot Programme. Not affiliated with Cathay Pacific Airways.</p>
    <p class="muted">Last updated 22 November 2026 · <a href="https://github.com/flyifei" target="_blank" rel="noopener">GitHub</a></p>
  </div>
</footer>

</body>
</html>
'''
    page = page.replace('{{', '{').replace('}}', '}')
    page = page.replace('__SVG__', svg_body)
    page = page.replace('__NLEGS__', str(len(drawn)))
    page = page.replace('__NAPT__', str(len(airports)))
    page = page.replace('__ROWS__', '\n'.join(rows))
    if skipped:
        lis = ', '.join('%s → %s' % (a, b) for a, b, n, _ in skipped)
        page = page.replace('__SKIPPED__', '<p class="muted">Not drawn (airport not in the coordinate database): %s</p>' % lis)
    else:
        page = page.replace('__SKIPPED__', '')

    open(args.out, 'w', encoding='utf-8', newline='\n').write(page)
    print('wrote %s  (%d legs, %d airports, %d land paths, %.1f KB)'
          % (args.out, len(drawn), len(airports), len(land_paths), os.path.getsize(args.out) / 1024.0))
    if missing:
        print('missing coordinates:', ', '.join(missing))


if __name__ == '__main__':
    main()