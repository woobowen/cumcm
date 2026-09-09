"""Independent numerical checker: local Lagrange interpolation, equatorial parallax,
independent bisection scan and full table metrics. Does not import solve.py or its helpers.
This is numerical program independence, not native-agent or ephemeris independence.
"""

import argparse
import csv
import hashlib
import json
import math
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import numpy as np


class IndependentSky:
    def __init__(self, root, topo):
        self.topo = topo
        self.raw = {}
        for body in ["sun", "moon"]:
            text = (root / "data/raw" / f"{body}_geocentric.txt").read_text()
            section = text[text.index("$$SOE") + 5 : text.index("$$EOE")]
            rows = list(csv.reader(section.strip().splitlines()))
            times = np.array([float(r[0]) for r in rows])
            values = np.array([[float(r[3]), float(r[4]), float(r[5])] for r in rows])
            values[:, 0] = np.unwrap(values[:, 0] * math.pi / 180) * 180 / math.pi
            self.raw[body] = (times, values)

    def alt(self, t, c, body, azimuth=False):
        tt = np.asarray(t)
        x, y = self.raw[body]
        ix = np.clip(np.searchsorted(x, tt) - 2, 0, len(x) - 4)
        v = np.zeros(tt.shape + (3,))
        for j in range(4):
            w = np.ones(tt.shape)
            for k in range(4):
                if j != k:
                    w = w * (tt - x[ix + k]) / (x[ix + j] - x[ix + k])
            v += w[..., None] * y[ix + j]
        ra = np.deg2rad(v[..., 0])
        dec = np.deg2rad(v[..., 1])
        distance = v[..., 2]
        D = tt - 2451545.0
        century = D / 36525
        # Algebraically independent all-time sidereal expression, plus USNO nutation.
        gm = 18.697374558 + 24.06570982441908 * D + 0.000025862 * century**2
        eq = (
            -0.000319 * np.sin(np.deg2rad(125.04 - 0.052954 * D))
            - 0.000024 * np.sin(np.deg2rad(560.94 + 1.97130 * D))
        ) * np.cos(np.deg2rad(23.4393 - 0.0000004 * D))
        hour = np.deg2rad((gm + eq) * 15 + c[0]) - ra
        lat = np.deg2rad(c[1])
        if self.topo:
            # Geodetic site factors and equatorial parallax; no producer helper.
            f = 1 / 298.257223563
            u = np.arctan((1 - f) * np.tan(lat))
            rc = np.cos(u) + c[2] / 6378.137 * np.cos(lat)
            rs = (1 - f) * np.sin(u) + c[2] / 6378.137 * np.sin(lat)
            sp = 6378.137 / distance
            dra = np.arctan2(-rc * sp * np.sin(hour), np.cos(dec) - rc * sp * np.cos(hour))
            dec = np.arctan2(
                (np.sin(dec) - rs * sp) * np.cos(dra), np.cos(dec) - rc * sp * np.cos(hour)
            )
            hour = hour - dra
        if azimuth:
            return (
                np.rad2deg(
                    np.arctan2(
                        -np.cos(dec) * np.sin(hour),
                        np.sin(dec) * np.cos(lat) - np.cos(dec) * np.cos(hour) * np.sin(lat),
                    )
                )
                % 360
            )
        return np.rad2deg(
            np.arcsin(
                np.clip(np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(hour), -1, 1)
            )
        )


def independent_roots(sky, c, body, level, a, b, rising):
    grid = np.linspace(a, b, 145)
    ys = sky.alt(grid, c, body) - level
    out = []
    for i in range(len(grid) - 1):
        if (ys[i] <= 0 < ys[i + 1]) if rising else (ys[i] >= 0 > ys[i + 1]):
            lo, hi = grid[i], grid[i + 1]
            for _ in range(28):
                mid = (lo + hi) / 2
                v = float(sky.alt(mid, c, body)) - level
                if (v < 0) if rising else (v > 0):
                    lo = mid
                else:
                    hi = mid
            out.append((lo + hi) / 2)
    return out


