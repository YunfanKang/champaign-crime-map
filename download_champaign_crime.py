#!/usr/bin/env python3
"""
Download 2025 crime/incident data for Champaign County, IL.

Source: METCAD (Metropolitan Computer-Aided Dispatch) -- the consolidated 911
dispatch center for Champaign County -- via its public Tyler/Socrata
"Citizen Connect" portal: https://metcadil-transparency.connect.socrata.com
(underlying private dataset nfkn-sftu, "cases").

The read proxy (/api/tickets/details.json) caps each response at 100 rows and
its offset paging is NOT order-stable (it duplicates and drops rows). The date
filter is day-granular and a single day under 100 rows comes back complete in
one request. So we fetch DAY BY DAY (one clean request per day); any day that
hits the 100 cap is split by category (categories are disjoint NCIC groupings,
so the union stays complete) -- no offset paging anywhere.
"""
import csv, json, time, sys, datetime as dt
import urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# Date range + output paths (override on CLI: download_champaign_crime.py START END LABEL)
START = sys.argv[1] if len(sys.argv) > 1 else "2025-01-01"
END   = sys.argv[2] if len(sys.argv) > 2 else "2025-12-31"
LABEL = sys.argv[3] if len(sys.argv) > 3 else "2025"
OUT_CSV = f"champaign_crime_{LABEL}.csv"
OUT_RAW = f"champaign_crime_{LABEL}_raw.json"

BASE = "https://metcadil-transparency.connect.socrata.com"
HID  = "metcadil-transparency.connect.socrata.com"
CACHE_VERSION = "1748623607840"
BBOX = {"lat1": "40.65", "lng1": "-87.45", "lat2": "39.70", "lng2": "-88.75"}
ALL_CAT_IDS = list(range(2, 58))            # 56 leaf categories under super-cat "Cases" (id 1)

def cat_param(ids):
    return "1:" + "&".join(f"{i}=" for i in ids)

def build_url(start, end, cat_ids, limit=100, offset=0):
    params = {**BBOX, "zoom": "10", "host_or_app_id": HID,
              "cache_version": CACHE_VERSION, "categories": cat_param(cat_ids),
              "start_date": start, "end_date": end,
              "limit": str(limit), "offset": str(offset)}
    return f"{BASE}/api/tickets/details.json?" + urllib.parse.urlencode(params)

def fetch(url, retries=5):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                                       "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            last = e
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"failed: {last}")

def fetch_slice(day, cat_ids):
    """Fetch one day for a subset of categories. If the 100 cap is hit, split
    the category set in half and recurse (disjoint -> complete)."""
    d = fetch(build_url(day, day, cat_ids))
    recs = d.get("api_data", {}).get("records", [])
    if len(recs) < 100 or len(cat_ids) == 1:
        if len(recs) >= 100 and len(cat_ids) == 1:
            print(f"  ! {day} cat {cat_ids[0]} hit cap (rare)", file=sys.stderr)
        return recs
    mid = len(cat_ids) // 2
    return fetch_slice(day, cat_ids[:mid]) + fetch_slice(day, cat_ids[mid:])

def fetch_day(day):
    return day, fetch_slice(day, ALL_CAT_IDS)

def days_in_range(start, end):
    d, last = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
    while d <= last:
        yield d.isoformat()
        d += dt.timedelta(days=1)

def main():
    days = list(days_in_range(START, END))
    print(f"Fetching {len(days)} days ({START}..{END}) of Champaign County incidents (day-by-day)...")
    by_day, done = {}, 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_day, d): d for d in days}
        for fut in as_completed(futs):
            day, recs = fut.result()
            by_day[day] = recs
            done += 1
            if done % 60 == 0:
                print(f"  ...{done}/{len(days)} days")

    all_recs = [r for d in days for r in by_day[d]]
    with open(OUT_RAW, "w") as f:
        json.dump(all_recs, f)

    # Dedupe by row id ':id' (within-day category splits are disjoint, so this
    # is just belt-and-suspenders).
    seen, rows = set(), []
    for r in all_recs:
        rid = r.get(":id")
        if rid in seen:
            continue
        seen.add(rid)
        loc = r.get("location") or {}
        coords = loc.get("coordinates") if isinstance(loc, dict) else None
        lng, lat = (coords + [None, None])[:2] if coords else (None, None)
        rows.append({"row_id": rid, "ticket_id": r.get("ticket_id"),
                     "category": r.get("category"),
                     "datetime": r.get("ticket_created_at"),
                     "latitude": lat, "longitude": lng})

    rows.sort(key=lambda x: (x["datetime"] or ""))
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["row_id", "ticket_id", "category",
                                          "datetime", "latitude", "longitude"])
        w.writeheader()
        w.writerows(rows)

    capped = sum(1 for d in days if len(by_day[d]) >= 100)
    print(f"\nDays that needed category-splitting (>=100): {capped}")
    print(f"Total unique incidents: {len(rows)}")
    print(f"Saved: {OUT_CSV}")
    return rows

if __name__ == "__main__":
    main()
