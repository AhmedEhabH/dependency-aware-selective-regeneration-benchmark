#!/usr/bin/env python3
"""POST-ICCI — Independent audit of the closure outputs (ZERO API).

Cross-checks the POST-ICCI closure artifacts against the frozen evidence:

1. Two-way LocAgent recomputation JSON:
   - A (fail-closed all-10) micro == frozen shared_comparison.json LocAgent micro.
   - B (usable-5) micro is internally consistent with per-task rows and is
     explicitly labelled diagnostic/survivor-conditioned (NOT headline).
   - failure taxonomy counts == 2 timeout / 1 context-length / 2 completed-but-empty.
2. Four-action FN breakdown:
   - per-arm FN totals == frozen P1 micro FN (Full 70 / Sparse 82).
   - REGENERATE never appears (FN = missed gold, so actions are
     PRESERVE/VALIDATE/HUMAN_REVIEW only).
3. Submission record:
   - ZIP SHA-256 matches sidecar and committed blob.
   - blind/supervisor PDF hashes match the record.

ZERO API. Read-only over frozen evidence.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent

TWO_WAY = _PACKAGE_ROOT / "research" / "locagent-p5b" / "locagent_two_way.json"
SHARED = _PACKAGE_ROOT / "research" / "locagent-p5b" / "shared_comparison.json"
FN_BREAKDOWN = _PACKAGE_ROOT / "research" / "post-icci-zero-api-closure" / "four_action_fn_breakdown.json"
P1_METRICS = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "final_metrics.json"
SUBMISSION = _PACKAGE_ROOT / "paper" / "v20-final" / "ICCI_SUBMISSION_RECORD_2026-09-15.json"
ZIP = _PACKAGE_ROOT / "paper" / "v20-final" / "V20_FINAL_SUBMISSION.zip"
ZIP_SHA = _PACKAGE_ROOT / "paper" / "v20-final" / "V20_FINAL_SUBMISSION.zip.sha256"
BLIND_PDF = _PACKAGE_ROOT / "paper" / "v20-final" / "paper_v20_blind.pdf"
SUPER_PDF = _PACKAGE_ROOT / "paper" / "v20-final" / "paper_v20_supervisor.pdf"


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))
        if not ok:
            failures.append(f"{name}: {detail}")

    two = _load(TWO_WAY)
    shared = _load(SHARED)
    fnb = _load(FN_BREAKDOWN)
    p1 = _load(P1_METRICS)

    # 1. A headline matches frozen shared comparison.
    a = two["headline_A_fail_closed_all_10"]["micro_pooled"]
    frozen = shared["micro_pooled"]["LocAgent"]
    check("A_headline_matches_frozen", a == frozen, str(a))
    check("A_label_is_headline", "HEADLINE" in two["headline_A_fail_closed_all_10"]["label"])

    # 2. B diagnostic consistency + labelling.
    b = two["diagnostic_B_usable_5"]
    pt = two["per_task"]
    tps = sum(pt[c]["tp"] for c in b["usable_task_ids"])
    fps = sum(pt[c]["fp"] for c in b["usable_task_ids"])
    fns = sum(pt[c]["fn"] for c in b["usable_task_ids"])
    check("B_micro_internally_consistent",
          (tps, fps, fns) == (b["micro_pooled"]["tp"], b["micro_pooled"]["fp"], b["micro_pooled"]["fn"]),
          f"tp={tps} fp={fps} fn={fns}")
    check("B_label_is_diagnostic", "DIAGNOSTIC" in b["label"] and "survivor-conditioned" in b["label"])
    check("B_warning_present", "NOT the headline" in b["warning"])

    # 3. Failure taxonomy.
    ft = two["failure_taxonomy"]["counts"]
    check("taxonomy_2_timeout", ft["timeout"] == 2, str(ft["timeout"]))
    check("taxonomy_1_context", ft["context_length_badrequest"] == 1, str(ft["context_length_badrequest"]))
    check("taxonomy_2_completed_empty", ft["completed_but_empty"] == 2, str(ft["completed_but_empty"]))
    check("taxonomy_total_5", ft["total_empty"] == 5, str(ft["total_empty"]))

    # 4. FN breakdown totals match frozen P1 micro FN.
    for arm in ("full_v2", "sparse_v2"):
        agg = sum(fnb["aggregate"][arm].values())
        frozen_fn = p1["arms"][arm]["micro_overall"]["fn"]
        check(f"fn_breakdown_{arm}_matches_frozen", agg == frozen_fn, f"agg={agg} frozen={frozen_fn}")
        assert "REGENERATE" not in fnb["aggregate"][arm]
    check("fn_breakdown_all_decoded", fnb["decoded_cells"] == 60 and fnb["decode_failures"] == [])

    # 5. Submission record ZIP + PDF hashes.
    record = _load(SUBMISSION)
    zip_hash = _sha(ZIP)
    sidecar = ZIP_SHA.read_text(encoding="utf-8").strip().upper()
    check("zip_hash_matches_sidecar", zip_hash == sidecar, zip_hash[:16])
    check("zip_hash_matches_record", zip_hash == record["submission_artifact"]["zip_sha256"], zip_hash[:16])
    check("blind_pdf_hash_matches",
          _sha(BLIND_PDF) == record["submitted_files"]["blind_pdf"]["sha256"])
    check("supervisor_pdf_hash_matches",
          _sha(SUPER_PDF) == record["submitted_files"]["supervisor_pdf"]["sha256"])

    print("=== POST-ICCI INDEPENDENT AUDIT ===")
    for name, ok, detail in checks:
        extra = f"  [{detail[:100]}]" if detail else ""
        print(f"[{'PASS' if ok else 'FAIL'}] {name}{extra}")
    print(f"\nAUDIT: {'PASS' if not failures else 'FAIL'}")
    for f in failures:
        print(f"  - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