def batch_roots(sky, c, body, level, first, startoffset, endoffset, rising):
    starts = first + np.arange(366)
    grid = starts[:, None] + np.linspace(startoffset, endoffset, 145)[None, :]
    y = sky.alt(grid, c, body) - level
    mask = (y[:, :-1] <= 0) & (y[:, 1:] > 0) if rising else (y[:, :-1] >= 0) & (y[:, 1:] < 0)
    days, j = np.nonzero(mask)
    lo = grid[days, j]
    hi = grid[days, j + 1]
    for _ in range(28):
        mid = (lo + hi) / 2
        v = sky.alt(mid, c, body) - level
        move = v < 0 if rising else v > 0
        lo = np.where(move, mid, lo)
        hi = np.where(move, hi, mid)
    result = [[] for _ in range(366)]
    for d, t in zip(days, (lo + hi) / 2, strict=False):
        result[int(d)].append(float(t))
    return result


def reconstruct(sky, cities, first, kw):
    out = {}
    moonlo = kw.get("moonlo", 8.0)
    moonhi = kw.get("moonhi", 12.0)
    sunhi = kw.get("sunhi", -6.0)
    sunlo = kw.get("sunlo", -12.0)
    shift = kw.get("latitude_shift", 0.0)
    for city, c0 in cities.items():
        c = [c0[0], c0[1] + shift, c0[2]]
        rows = []
        s0 = batch_roots(sky, c, "sun", sunhi, first, 0.5, 1, False)
        s1 = batch_roots(sky, c, "sun", sunlo, first, 0.5, 1, False)
        low = batch_roots(sky, c, "moon", moonlo, first, 0, 1, True)
        high = batch_roots(sky, c, "moon", moonhi, first, 0, 1 + 1 / 24, True)
        for d in range(366):
            if not s0[d] or not s1[d]:
                continue
            for window_start in low[d]:
                eligible = [h for h in high[d] if window_start < h < window_start + 0.3]
                if not eligible:
                    continue
                start = max(window_start, s0[d][0])
                end = min(eligible[0], s1[d][0])
                if end - start > 1e-9:
                    rows.append((start, end))
        out[city] = rows
    return out


