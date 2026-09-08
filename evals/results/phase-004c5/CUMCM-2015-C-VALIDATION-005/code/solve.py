"""First-party spherical astronomy model driven by registered JPL geocentric tables.
No network and no fitted coefficients. Candidate difference is lunar/solar parallax.
"""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq


def table(path):
    s = path.read_text().split("$$SOE")[1].split("$$EOE")[0]
    return np.array(
        [
            [float(r[0]), *[float(x) for x in r[3:] if x.strip()]]
            for r in csv.reader(s.strip().splitlines())
        ]
    )


class Sky:
    def __init__(self, root, topo):
        self.topo = topo
        self.eph = {}
        for body in ["sun", "moon"]:
            a = table(root / "data/raw" / f"{body}_geocentric.txt")
            a[:, 1] = np.unwrap(np.deg2rad(a[:, 1]))
            a[:, 2] = np.deg2rad(a[:, 2])
            self.eph[body] = CubicSpline(a[:, 0], a[:, 1:4], axis=0)

    def position(self, t, coords, body):
        t = np.asarray(t)
        ra, dec, r = np.moveaxis(self.eph[body](t), -1, 0)
        d = t - 2451545.0
        t0 = np.floor(t - 0.5) + 0.5
        H = (t - t0) * 24
        du = t0 - 2451545.0
        T = d / 36525
        gmst = 6.697375 + 0.065709824279 * du + 1.0027379 * H + 0.0000258 * T * T
        eq = (
            -0.000319 * np.sin(np.deg2rad(125.04 - 0.052954 * d))
            - 0.000024 * np.sin(np.deg2rad(2 * (280.47 + 0.98565 * d)))
        ) * np.cos(np.deg2rad(23.4393 - 0.0000004 * d))
        theta = np.deg2rad(15 * (gmst + eq) + coords[0])
        phi = np.deg2rad(coords[1])
        altkm = coords[2]
        x = r * np.cos(dec) * np.cos(ra)
        y = r * np.cos(dec) * np.sin(ra)
        z = r * np.sin(dec)
        if self.topo:
            e2 = 6.69437999014e-3
            N = 6378.137 / np.sqrt(1 - e2 * np.sin(phi) ** 2)
            x = x - (N + altkm) * np.cos(phi) * np.cos(theta)
            y = y - (N + altkm) * np.cos(phi) * np.sin(theta)
            z = z - (N * (1 - e2) + altkm) * np.sin(phi)
        east = -np.sin(theta) * x + np.cos(theta) * y
        north = -np.sin(phi) * np.cos(theta) * x - np.sin(phi) * np.sin(theta) * y + np.cos(phi) * z
        up = np.cos(phi) * np.cos(theta) * x + np.cos(phi) * np.sin(theta) * y + np.sin(phi) * z
        alt = np.rad2deg(np.arctan2(up, np.hypot(east, north)))
        az = np.rad2deg(np.arctan2(east, north)) % 360
        return alt, az

    def altitude(self, t, coords, body):
        return self.position(t, coords, body)[0]


def roots(sky, coords, body, level, start, stop, rising):
    ts = np.linspace(start, stop, 289)
    ys = sky.altitude(ts, coords, body) - level
    res = []
    for i in range(len(ts) - 1):
        if (ys[i] <= 0 < ys[i + 1]) if rising else (ys[i] >= 0 > ys[i + 1]):
            res.append(
                float(
                    brentq(
                        lambda t: float(sky.altitude(t, coords, body)) - level,
                        ts[i],
                        ts[i + 1],
                        xtol=2e-10,
                    )
                )
            )
    return res


def local(t):
    return (
        datetime.fromtimestamp(round((t - 2440587.5) * 86400, 3), UTC)
        .astimezone(timezone(timedelta(hours=8)))
        .isoformat(timespec="seconds")
    )


