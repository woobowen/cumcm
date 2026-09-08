"""Case-local first-party orchestration. Shared frozen core remains authoritative."""

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SKILL = REPO / ".agents/skills/cumcm-modeling-evidence"
spec = importlib.util.spec_from_file_location("frozen_case_core", SKILL / "scripts/cumcm_case.py")
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
ROOT = REPO / ".cache/pr12-rc8/fresh/2015/case"
PUB = REPO / "evals/results/phase-004c5/CUMCM-2015-C-VALIDATION-005"
CODE = PUB / "code"
CITIES = {
    "Beijing": [116.4074, 39.9042, 0.0],
    "Harbin": [126.6424, 45.7567, 0.0],
    "Shanghai": [121.4737, 31.2304, 0.0],
    "Guangzhou": [113.2644, 23.1291, 0.0],
    "Kunming": [102.8329, 24.8801, 0.0],
    "Chengdu": [104.0665, 30.5728, 0.0],
    "Urumqi": [87.6168, 43.8256, 0.0],
}
IDS = ["REQ-DEFINITION", "REQ-VALIDATION"] + ["REQ-" + c.upper() for c in CITIES]


def put(k, v):
    core.write_json(ROOT / core.ARTIFACT_PATHS[k], core.artifact(k, v))


def cli(command, *args):
    argv = [
        str(REPO / ".venv/bin/python"),
        str(SKILL / "scripts/cumcm_case.py"),
        command,
        "--case-root",
        str(ROOT),
        *map(str, args),
    ]
    t = datetime.now(UTC).isoformat()
    r = subprocess.run(argv, cwd=REPO, capture_output=True, text=True)
    p = ROOT / "state/cli_journal.jsonl"
    p.open("a").write(
        json.dumps(
            {
                "at": t,
                "argv": [
                    ".venv/bin/python",
                    ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
                    command,
                    "--case-root",
                    "CASE_ROOT",
                    *map(str, args),
                ],
                "exit_code": r.returncode,
                "stdout": r.stdout,
                "stderr": r.stderr,
                "stdout_sha256": hashlib.sha256(r.stdout.encode()).hexdigest(),
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    print(r.stdout.strip(), flush=True)
    if r.returncode:
        raise RuntimeError(f"CLI_{command}_EXIT_{r.returncode}")
    return json.loads(r.stdout)


def advance(target):
    while core.load_state(ROOT)["state"] != target:
        cli("validate")


def prepare():
    for name in ["solve.py", "check.py", "controller.py"]:
        shutil.copyfile(CODE / name, ROOT / "models" / name)
    original = (
        REPO / ".cache/pr12-rc8/fresh/2015/official/c_files/CUMCM-2015-problem C-Chinese.docx"
    )
    shutil.copyfile(original, ROOT / "data/raw/problem.docx")
    settings = {
        "cities": CITIES,
        "coordinate_interpretation": (
            "Explicit nominal central-site scenarios, approximate city posi"
            "tions; no measured site claim; ellipsoid height set zero."
        ),
        "year": 2016,
        "time_zone": "UTC+08:00",
        "moon_band_deg": [8, 12],
        "sun_band_deg": [-12, -6],
        "rising_moon_required": True,
        "tree_geometry": {"eye_height_m": 1.7, "distance_m": 50.0, "tree_top_angle_deg": 10.0},
        "pressure_refraction": "AIRLESS",
        "root_tolerance_seconds": 0.1,
    }
    core.write_json(ROOT / "data/processed/settings.json", settings)
    texts = {
        "REQ-DEFINITION": (
            "Define the willow-top altitude and after-dusk interval, derive"
            " astronomical date/time model, and supply separate moon10 risi"
            "ng and sunset/dusk event calendars."
        ),
        "REQ-VALIDATION": (
            "Validate model numerical reasonableness against existing astro"
            "nomical position information, explicitly distinguishing epheme"
            "ris consistency from independent observed reality."
        ),
    }
    texts.update(
        {
            "REQ-" + c.upper(): (
                f"Determine whether the defined scene occurs at nominal {c} "
                f"during 2016 and give all date/time windows or an absence "
                f"reason."
            )
            for c in CITIES
        }
    )
    reqs = [
        {
            "requirement_id": i,
            "text": texts[i],
            "role": "PRIMARY",
            "required_evidence_classes": ["THEORETICAL"]
            if i == "REQ-VALIDATION"
            else ["THEORETICAL", "ASSUMPTION"],
            "allowed_evidence_classes": ["THEORETICAL", "ASSUMPTION"],
            "minimum_data_fields": ["jd_utc", "topocentric_altitude_deg"]
            if i == "REQ-VALIDATION"
            else [
                "jd_utc",
                "geocentric_apparent_ra_deg",
                "geocentric_apparent_dec_deg",
                "range_km",
                "site_lon_lat_deg",
            ],
            "required_time_scope": ["2016"],
            "required_entity_scope": ["Earth"],
            "external_data_allowed": True,
            "external_data_required": True,
            "simulation_substitution_allowed": False,
            "partial_completion_allowed": False,
            "dependency_requirements": [],
            "completion_rule": (
                "All requested dates/times under explicit simplifying definitio"
                "ns plus actual ephemeris consistency check; no claim of observ"
                "ed poem event."
            ),
            "scientific_facts_required": True,
        }
        for i in IDS
    ]
    put(
        "problem_requirements",
        {
            "contract_version": "requirement-evidence/v1",
            "case_id": "CUMCM-2015-C-VALIDATION-005",
            "requirements": reqs,
        },
    )
    advance("REQUIREMENTS_VALIDATED")
    recs = json.loads((ROOT / "research/retrieval_ledger.json").read_text())
    sources = []
    for r in recs:
        if "sha256" not in r:
            continue
        name = Path(r["file"]).name
        geo = name.endswith("_geocentric.txt")
        ref = name.endswith("_reference.txt")
        support = IDS if geo else ["REQ-VALIDATION"] if ref else []
        sid = (
            ("SRC-JPL-" + name.split("_")[0].upper() + "-GEO")
            if geo
            else (
                "SRC-JPL-" + name.split("_")[0].upper() + "-" + name.split("_")[1].upper() + "-REF"
            )
            if ref
            else "SRC-DOC-" + name.split(".")[0].upper().replace("_", "-")
        )
        fields = (
            ["jd_utc", "geocentric_apparent_ra_deg", "geocentric_apparent_dec_deg", "range_km"]
            if geo
            else ["jd_utc", "topocentric_altitude_deg", "topocentric_azimuth_deg"]
            if ref
            else ["method_definition"]
        )
        sources.append(
            {
                "source_id": sid,
                "supports_requirement_ids": support,
                "evidence_class": "THEORETICAL",
                "provenance": r["url"],
                "authority": "NASA/JPL Horizons"
                if geo or ref or "horizons" in name
                else "NOAA"
                if "noaa" in name
                else "US Naval Observatory",
                "retrieval_time": r["retrieved_at"],
                "license_or_usage_status": (
                    "Public official scientific information accessed without paid A"
                    "PI; raw retained locally only."
                ),
                "geographic_scope": ["Earth"],
                "time_scope": ["2016"],
                "entity_scope": (["Earth", name.split("_")[0]] if ref else ["Earth"]),
                "field_schema": fields,
                "hash": r["sha256"],
                "input_path": r["file"],
                "freshness": "CURRENT_FOR_RECONSTRUCTION_SCOPE",
                "limitations": [
                    "Computed dynamical ephemeris, not direct local empirical observation."
                ]
                if geo or ref
                else ["General definitions do not establish a unique interpretation of the poem."],
            }
        )
    sources.append(
        {
            "source_id": "SRC-SCENARIO",
            "supports_requirement_ids": [i for i in IDS if i != "REQ-VALIDATION"],
            "evidence_class": "ASSUMPTION",
            "provenance": "First-party explicitly declared nominal scene settings",
            "authority": "Case modeler; assumptions only",
            "retrieval_time": datetime.now(UTC).isoformat(),
            "license_or_usage_status": "FIRST_PARTY",
            "geographic_scope": ["Earth"],
            "time_scope": ["2016"],
            "entity_scope": ["Earth", *CITIES],
            "field_schema": ["site_lon_lat_deg", "tree_angle_deg"],
            "hash": core.file_hash(ROOT / "data/processed/settings.json"),
            "input_path": "data/processed/settings.json",
            "freshness": "FROZEN_SCENARIO",
            "limitations": ["Not surveyed trees or surveyed observing sites."],
        }
    )
    put(
        "source_ledger",
        {
            "contract_version": "requirement-evidence/v1",
            "sources": sources,
            "answer_access_status": "NOT_ACCESSED",
        },
    )
    put(
        "research_plan",
        {
            "mode": "REGISTERED_GENERAL_ASTRONOMY_SEARCH",
            "questions": [texts[i] for i in IDS],
            "external_search": True,
            "search_restrictions": (
                "Only official general astronomy documentation and raw JPL ephe"
                "merides; no problem title/year solution searches."
            ),
            "retrieval_ledger": "research/retrieval_ledger.json",
        },
    )
    advance("SOURCES_PLANNED")
    put(
        "assumptions_and_symbols",
        {
            "assumptions": [
                (
                    "Flat unobstructed local horizon, airless lunar centre; nominal"
                    " tree angle arctan((H_tree-H_eye)/D)=10 deg with visual band ["
                    "8,12] deg; tree direction can align with the rising moon."
                ),
                (
                    "After dusk is explicitly the interval solar centre altitude [-"
                    "12,-6] degrees while descending. Alternatives are recomputed, "
                    "not asserted equivalent."
                ),
                (
                    "Use seven declared approximate city central sites with zero el"
                    "lipsoid elevation and all civil times UTC+08; shift latitude b"
                    "y +0.05 degree in robustness."
                ),
                (
                    "Retrospective deterministic 2016 astronomy. JPL apparent equat"
                    "orial positions are given forcing; UTC approximates UT1; appro"
                    "ximate GAST introduces bounded checked numerical error."
                ),
                (
                    "No inference on weather, terrain, real willow presence, histor"
                    "ical date of the poem or probability of meeting."
                ),
            ],
            "symbols": {
                "t": "Julian day UTC, day",
                "alpha": "geocentric apparent right ascension, rad",
                "delta": "geocentric apparent declination, rad",
                "r": "geocentric apparent distance, km",
                "phi": "geodetic latitude, rad",
                "lambda": "east longitude, rad",
                "h": "airless apparent altitude, degree",
                "theta": "local apparent sidereal angle, rad",
            },
            "formulas": [
                (
                    "h_tree=atan((H_tree-H_eye)/D); nominal h_tree=10 degrees, acce"
                    "pted band 8<=h_moon<=12."
                ),
                (
                    "r_geo=r*(cos(delta)*cos(alpha),cos(delta)*sin(alpha),sin(delta"
                    ")); r_topo=r_geo-r_observer."
                ),
                (
                    "Local east/north/up rotation of r_topo gives h=atan2(up,sqrt(e"
                    "ast^2+north^2)), az=atan2(east,north)."
                ),
                (
                    "theta=15*(GMST+equation_of_equinoxes)+east_longitude; USNO GAS"
                    "T formula and WGS84 ellipsoid are used."
                ),
                (
                    "Scene interval = rising-Moon [8,12] altitude interval intersec"
                    "t descending-Sun [-12,-6] interval; all interval endpoints sol"
                    "ved numerically."
                ),
                "Reference RMSE=sqrt(sum((h_model-h_JPL_topocentric)^2)/168).",
            ],
        },
    )
    hashes = {
        p.relative_to(ROOT).as_posix(): core.file_hash(p)
        for p in sorted((ROOT / "data").rglob("*"))
        if p.is_file() and p.suffix not in []
    }
    # Audit raw and processed inputs only; no changing audit artifact in its own hash set.
    hashes = {k: v for k, v in hashes.items() if k.startswith(("data/raw/", "data/processed/"))}
    counts = {}
    for p in (ROOT / "data/raw").glob("*.txt"):
        s = p.read_text()
        assert "$$SOE" in s and "$$EOE" in s
        counts[p.name] = len(s.split("$$SOE")[1].split("$$EOE")[0].strip().splitlines())
    assert counts["sun_geocentric.txt"] == counts["moon_geocentric.txt"] == 8833
    assert (
        all(v == 12 for k, v in counts.items() if k.endswith("_reference.txt"))
        and len(counts) == 16
    )
    put(
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": hashes,
            "raw_data_hashes": {k: v for k, v in hashes.items() if "/raw/" in k},
            "leakage_findings": [],
            "acquisition_plans": [],
            "row_counts": counts,
            "units": "JD UTC; RA/DEC/altitude/azimuth in degrees; range km.",
            "quality": (
                "Full requested SOE/EOE tables present; exact header/row count "
                "checks; no missing numerical output expected. Source outputs a"
                "re computed ephemerides, not direct observations."
            ),
            "nominal_reference_rows": 168,
            "processing_lineage": {
                "data/processed/settings.json": "FIRST_PARTY_ASSUMPTION_NOT_EMPIRICAL"
            },
        },
    )
    put(
        "data_sufficiency",
        {
            "contract_version": "data-sufficiency/v1",
            "requirements": reqs,
            "sources": sources,
            "acquisition_plans": [],
            "aggregate_completion_claimed": False,
            "requirement_assessments": [
                {
                    "requirement_id": i,
                    "data_sufficiency_status": "SUFFICIENT",
                    "missing_fields": [],
                    "missing_entities": [],
                    "missing_time_scope": [],
                    "candidate_sources": [
                        s["source_id"] for s in sources if i in s["supports_requirement_ids"]
                    ],
                    "acquisition_cost": "FREE_PUBLIC_API",
                    "acquisition_time": "COMPLETED_BEFORE_MODEL_RUN",
                    "allowed_substitutions": [],
                    "forbidden_substitutions": [
                        "Treating model ephemerides as independently observed ground truth"
                    ],
                    "affected_downstream_stages": [],
                }
                for i in IDS
            ],
        },
    )
    advance("DATA_AUDITED")
    cli("data-sufficiency")
    put(
        "model_candidates",
        {
            "candidates": [
                {
                    "candidate_id": "GEOCENTRIC",
                    "baseline": True,
                    "mechanism": (
                        "Cubic apparent equatorial interpolation and spherical local al"
                        "titude with Earth-centre observer; ignores parallax."
                    ),
                    "applicability": "Simple baseline expected to show lunar parallax error.",
                },
                {
                    "candidate_id": "TOPOCENTRIC",
                    "baseline": False,
                    "mechanism": (
                        "Same orbital forcing with WGS84 surface observer translation b"
                        "efore local horizontal rotation."
                    ),
                    "applicability": (
                        "Nominal ground sites; small residual aberration/time approxima"
                        "tions checked against JPL."
                    ),
                },
            ]
        },
    )
    advance("MODELS_PROPOSED")
    probe = {
        "candidate_id": "CONTRACT-PROBE",
        "status": "CONTRACT_PROBE",
        "probe_only": True,
        "ranking_eligible": False,
        "result_values_are_placeholders": True,
        "final_metrics": {"reference_altitude_rmse_deg": 0.0},
        "claim_scope": "PLACEHOLDER",
        "requirement_claims": {
            i: {
                "claim_id": "CLAIM-PROBE-" + i[4:],
                "claim_text": "PLACEHOLDER NONRESULT",
                "evidence_artifact_ids": ["experiments/selected_output_contract_probe.json"],
            }
            for i in IDS
        },
        "figure_ready_data": [{"series": [0]}],
        "uncertainty": {"scope": "PLACEHOLDER"},
        "limitations": ["NONRESULT PLACEHOLDER"],
        "robustness_evidence": {
            "metric": "scenario_event_count",
            "metric_direction": "MAX",
            "perturbations": [
                {
                    "perturbation_id": "PLACEHOLDER",
                    "metric": "scenario_event_count",
                    "result": 0,
                    "evidence": "DETERMINISTIC_RECOMPUTATION_FROM_BOUND_INPUTS",
                }
            ],
            "failure_cases": ["NONRESULT"],
        },
    }
    core.write_json(ROOT / "experiments/selected_output_contract_probe.json", probe)
    cli("preflight-output", "--path", "experiments/selected_output_contract_probe.json")
    export("pre_run")


def freeze(commit):
    cf = [
        {
            "scope": "SKILL_ROOT",
            "path": "scripts/cumcm_case.py",
            "repository_path": ".agents/skills/cumcm-modeling-evidence/scripts/cumcm_case.py",
            "sha256": core.file_hash(SKILL / "scripts/cumcm_case.py"),
        }
    ]
    for n in ["solve.py", "check.py", "controller.py"]:
        cf.append(
            {
                "scope": "CASE_ROOT",
                "path": "models/" + n,
                "repository_path": "evals/results/phase-004c5/CUMCM-2015-C-VALIDATION-005/code/"
                + n,
                "sha256": core.file_hash(ROOT / "models" / n),
            }
        )
    p = {
        "preregistered": True,
        "execution_prepared": True,
        "candidate_ids": ["GEOCENTRIC", "TOPOCENTRIC"],
        "baseline_id": "GEOCENTRIC",
        "metric": "reference_altitude_rmse_deg",
        "metric_direction": "MIN",
        "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
        "selection_rule": "ARGMIN_THEN_ID",
        "random_seeds": [201509],
        "splits": {"train": [], "validation": [], "test": []},
        "required_input_hashes": core.read_artifact(ROOT, "data_audit")["content"]["data_hashes"],
        "required_code_files": cf,
        "code_commit": commit,
        "stop_rule": (
            "One attempt per two frozen candidates, one deterministic seed."
            " Maximum 2 model captures per revision; at most 3 case-only re"
            "pair revisions before Final with all failures retained outside"
            " fresh revision case. No shared-code edits. Final selected che"
            "cker once; no Final-driven tuning or post-terminal Run. Hard d"
            "eadline 2026-09-08T23:53:34Z; fixed package target 23:33:34Z."
        ),
        "handoff_generated_at": "2026-09-08T21:53:34Z",
        "evaluation_design": {
            "handoff_timestamp_semantics": (
                "handoff_generated_at is a frozen protocol label at the actual "
                "episode anchor; not actual final handoff creation time. See ha"
                "ndoff/actual_generation.json for actual_generated_at."
            ),
            "mode": "NONPREDICTIVE_FINAL_VERIFICATION",
            "scientific_final_method": (
                "Independent geocentric interpolation + equatorial parallax + c"
                "omplete event recomputation in frozen check.py."
            ),
            "prediction_test_access_count": 0,
            "reference_sampling": "Seven sites, monthly15 at11:30 UTC, Sun+Moon, 168 positions.",
            "acceptance_tolerances": {
                "reference_max_abs_deg": 0.05,
                "independent_angle_agreement_deg": 0.002,
                "event_endpoint_seconds": 2.0,
            },
            "perturbations": [
                "tree[3,7]",
                "tree[13,17]",
                "tree[6,14]",
                "sun[-6,-.833]",
                "latitude+0.05",
            ],
        },
    }
    h = core.canonical_hash
    p["trusted_freeze_registry"] = {
        "candidate_set": h(p["candidate_ids"]),
        "metric": h(
            {
                "name": p["metric"],
                "direction": p["metric_direction"],
                "aggregation_rule": p["aggregation_rule"],
                "selection_rule": p["selection_rule"],
            }
        ),
        "seed_schedule": h(p["random_seeds"]),
        "split_assignment": h(p["splits"]),
        "baseline": h(p["baseline_id"]),
        "input_set": h(p["required_input_hashes"]),
        "execution_policy": h(
            core.execution_policy_payload(
                p["stop_rule"], p["handoff_generated_at"], p["evaluation_design"]
            )
        ),
        "code_set": h(cf),
        "code_commit": h(commit),
    }
    put("experiment_plan", p)
    advance("EXPERIMENT_PLAN_VALIDATED")
    export("pre_run")


def export(folder):
    dest = PUB / folder / "case_bundle"
    dest.mkdir(parents=True, exist_ok=True)
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if str(rel).startswith(("data/raw/", "models/")) and p.suffix == ".py":
            continue
        if str(rel).startswith("data/raw/"):
            continue
        q = dest / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, q)
    core.write_json(
        PUB / folder / "bundle_manifest.json",
        {
            "files": {
                p.relative_to(dest).as_posix(): core.file_hash(p)
                for p in sorted(dest.rglob("*"))
                if p.is_file()
            },
            "raw_inputs": "Immutable ignored raw files listed by hash in data_audit.",
            "exported_at": datetime.now(UTC).isoformat(),
        },
    )


def execute(remote_freeze):
    assert isinstance(remote_freeze, str) and len(remote_freeze) == 40
    core.write_json(
        ROOT / "evidence/remote_execution_authorization.json",
        {
            "confirmed_remote_freeze": remote_freeze,
            "received_from": "MAIN_AGENT",
            "at": datetime.now(UTC).isoformat(),
        },
        overwrite=False,
    )
    advance("RUNNING")
    p = core.read_artifact(ROOT, "experiment_plan")["content"]
    for c in p["candidate_ids"]:
        cli(
            "execute",
            "--run-id",
            "RUN-2015-" + c,
            "--candidate-id",
            c,
            "--seed",
            201509,
            "--code-path",
            "models/solve.py",
            "--timeout-seconds",
            900,
        )
        # Development numerical checks are performed before a Final selection lock.
        cli(
            "verify-evidence",
            "--run-id",
            "RUN-2015-" + c,
            "--code-path",
            "models/check.py",
            "--timeout-seconds",
            900,
        )
    export("candidate_artifacts")


def select():
    p = core.read_artifact(ROOT, "experiment_plan")["content"]
    attempts = core._development_attempt_registry(ROOT, p)
    choice = core.select_development_candidate(attempts, p)
    dh = core.canonical_hash(choice)
    core.write_json(
        ROOT / "evidence/selected_configuration_lock.json",
        {
            "decision": choice,
            "decision_hash": dh,
            "selected_run_id": "RUN-2015-" + choice["selected_candidate_id"],
            "configuration_fixed_at": datetime.now(UTC).isoformat(),
            "final_started": False,
        },
        overwrite=False,
    )
    for row in attempts:
        cli("seal-run", "--run-id", row["run_id"], "--decision-hash", dh)
    export("candidate_artifacts")


def finish():
    lock = core.load_json(ROOT / "evidence/selected_configuration_lock.json")
    rid = lock["selected_run_id"]
    dh = lock["decision_hash"]
    p = core.read_artifact(ROOT, "experiment_plan")["content"]
    man = core.load_json(ROOT / "runs" / rid / "manifest.json")
    o = core.load_json(ROOT / "runs" / rid / "output.json")
    attempts = core._development_attempt_registry(ROOT, p)
    # Once-only nonpredictive Final authorization consumed before the actual replay.
    ledger = ROOT / "evidence/nonpredictive_final_verification.json"
    core.write_json(
        ledger,
        {
            "status": "STARTED",
            "scientific_final_verification_count": 1,
            "test_access_count": 0,
            "run_id": rid,
            "decision_hash": dh,
            "started_at": datetime.now(UTC).isoformat(),
        },
        overwrite=False,
    )
    checked = core.verify_scientific_check(ROOT, run_id=rid)
    for i, r in checked["requirements"].items():
        if not core.scientific_residuals_pass(r["recalculation_residuals"]):
            raise RuntimeError("FINAL_NUMERICAL_RECALCULATION_FAILED:" + i)
        if not r["feasible"] or not core.scientific_residuals_pass(r["constraint_residuals"]):
            raise RuntimeError("FINAL_DOMAIN_CHECK_FAILED:" + i)
    core.write_json(
        ledger,
        {
            **core.load_json(ledger),
            "status": "PASS",
            "completed_at": datetime.now(UTC).isoformat(),
            "output_sha256": core.file_hash(ROOT / "runs" / rid / "output.json"),
            "checker_capture_sha256": core.file_hash(
                ROOT / "runs" / rid / "scientific_check_capture.json"
            ),
        },
    )
    comparison = {
        k: p[k]
        for k in [
            "candidate_ids",
            "baseline_id",
            "metric",
            "metric_direction",
            "aggregation_rule",
            "selection_rule",
            "random_seeds",
            "splits",
            "required_input_hashes",
            "required_code_files",
            "code_commit",
            "stop_rule",
            "handoff_generated_at",
        ]
    }
    comparison.update(
        {
            "freeze_bindings": core.trusted_freezes(ROOT),
            "attempts": attempts,
            "selected_candidate_id": o["candidate_id"],
            "selection_decision_hash": dh,
            "leakage_checks": {
                "test_used_for_candidate_generation": False,
                "test_used_for_feature_selection": False,
                "test_used_for_threshold_selection": False,
                "future_information": False,
                "group_overlap": False,
                "target_in_features": False,
                "time_order_valid": True,
            },
            "test_access": {
                "mode": "NONPREDICTIVE_FINAL_VERIFICATION",
                "authorized": True,
                "count": 0,
                "scientific_verification_count": 1,
                "used_for_selection": False,
            },
            "reliability": {
                "attempts": len(attempts),
                "successful": sum(x["outcome"] == "SUCCESS" for x in attempts),
                "failed_or_infeasible": sum(x["outcome"] != "SUCCESS" for x in attempts),
            },
        }
    )
    put("model_comparison", comparison)
    output_ids = ["OUT-" + i for i in IDS]
    allmetrics = list(o["final_metrics"])
    runrec = {
        "run_id": rid,
        "outcome": "SUCCESS",
        "sealed": True,
        "current": True,
        "supported_requirement_ids": IDS,
        "selected_output_ids": output_ids,
        "metric_ids": allmetrics,
        "input_hash": man["input_hash"],
        "scenario_hash": man["scenario_hash"],
        "policy_exposure": 0,
    }
    selection = {
        "contract_version": "requirement-selection/v1",
        "requirements": [
            {
                "requirement_id": i,
                "selection_metric": next(iter(o["scientific_evidence"][i]["metric_values"])),
                "selection_direction": "MIN",
                "dependency_requirements": [],
                "cross_requirement_constraints": [],
            }
            for i in IDS
        ],
        "runs": [runrec],
        "selection": {
            "selection_mode": "GLOBAL_JOINT",
            "requirement_to_run_map": {i: [rid] for i in IDS},
            "requirement_to_output_map": {i: ["OUT-" + i] for i in IDS},
            "shared_input_hashes": [man["input_hash"]],
            "shared_scenario_hashes": [man["scenario_hash"]],
            "compatibility_checks": ["INPUT", "SCENARIO", "CONSTRAINTS"],
            "cross_requirement_constraints": [],
            "aggregate_objective": (
                "Minimum predeclared JPL reference altitude RMSE selects the co"
                "mmon coordinate model. Counts are requirement outputs, not obj"
                "ectives to maximize."
            ),
            "tradeoff_rule": "Global minimum RMSE then ID; preserve all definitions and cities.",
            "limitations": o["limitations"],
        },
    }
    put("requirement_selection", selection)
    cli("selection-check")
    cli("compare-check")
    rob = {
        "status": "VALIDATED",
        "selected_model": o["candidate_id"],
        "run_id": rid,
        "input_hash": man["input_hash"],
        "configuration_hash": man["configuration_hash"],
        "output_hash": man["output_hash"],
        "decision_hash": dh,
        **o["robustness_evidence"],
    }
    put("robustness_analysis", rob)
    advance("RUN_VALIDATED")
    advance("ROBUSTNESS_VALIDATED")
    claims = []
    outputs = []
    for i in IDS:
        facts = o["scientific_evidence"][i]
        record = o["requirement_claims"][i]
        mids = list(facts["metric_values"])
        ctype = "DESCRIPTIVE" if i == "REQ-VALIDATION" else "SIMULATION_CONDITIONAL"
        claims.append(
            {
                "claim_id": record["claim_id"],
                "requirement_id": i,
                "claim_type": ctype,
                "statement": record["claim_text"],
                "scope": facts["scope"],
                "evidence_class": "THEORETICAL",
                "selected_run_ids": [rid],
                "selected_output_ids": ["OUT-" + i],
                "metric_ids": mids,
                "comparator_ids": [],
                "support_predicates": {
                    "scope_bounded": True,
                    "registered_assumptions_bound": ctype == "SIMULATION_CONDITIONAL",
                },
                "uncertainty": o["uncertainty"],
                "counter_evidence": [],
                "limitations": o["limitations"],
                "claim_strength": "CONDITIONAL_TIMING"
                if ctype != "DESCRIPTIVE"
                else "BOUNDED_EPHEMERIS_CONSISTENCY",
                "status": "SUPPORTED",
            }
        )
        outputs.append(
            {"output_id": "OUT-" + i, "metric_ids": mids, "owner_run_id": rid, "requirement_id": i}
        )
    semantic = {
        "contract_version": "claim-evidence/v3",
        "claims": claims,
        "runs": [runrec],
        "outputs": outputs,
        "comparators": [],
        "validation": {"counter_evidence_detected": False},
        "aggregate": {
            "primary_requirement_ids": IDS,
            "supported_requirement_ids": IDS,
            "requirement_claim_ids": {i: o["requirement_claims"][i]["claim_id"] for i in IDS},
        },
    }
    put("semantic_claim_support", semantic)
    cli("semantic-check")
    final = core.build_runtime_final_result(selection, semantic, {rid: man})
    put("final_result", final)
    put("claim_evidence", core.build_runtime_claim_evidence(final, selection, semantic, {rid: man}))
    advance("EVIDENCE_VALIDATED")
    core.write_json(
        ROOT / "handoff/modeling_to_paper.json",
        core.build_runtime_handoff(ROOT, core.load_state(ROOT)),
    )
    core.write_json(
        ROOT / "handoff/actual_generation.json",
        {
            "actual_generated_at": datetime.now(UTC).isoformat(),
            "frozen_protocol_label_timestamp": p["handoff_generated_at"],
            "timestamp_semantics": (
                "Core generated_at is frozen protocol label only. This sidecar "
                "records actual handoff artifact creation."
            ),
            "handoff_sha256": core.file_hash(ROOT / "handoff/modeling_to_paper.json"),
        },
        overwrite=False,
    )
    cli("handoff", "--check")
    advance("READY_FOR_PAPER_HANDOFF")
    export("candidate_artifacts")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("mode", choices=["prepare", "freeze", "execute", "select", "finish", "export"])
    a.add_argument("--commit")
    a.add_argument("--remote-freeze")
    v = a.parse_args()
    if v.mode == "prepare":
        prepare()
    elif v.mode == "freeze":
        freeze(v.commit)
    elif v.mode == "execute":
        execute(v.remote_freeze)
    elif v.mode == "select":
        select()
    elif v.mode == "finish":
        finish()
    else:
        export("candidate_artifacts")
