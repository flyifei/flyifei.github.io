# Cathay Pacific Cadet Pilot — Preparation Notes

Personal study site for the Cathay Pacific Cadet Pilot Programme.
Live at **https://flyifei.github.io**

## Pages

| File | Content |
| --- | --- |
| `index.html` | Home: purpose, section index, live VHHH METAR/TAF, about |
| `application.html` | Eligibility, English requirements, six-step selection process, checklist |
| `cathay.html` | Career ladder, ~80-week training pathway, fleet, Second Officer package |
| `resources.html` | Official sources, ATPL subjects, radiotelephony drills, simulator drills, books |
| `logbook.html` | Simulator and real flight tables with totals |
| `404.html` | Not found |

Plain static HTML with one shared stylesheet. No build step, no framework, no JavaScript except the
weather fetch on the home page. English only.

## Local preview

```powershell
cd flyifei-site
python -m http.server 8080
# open http://127.0.0.1:8080
```

The site also works opened directly from disk (`file://`), except the METAR/TAF box, which needs HTTP
for the cross-origin fetch.

## Editing

- **Flight log**: add a `<tr>` to the simulator or real table in `logbook.html`, then update the totals table at the top.
- **ATPL subject status**: edit the status column in the `resources.html` subject table.
- **Checklist**: plain `<ul>` in `application.html`.
- **Style**: `assets/css/style.css` — off-white background, system fonts, 900 px column, thin table borders.

## Deployment

GitHub Pages serves this repository's `master` branch as the user site `flyifei.github.io`.
The `.nojekyll` file stops Jekyll from processing the directory.

```powershell
git add .
git commit -m "Update notes"
git push
```

## Sources

Programme facts (about 80 weeks, eligibility, English scores, selection steps, Second Officer figures)
are taken from `careers.cathaypacific.com`, with figures dated January 2026. Requirements are reviewed by
the airline periodically — check the official pages before relying on anything here.

Weather data: MET Norway `api.met.no` tafmetar API (CORS-enabled, latest report only).

This is a personal study site and is not affiliated with Cathay Pacific Airways.