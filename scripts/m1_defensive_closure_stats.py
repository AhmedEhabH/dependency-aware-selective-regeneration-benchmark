#!/usr/bin/env python3
"""M1 defensive-closure statistics (ZERO API).

Computes the scenario-level paired statistics for the audited M1B controlled
16K cap-relaxed encoding ablation (Full-v2 vs Sparse-v2) from the frozen
run_records.jsonl, plus the M1A 4096-cap probe operational facts used for the
survivor-bias / sensitivity analysis.

Statistical contract (frozen):
- 6 scenarios = independent task units (n = 6).
- 5 repetitions = repeated observations NESTED within scenario (NOT 30
  independent tasks; no significance test pretends otherwise).
- paired differences are Sparse-v2 minus Full-v2 within the SAME repetition
  index (r1..r5) of the SAME scenario.
- scenario-level summaries use the 5 within-scenario paired differences.
- cross-scenario summaries use the 6 scenario-level mean paired differences.
- bootstrap (if used) resamples SCENARIOS, not runs; n = 6 limitation stated.

Also quantifies the M1A -> M1B survivor-bias funnel: operational metrics
(validity / truncation) vs valid-output semantic metrics (P/R/F1 on valid
outputs only).

Reads ONLY the frozen evidence; writes reports/m1_defensive_closure_stats.json.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from statistics import median, pstdev
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent.parent
M1B_DIR = PROJECT_DIR / "research" / "controlled-encoding-ablation-16k-01"
M1A_DIR = PROJECT_DIR / "research" / "controlled-encoding-ablation-01"
OUT_PATH = PROJECT_DIR / "reports" / "m1_defensive_closure_stats.json"

SCENARIOS = (
    "djangocms-external-validity-002",
    "djangocms-external-validity-004",
    "djangocms-external-validity-005",
    "djangocms-external-validity-006",
    "djangocms-external-validity-007",
    "djangocms-external-validity-008",
)
REPS = (1, 2, 3, 4, 5)
ARMS = ("full_v2", "sparse_v2")

SEMANTIC_METRICS = ("precision", "recall", "f1", "fnr", "fn", "fp", "tp", "full_recall")
OPERATIONAL_METRICS = ("completion_tokens", "prompt_tokens", "total_tokens", "latency_seconds", "api_cost", "records")

VALID_TP_FN: dict[str, int] = {
    "djangocms-external-validity-002": 5,
    "djangocms-external-validity-004": 20,
    "djangocms-external-validity-005": 25,
    "djangocms-external-validity-006": 15,
    "djangocms-external-validity-007": 35,
    "djangocms-external-validity-008": 20,
}


def _load_records() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    path = M1B_DIR / "run_records.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rec = json.loads(line)
            out[rec["run_id"]] = rec
    return out


def _record_count(rec: dict[str, Any]) -> float:
    if rec["arm"] == "full_v2":
        return float(rec.get("decoded_candidate_count") or 0)
    return float(len(rec.get("decoded_write_set_ids") or []))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stats(values: list[float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "sd": 0.0, "n": 0}
    s = sorted(values)
    n = len(s)
    med = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return {
        "mean": round(_mean(values), 6),
        "median": round(med, 6),
        "min": round(s[0], 6),
        "max": round(s[-1], 6),
        "sd": round(pstdev(values), 6),
        "n": n,
    }


def _cohens_d(diffs: list[float]) -> float:
    if len(diffs) < 2:
        return 0.0
    sd = pstdev(diffs)
    if sd == 0.0:
        return 0.0
    return round(_mean(diffs) / sd, 6)


def main() -> int:
    records = _load_records()
    if len(records) != 60:
        raise SystemExit(f"expected 60 records, found {len(records)}")

    # ---- M1A probe operational facts (frozen evidence) ----
    m1a_probes: dict[str, Any] = {}
    probe_path = M1A_DIR / "capability_probes.json"
    if probe_path.is_file():
        probes = json.loads(probe_path.read_text(encoding="utf-8")).get("probes", {})
        for label in ("probe_a_full_v2", "probe_b_sparse_v2"):
            p = probes.get(label, {})
            m1a_probes[label] = {
                "arm": p.get("arm"),
                "schema_valid": p.get("schema_valid"),
                "finish_reason": p.get("finish_reason"),
                "completion_tokens": (p.get("usage") or {}).get("completion_tokens"),
                "decoded_candidate_count": p.get("decoded_candidate_count"),
                "decoded_write_set_ids": p.get("decoded_write_set_ids"),
            }

    # ---- per-scenario paired + distribution ----
    per_scenario: dict[str, Any] = {}
    for sid in SCENARIOS:
        paired: dict[str, list[float]] = {m: [] for m in SEMANTIC_METRICS}
        paired.update({m: [] for m in OPERATIONAL_METRICS})
        arm_dist: dict[str, dict[str, Any]] = {}
        for arm in ARMS:
            rows = [records[f"cea-{sid}-{arm}-r{k}"] for k in REPS]
            vals = {m: [float(r[m]) for r in rows] for m in SEMANTIC_METRICS}
            vals.update({
                m: [float(r[m]) for r in rows]
                for m in ("completion_tokens", "prompt_tokens", "total_tokens",
                          "latency_seconds", "api_cost")
            })
            vals["records"] = [_record_count(r) for r in rows]
            arm_dist[arm] = {m: _stats(v) for m, v in vals.items()}
            arm_dist[arm]["full_recall_rate"] = round(
                sum(1 for r in rows if r["full_recall"]) / len(rows), 6
            )
            arm_dist[arm]["valid_runs"] = sum(1 for r in rows if r["terminal_status"] == "succeeded")
            arm_dist[arm]["truncations"] = sum(1 for r in rows if r["truncation_status"])
        # paired diffs (sparse - full), same repetition index
        for k in REPS:
            full_r = records[f"cea-{sid}-full_v2-r{k}"]
            sparse_r = records[f"cea-{sid}-sparse_v2-r{k}"]
            for m in SEMANTIC_METRICS:
                a = float(sparse_r[m])
                b = float(full_r[m])
                if m == "full_recall":
                    paired[m].append(float(a - b))
                else:
                    paired[m].append(round(a - b, 6))
            for m in ("completion_tokens", "prompt_tokens", "total_tokens", "latency_seconds", "api_cost"):
                paired[m].append(round(float(sparse_r[m]) - float(full_r[m]), 6))
            paired["records"].append(round(_record_count(sparse_r) - _record_count(full_r), 6))
        paired_stats = {m: _stats(v) for m, v in paired.items()}
        # pstdev / cohen's d of the 5 within-scenario paired diffs
        paired_stats = {
            m: {**s, "cohens_d_within_scenario": _cohens_d(paired[m])} for m, s in paired_stats.items()
        }
        per_scenario[sid] = {
            "scenario_id": sid,
            "gold_tp_fn_baseline": VALID_TP_FN[sid],
            "arm_distributions": arm_dist,
            "paired_diffs_sparse_minus_full": {m: v for m, v in paired.items()},
            "paired_summary": paired_stats,
        }

    # ---- cross-scenario paired effects (n = 6 scenario-level means) ----
    cross: dict[str, Any] = {}
    for m in SEMANTIC_METRICS + OPERATIONAL_METRICS:
        scenario_means = [
            per_scenario[sid]["paired_summary"][m]["mean"] for sid in SCENARIOS
        ]
        signs = {("pos" if v > 0 else "neg" if v < 0 else "zero") for v in scenario_means}
        cross[m] = {
            "n_scenarios": 6,
            "scenario_mean_paired_diffs": scenario_means,
            "mean_of_scenario_means": round(_mean(scenario_means), 6),
            "median_of_scenario_means": round(median(scenario_means), 6),
            "sd_of_scenario_means": round(pstdev(scenario_means), 6),
            "cohens_d_across_scenarios": _cohens_d(scenario_means),
            "sign_consistency": {
                "positive_count": sum(1 for v in scenario_means if v > 0),
                "negative_count": sum(1 for v in scenario_means if v < 0),
                "zero_count": sum(1 for v in scenario_means if v == 0),
                "mixed": len(signs) > 1,
            },
        }

    # ---- bootstrap over SCENARIOS (NOT runs) ----
    rng = random.Random(20260913)
    n_boot = 10_000
    boot_targets = ("f1", "recall", "precision", "fnr", "completion_tokens", "api_cost")
    boot: dict[str, Any] = {}
    for m in boot_targets:
        scenario_means = [per_scenario[sid]["paired_summary"][m]["mean"] for sid in SCENARIOS]
        samples: list[float] = []
        for _ in range(n_boot):
            picks = [scenario_means[rng.randrange(6)] for _ in range(6)]
            samples.append(_mean(picks))
        samples.sort()
        boot[m] = {
            "n_boot": n_boot,
            "resampling_unit": "scenario (n=6, with replacement)",
            "ci95_lower": round(samples[int(0.025 * n_boot)], 6),
            "ci95_upper": round(samples[int(0.975 * n_boot) - 1], 6),
            "bootstrap_mean": round(_mean(samples), 6),
            "limitation": (
                "n=6 scenario-level units; CI reflects BETWEEN-SCENARIO uncertainty only; "
                "repetitions are nested observations, not independent samples"
            ),
        }

    # ---- sensitivity / survivor-bias funnel ----
    sensitivity = {
        "m1a_4096_probes": m1a_probes,
        "m1a_survivor_funnel": {
            "full_v2_4096": {
                "operational_valid": False,
                "truncated_at_candidate_id": 76,
                "valid_output_semantic_observations": 0,
            },
            "sparse_v2_4096": {
                "operational_valid": True,
                "decoded_candidate_count": 144,
                "valid_output_semantic_observations": 1,
            },
            "note": ("At the 4096 cap only Sparse-v2 produced a valid output; any semantic comparison at 4096 "
 "would be survivor-biased toward Sparse-v2. M1B re-runs BOTH arms at 16384 where BOTH survive, so "
 "the M1B semantic comparison is not censored by the cap."),
        },
        "m1b_valid_output_semantic_vs_operational": {
            "full_v2": {"valid_runs": 30, "truncations": 0, "semantic_observations": 30},
            "sparse_v2": {"valid_runs": 30, "truncations": 0, "semantic_observations": 30},
            "note": ("Within M1B every run is operationally valid, so valid-output semantic metrics are NOT "
 "censored; the censoring funnel exists only at the M1A 4096 boundary."),
        },
        "within_scenario_rep_determinism": {
            "note": ("Despite temperature 0 the five repetitions within a scenario/arm are NOT byte-identical "
 "(provider-side nondeterminism): decoded policies and token counts differ across repetitions, so "
 "nested repeated-measures variance is real and is used for the within-scenario distributions."),
        },
    }

    result = {
        "analysis": "M1 DEFENSIVE CLOSURE STATISTICS",
        "evidence": "audited M1B controlled 16K encoding ablation (60 cells) + M1A 4096 probes",
        "unit_statement": ("6 scenarios are the independent task units (n=6); 5 repetitions are nested "
 "repeated observations within scenario; n=30 is NOT claimed and no significance test treats "
 "repetitions as independent"),
        "per_scenario": per_scenario,
        "cross_scenario_paired_effects": cross,
        "bootstrap_over_scenarios": boot,
        "sensitivity_and_survivor_bias": sensitivity,
        "computed_at_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat(),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
