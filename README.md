# Champaign County Crime Map (2025–2026)

An interactive, self-updating crime map for Champaign County, IL — built from
[METCAD 911](https://metcadil-transparency.connect.socrata.com/) dispatch data
(the county's consolidated 911 center, covering Champaign PD, Urbana PD, UIUC,
Savoy, Rantoul, the Sheriff, etc.).

**Live map:** `https://<your-username>.github.io/champaign-crime-map/`

## Features
- Heatmap / clustered-pin views, color-coded by 13 harmonized crime groups
- Year toggle (Both / 2025 / 2026), date-range and hour-of-day filters
- Location search (geocode + radius crime count)
- A → B route planner that counts crimes along the route
- All filters compose; "Other/Admin" (non-crime reports) is off by default

## How the daily auto-update works
`.github/workflows/update.yml` runs every day (11:00 UTC):
1. `download_champaign_crime.py 2026-01-01 <today> 2026` — re-fetches the current
   year from METCAD's Citizen Connect API, day-by-day (its API caps responses at
   100 rows and offset paging is unstable, so day-by-day is the reliable method).
2. `build_combined_map.py` — regenerates `champaign_crime_combined_map.html` and
   copies it to `index.html`.
3. Commits the refreshed data + map back to `main`, which republishes Pages.

`champaign_crime_2025.csv` is the complete, static 2025 dataset.
`champaign_crime_2026.csv` is refreshed daily.

## One-time setup
1. Push this repo to GitHub.
2. **Settings → Pages → Build and deployment → Source: "Deploy from a branch",
   Branch: `main` / `/ (root)`.** The site appears at the URL above.
3. **Settings → Actions → General → Workflow permissions → "Read and write
   permissions"** (so the daily job can commit). Then the workflow runs on
   schedule, or trigger it now via **Actions → Update… → Run workflow**.

## Run locally
```bash
python download_champaign_crime.py 2026-01-01 $(date +%F) 2026   # refresh 2026
python build_combined_map.py                                     # rebuild HTML
open champaign_crime_combined_map.html
```

## Note for 2027+
`build_combined_map.py` currently reads `champaign_crime_2025.csv` +
`champaign_crime_2026.csv`. When 2027 begins, add a 2027 CSV and update the
year list in `build_combined_map.py` and the year/date in `update.yml`.

## Data caveats
- Countywide **dispatch** data: includes some non-crime calls (accidents,
  lost & found, assists) — grouped under "Other/Admin", off by default.
- Locations are block-level; the most recent 1–3 days lag as reports finalize.
- Map tiles/geocoding/routing use OpenStreetMap, CARTO, Nominatim and OSRM.
