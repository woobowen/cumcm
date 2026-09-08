"""First-party raw ephemeris/document acquisition; never executes downloaded code."""

import hashlib
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(".cache/pr12-rc8/fresh/2015/case")
CITIES = {
    "Beijing": [116.4074, 39.9042, 0.0],
    "Harbin": [126.6424, 45.7567, 0.0],
    "Shanghai": [121.4737, 31.2304, 0.0],
    "Guangzhou": [113.2644, 23.1291, 0.0],
    "Kunming": [102.8329, 24.8801, 0.0],
    "Chengdu": [104.0665, 30.5728, 0.0],
    "Urumqi": [87.6168, 43.8256, 0.0],
}
ledger = ROOT / "research/retrieval_ledger.json"
records = json.loads(ledger.read_text()) if ledger.exists() else []


def get(name, url, purpose):
    p = ROOT / "data/raw" / name
    if p.exists():
        return
    start = datetime.now(UTC).isoformat()
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
            status = r.status
        p.write_bytes(data)
        item = {
            "file": str(p.relative_to(ROOT)),
            "url": url,
            "retrieved_at": start,
            "http_status": status,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "purpose": purpose,
            "answer_contamination": "NONE_OBSERVED",
            "code_executed": False,
        }
    except Exception as e:
        item = {
            "file": str(p.relative_to(ROOT)),
            "url": url,
            "retrieved_at": start,
            "error": type(e).__name__ + ": " + str(e),
            "purpose": purpose,
            "answer_contamination": "NONE_OBSERVED",
        }
    records.append(item)
    ledger.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(item, ensure_ascii=False), flush=True)
    if "error" in item:
        raise RuntimeError("ACQUISITION_FAILED_STOP_BATCH")


def api(name, extra, purpose):
    d = {
        "format": "text",
        "OBJ_DATA": "'YES'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CSV_FORMAT": "'YES'",
        "ANG_FORMAT": "'DEG'",
        "EXTRA_PREC": "'YES'",
        "CAL_FORMAT": "'JD'",
        "TIME_DIGITS": "'SECONDS'",
        "TIME_TYPE": "'UT'",
        "APPARENT": "'AIRLESS'",
        "RANGE_UNITS": "'KM'",
    }
    d.update(extra)
    get(name, "https://ssd.jpl.nasa.gov/api/horizons.api?" + urllib.parse.urlencode(d), purpose)


if __name__ == "__main__":
    import argparse

    a = argparse.ArgumentParser()
    a.add_argument("--mode", choices=["docs", "geocentric", "reference"], required=True)
    args = a.parse_args()
    if args.mode == "docs":
        for name, url in [
            ("horizons_api.html", "https://ssd-api.jpl.nasa.gov/doc/horizons.html"),
            ("horizons_manual.html", "https://ssd.jpl.nasa.gov/horizons/manual.html"),
            ("noaa_twilight.html", "https://gml.noaa.gov/grad/solcalc/glossary.html"),
            ("usno_sidereal.html", "https://aa.usno.navy.mil/faq/GAST"),
        ]:
            get(
                name,
                url,
                "Official general method/reference definitions; no problem-specific solution",
            )
    if args.mode == "geocentric":
        for body, command in [("sun", "10"), ("moon", "301")]:
            api(
                body + "_geocentric.txt",
                {
                    "COMMAND": repr(command),
                    "CENTER": "'500@399'",
                    "START_TIME": "'2015-12-31 00:00'",
                    "STOP_TIME": "'2017-01-02 00:00'",
                    "STEP_SIZE": "'1 h'",
                    "QUANTITIES": "'2,20'",
                },
                (
                    "Geocentric apparent RA/DEC and range forcing for first-party p"
                    "hysical coordinate model; ephemeris-derived not raw empirical"
                ),
            )
    if args.mode == "reference":
        times = [
            datetime(2016, m, 15, h, 30, tzinfo=UTC).timestamp() / 86400 + 2440587.5
            for m in range(1, 13)
            for h in [11]
        ]
        for city, coords in CITIES.items():
            for body, command in [("sun", "10"), ("moon", "301")]:
                api(
                    city + "_" + body + "_reference.txt",
                    {
                        "COMMAND": repr(command),
                        "CENTER": "'coord@399'",
                        "SITE_COORD": repr(",".join(map(str, coords))),
                        "COORD_TYPE": "'GEODETIC'",
                        "TLIST": " ".join(repr(f"{t:.9f}") for t in times),
                        "TLIST_TYPE": "'JD'",
                        "QUANTITIES": "'4'",
                    },
                    (
                        "Independent JPL topocentric angular check: monthly day15 at 11"
                        ":30 UTC, predeclared without model results"
                    ),
                )
