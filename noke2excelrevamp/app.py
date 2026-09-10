import csv
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from flask import Flask, abort, render_template, send_from_directory
from main3 import BASE_URL, UNIT_FILTERS, UNITS_PATH, extract_unit_info, login
from werkzeug.middleware.proxy_fix import ProxyFix

# See main3.py: Windows console isn't UTF-8 by default, which crashes prints
# containing arrows/dashes.
sys.stdout.reconfigure(encoding="utf-8")

app = Flask(__name__)

# Served behind nginx at soundcheck.tools/lockers. ProxyFix honors the
# X-Forwarded-Prefix / -Proto headers nginx sends, so url_for() builds correct
# https://soundcheck.tools/lockers/... links instead of bare "/..." paths.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)

# Leading locker-id portion of a unit name, e.g. "L121 / L154 - " or "L002- ".
_LOCKER_PREFIX = re.compile(r"^\s*L\d+\s*(?:/\s*L?\d+\s*)*[-–]?\s*")

# Folder holding the saved monthly spreadsheets shown on the Past Months page.
# Must match main3.py's OUTPUT_DIR — that's the script that writes the files.
SPREADS_DIR = Path(__file__).parent / "spreads"

# How often the background thread refreshes the cached units (seconds).
REFRESH_SECONDS = 300  # 5 minutes

# Server runs in UTC; show "updated at" in Nashville (Central) time.
CENTRAL = ZoneInfo("America/Chicago")

# In-memory cache so page loads are instant and we hit the API at most once
# per REFRESH_SECONDS instead of once per visitor.
_cache_lock = threading.Lock()
_cache = {"units": [], "updated_at": None}


def load_locker_info():
    """Map every individual locker id to its CSV row.

    Some CSV rows cover combined lockers keyed as "L121/L154", but the live
    API lists those under a single id ("L121"). Register each component id so
    the join still finds the row.
    """
    lockers = {}
    with open("lockers.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            parts = [p.strip() for p in row["locker_id"].split("/") if p.strip()]
            prefix = ""
            for p in parts:
                if not p[0].isdigit():
                    prefix = p[0]  # carry the "L" across bare-number parts ("L133/134")
                locker_id = p if p[0].isdigit() is False else prefix + p
                lockers[locker_id] = row
    return lockers


def artist_from_name(unit_name):
    """Pull the live artist name out of the unit name (everything after the id)."""
    return _LOCKER_PREFIX.sub("", unit_name or "").strip()


def get_units():
    token = login()
    headers = {"Authorization": f"Bearer {token}", "content-type":
        "application/json"}
    response = requests.post(BASE_URL + UNITS_PATH, headers=headers,
                             json={"filter": UNIT_FILTERS}, timeout=10)
    units = extract_unit_info(response.json(), token)
    lockers = load_locker_info()
    for unit in units:
        unit["locker"] = lockers.get(unit["unit_id"], {})
        unit["artist_name"] = artist_from_name(unit["unit_name"])
    return units


def refresh_cache():
    """Pull fresh units from the API and store them in the cache."""
    units = get_units()
    with _cache_lock:
        _cache["units"] = units
        _cache["updated_at"] = datetime.now(CENTRAL)
    print(f"Cache refreshed at {datetime.now(CENTRAL):%H:%M:%S} — {len(units)} units")


def _refresh_loop():
    """Background worker: refresh the cache every REFRESH_SECONDS forever."""
    while True:
        time.sleep(REFRESH_SECONDS)
        try:
            refresh_cache()
        except Exception as e:
            print(f"Background refresh failed (keeping old cache): {e}")


def list_spreadsheets():
    """Return saved spreadsheets in the spreads folder, newest file first."""
    if not SPREADS_DIR.exists():
        return []
    months = []
    for p in SPREADS_DIR.glob("*.xlsx"):
        # Skip Excel temp lock files and the live current-month file.
        if p.name.startswith("~$") or p.name.startswith("Current_"):
            continue
        try:
            dt = datetime.strptime(p.stem, "%B_%Y")  # "April_2026" -> date
        except ValueError:
            continue  # ignore anything not named like "Month_Year"
        months.append((dt, p))
    months.sort(key=lambda x: x[0], reverse=True)  # newest first (April -> March)
    return [
        {"filename": p.name, "label": dt.strftime("%B %Y")}
        for dt, p in months
    ]


@app.route("/")
def home():
    with _cache_lock:
        units = _cache["units"]
        updated_at = _cache["updated_at"]
    return render_template("index.html", units=units, updated_at=updated_at)


@app.route("/pastmonths")
def past_months():
    return render_template("pastmonths.html", spreadsheets=list_spreadsheets())


@app.route("/download/current")
def download_current():
    """Download this month's live spreadsheet (Current_<Month>_<Year>.xlsx)."""
    month_year = datetime.today().strftime("%B_%Y")  # e.g. "June_2026"
    filename = f"Current_{month_year}.xlsx"
    if not (SPREADS_DIR / filename).exists():
        abort(404)
    return send_from_directory(SPREADS_DIR, filename, as_attachment=True)


@app.route("/spreads/<path:filename>")
def download_spreadsheet(filename):
    # send_from_directory blocks path traversal and 404s missing files.
    if not filename.endswith(".xlsx"):
        abort(404)
    return send_from_directory(SPREADS_DIR, filename, as_attachment=True)


def start_background_refresh():
    """Prime the cache once, then refresh forever in the background.

    Runs at import time (below) so it also works under gunicorn, which
    imports `app` instead of executing the __main__ block. Wrapped in
    try/except so a NOKE hiccup at boot doesn't stop the server coming
    up — the page just shows an empty table until the first good refresh.
    """
    try:
        refresh_cache()
    except Exception as e:
        print(f"Initial cache load failed (will retry in background): {e}")
    threading.Thread(target=_refresh_loop, daemon=True).start()


# Run on import so gunicorn (server) and `python app.py` (local) both get it.
# With gunicorn --workers 1 this fires once → a single refresh thread.
start_background_refresh()


if __name__ == "__main__":
    # Local dev only — gunicorn ignores this block on the server.
    # use_reloader=False so we don't spawn a second refresh thread (= double API hits).
    app.run(debug=True, port=5000, use_reloader=False)