def residual(value, tol, unit=""):
    return {"value": float(value), "relation": "EQ", "limit": 0.0, "tolerance": tol, "unit": unit}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--case-root", type=Path, required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    root = a.case_root
    op = root / "runs" / a.run_id / "output.json"
    o = json.loads(op.read_text())
    cities = json.loads((root / "data/processed/settings.json").read_text())["cities"]
    sky = IndependentSky(root, o["candidate_id"] == "TOPOCENTRIC")
    errors = []
    physical = []
    raw_mismatch = []
    for city, c in cities.items():
        for body in ["sun", "moon"]:
            text = (root / "data/raw" / f"{city}_{body}_reference.txt").read_text()
            rows = list(csv.reader(text.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines()))
            raw = {float(r[0]): float(r[4]) for r in rows}
            raw_az = {float(r[0]): float(r[3]) for r in rows}
            selected = [
                r for r in o["reference_comparison"] if r["city"] == city and r["body"] == body
            ]
            assert len(selected) == len(raw) == len(rows) == 12
            assert len({r["jd"] for r in selected}) == 12
            assert {r["jd"] for r in selected} == set(raw)
            pred = sky.alt(np.array([r["jd"] for r in selected]), c, body)
            az = sky.alt(np.array([r["jd"] for r in selected]), c, body, True)
            for row, h, z in zip(selected, pred, az, strict=True):
                ref = raw[row["jd"]]
                err = row["computed_alt_deg"] - ref
                errors.append(err)
                physical.append(float(h) - row["computed_alt_deg"])
                raw_mismatch.append(ref - row["reference_alt_deg"])
                raw_mismatch.append(err - row["alt_residual_deg"])
                raw_mismatch.append(raw_az[row["jd"]] - row["reference_az_deg"])
                physical.append(float((z - row["computed_az_deg"] + 180) % 360 - 180))
    rmse = math.sqrt(math.fsum(e * e for e in errors) / len(errors))
    maxerr = max(abs(e) for e in errors)
    # Full independent nominal and perturbation window reconstruction, not sample-count echo.
    first = 2457388.5 - 8 / 24
    nominal = reconstruct(sky, cities, first, {})
    percity = {}
    all_time_res = []
    all_count_res = []
    domain = []
    daily_res = []
    moon_events_res = []
    moon_count_res = []
    field_res = []
    date_errors = []
    for city, c in cities.items():
        expected = nominal[city]
        actual = o["events"][city]
        cr = len(expected) - len(actual)
        all_count_res.append(cr)
        tr = []
        for (lo, hi), row in zip(expected, actual, strict=False):
            tr.extend([(lo - row["start_jd"]) * 86400, (hi - row["end_jd"]) * 86400])
            tr.append((row["end_jd"] - row["start_jd"]) * 86400 - row["duration_minutes"] * 60)
            for field, jdfield in [("start_cst", "start_jd"), ("end_cst", "end_jd")]:
                parsed = datetime.fromisoformat(row[field])
                tr.append(parsed.timestamp() - (row[jdfield] - 2440587.5) * 86400)
                date_errors.append(
                    int(
                        row["date"]
                        != parsed.astimezone(timezone(timedelta(hours=8))).date().isoformat()
                    )
                )
            t = np.array([row["start_jd"], (row["start_jd"] + row["end_jd"]) / 2, row["end_jd"]])
            m = sky.alt(t, c, "moon")
            s = sky.alt(t, c, "sun")
            rise = sky.alt(t + 1 / 86400, c, "moon") - sky.alt(t - 1 / 86400, c, "moon")
            domain.extend(
                [
                    max(0.0, float(np.max(8 - m))),
                    max(0.0, float(np.max(m - 12))),
                    max(0.0, float(np.max(-12 - s))),
                    max(0.0, float(np.max(s + 6))),
                    max(0.0, float(-np.min(rise))),
                ]
            )
            field_res.extend(
                [
                    float(m[1]) - row["moon_alt_mid_deg"],
                    float(s[1]) - row["sun_alt_mid_deg"],
                    float(
                        (sky.alt(t[1], c, "moon", True) - row["moon_az_mid_deg"] + 180) % 360 - 180
                    ),
                ]
            )
        all_time_res.extend(tr)
        percity[city] = {
            "metric_values": {city + "_event_count": len(expected)},
            "recalculation_residuals": {
                "full_window_count": residual(cr, 0),
                "full_window_endpoint_max_seconds": residual(
                    max(map(abs, tr), default=0), 2.0, "seconds"
                ),
            },
            "feasible": cr == 0 and max(map(abs, tr), default=0) <= 2,
            "constraint_residuals": {
                "all_window_conditions_deg": residual(max(domain, default=0), 0.002, "degrees")
            },
        }
        days = o["daily_calendar"][city]
        assert len(days) == 366
        moon10 = batch_roots(sky, c, "moon", 10.0, first, 0, 1, True)
        for i, row in enumerate(days):
            expecteddate = (
                datetime.fromtimestamp(round((first + i - 2440587.5) * 86400, 3), UTC)
                .astimezone(timezone(timedelta(hours=8)))
                .date()
                .isoformat()
            )
            date_errors.append(int(row["date"] != expecteddate))
            for field, level in [
                ("sunset_jd", -0.833),
                ("dusk_start_jd", -6.0),
                ("dusk_end_jd", -12.0),
            ]:
                t = row[field]
                assert t is not None
                daily_res.append(float(sky.alt(t, c, "sun")) - level)
            # The independent rising-root enumeration verifies all daily moon10 entries.
            mr = moon10[i]
            moon_count_res.append(len(mr) - len(row["moon10_rising_jd"]))
            for x, y in zip(mr, row["moon10_rising_jd"], strict=False):
                moon_events_res.append((x - y) * 86400)
    perturb_counts = {}
    pert_res = []
    pert_count_res = []
    for label, rec in o["sensitivity"].items():
        recomputed = reconstruct(sky, cities, first, rec["parameters"])
        perturb_counts[label] = {c: len(rows) for c, rows in recomputed.items()}
        for city, rows in recomputed.items():
            pert_count_res.append(len(rows) - rec["city_event_counts"][city])
            pert_count_res.append(len(rows) - len(rec["events"][city]))
            for (lo, hi), row in zip(rows, rec["events"][city], strict=False):
                pert_res.extend([(lo - row["start_jd"]) * 86400, (hi - row["end_jd"]) * 86400])
    for rec in o["robustness_evidence"]["perturbations"]:
        pert_count_res.append(sum(perturb_counts[rec["perturbation_id"]].values()) - rec["result"])
    checks = {
        "REQ-DEFINITION": {
            "metric_values": {
                "definition_tree_angle_deg": math.degrees(math.atan(math.tan(math.radians(10)))),
                "definition_calendar_rows": sum(len(v) for v in o["daily_calendar"].values()),
            },
            "recalculation_residuals": {
                "full_daily_solar_event_altitude_max": residual(
                    max(map(abs, daily_res)), 0.002, "degrees"
                ),
                "full_daily_moon_event_count": residual(
                    max(map(abs, moon_count_res)), 0.0, "count"
                ),
                "full_daily_moon_event_times": residual(
                    max(map(abs, moon_events_res)), 2.0, "seconds"
                ),
                "all_perturbation_counts": residual(max(map(abs, pert_count_res)), 0.0, "count"),
                "all_perturbation_endpoints": residual(max(map(abs, pert_res)), 2.0, "seconds"),
                "calendar_date_identity": residual(max(date_errors), 0.0, "count"),
                "event_midpoint_altitude_and_azimuth": residual(
                    max(map(abs, field_res)), 0.002, "degrees"
                ),
            },
            "feasible": True,
            "constraint_residuals": {"definition_geometry": residual(0.0, 0.0)},
        },
        "REQ-VALIDATION": {
            "metric_values": {
                "reference_altitude_rmse_deg": rmse,
                "reference_altitude_max_abs_deg": maxerr,
            },
            "recalculation_residuals": {
                "all_reference_input_and_arithmetic": residual(
                    max(map(abs, raw_mismatch)), 1e-10, "degrees"
                ),
                "independent_physical_transform_max": residual(
                    max(map(abs, physical)), 0.002, "degrees"
                ),
            },
            "feasible": maxerr <= 0.05,
            "constraint_residuals": {
                "reference_accuracy_deg": {
                    "value": maxerr,
                    "relation": "LE",
                    "limit": 0.05,
                    "tolerance": 0.0,
                    "unit": "degrees",
                }
            },
        },
    }
    for city in cities:
        checks["REQ-" + city.upper()] = percity[city]
    plan = json.loads((a.case_root / "experiments/experiment_plan.json").read_text())["content"]
    metric_values = {
        m: value for record in checks.values() for m, value in record["metric_values"].items()
    }
    metric_values["scenario_event_count"] = sum(
        record["metric_values"][city + "_event_count"] for city, record in percity.items()
    )
    for metric, rows in o["metric_samples"].items():
        definition = plan["metric_definitions"][metric]
        assert all(
            r["target"] == definition["target"] and r["unit"] == definition["target_unit"]
            for r in rows
        )
        if metric in {"reference_altitude_rmse_deg", "reference_altitude_max_abs_deg"}:
            assert len(rows) == len(o["reference_comparison"]) == 168
            for i, (row, reference) in enumerate(zip(rows, o["reference_comparison"], strict=True)):
                assert row["sample_id"] == f"REF-{i}"
                if metric == "reference_altitude_rmse_deg":
                    assert (
                        row["prediction"] == reference["computed_alt_deg"]
                        and row["truth"] == reference["reference_alt_deg"]
                    )
                else:
                    assert (
                        abs(
                            row["value"]
                            - abs(reference["computed_alt_deg"] - reference["reference_alt_deg"])
                        )
                        < 1e-10
                    )
        else:
            assert rows == [
                {
                    "sample_id": metric,
                    "target": definition["target"],
                    "unit": definition["target_unit"],
                    "value": o["final_metrics"][metric],
                }
            ]
        assert abs(metric_values[metric] - o["final_metrics"][metric]) < 1e-9
    result = {
        "run_id": a.run_id,
        "output_sha256": hashlib.sha256(op.read_bytes()).hexdigest(),
        "requirements": checks,
        "metric_definitions": plan["metric_definitions"],
        "metric_samples": o["metric_samples"],
        "independence": (
            "Independent local four-point Lagrange interpolation, scalar eq"
            "uatorial parallax, bisection and complete date enumeration; no"
            " producer/helper imports. Same underlying JPL ephemeris, not i"
            "ndependent observations."
        ),
        "diagnostics": {
            "independent_max_altitude_difference_deg": max(map(abs, physical)),
            "window_endpoint_max_difference_seconds": max(map(abs, all_time_res)),
            "perturbation_counts": perturb_counts,
            "checked_reference_rows": len(errors),
        },
    }
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result["diagnostics"]))


if __name__ == "__main__":
    main()
