"Write DRAFT design proposals and a placeholder-only contract probe; never run a model."

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pipeline import CANDIDATES, GLOBAL_SCOPE, REQUIREMENTS, SCOPES, contract_probe

ROOT = Path(__file__).resolve().parents[4]
CASE = ROOT / "evals/results/phase-004c2/CUMCM-2019-C-VALIDATION-002"
OFFICIAL_SHA256 = "e6c3bcbfdb92c633d49712fff7a2ef4bfc9dbaf540b1de4036b0e71503d962d0"


def canonical_hash(value):
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def write(relative, value):
    path = CASE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def proposal(relative, kind, content):
    write(
        relative,
        {
            "artifact_type": kind,
            "status": "DRAFT",
            "content_hash": canonical_hash(content),
            "content": content,
        },
    )


def main():
    scenario = {
        "schema_version": "airport-scenario-assumptions/v1",
        "source_type": "REGISTERED_ASSUMPTIONS_NOT_OBSERVATIONS",
        "empirical_data_available": False,
        "outer_seeds": [101, 202, 303],
        "sealed_test_evaluation_offset": 7000000,
        "q1": {
            "intensity_horizon_min": 720,
            "background_groups_per_min": 0.35,
            "assumed_flight_cohorts": [
                {"exit_center_min": 35, "half_width_min": 25, "taxi_groups": 60},
                {"exit_center_min": 95, "half_width_min": 30, "taxi_groups": 100},
                {"exit_center_min": 165, "half_width_min": 35, "taxi_groups": 80},
                {"exit_center_min": 235, "half_width_min": 30, "taxi_groups": 50},
            ],
            "decision_states": [
                {"id": f"STATE-T{minute}-Q{queue}", "minute": minute, "taxis_ahead": queue}
                for minute in [0, 60, 120, 180]
                for queue in [0, 20, 80, 160]
            ],
            "training_repeats": 256,
            "validation_repeats": 128,
            "static_averaging_window_min": 240,
            "city_net_cny_per_hour": 45.0,
            "cost_per_km_cny": 0.75,
            "fare_intercept_cny": 9.0,
            "fare_per_km_cny": 2.1,
            "speed_km_per_min": 0.5,
            "empty_return_km": 30.0,
            "boarding_min": 2.0,
            "distances_km": [8.0, 25.0, 50.0],
            "distance_probabilities": [0.3, 0.45, 0.25],
        },
        "q3": {
            "candidate_bays_per_lane": [1, 2, 3, 4, 5],
            "control_bays_per_lane": 3,
            "lane_length_m": 35.0,
            "bay_pitch_m": 7.0,
            "maximum_total_bays": 10,
            "boarding_mean_s": 35.0,
            "boarding_cv": 0.4,
            "admit_fixed_s": 6.0,
            "admit_headway_s": 2.5,
            "walk_fixed_s": 5.0,
            "walk_per_bay_s": 1.0,
            "clearance_s": 6.0,
            "exit_headway_s": 2.5,
            "training_batches": 128,
            "validation_batches": 192,
        },
        "q4": {
            "fleet_size": 80,
            "horizon_min": 480.0,
            "dispatch_interval_min": 1.5,
            "distances_km": [8.0, 25.0, 50.0],
            "distance_probabilities": [0.3, 0.45, 0.25],
            "fare_intercept_cny": 9.0,
            "fare_per_km_cny": 2.1,
            "cost_per_km_cny": 0.75,
            "speed_km_per_min": 0.5,
            "turnaround_min": 5.0,
            "short_trip_km": 12.0,
            "target_net_cny_per_hour": 45.0,
            "credit_cap_min": 20.0,
            "credit_expiry_min": 90.0,
            "priority_spacing_dispatches": 3,
            "ordinary_wait_cap_min": 60.0,
            "control_promotion_after_min": 15.0,
        },
        "robustness": {
            "q1": [
                {"id": "DEMAND_MINUS_30_PERCENT", "arguments": {"demand_scale": 0.7}},
                {"id": "DEMAND_PLUS_30_PERCENT", "arguments": {"demand_scale": 1.3}},
                {"id": "FLIGHT_EXIT_DELAY_30_MIN", "arguments": {"delay_min": 30}},
                {"id": "COST_PLUS_25_PERCENT", "arguments": {"cost_scale": 1.25}},
                {
                    "id": "COMBINED_LOW_DEMAND_DELAY_HIGH_COST",
                    "arguments": {"demand_scale": 0.7, "delay_min": 30, "cost_scale": 1.25},
                },
            ],
            "boarding_scales": [0.8, 1.3],
            "distance_scales": [0.8, 1.2],
        },
    }
    write("experiments/scenario_assumptions.json", scenario)
    scenario_hash = hashlib.sha256(
        (CASE / "experiments/scenario_assumptions.json").read_bytes()
    ).hexdigest()
    requirements = [
        {
            "requirement_id": "REQ-Q1",
            "role": "PRIMARY",
            "text": ("分析影响机理与乘客数量变化，结合司机收益建立候客/空返决策模型并给出策略。"),
            "depends_on": [],
            "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
            "source_locator": "题面第(1)问",
            "acceptance_tests": [
                "明确可观察航班与蓄车池队列、潜在出客人数与等待时间的关系",
                "统一CNY/min/km单位下比较A、B期望净收益",
                "给出可复算的条件策略、baseline/control对照及不确定性",
            ],
            "expected_output_paths": ["question_1.rows", "question_1.independent_check"],
            "supported_scope": SCOPES["REQ-Q1"],
        },
        {
            "requirement_id": "REQ-Q2",
            "role": "PRIMARY",
            "text": (
                "收集国内某机场及所在城市出租车实际数据，给出该机场司机"
                "选择方案并分析合理性与因素依赖性。"
            ),
            "depends_on": ["REQ-Q1"],
            "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
            "source_locator": "题面第(2)问",
            "acceptance_tests": [
                "真实命名机场和城市的数据来源、观测期、单位、许可与hash齐全",
                "参数由观测数据校准并用独立观测检查合理性",
                "给出该机场方案及定量敏感性",
            ],
            "expected_output_paths": [
                "question_2.status",
                "question_2.observations",
                "question_2.assumption_sensitivity",
            ],
            "known_gap": "VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING",
            "non_compensable": True,
            "supported_scope": SCOPES["REQ-Q2"],
        },
        {
            "requirement_id": "REQ-Q3",
            "role": "PRIMARY",
            "text": (
                "两条并行车道设置上车点，安排出租车与乘客，在保证安全条"
                "件下提高总乘车效率并说明最优性边界。"
            ),
            "depends_on": ["REQ-Q1"],
            "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
            "source_locator": "题面第(3)问",
            "acceptance_tests": [
                "给出几何、乘客通行与车辆移动互锁约束",
                "枚举有限上车点方案与baseline/control并评估groups/hour",
                "独立复算每个事件批次的容量与安全规则",
                "只声明预注册模型内经验最优，禁止现实全局最优",
            ],
            "expected_output_paths": [
                "question_3.events",
                "question_3.training_comparison",
                "question_3.independent_check",
            ],
            "supported_scope": SCOPES["REQ-Q3"],
        },
        {
            "requirement_id": "REQ-Q4",
            "role": "PRIMARY",
            "text": (
                "针对短途载客后返回的出租车提出优先安排，在不选客、不拒"
                "载、可多次往返条件下尽量均衡收益。"
            ),
            "depends_on": ["REQ-Q1", "REQ-Q3"],
            "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
            "source_locator": "题面第(4)问",
            "acceptance_tests": [
                "明确短途资格、额度、失效与使用一次规则及普通队列保护",
                "目的地按外生到客序列揭示，不允许选客拒载",
                "与FCFS/control比较Gini、底部分位数、吞吐和最大等待",
                ("独立复算车辆往返、收入与优先额度账本，记录未改善和有限时域偏差"),
            ],
            "expected_output_paths": [
                "question_4.ledger",
                "question_4.independent_check",
                "question_4.income_rate_gini",
            ],
            "supported_scope": SCOPES["REQ-Q4"],
        },
    ]
    proposal(
        "problem/proposed_problem_requirements.json",
        "problem_requirements",
        {
            "case_id": "CUMCM-2019-C-VALIDATION-002",
            "requirements": requirements,
            "input_inventory": [
                {
                    "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
                    "sha256": OFFICIAL_SHA256,
                    "role": "IMMUTABLE_OFFICIAL_PROBLEM",
                    "numeric_data_attachment_count": 0,
                }
            ],
            "primary_requirement_count": 4,
            "case_kind_proposal": "general",
            "ambiguities": [
                "题面没有特定机场、日期、航班/队列/费用观测或车道实测几何",
                ("乘车效率定义为完成上车的乘客组/小时，组作为一辆出租车服务单位"),
                ("收益均衡以完整往返现金流/司机实际暴露小时的分布衡量，另报绝对收入"),
            ],
            "non_compensable_gaps": ["VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING"],
            "global_scope": GLOBAL_SCOPE,
        },
    )
    proposal(
        "research/proposed_research_plan.json",
        "research_plan",
        {
            "mode": "OFFICIAL_INPUTS_ONLY_OFFLINE",
            "external_search": False,
            "questions": [
                "如何从可观察航班与排队车辆建立等待/收益比较",
                "如何在缺实测情况下限制推论范围",
                "如何使行人与车辆互锁可独立验证",
                "如何使短途补偿可核查且不挤占全部普通队列机会",
            ],
            "allowed_inputs": [
                "OFFICIAL_PROBLEM_PDF",
                "REGISTERED_SCENARIO_ASSUMPTIONS",
                "FROZEN_FORMAL_SKILL_INTERFACE",
            ],
            "prohibited_inputs": [
                "REFERENCE_ANSWERS",
                "OTHER_CASE_RESULTS",
                "AIRPORT_OBSERVATIONS_OUTSIDE_USER_ACCESS_BOUNDARY",
            ],
            "data_acquisition_gap": (
                "Q2 needs airport/city observations absent from authoriz"
                "ed official archive; no external acquisition authorized"
                "."
            ),
        },
    )
    proposal(
        "research/proposed_source_ledger.json",
        "source_ledger",
        {
            "sources": [
                {
                    "source_id": "SOURCE-OFFICIAL-2019-C-PDF",
                    "title": "2019 C 官方题面",
                    "source_type": "OFFICIAL_PROBLEM",
                    "sha256": OFFICIAL_SHA256,
                    "case_path": "data/raw/problem.pdf",
                    "supports": list(REQUIREMENTS),
                    "numeric_observations_provided": False,
                }
            ],
            "answer_access_status": "NOT_ACCESSED",
            "queries": [],
            "model_prior_status": "MODEL_PRIOR_EXPOSURE_UNVERIFIABLE",
            "assumption_origin": (
                "Fresh worker registered all scenario parameters before "
                "numerical execution; they are not external facts."
            ),
        },
    )
    assumptions = [
        {
            "assumption_id": "A1",
            "text": (
                "Passenger parties follow a piecewise-constant NHPP indu"
                "ced by assumed flight-exit pulses; taxis ahead depart o"
                "ne per party in FCFS order."
            ),
            "challenge": (
                "Correlated batches, abandonment and matching bottleneck"
                "s violate the waiting model."
            ),
            "requirements": ["REQ-Q1", "REQ-Q2"],
        },
        {
            "assumption_id": "A2",
            "text": (
                "Taxi destination mix is independent of queue waiting; c"
                "ity net opportunity cost is constant, A/B compared rela"
                "tive to future city earning."
            ),
            "challenge": "Congestion, shifts and risk aversion can alter the decision.",
            "requirements": ["REQ-Q1"],
        },
        {
            "assumption_id": "A3",
            "text": (
                "Q3 has two 35m lanes, 7m bay pitch, protected holding a"
                "nd fenced crossings; passenger access and all vehicle m"
                "otion are mutually exclusive."
            ),
            "challenge": (
                "These are assumed design conditions, not surveyed facts"
                "; real geometry or violations invalidate safety applica"
                "bility."
            ),
            "requirements": ["REQ-Q3"],
        },
        {
            "assumption_id": "A4",
            "text": (
                "Q3 saturated passenger and taxi queues give a capacity "
                "bound; batch boarding durations are independent lognorm"
                "al variables."
            ),
            "challenge": (
                "Insufficient demand/supply or correlated boarding changes achieved throughput."
            ),
            "requirements": ["REQ-Q3"],
        },
        {
            "assumption_id": "A5",
            "text": (
                "Q4 closed fleet returns empty, destinations exogenous, "
                "credits cannot be sold or split and expire after one re"
                "turn visit."
            ),
            "challenge": (
                "Outside drivers, fraud and refusal require operating co"
                "ntrols outside this simulation."
            ),
            "requirements": ["REQ-Q4"],
        },
        {
            "assumption_id": "A6",
            "text": (
                "Every numeric scenario value is an explicit modeling as"
                "sumption; no real airport/urban taxi observations are s"
                "upplied."
            ),
            "challenge": (
                "Actual calibration and external validation cannot be replaced by simulation."
            ),
            "requirements": ["REQ-Q2"],
        },
    ]
    formulas = [
        {
            "formula_id": "F1",
            "expression": (
                "lambda(t)=lambda0+sum_j G_j/w_j*max(0,1-|t-c_j|/w_j); L"
                "ambda(t)=integral_0^t lambda(s) ds"
            ),
            "requirement_ids": ["REQ-Q1", "REQ-Q2"],
            "description": (
                "Assumed party arrivals; G groups, t,c,w minutes, lambda groups/minute."
            ),
        },
        {
            "formula_id": "F2",
            "expression": (
                "Lambda(t+W)-Lambda(t)~Gamma(q+1,1); Delta=margin_loaded"
                "+cost_empty+r_city*(t_empty-t_loaded-W)"
            ),
            "requirement_ids": ["REQ-Q1"],
            "description": (
                "NHPP time-change order statistic, Δ CNY, r_city CNY/min; choose A if E[Delta]>=0."
            ),
        },
        {
            "formula_id": "F3",
            "expression": ("W_star=(E[margin_loaded]+cost_empty)/r_city+t_empty-E[t_loaded]"),
            "requirement_ids": ["REQ-Q1"],
            "description": (
                "A iff estimated E[W]<=W_star; ties choose A. Baseline s"
                "tatic intensity, main MC, control fluid inverse."
            ),
        },
        {
            "formula_id": "F4",
            "expression": (
                "observed_calibration_loss=(1/n)*sum_i (observed_wait_i-predicted_wait_i)^2"
            ),
            "requirement_ids": ["REQ-Q2"],
            "description": (
                "Required empirical validation target in min²; NOT COMP"
                "UTED because no observed values exist."
            ),
        },
        {
            "formula_id": "F5",
            "expression": (
                "capacity(n)=3600*sum_b(2*n)/sum_b(admit(n)+transfer(n)+"
                "max_k boarding_bk+clearance+release(n)); n*bay_pitch<=l"
                "ane_length"
            ),
            "requirement_ids": ["REQ-Q3"],
            "description": (
                "Groups/hour; empirical capacity maximized over frozen n"
                "=1..5, all movement phases exclude pedestrians."
            ),
        },
        {
            "formula_id": "F6",
            "expression": (
                "net_i=fare_intercept+(fare_per_km-2*cost_per_km)*d_i; c"
                "ycle_i=2*d_i/speed+turnaround; credit_i=min(cap,60*max("
                "0,target_rate*cycle_i/60-net_i)/target_rate)"
            ),
            "requirement_ids": ["REQ-Q4"],
            "description": (
                "Short-trip credit in minutes, one use, expiry; priority"
                " at most every third dispatch and suspended when oldest"
                " ordinary wait reaches aging trigger."
            ),
        },
        {
            "formula_id": "F7",
            "expression": (
                "income_rate_i=60*sum_trip net_trip/max(horizon,last_ret"
                "urn_i); Gini=sum_i(2*i-N-1)*sorted_rate_i/(N*sum_i rate"
                "_i)"
            ),
            "requirement_ids": ["REQ-Q4"],
            "description": (
                "Full round-trip tail accounting; fairness, throughput a"
                "nd delays reported separately without adjustable weight"
                "ing."
            ),
        },
    ]
    proposal(
        "models/proposed_assumptions_and_symbols.json",
        "assumptions_and_symbols",
        {
            "assumptions": assumptions,
            "symbols": {
                "t": "elapsed time [min]",
                "q": "taxis ahead [vehicles]",
                "lambda": "arriving passenger parties [groups/min]",
                "W": "waiting time [min]",
                "d": "distance [km]",
                "r_city": "outside net earning opportunity [CNY/min]",
                "Delta": "incremental net value A over B [CNY]",
                "n": "boarding bays per lane [count]",
                "capacity": "completed boarding [groups/hour]",
                "credit": "priority time discount [min]",
                "Gini": "income-rate inequality [dimensionless]",
            },
            "formulas": [
                {
                    "formula_id": formula["formula_id"],
                    "expression": formula["expression"],
                    "requirements": formula["requirement_ids"],
                }
                for formula in formulas
            ],
            "formula_explanations": {
                formula["formula_id"]: formula["description"] for formula in formulas
            },
            "scenario_configuration": "experiments/scenario_assumptions.json",
            "unit_checks": [
                "All Q1 opportunity costs multiply CNY/min by minutes",
                "Q3 seconds-to-hours factor 3600",
                "Q4 hourly income uses minute exposure times factor 60",
            ],
        },
    )
    proposal(
        "experiments/proposed_data_audit.json",
        "data_audit",
        {
            "raw_immutable": True,
            "data_hashes": {
                "data/raw/problem.pdf": OFFICIAL_SHA256,
                "experiments/scenario_assumptions.json": scenario_hash,
            },
            "raw_data_hashes": {"data/raw/problem.pdf": OFFICIAL_SHA256},
            "processed_data_hashes": {"experiments/scenario_assumptions.json": scenario_hash},
            "lineage": [
                {
                    "artifact": "experiments/scenario_assumptions.json",
                    "origin": "PROSPECTIVE_MODEL_ASSUMPTIONS",
                    "derived_from_observations": False,
                }
            ],
            "leakage_findings": [],
            "empirical_data_available": False,
            "data_dictionary": {
                "official_pdf": "Problem statements only; no numeric observations",
                "scenario_assumptions": (
                    "Declared simulation parameters with units in formalizat"
                    "ion; never imputed observations"
                ),
            },
            "missingness": {
                "airport_flights_and_exit_counts": "NOT_SUPPLIED",
                "taxi_queues_and_waits": "NOT_SUPPLIED",
                "city_fares_costs_trip_distances": "NOT_SUPPLIED",
                "lane_geometry_and_boarding_times": "NOT_SUPPLIED",
            },
            "non_compensable_primary_gaps": [
                {
                    "requirement_id": "REQ-Q2",
                    "reason_code": "VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING",
                    "status": "UNRESOLVED",
                }
            ],
            "calibration_status": "NOT_POSSIBLE_NO_OBSERVATIONS",
            "empirical_validation_status": "NOT_POSSIBLE_NO_OBSERVATIONS",
        },
    )
    portfolio = [
        {
            "candidate_id": CANDIDATES[0],
            "baseline": True,
            "mechanism": (
                "Static mean-intensity analytic wait; one bay per lane; "
                "ordinary FCFS recurrent fleet."
            ),
            "applicability": (
                "Transparent stationary reference; intentionally ignores flight-phase variation."
            ),
            "failure_expectation": (
                "Time-varying arrivals distort queue wait; safe minimum bays may underuse capacity."
            ),
        },
        {
            "candidate_id": CANDIDATES[1],
            "baseline": False,
            "mechanism": (
                "NHPP Gamma inverse Monte Carlo expected wait; finite ba"
                "y empirical-capacity maximization; deficit-sized short-"
                "trip credit with quota and aging."
            ),
            "applicability": (
                "Conditional assumed intensity, geometry and closed-fleet scenarios."
            ),
            "failure_expectation": (
                "Unobserved parameter error and demand correlation may d"
                "ominate MC accuracy; credit may not improve fairness."
            ),
        },
        {
            "candidate_id": CANDIDATES[2],
            "baseline": False,
            "mechanism": (
                "Deterministic cumulative-intensity fluid threshold; fix"
                "ed three bays per lane; fixed-delay short-trip aging pr"
                "omotion."
            ),
            "applicability": (
                "Structural control without stochastic wait estimation or deficit-sized credit."
            ),
            "failure_expectation": (
                "Inverse-of-mean differs from mean inverse; fixed credit"
                " promotion can trade fairness against waits."
            ),
        },
    ]
    proposal(
        "models/proposed_model_candidates.json",
        "model_candidates",
        {
            "candidates": portfolio,
            "independent_checker": "models/runtime/independent_checks.py",
            "baseline_id": CANDIDATES[0],
            "selection_scope": "Q1_CONDITIONAL_VALIDATION_ONLY",
            "cross_question_consistency": [
                "Common fare, operating cost and distance units",
                (
                    "Q1 marginal loaded-trip decision differs deliberately f"
                    "rom Q4 complete airport round-trip income"
                ),
                (
                    "Q3 is capacity under saturation; Q1 does not silently a"
                    "ssume unlimited actual boarding capacity"
                ),
                (
                    "Q4 dispatch capacity assumption is separate from Q3 max"
                    "imum; comparison must check it does not exceed selected"
                    " Q3 capacity"
                ),
            ],
        },
    )
    proposal(
        "experiments/proposed_experiment_plan.json",
        "experiment_plan",
        {
            "preregistered": False,
            "execution_prepared": False,
            "candidate_ids": list(CANDIDATES),
            "baseline_id": CANDIDATES[0],
            "metric": "opportunity_loss_cny",
            "metric_direction": "MIN",
            "aggregation_rule": "MEAN_PER_CANDIDATE_THEN_DIRECTION_THEN_ID",
            "selection_rule": "ARGMIN_THEN_ID",
            "random_seeds": scenario["outer_seeds"],
            "splits": {
                "train": ["REGISTERED_TRAIN_STREAMS"],
                "validation": ["REGISTERED_VALIDATION_STREAMS"],
                "test": ["RESERVED_TEST_SCENARIOS"],
            },
            "required_input_hashes": {
                "data/raw/problem.pdf": OFFICIAL_SHA256,
                "experiments/scenario_assumptions.json": scenario_hash,
            },
            "required_code_files": [],
            "code_commit": "MAIN_AGENT_FILL_AFTER_CODE_COMMIT",
            "trusted_freeze_registry": {},
            "stop_rule": (
                "ONE_SHOT_3_CANDIDATES_X_3_SEEDS_EACH_ONCE_NO_MODEL_RETR"
                "Y_900_SECONDS_PER_RUN_14400_SECONDS_TOTAL_KEEP_ALL_FAIL"
                "URES_NO_RETUNING"
            ),
            "handoff_generated_at": "MAIN_AGENT_FREEZE_UTC_BEFORE_RUN",
            "timebox_seconds": 14400,
            "per_run_timeout_seconds": 900,
            "retry_policy": (
                "No numerical/model retries. Only existing policy's boun"
                "ded pure-infrastructure retries, with all attempts pres"
                "erved and independently classified."
            ),
            "test_protocol": {
                "generation": (
                    "Each run computes independent test evaluation streams u"
                    "sing frozen training policy, encodes JSON in sealed_tes"
                    "t_metrics_b64, records sealed_test_payload_sha256."
                ),
                "selection": (
                    "Read only validation_metrics.opportunity_loss_cny; free"
                    "ze selected candidate and selection decision hash befor"
                    "e decoding any test payload."
                ),
                "access": (
                    "Decode exactly once selected candidate's lexicographica"
                    "lly minimum random_seed/run_id SUCCESS Run; verify payl"
                    "oad hash and record actual access receipt."
                ),
                "boundary": (
                    "Base64 prevents accidental reading only; no cryptograph"
                    "ic or OS isolation claim. Unselected test payloads rema"
                    "in undisclosed."
                ),
            },
            "numeric_robustness": scenario["robustness"],
            "selection_metric_interpretation": (
                "Mean realized oracle opportunity loss under frozen assu"
                "med scenarios; it compares Q1 policies, not empirical v"
                "alidity or joint Q1-Q4 optimality."
            ),
            "mandatory_uncompensated_check": (
                "VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING independently"
                " prevents all-primary PASS regardless of rankings."
            ),
            "freeze_fill_instructions": (
                "Main orchestrator accepts DRAFTs, binds copied raw/scen"
                "ario bytes and both case-local code files plus exact fr"
                "ozen core runner; obtains real code commit and computes"
                " trusted_freeze_registry using native canonical_hash fi"
                "elds. Never fill placeholders with invented hashes."
            ),
        },
    )
    write("experiments/selected_output_contract_probe.json", contract_probe())
    write(
        "experiments/proposed_output_contract.json",
        {
            "schema": "NATIVE_SELECTED_OUTPUT_CONTRACT_PLUS_CASE_EVIDENCE_V1",
            "result_generation": (
                "Only frozen execute produces SUCCESS output. This file has no numeric results."
            ),
            "primary_requirements": list(REQUIREMENTS),
            "global_scope": GLOBAL_SCOPE,
            "native_fields": [
                "candidate_id",
                "status",
                "final_metrics",
                "claim_scope",
                "requirement_claims",
                "figure_ready_data",
                "uncertainty",
                "limitations",
                "robustness_evidence",
            ],
            "case_fields": [
                "validation_metrics",
                "empirical_data_available",
                "empirical_requirement_satisfied",
                "primary_completion",
                "primary_requirement_status",
                "hard_evidence_gaps",
                "question_1",
                "question_2",
                "question_3",
                "question_4",
                "sealed_test_metrics_b64",
                "sealed_test_payload_sha256",
            ],
            "primary_status_rule": (
                "Q2=false and EMPIRICAL_EVIDENCE_INSUFFICIENT unless act"
                "ual authorized observations exist; no observation subst"
                "itution by simulations. Q1/Q3/Q4 completion is explicit"
                "ly conditional model-deliverable scope."
            ),
            "claim_evidence_rule": (
                "Each PRIMARY has a unique output-bound local Claim ID. "
                "Each local evidence list includes this Run's dynamic "
                "case-relative output path in addition to sources. "
                "The non-result probe references its own experiments path. "
                "Q2 local statement supports the data-gap finding, never"
                " a completed empirical solution. Aggregate scope retain"
                "s that gap."
            ),
            "final_metrics_scope": "VALIDATION_SCENARIO_SUMMARY_NOT_TEST_METRICS",
        },
    )
    write(
        "experiments/proposed_rubric_hard_failures.json",
        {
            "status": "PROPOSAL_ONLY_MAIN_RUBRIC_IS_AUTHORITATIVE",
            "non_compensable_primary_gap": "VALIDATION_PRIMARY_EMPIRICAL_DATA_MISSING",
            "hard_failures": [
                "RAW_INPUT_OR_SKILL_DRIFT",
                "ANSWER_CONTAMINATION",
                "NONFINITE_NUMERICS",
                "FAILED_BASELINE_OR_PRIMARY",
                "SAFETY_INTERLOCK_FAILURE",
                "GEOMETRIC_INFEASIBILITY",
                "INCOME_OR_RETURN_LEDGER_FAILURE",
                "PASSENGER_REFUSAL_OR_REORDERING",
                "PRIORITY_QUOTA_OR_AGING_FAILURE",
                "TEST_USED_FOR_SELECTION",
                "UNFROZEN_OR_RESULT_DRIVEN_RETRY",
                "TIMEBOX_EXCEEDED",
            ],
            "quantitative_checks": {
                "queue_inverse_residual_max": 1e-8,
                "accounting_residual_max": 1e-8,
                "all_lane_and_priority_violation_counts": 0,
                "robustness_perturbations_q1": 5,
                "robustness_perturbations_q3": 2,
                "robustness_perturbations_q4": 2,
                "independent_outer_repeats": 3,
            },
            "quality_reports_without_forced_threshold": [
                "Q1 opportunity loss and conditional uncertainty",
                "Q3 empirical batch capacity and enumerated geometry",
                (
                    "Q4 Gini, bottom decile income rate, throughput and max "
                    "waiting; retain adverse results"
                ),
            ],
            "terminal_rule": (
                "Evaluate every hard failure as well as Q2 insufficiency"
                "; never suppress model failures using the known empiric"
                "al gap."
            ),
        },
    )
    print(
        json.dumps(
            {
                "status": "DRAFT_PROPOSALS_WRITTEN",
                "model_executions": 0,
                "candidate_count": len(CANDIDATES),
                "primary_requirement_count": len(REQUIREMENTS),
            }
        )
    )


if __name__ == "__main__":
    main()
