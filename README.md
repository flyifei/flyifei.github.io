# Jeff Li — Cadet Pilot Notes

Personal study site for the Cathay Pacific Cadet Pilot Programme.
Live at **https://flyifei.github.io**

## Pages

| File | Content |
| --- | --- |
| `index.html` | Home: hero, profile summary, section index, live VHHH METAR/TAF |
| `about.html` | Full profile — engineering background, leadership, what I bring to a flight deck |
| `application.html` | Eligibility, English requirements, six-step selection process, checklist |
| `cathay.html` | Career ladder, ~80-week training pathway, fleet, Second Officer package |
| `resources.html` | Official sources, ATPL subjects, radiotelephony drills, simulator drills, books |
| `logbook.html` | Flight log: at-a-glance comparison, real flying table, simulator table + route map |
| `404.html` | Not found |

## Stack

Plain static HTML and a single shared stylesheet. No build step, no framework, no dependencies.
Light blue and white theme (`#0b5f9e` / `#ffffff`, `#eaf4fc` table header, `#d5e6f5` borders).
The only JavaScript is the METAR/TAF fetch on the home page.

## Local preview

```powershell
cd flyifei-site
python -m http.server 8080
# open http://127.0.0.1:8080
```

The pages open fine from disk (`file://`) too, except the weather box, which needs HTTP for the
cross-origin fetch.

## Editing

- **Flight log**: add a `<tr>` to the *Real flying* or *Simulated flying* table in `logbook.html`, keeping the two separate, then update the matching column in the *At a glance* table.
- **ATPL subject status**: edit the status column in the `resources.html` subject table.
- **Checklist**: plain `<ul>` in `application.html`.
- **Navigation**: the `<header>` block is duplicated in every page — when adding a page, update all of them.
- **Theme**: `assets/css/style.css`, CSS variables at the top (`--blue`, `--blue-fill`, `--blue-line`).

## Route map

Inside `logbook.html`, under *Simulated flying*, there is a world map of every simulator leg drawn as
inline SVG — no tiles, no CDN, no JavaScript. It is generated from `routes.csv` into the block between
`<!-- ROUTEMAP:START -->` and `<!-- ROUTEMAP:END -->`, so re-running the build is idempotent.

```powershell
# 1. re-extract legs from the simulator logbook (MSFS 2024, Steam cloud save)
python tools/extract_routes.py "D:\steam\userdata\1041263203\2537590\remote\sr_logbook" > routes.csv

# 2. redraw the map inside logbook.html
python tools/build_map.py --routes routes.csv --airports airports.json --land ne_110m_land.geojson
```

- `routes.csv` — three columns (`from,to,count`); edit by hand if you prefer.
- `airports.json` (mwgg/Airports) and `ne_110m_land.geojson` (Natural Earth 110m land) are build-time
  inputs only and are **not** shipped with the site.
- The map covers simulator legs only. Real flights are never plotted on it.

## Deployment
GitHub Pages serves this repository's `master` branch as the user site `flyifei.github.io`.
`.nojekyll` stops Jekyll from processing the directory.

```powershell
git add .
git commit -m "Update notes"
git push
```

## Sources

Programme facts (about 80 weeks, eligibility, English scores, selection steps, Second Officer figures)
come from `careers.cathaypacific.com`, figures dated January 2026. Requirements are reviewed periodically —
check the official pages before relying on anything here.

Weather data: MET Norway `api.met.no` tafmetar API (CORS-enabled, latest report shown).

Personal study site, not affiliated with Cathay Pacific Airways.