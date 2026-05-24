# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt   # install dependencies

python monitor.py                 # fetch flights from API and save to flights.db
python report.py                  # read flights.db and generate index.html
update.bat                        # full pipeline: fetch → report → git push (Windows)
```

## Architecture

The project is a three-stage pipeline: **fetch → store → report → deploy**.

**`monitor.py`** — orchestrates the fetch stage. For each date window it calls the **SerpAPI Google Flights engine** (`https://serpapi.com/search?engine=google_flights`) using IATA codes directly (SJO → CUN). It filters out any itinerary whose first segment does not depart from `ORIGIN` (SJO), then passes the parsed results to `db.py`. No airport ID caching file is needed.

**`db.py`** — all SQLite logic. A single table `flight_prices` uses a `flight_id` column (16-char SHA-256 hex of `departure_date|return_date|airline|price_usd|stops|query_date`) as PRIMARY KEY. `INSERT OR IGNORE` makes every insert idempotent. `init_db` is safe to call on every run.

Table schema:
```
flight_id      TEXT  PRIMARY KEY   (sha256 hash, 16 chars)
queried_at     TEXT  NOT NULL      (ISO-8601 UTC timestamp)
query_date     TEXT  NOT NULL      (YYYY-MM-DD, derived from queried_at)
departure_date TEXT  NOT NULL
return_date    TEXT  NOT NULL
airline        TEXT  NOT NULL
price_usd      REAL  NOT NULL
stops          INTEGER NOT NULL
duration_min   INTEGER NOT NULL    (total flight duration in minutes)
```

**`report.py`** — reads from `flight_prices` using pandas, annotates the cheapest row per date window (`is_min=True`), formats duration as `Xh Ym`, appends a Kayak deep-link per row, and renders `index.html` via an inline Jinja2 template. The min-price row gets the CSS class `min-price` (green highlight).

**`update.bat`** — Windows script that runs the full pipeline end to end:
1. `python monitor.py` — fetch and store
2. `python report.py` — generate `index.html`
3. `git add index.html && git commit && git push` — publish to GitHub Pages

## Deployment

The report is published to **GitHub Pages**:
- Repo: `https://github.com/jojosejavier/monitor-vuelos`
- Live URL: `https://jojosejavier.github.io/monitor-vuelos/`

The `index.html` in the repo root is what GitHub Pages serves. Every `git push` to `main` updates the live report automatically.

## Automation (Windows Task Scheduler)

The task **`MonitorVuelos`** is registered in Windows Task Scheduler to run `update.bat` automatically at every user logon, with a 1-minute delay to ensure network is available.

| Action | Command |
|---|---|
| Run manually now | double-click `update.bat` or `schtasks /run /tn "MonitorVuelos"` |
| Pause | `schtasks /change /tn "MonitorVuelos" /disable` |
| Resume | `schtasks /change /tn "MonitorVuelos" /enable` |
| Remove | `schtasks /delete /tn "MonitorVuelos" /f` |
| Reinstall | run `instalar-tarea.ps1` as Administrator (self-elevating) |

## Key constants to update

Both `monitor.py` and `report.py` share hardcoded `DATE_WINDOWS`.

In **`monitor.py`** (2-tuple):
```python
DATE_WINDOWS = [
    ("2027-02-13", "2027-02-20"),
    ("2027-02-20", "2027-02-27"),
]
```

In **`report.py`** (3-tuple — includes display label):
```python
DATE_WINDOWS = [
    ("2027-02-13", "2027-02-20", "13-20 de febrero 2027"),
    ("2027-02-20", "2027-02-27", "20-27 de febrero 2027"),
]
```

If the monitored dates change, update this list in **both files** (keeping the correct tuple format for each).

## Environment

Requires a `.env` file in the project root:

```
SERPAPI_KEY=your_serpapi_key_here
```

The API is **SerpAPI** (`serpapi.com`) using the `google_flights` engine — free tier has a limited monthly quota. If `parse_offers` returns 0 results, print `data.get("best_flights", [])[:1]` to inspect the raw payload and check for API/schema changes.

## Generated / local files (not committed)

| File | Created by | Notes |
|---|---|---|
| `flights.db` | `monitor.py` on first run | SQLite database |
| `reporte.html` | legacy name, no longer used | replaced by `index.html` |
| `guia de uso.txt` | manual | local usage guide |
| `instalar-tarea.ps1` | manual | Task Scheduler installer, run as admin |

## Dependencies (`requirements.txt`)

```
requests>=2.31.0
python-dotenv>=1.0.0
pandas>=2.0.0
Jinja2>=3.1.0
```