def events(sky, cities, moonlo=8.0, moonhi=12.0, sunlo=-12.0, sunhi=-6.0, latitude_shift=0.0):
    allrows = {}
    daily = {}
    start = (
        datetime(2016, 1, 1, tzinfo=timezone(timedelta(hours=8))).timestamp() / 86400 + 2440587.5
    )
    for city, c0 in cities.items():
        c = [c0[0], c0[1] + latitude_shift, c0[2]]
        rows = []
        days = []
        for day in range(366):
            a = start + day
            lo = a + 0.5
            hi = a + 1
            # Bisection/bracketing domain includes each complete evening for the seven sites.
            solar = {str(h): roots(sky, c, "sun", h, lo, hi, False) for h in [-0.833, sunhi, sunlo]}
            m0 = roots(sky, c, "moon", moonlo, a, a + 1, True)
            m1 = roots(sky, c, "moon", moonhi, a, a + 1 + 1 / 24, True)
            m10 = roots(sky, c, "moon", 10.0, a, a + 1, True)
            days.append(
                {
                    "date": local(a)[:10],
                    "sunset_jd": solar["-0.833"][0] if solar["-0.833"] else None,
                    "dusk_start_jd": solar[str(sunhi)][0] if solar[str(sunhi)] else None,
                    "dusk_end_jd": solar[str(sunlo)][0] if solar[str(sunlo)] else None,
                    "moon10_rising_jd": m10,
                }
            )
            if not solar[str(sunhi)] or not solar[str(sunlo)]:
                continue
            s0, s1 = solar[str(sunhi)][0], solar[str(sunlo)][0]
            for x in m0:
                ends = [y for y in m1 if x < y < x + 0.3]
                if not ends:
                    continue
                window_start = max(x, s0)
                u = min(ends[0], s1)
                if u - window_start > 1e-9:
                    mid = (window_start + u) / 2
                    mh, az = sky.position(mid, c, "moon")
                    sh = sky.altitude(mid, c, "sun")
                    rows.append(
                        {
                            "date": local(window_start)[:10],
                            "start_jd": window_start,
                            "end_jd": u,
                            "start_cst": local(window_start),
                            "end_cst": local(u),
                            "duration_minutes": (u - window_start) * 1440,
                            "moon_alt_mid_deg": float(mh),
                            "sun_alt_mid_deg": float(sh),
                            "moon_az_mid_deg": float(az),
                            "sunset_cst": local(solar["-0.833"][0]),
                            "dusk_start_cst": local(s0),
                            "dusk_end_cst": local(s1),
                        }
                    )
        allrows[city] = rows
        daily[city] = days
    return allrows, daily


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-root", type=Path, required=True)
    p.add_argument("--candidate-id", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    root = a.case_root
    settings = json.loads((root / "data/processed/settings.json").read_text())
    cities = settings["cities"]
    sky = Sky(root, a.candidate_id == "TOPOCENTRIC")
    reference = []
    for city, c in cities.items():
        for body in ["sun", "moon"]:
            tab = table(root / "data/raw" / f"{city}_{body}_reference.txt")
            alts, az = sky.position(tab[:, 0], c, body)
            for t, refaz, refalt, h, z in zip(
                tab[:, 0], tab[:, 1], tab[:, 2], alts, az, strict=False
            ):
                reference.append(
                    {
                        "city": city,
                        "body": body,
                        "jd": float(t),
                        "reference_alt_deg": float(refalt),
                        "computed_alt_deg": float(h),
                        "alt_residual_deg": float(h - refalt),
                        "reference_az_deg": float(refaz),
                        "computed_az_deg": float(z),
                    }
                )
    residuals = np.array([r["alt_residual_deg"] for r in reference])
    rmse = float(np.sqrt(np.mean(residuals**2)))
    maxerr = float(np.max(np.abs(residuals)))
    ev, daily = events(sky, cities)
    sensitivity = {}
    pert = []
    for label, kw in [
        ("LOWER_TREE", {"moonlo": 3.0, "moonhi": 7.0}),
        ("HIGHER_TREE", {"moonlo": 13.0, "moonhi": 17.0}),
        ("WIDER_TREE_BAND", {"moonlo": 6.0, "moonhi": 14.0}),
        ("CIVIL_TWILIGHT", {"sunlo": -6.0, "sunhi": -0.833}),
        ("LATITUDE_PLUS_005", {"latitude_shift": 0.05}),
    ]:
        ee, _ = events(sky, cities, **kw)
        count = {c: len(v) for c, v in ee.items()}
        sensitivity[label] = {"parameters": kw, "city_event_counts": count, "events": ee}
        pert.append(
            {
                "perturbation_id": label,
                "metric": "scenario_event_count",
                "result": sum(count.values()),
                "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
            }
        )
    metrics = {
        "reference_altitude_rmse_deg": rmse,
        "reference_altitude_max_abs_deg": maxerr,
        "definition_tree_angle_deg": 10.0,
        "definition_calendar_rows": sum(len(v) for v in daily.values()),
        "scenario_event_count": sum(len(v) for v in ev.values()),
    }
    reqmetrics = {
        "REQ-DEFINITION": ["definition_tree_angle_deg", "definition_calendar_rows"],
        "REQ-VALIDATION": ["reference_altitude_rmse_deg", "reference_altitude_max_abs_deg"],
    }
    for c in cities:
        metrics[c + "_event_count"] = len(ev[c])
        reqmetrics["REQ-" + c.upper()] = [c + "_event_count"]
    limitations = [
        (
            "Dates are conditional on the explicit tree-angle and post-civi"
            "l-twilight definitions; these are not unique historical interp"
            "retations."
        ),
        (
            "JPL ephemerides are model-derived astronomical reference data,"
            " not local field observations; the reference check shares the "
            "JPL ephemeris family."
        ),
        (
            "Nominal city coordinates, zero ellipsoid height, airless lunar"
            " centre, flat unobstructed horizon, UTC approximately UT1; no "
            "weather, terrain, leaf season, or human encounter probability."
        ),
        (
            "The astronomical reconstruction is not a statistical predictio"
            "n accuracy or a verification of the poem historical event."
        ),
        (
            "Sunset uses conventional solar centre -0.833 deg; primary dusk"
            " and lunar altitude use airless centre geometry."
        ),
    ]
    claims = {}
    facts = {}
    asshash = hashlib.sha256(
        (root / "models/assumptions_and_symbols.json").read_bytes()
    ).hexdigest()
    for req, mids in reqmetrics.items():
        if req == "REQ-DEFINITION":
            text = (
                "At tree angle 10 degrees with band [8,12], the geometric model"
                " supplies 366 daily sunset/dusk/moon-rise calendars at each of"
                " seven nominal sites."
            )
        elif req == "REQ-VALIDATION":
            text = (
                f"Against 168 predeclared JPL topocentric positions, altitude "
                f"RMSE is {rmse:.9f} degrees and maximum absolute residual is "
                f"{maxerr:.9f} degrees; this is ephemeris consistency, not "
                f"independent field validation."
            )
        else:
            c = next(c for c in cities if req == "REQ-" + c.upper())
            text = (
                f"At the nominal {c} site in 2016 the defined "
                f"rising-Moon/post-civil-twilight scene has {len(ev[c])} "
                f"nonempty evening windows, listed with UTC+08 times."
            )
        claims[req] = {
            "claim_id": "CLAIM-2015-" + req[4:],
            "claim_text": text,
            "evidence_artifact_ids": [a.output.as_posix()],
        }
        scope = {
            "fields": mids,
            "time": ["2016"],
            "entities": list(cities) if req in ["REQ-DEFINITION", "REQ-VALIDATION"] else [c],
        }
        facts[req] = {
            "generation_method": "DEVELOPMENT_DIAGNOSTIC"
            if req == "REQ-VALIDATION"
            else "CONDITIONAL_SIMULATION",
            "source_ids": ["SRC-JPL-SUN-GEO", "SRC-JPL-MOON-GEO"]
            + (
                [
                    "SRC-JPL-" + x.upper() + "-" + b.upper() + "-REF"
                    for x in cities
                    for b in ["sun", "moon"]
                ]
                if req == "REQ-VALIDATION"
                else []
            ),
            "scope": scope,
            "conditional_scope": scope,
            "metric_values": {m: metrics[m] for m in mids},
            "assumption_artifact_sha256": asshash,
            "status": "COMPUTED",
        }
    out = {
        "candidate_id": a.candidate_id,
        "status": "SUCCESS",
        "validation_metrics": {"reference_altitude_rmse_deg": rmse},
        "final_metrics": metrics,
        "claim_scope": (
            "2016 seven nominal Chinese sites: explicit geometric scene, ai"
            "rless centre, conditional timing and ephemeris consistency onl"
            "y."
        ),
        "requirement_claims": claims,
        "scientific_evidence": facts,
        "events": ev,
        "daily_calendar": daily,
        "reference_comparison": reference,
        "sensitivity": sensitivity,
        "figure_ready_data": [
            {
                "figure_id": "city_event_counts",
                "series": [{"city": c, "count": len(v)} for c, v in ev.items()],
            },
            {"figure_id": "reference_residuals", "series": reference},
        ],
        "uncertainty": {
            "reference_max_abs_alt_deg": maxerr,
            "root_numeric_tolerance_seconds": 0.1,
            "definition_uncertainty": (
                "See five genuinely recomputed perturbations; geometric definit"
                "ions dominate numerical error."
            ),
        },
        "limitations": limitations,
        "robustness_evidence": {
            "metric": "scenario_event_count",
            "metric_direction": "MAX",
            "perturbations": pert,
            "failure_cases": [
                (
                    "Poorer geometry or alternative dusk/tree definitions can exclu"
                    "de individual dates; no clear-sky visibility guarantee."
                )
            ],
        },
    }
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"candidate": a.candidate_id, "metrics": metrics}))


if __name__ == "__main__":
    main()
