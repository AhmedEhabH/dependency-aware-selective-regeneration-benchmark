#!/usr/bin/env python3
"""WP-2 Env Closure V3.1 E2.10/E3.1 - derive historical DEV/TEST closure for
the 16 ENG tasks from TARGET-commit evidence (ZERO API, no task-ID branches).

Persists research/wp2/harness_v3_2026-09-26/env_closure_v31_dev_closures.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

OUT_ROOT = PROJECT / "research/wp2/harness_v3_2026-09-26"
CENSUS = json.loads((PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
SALEOR_CACHE = PROJECT / "dist/pilot-repo-cache/saleor"
INVENTORY = json.loads((PROJECT / "research/wp2/" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))

from benchmark.wp2.dep_compiler import (  # noqa: E402
    PYTHON_VERSION_BY_ERA,
    derive_dev_test_closure,
    vcr_family_present,
)

MANIFEST_NAMES = ("pyproject.toml", "poetry.lock", "uv.lock", "requirements.txt",
                  "requirements_dev.txt", "requirements-test.txt")


def git_show(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def task_commits(task_id: str) -> tuple[str, str]:
    for t in CENSUS.get("tasks", []):
        if t["task_id"] == task_id:
            return t["parent_commit"], t["target_commit"]
    raise KeyError(task_id)


def era_of(task_id: str) -> str:
    for r in INVENTORY["tasks"]:
        if r["task_id"] == task_id:
            return r["era_key"]
    return ""


def main() -> int:
    eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = sorted(eng["oracle_valid_union_task_ids"])

    out = {"artifact": "env_closure_v31_dev_closures",
           "note": "exact historical DEV/TEST supplement per task, derived by rule "
                   "from target-commit manifests",
           "per_task": {}}
    for tid in union:
        _, target = task_commits(tid)
        era = era_of(tid)
        manifests = {}
        for name in MANIFEST_NAMES:
            txt = git_show(target, name)
            if txt is not None and txt.strip():
                manifests[name] = txt
        closure = derive_dev_test_closure(manifests, python_version=PYTHON_VERSION_BY_ERA.get(era, "3.11"))
        closure["vcr_family_present"] = vcr_family_present(closure.get("pins", []))
        closure["era_key"] = era
        closure["python_version"] = PYTHON_VERSION_BY_ERA.get(era, "3.11")
        closure["manifest_sha256"] = {n: _sha256(manifests[n]) for n in manifests}
        out["per_task"][tid] = closure
        print(f"{tid:31s} {closure['mechanism']:12s} pins={len(closure.get('pins', []))} "
              f"unsupported={len(closure.get('unsupported', []))} "
              f"vcr={closure.get('vcr_family_present')}")

    dst = OUT_ROOT / "env_closure_v31_dev_closures.json"
    dst.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", dst)

    # E2.10 explicit legacy-format inspection
    for probe in ("saleor-rc-22ec4dab0154", "saleor-rc-dc6ac9d252df"):
        c = out["per_task"][probe]
        print(f"\n[{probe}] mechanism={c['mechanism']}")
        for rec in c.get("records", [])[:6]:
            print("   ", rec["name"], rec.get("version"), "dev=", rec["dev"],
                  "src=", rec["source"], "markers=", rec.get("markers"))
    return 0


def _sha256(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
