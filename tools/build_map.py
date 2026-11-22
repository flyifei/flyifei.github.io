"""Render the simulator route map into logbook.html (between the ROUTEMAP markers).

Each leg is coloured by the aircraft flown; local circuits (from == to) are drawn
as rings. Output is plain SVG with no external dependencies, plus zoom controls
handled by assets/js/map-zoom.js.

Usage:
  python build_map.py --routes routes.csv --airports airports.json --land land.geojson
"""
import argparse, csv, json, math, os

W = 1000.0
LAT_MAX, LAT_MIN = 82.0, -58.0
H = W * (LAT_MAX - LAT_MIN) / 360.0
START, END = '<!-- ROUTEMAP:START -->', '<!-- ROUTEMAP:END -->'

# one colour per aircraft type (Okabe-Ito inspired, readable on light blue)
COLORS = {
    'C152': '#0072B2', 'C172S': '#009E73', 'DA40': '#4C9F70', 'DA62': '#E69F00',
    'C400': '#CC79A7', 'C208B': '#8C564B', 'DHC-6': '#56B4E9', 'Savage Cub': '#6A4C93',
    'Optica': '#17BECF', 'VL-3': '#B79F00', 'SF50': '#7F7F7F',
    '737 MAX': '#D55E00', 'A350': '#111827', 'A320': '#333333', '747': '#000000',
    'F/A-18E': '#B30000',
}
FALLBACK = '#5d6d7e'


def color(ac):
    return COLORS.get(ac, FALLBACK)


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
            out[code] = {'lat': float(a['lat']), 'lon': float(a['lon']), 'name': a.get('name') or code}
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


