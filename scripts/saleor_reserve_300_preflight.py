#!/usr/bin/env python3
"""SALEOR_RESERVE_300_RMCSS - label-free eligibility preflight (§9).

Before reading target diff / historical proxy / changed-file labels / model
prediction results, build/preflight each sampled task using ONLY permitted
metadata:

  - case metadata record exists (sha, parent, status, eligibility header);
  - eligibility.eligible flag + reason_codes (label-free);
  - parent commit exists in the frozen Saleor git cache;
  - target commit exists in the frozen Saleor git cache;
  - name-status map non-empty (bundle constructible).

A sampled task may be excluded ONLY for a label-free infrastructure condition
(parent unavailable / intent unavailable / legal file universe unavailable /
repository state unavailable). NO replacement sampling. This script NEVER reads
proxy_paths / eligibility.proxy_paths / observed_change_set_proxy.

Output: research/saleor-reserve-300-rmcss/saleor_reserve_300_preflight.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))

SC_META = _PROJECT_DIR / "research" / "transparency" / "saleor_candidate_metadata.json"
SC_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
SAMPLE = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_sample.json"
OUT_DIR = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss"


def _git_has(cache: Path, rev: str) -> bool:
    if not rev:
        return False
    r = subprocess.run(["git", "-C", str(cache), "cat-file", "-e", f"{rev}^{{commit}}"],
                       capture_output=True, check=False)
    return r.returncode == 0


def main() -> int:
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    meta = json.loads(SC_META.read_text(encoding="utf-8"))
    selected = sample["selected_ids"]

    results = {}
    exclusions = []
    ok = 0
    for cid in selected:
        rec = meta.get(cid)
        reasons = []
        if rec is None:
            reasons.append("metadata_record_missing")
        else:
            elig = rec.get("eligibility") or {}
            if not elig.get("eligible"):
                reasons.append(f"eligibility_flag_false:{','.join(elig.get('reason_codes') or ['?'])}")
            if not rec.get("parent"):
                reasons.append("parent_commit_missing")
            elif not _git_has(SC_CACHE, rec["parent"]):
                reasons.append("parent_commit_unavailable_in_git")
            if not rec.get("sha"):
                reasons.append("target_commit_missing")
            elif not _git_has(SC_CACHE, rec["sha"]):
                reasons.append("target_commit_unavailable_in_git")
            status = rec.get("status") or {}
            if not status:
                reasons.append("name_status_empty")
        if reasons:
            exclusions.append({"case_id": cid, "reasons": reasons})
            results[cid] = {"pass": False, "reasons": reasons}
        else:
            ok += 1
            results[cid] = {"pass": True}

    out = {
        "sampled": len(selected),
        "preflighted_ok": ok,
        "excluded": len(exclusions),
        "exclusion_rule": "label-free infrastructure conditions only; no replacement sampling",
        "exclusions": exclusions,
        "per_case": results,
    }
    (OUT_DIR / "saleor_reserve_300_preflight.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"sampled={len(selected)} preflighted_ok={ok} excluded={len(exclusions)}")
    for e in exclusions:
        print("  EXCL", e)
    print(f"wrote {OUT_DIR / 'saleor_reserve_300_preflight.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
