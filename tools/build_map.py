"""Render the simulator route map into logbook.html (section between markers).

Usage:
  python build_map.py --routes routes.csv --airports airports.json --land land.geojson [--page logbook.html]

routes.csv    : from,to,count
airports.json : mwgg/Airports style dict keyed by ICAO (needs lat/lon/name)
land.geojson  : Natural Earth 110m land, FeatureCollection of Polygon/MultiPolygon

The generated block replaces everything between
    <!-- ROUTEMAP:START -->  and  <!-- ROUTEMAP:END -->
so re-running is idempotent.
"""
import argparse, csv, json, math, os

W = 1000.0
LAT_MAX, LAT_MIN = 82.0, -58.0
H = W * (LAT_MAX - LAT_MIN) / 360.0
START, END = '<!-- ROUTEMAP:START -->', '<!-- ROUTEMAP:END -->'


def xy(lon, lat):
    return ((lon + 180.0) / 360.0 * W, (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * H)


def load_airports(path, wanted):
    raw = json.load(open(path, encoding='utf-8'))
    out = {}
    for code in wanted:
        a = raw.get(code)
        if a is None:
            for v in raw.values():
                if v.get('icao') == code:
                    a = v
                    break
        if a and a.get('lat') is not None and a.get('lon') is not None:
            out[code] = {'lat': float(a['lat']), 'lon': float(a['lon']),
                         'name': a.get('name') or code}
    return out


def load_land(path):
    gj = json.load(open(path, encoding='utf-8'))
    paths = []
    for feat in gj['features']:
        g = feat['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            for ring in poly:
                d = []
                for i, (lon, lat) in enumerate(ring):
                    x, y = xy(lon, max(LAT_MIN, min(LAT_MAX, lat)))
                    d.append(('M' if i == 0 else 'L') + '%.1f,%.1f' % (x, y))
                paths.append(''.join(d) + 'Z')
    return paths


def great_circle(a, b, steps=72):
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    d = 2 * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 +
                                math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    if d == 0:
        return [(a[1], a[0]), (b[1], b[0])]
    out = []
    for i in range(steps + 1):
        f = i / steps
        A = math.sin((1 - f) * d) / math.sin(d)
        B = math.sin(f * d) / math.sin(d)
        x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
        y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
        z = A * math.sin(lat1) + B * math.sin(lat2)
        out.append((math.degrees(math.atan2(y, x)), math.degrees(math.atan2(z, math.hypot(x, y)))))
    return out


def arc_path(a, b):
    pts = great_circle(a, b)
    segs, cur, prev = [], [], None
    for lon, lat in pts:
        if prev is not None and abs(lon - prev) > 180:
            segs.append(cur); cur = []
        cur.append(xy(lon, lat)); prev = lon
    segs.append(cur)
    return ' '.join('M' + ' L'.join('%.1f,%.1f' % q for q in seg) for seg in segs if len(seg) > 1)


def build_fragment(routes, airports, land_paths):
    drawn = [(a, b, n) for a, b, n in routes if a in airports and b in airports]
    skipped = [(a, b, n) for a, b, n in routes if not (a in airports and b in airports)]
    max_n = max([n for _, _, n in drawn], default=1)

    g = ['<div class="map-box">']
    g.append('<svg viewBox="0 0 %.0f %.0f" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of simulator routes">' % (W, H))
    g.append('<rect width="%.0f" height="%.0f" fill="#f7fbfe"/>' % (W, H))
    grat = []
    for lon in range(-180, 181, 30):
        x, _ = xy(lon, 0)
        grat.append('M%.1f,0 L%.1f,%.1f' % (x, x, H))
    for lat in range(-60, 81, 20):
        _, y = xy(0, lat)
        grat.append('M0,%.1f L%.1f,%.1f' % (y, W, y))
    g.append('<path d="%s" stroke="#dbe9f5" stroke-width="0.6" fill="none"/>' % ' '.join(grat))
    g.append('<g fill="#e6eff8" stroke="#c3d8ea" stroke-width="0.7" stroke-linejoin="round">')
    g.extend('<path d="%s"/>' % d for d in land_paths)
    g.append('</g>')
    g.append('<g fill="none" stroke-linecap="round">')
    for a, b, n in sorted(drawn, key=lambda r: r[2]):
        p = arc_path((airports[a]['lat'], airports[a]['lon']), (airports[b]['lat'], airports[b]['lon']))
        width = 0.8 + 2.2 * (n / max_n)
        opacity = 0.30 + 0.55 * (n / max_n)
        dash = ' stroke-dasharray="3 3"' if n == 1 else ''
        g.append('<path class="route" d="%s" stroke="#1a6fb5" stroke-width="%.2f" stroke-opacity="%.2f"%s><title>%s → %s (%d)</title></path>'
                 % (p, width, opacity, dash, a, b, n))
    g.append('</g>')
    busiest = {c: 0 for c in airports}
    for a, b, n in drawn:
        busiest[a] += n; busiest[b] += n
    g.append('<g>')
    for code, a in airports.items():
        x, y = xy(a['lon'], a['lat'])
        r = 3.6 if code == 'VHHH' else 2.4
        fill = '#08446f' if code == 'VHHH' else '#1a6fb5'
        g.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="#fff" stroke-width="0.6"><title>%s — %s</title></circle>'
                 % (x, y, r, fill, code, a['name']))
    g.append('</g>')
    g.append('<g font-family="-apple-system, Segoe UI, sans-serif" font-size="8.5" fill="#08446f">')
    for code, a in airports.items():
        if code != 'VHHH' and busiest.get(code, 0) < 4:
            continue
        x, y = xy(a['lon'], a['lat'])
        anchor = 'start' if a['lon'] > -30 else 'end'
        g.append('<text x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                 % (x + (5 if anchor == 'start' else -5), y + 2.5, anchor, code))
    g.append('</g>')
    g.append('</svg>')
    g.append('<div class="legend">'
             '<span><i></i> leg flown more than once</span>'
             '<span><i class="weak"></i> leg recorded once</span>'
             '<span><i class="dot"></i> airport (dark = Hong Kong, home base)</span>'
             '</div>')
    g.append('</div>')

    rows = ''.join(
        '<tr%s><td><strong>%s</strong> → <strong>%s</strong></td><td>%s → %s</td><td>%d</td></tr>'
        % (' class="weak"' if n == 1 else '', a, b, airports[a]['name'], airports[b]['name'], n)
        for a, b, n in sorted(drawn, key=lambda r: (-r[2], r[0], r[1])))

    frag = '\n'.join([
        START,
        '<h3>Simulator route map</h3>',
        '',
        '<p>Every leg recorded in the simulator logbook — not real flying — drawn as great-circle arcs between '
        'the airports actually departed and arrived. Line weight follows how often the leg appears.</p>',
        '',
        '\n'.join(g),
        '',
        '<p class="small">%d legs between %d airports. Labels mark the most frequently used fields; hover a line or a point for details.</p>'
        % (len(drawn), len(airports)),
        '',
        '<div class="table-scroll">',
        '<table>',
        '  <thead><tr><th style="width:26%">Leg</th><th>Airports</th><th style="width:12%">Times</th></tr></thead>',
        '  <tbody>',
        rows,
        '  </tbody>',
        '</table>',
        '</div>',
        '',
        ('<p class="small">Not drawn — airport coordinates unknown: %s.</p>'
         % ', '.join('%s → %s' % (a, b) for a, b, n in skipped)) if skipped else '',
        '',
        '<div class="note">',
        '  <p><strong>How this is built.</strong> Airport codes are read from the simulator\'s own logbook file '
        '(<code>sr_logbook</code>), which stores them in a binary stream. Repeated entries are collapsed and '
        'neighbouring airports counted as legs, so a leg marked “recorded once” may be an artefact of two '
        'sessions sitting next to each other in the file. Dates, block times and landing counts are not stored '
        'as plain values — they only exist on the simulator\'s logbook screen.</p>',
        '</div>',
        END,
    ])
    missing_codes = sorted({c for rr in routes for c in rr[:2] if c not in airports})
    return frag, len(drawn), len(airports), missing_codes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--routes', required=True)
    ap.add_argument('--airports', required=True)
    ap.add_argument('--land', required=True)
    ap.add_argument('--page', default='logbook.html')
    a = ap.parse_args()

    routes = []
    with open(a.routes, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            routes.append((row['from'].strip(), row['to'].strip(), int(row['count'])))
    codes = sorted({c for r in routes for c in r[:2]})
    airports = load_airports(a.airports, codes)
    land = load_land(a.land)

    frag, nlegs, napt, missing = build_fragment(routes, airports, land)

    html = open(a.page, encoding='utf-8').read()
    if START not in html or END not in html:
        raise SystemExit('markers %s / %s not found in %s' % (START, END, a.page))
    head, rest = html.split(START, 1)
    _, tail = rest.split(END, 1)
    open(a.page, 'w', encoding='utf-8', newline='\n').write(head + frag + tail)
    print('map written into %s: %d legs, %d airports, %d land paths (page %.1f KB)'
          % (a.page, nlegs, napt, len(land), os.path.getsize(a.page) / 1024.0))
    if missing:
        print('no coordinates:', ', '.join(sorted(set(missing))))


if __name__ == '__main__':
    main()