def build_fragment(rows, airports, land_paths):
    legs = [(a, b, ac, n) for a, b, ac, n in rows if a in airports and b in airports]
    skipped = [(a, b, ac, n) for a, b, ac, n in rows if not (a in airports and b in airports)]
    routes = [r for r in legs if r[0] != r[1]]
    circuits = [r for r in legs if r[0] == r[1]]
    max_n = max([n for _, _, _, n in routes], default=1)

    # legend order: most-flown aircraft first
    by_ac = {}
    for a, b, ac, n in legs:
        by_ac[ac] = by_ac.get(ac, 0) + 1
    ac_order = sorted(by_ac, key=lambda k: -by_ac[k])

    g = ['<div class="map-box">']
    g.append('<div class="map-controls">'
             '<button type="button" data-zoom="in" aria-label="Zoom in">+</button>'
             '<button type="button" data-zoom="out" aria-label="Zoom out">−</button>'
             '<button type="button" data-zoom="reset">Reset</button>'
             '<span class="map-hint">scroll or pinch to zoom · drag to pan</span>'
             '</div>')
    g.append('<svg viewBox="0 0 %.0f %.0f" preserveAspectRatio="xMidYMid meet" role="img" aria-label="World map of simulator routes by aircraft type">' % (W, H))
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
    for a, b, ac, n in sorted(routes, key=lambda r: r[3]):
        p = arc_path((airports[a]['lat'], airports[a]['lon']), (airports[b]['lat'], airports[b]['lon']))
        width = 0.9 + 2.0 * (n / max_n)
        opacity = 0.95 if n > 1 else 0.6
        dash = ' stroke-dasharray="4 3"' if n == 1 else ''
        g.append('<path class="route" data-ac="%s" d="%s" stroke="%s" stroke-width="%.2f" stroke-opacity="%.2f"%s>'
                 '<title>%s → %s · %s · %d×</title></path>'
                 % (ac, p, color(ac), width, opacity, dash, a, b, ac, n))
    g.append('</g>')

    g.append('<g fill="none">')
    for a, b, ac, n in circuits:
        x, y = xy(airports[a]['lon'], airports[a]['lat'])
        r = 5.0 + 1.6 * n
        g.append('<circle data-ac="%s" cx="%.1f" cy="%.1f" r="%.1f" stroke="%s" stroke-width="1.3" stroke-dasharray="2 2" fill="none" opacity="0.85">'
                 '<title>%s · local circuits · %s · %d×</title></circle>'
                 % (ac, x, y, r, color(ac), a, ac, n))
    g.append('</g>')

    busiest = {c: 0 for c in airports}
    for a, b, ac, n in legs:
        busiest[a] += n
        busiest[b] += n
    g.append('<g>')
    for code, ap in airports.items():
        x, y = xy(ap['lon'], ap['lat'])
        r = 3.4 if code == 'VHHH' else 2.2
        g.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="#274b6d" stroke="#fff" stroke-width="0.7">'
                 '<title>%s — %s</title></circle>' % (x, y, r, code, ap['name']))
    g.append('</g>')
    g.append('<g font-family="-apple-system, Segoe UI, sans-serif" font-size="8.5" fill="#123c5c">')
    for code, ap in airports.items():
        if code != 'VHHH' and busiest.get(code, 0) < 5:
            continue
        x, y = xy(ap['lon'], ap['lat'])
        anchor = 'start' if ap['lon'] > -30 else 'end'
        g.append('<text x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                 % (x + (5 if anchor == 'start' else -5), y + 2.5, anchor, code))
    g.append('</g>')
    g.append('</svg>')

    legend = ['<div class="legend">']
    for ac in ac_order:
        legend.append('<span><i style="background:%s"></i>%s <b style="font-weight:600">%d</b></span>'
                      % (color(ac), ac, by_ac[ac]))
    legend.append('<span><i class="dash"></i> flown once</span>')
    legend.append('<span><i class="ring"></i> local circuits</span>')
    legend.append('</div>')
    g.append('\n'.join(legend))
    g.append('</div>')

    table = ''.join(
        '<tr%s><td><strong>%s</strong> → <strong>%s</strong></td><td>%s</td><td>%s → %s</td><td>%d</td></tr>'
        % (' class="weak"' if n == 1 else '', a, b, ac,
           airports[a]['name'], airports[b]['name'], n)
        for a, b, ac, n in sorted(legs, key=lambda r: (-r[3], r[2], r[0])))

    frag = '\n'.join([
        START,
        '<h3>Simulator route map</h3>',
        '',
        '<p>Every leg recorded in the simulator logbook — not real flying — drawn as great-circle arcs between '
        'the airports actually departed and arrived. Colour is the aircraft type; dashed lines were flown once; '
        'dashed rings are local circuits at a single field.</p>',
        '',
        '\n'.join(g),
        '',
        '<p class="small">%d legs and %d circuit entries across %d airports. Scroll or pinch to zoom, drag to pan; '
        'hover a line or a point for the aircraft and count.</p>'
        % (len(routes), len(circuits), len(airports)),
        '',
        '<div class="table-scroll">',
        '<table>',
        '  <thead><tr><th style="width:18%">Leg</th><th style="width:14%">Aircraft</th><th>Airports</th><th style="width:10%">Times</th></tr></thead>',
        '  <tbody>',
        table,
        '  </tbody>',
        '</table>',
        '</div>',
        '',
        ('<p class="small">Not drawn — airport coordinates unknown: %s.</p>'
         % ', '.join('%s → %s' % (a, b) for a, b, ac, n in skipped)) if skipped else '',
        '',
        '<div class="note">',
        '  <p><strong>How this is built.</strong> Airport codes and aircraft ids are read from the simulator\'s own '
        'logbook file (<code>sr_logbook</code>), which stores them in a binary stream; each airport code is attributed '
        'to the aircraft id that follows it, and neighbouring airports become legs. A leg marked “flown once” may be '
        'an artefact of two sessions sitting next to each other in the file rather than a flight you actually made. '
        'Dates, block times and landing counts are not stored as plain values — they exist only on the simulator\'s '
        'logbook screen.</p>',
        '</div>',
        END,
    ])
    return frag, len(routes), len(circuits), len(airports), sorted({c for a, b, ac, n in skipped for c in (a, b) if c not in airports})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--routes', required=True)
    ap.add_argument('--airports', required=True)
    ap.add_argument('--land', required=True)
    ap.add_argument('--page', default='logbook.html')
    a = ap.parse_args()

    rows = []
    with open(a.routes, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append((r['from'].strip(), r['to'].strip(), r['aircraft'].strip(), int(r['count'])))

    airports = load_airports(a.airports, sorted({c for r in rows for c in r[:2]}))
    land = load_land(a.land)
    frag, nlegs, ncirc, napt, missing = build_fragment(rows, airports, land)

    html = open(a.page, encoding='utf-8').read()
    if START not in html or END not in html:
        raise SystemExit('markers not found in %s' % a.page)
    head, rest = html.split(START, 1)
    _, tail = rest.split(END, 1)
    open(a.page, 'w', encoding='utf-8', newline='\n').write(head + frag + tail)
    print('map written into %s: %d legs, %d circuits, %d airports, %d land paths (%.1f KB)'
          % (a.page, nlegs, ncirc, napt, len(land), os.path.getsize(a.page) / 1024.0))
    if missing:
        print('no coordinates:', ', '.join(missing))


if __name__ == '__main__':
    main()