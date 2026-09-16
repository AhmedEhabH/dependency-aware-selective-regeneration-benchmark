"""Run Omission-Risk Feature Study V1 (deterministic, ZERO LLM, dev evidence).

Usage:
    python scripts/run_omission_risk_feature_study.py
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.omission_risk import study

if __name__ == "__main__":
    summary = study.run_study()
    print("OMISSION_RISK_FEATURE_STUDY_V1 complete")
    print("tasks:", summary["n_tasks"])
    print("prevalence_by_k:", summary["prevalence_by_k"])
    print("adaptive_k_summary:", json.dumps(summary["adaptive_k_summary"], indent=1))
    out = Path("research/omission-risk-feature-study-v1")
    print("outputs:", sorted(p.name for p in out.iterdir()))
