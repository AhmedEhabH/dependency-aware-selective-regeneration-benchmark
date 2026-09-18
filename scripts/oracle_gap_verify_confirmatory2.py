# ruff: noqa: E501
"""Section 1 — recompute the confirmatory (INTERNAL_TEST) error budget from raw records."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

RECORDS = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "run_records.jsonl"
METRICS = PROJECT_DIR / "research" / "djangocms-confirmatory-route-b" / "confirmatory_metrics.json"


def load() -> list[dict]:
    return [json.loads(line) for line in RECORDS.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    recs = load()
    sparse = [r for r in recs if r["arm"] == "sparse_v2" and r["terminal_status"] == "succeeded"]
    ver = [r for r in recs if r["arm"] == "verifier" and r["B"] == 5]

    # Sparse baseline: first succeeded per case
    fs = {}
    for r in sparse:
        if r["case_id"] not in fs:
            fs[r["case_id"]] = r
    print("sparse first-succeeded per case:", len(fs))

    tp = sum(r["tp"] for r in fs.values())
    fp = sum(r["fp"] for r in fs.values())
    fn = sum(r["fn"] for r in fs.values())
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    print(f"\nSPARSE BASELINE: TP={tp} FP={fp} FN={fn} P={p:.4f} R={r:.4f} F1={f1:.4f}")
    print("  mission diagnostic: TP=51 FP=104 FN=199 F1~0.252")

    # Verifier B=5: final set = Sparse write set + verifier_selected@B5
    vmap = {r["case_id"]: r for r in ver}
    final_tp = final_fp = final_fn = 0
    verifier_added_tp = 0
    verifier_added_fp = 0
    accepted_negatives = 0
    verifier_additions = 0
    # Aggregate via per-case tp/fp/fn deltas from verifier_recovered / verifier_selected.
    # final TP = sparse TP + verifier_recovered (files in proxy recovered by verifier at B5)
    # final FP = sparse FP + (verifier_selected minus proxy) - ... but verifier_selected files that were
    # already in sparse set? The verifier only adds candidates from top-B (omitted candidates).
    # final set = sparse_write_set ∪ verifier_selected@B5 (verifier_selected are omitted candidates accepted)
    for cid in fs:
        vrec = vmap.get(cid)
        if not vrec:
            continue
        added = set(vrec.get("verifier_selected") or [])
        recovered = set(vrec.get("verifier_recovered") or [])
        # proxy size = srec proxy_size; reconstruct positive set count via tp+fn
        # Use record counts: sparse tp/fp/fn per case are for sparse set only.
        added_tp = len(recovered)  # verifier_recovered are true positives added
        added_fp = len(added) - len(recovered)
        verifier_additions += len(added)
        verifier_added_tp += added_tp
        verifier_added_fp += added_fp
        accepted_negatives += added_fp

    # Final totals: final TP = sparse TP + added TP; final FP = sparse FP + added FP;
    # final FN = sparse FN - added TP (recovered positives no longer missed)
    final_tp = tp + verifier_added_tp
    final_fp = fp + verifier_added_fp
    final_fn = fn - verifier_added_tp
    p = final_tp / (final_tp + final_fp) if (final_tp + final_fp) else 0
    r = final_tp / (final_tp + final_fn) if (final_tp + final_fn) else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    print(f"\nFINAL VERIFIER B=5: TP={final_tp} FP={final_fp} FN={final_fn} P={p:.4f} R={r:.4f} F1={f1:.4f}")
    print("  frozen confirmatory: TP=71 FP=274 FN=179 F1=0.2387")
    print(f"\nverifier additions: {verifier_additions} (TP={verifier_added_tp}, FP={verifier_added_fp})")
    print(f"acceptance precision of B=5 verifier additions: {verifier_added_tp/(verifier_additions) if verifier_additions else 0:.4f}")

    # total hidden-proxy positives
    print("\ntotal hidden-proxy positives (tp+fn across sparse baseline):", tp + fn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
