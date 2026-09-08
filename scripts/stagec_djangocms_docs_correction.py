#!/usr/bin/env python3
"""Update DECISION_LOG / SYSTEM_STATE / TODO / README with the corrected
post-study closure truth (D056). Zero scientific calls."""

from __future__ import annotations
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

D056 = """

## Decision D056 - DJANGOCMS-EXTERNAL-VALIDITY-STUDY-01 REPORT CORRECTION: post-study evidence closure (D056)

- **Date:** 2026-09-08
- **Decision ID:** D056
- **Status:** ACCEPTED / COMPLETED (REPORTING / EVIDENCE / DOCUMENTATION closure ONLY; ZERO new scientific API calls; raw evidence immutable).
- **Category:** Reporting / Evidence / Documentation Correction
- **Description:** Corrected the post-study documentation for `scientific-stagec-djangocms-01` by recomputing every study fact from the 60 raw run records (`closure_recompute.json`) instead of trusting aggregates. Corrected failure accounting: **19** ImpactPlan completion truncations at the frozen 4096 cap (was wrongly written as 20 in the first STOP_REPORT; every truncation verified as `finish_reason=length`, `completion_tokens=4096`), 3 unknown/non-universe path rejections, 1 provider 429, 1 harness defect (ImpactPlan) + 4 provider 429, 1 empty-selection (Agent) = 29 failed / 31 valid (Agent 25/30, ImpactPlan 6/30). Added explicit VALID-vs-FAILED definitions; valid-run headline micro table with severe missing-data-asymmetry warning; ALL-CELL operational table (Agent 449,792 tok / 206 calls / 2265.517 s / $0.140850; ImpactPlan 184,401 tok / 28 calls / 2658.733 s / $0.123298; IP-vs-A tok -59.00%, calls -86.41%, cost -12.46%, time +17.36%); failure table with careful interpretation (truncation is NOT labeled bad reasoning); dedicated OUTPUT-BUDGET ASYMMETRY validity section (8x1024 sequential vs 1x4096 single-response; budgets not interchangeable; cap may confound representational scalability with completion-budget sufficiency); ZERO-API serialization-size analysis (minimal 144-path schema-valid plan = 17,364 bytes/chars; rough token estimate ~4,341 heuristic tokens, ESTIMATE ONLY; exact qwen3-coder tokenizer not locally available, not downloaded, no API call; all 19 truncated responses hit exactly 4096 completion tokens; successful ImpactPlan completions min 920 / median 2165 / max 3750); documented 8192-cap ablation proposal (`reports/DJANGOCMS_IMPACTPLAN_CAP_ABLATION_PROPOSAL.md`, POST-HOC, NOT RUN); conservative scientific interpretation (no universal-accuracy / universal-speed / end-to-end / large-repo generalization claims); baseline description (our implemented iterative repository-agent, not canonical); cost wording corrected ("Recorded API cost ... $0.264148; actual spend slightly higher due to one harness-defect call lacking cost provenance"); per-scenario tables use N/A for 0/5-valid arms.
- **Rationale:** Documentation conflicted with raw evidence on the truncation count (20 vs 19); the prior report also did not separate valid-run correctness from all-cell operational resources, did not document the output-budget asymmetry, and did not measure serialization size. RAW EVIDENCE WINS; corrected here with zero scientific calls.
- **Alternatives considered:** Trusting the prior aggregates - REJECTED (independently recomputed from raw records). Downloading the qwen3-coder tokenizer - REJECTED (no network/API in this closure; heuristic estimate labeled as such). Running the 8192 ablation - REJECTED (NOT part of primary study; ZERO new scientific calls authorized).
- **Impact:** Corrected FINAL_BENCHMARK_RESULTS.{md,csv}, BENCHMARK_VALIDITY_AND_LIMITATIONS.md, BENCHMARK_REPRODUCIBILITY_INDEX.md, STOP_REPORT.md, RESEARCH_TRUTH_MATRIX.md; new closure artifacts closure_recompute.json, serialization_size_analysis.json, raw_evidence_hashes.json; new ablation proposal doc; DECISION_LOG/SYSTEM_STATE/TODO/README updated. Raw evidence hashes verified unchanged (71 files). Six closure gates + audit PASS.
- **Evidence:** `reports/scientific-stagec-djangocms-study-01/closure_recompute.json`, `serialization_size_analysis.json`, `raw_evidence_hashes.json`, corrected reports listed above.
- **Next step:** STOP FOR GPT-5.6 SOL FINAL INDEPENDENT AUDIT. Do not run the 8192 ablation; do not merge main; do not create `v0.11.0-benchmark-complete`.
"""

CORRECTION_BLOCK = (
    "> **POST-STUDY CORRECTION CLOSURE (2026-09-08, D056 - REPORTING/EVIDENCE/DOCUMENTATION ONLY; "
    "ZERO NEW SCIENTIFIC API CALLS; RAW EVIDENCE UNCHANGED):** the djangoCMS study-01 documentation was "
    "corrected from raw evidence: ImpactPlan failures = **19** 4096-cap completion truncations "
    "(was wrongly 20; every one verified `finish_reason=length` / `completion_tokens=4096`) + 3 unknown-path "
    "+ 1 provider-429 + 1 harness defect; Agent failures = 4 provider-429 + 1 empty-selection; 29 failed / "
    "31 valid (Agent 25/30, ImpactPlan 6/30). Added valid-run vs ALL-CELL operational separation "
    "(Agent all-cell 449,792 tok/206 calls/2265.5 s/$0.140850; ImpactPlan all-cell 184,401 tok/28 calls/"
    "2658.7 s/$0.123298; IP-vs-A tok -59.0%, calls -86.4%, cost -12.5%, time +17.4%), explicit "
    "VALID-vs-FAILED definitions, output-budget asymmetry (8x1024 vs 1x4096; cap may confound "
    "representational scalability with completion-budget sufficiency), ZERO-API serialization-size "
    "measurement (minimal 144-path plan = 17,364 bytes; ~4,341 heuristic-estimate tokens; exact tokenizer "
    "not available/not downloaded), 8192-cap ablation proposal (POST-HOC, NOT RUN), conservative "
    "interpretation, and corrected cost wording (recorded $0.264148; one harness-defect call ~$0.003 "
    "lacks cost provenance; ceiling $0.50 -> COST_LOCK=PASS). Raw evidence hashes verified identical "
    "before/after (71 files, `raw_evidence_hashes.json`). Six closure gates + audit PASS."
)

# DECISION_LOG append
dl = PROJECT_DIR / "DECISION_LOG.md"
with dl.open("a", encoding="utf-8") as f:
    f.write(D056)
print(f"updated {dl}")

# SYSTEM_STATE / TODO / README prepend
for name in ("SYSTEM_STATE.md", "TODO.md", "README.md"):
    p = PROJECT_DIR / name
    text = p.read_text(encoding="utf-8")
    p.write_text(CORRECTION_BLOCK + "\n\n" + text, encoding="utf-8")
    print(f"updated {p}")

print("docs update complete")