#!/usr/bin/env python3
"""WP-2 Env Closure V3.1 E7 - mechanical rerun scope (ZERO API).

Compares OLD (f86007e4) vs CORRECTED normalized pip freeze + pytest plugin set
per task, and produces environment_rerun_scope.json with per-task affected
boolean + exact reason + C4/rediscovery/cap actions. No hardcoded task list.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
OLD = OUT_ROOT / "env_closure_v31_old_env"
CORRECTED = OUT_ROOT / "env_closure_v31_corrected_env"
FINGERPRINTS = json.loads((OUT_ROOT / "env_closure_v31_environment_fingerprints.json").read_text(encoding="utf-8"))
AUDIT = json.loads((OUT_ROOT / "dev_deps_gap_audit.json").read_text(encoding="utf-8"))


def normalize_freeze(freeze_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in freeze_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, rest = line.partition("==")
        if rest:
            out[name.strip().lower()] = rest.split(";")[0].strip()
        else:
            name = line.split(" @ ")[0].strip().lower()
            out[name] = "editable"
    return out


def plugins_from_trace(trace_text: str) -> set[str]:
    mods = set()
    for ln in trace_text.splitlines():
        m = re.search(r"PLUGIN registered: <module '([^']+)'", ln)
        if m:
            mods.add(m.group(1))
    return mods


def diff_sets(old: dict[str, str], new: dict[str, str]) -> dict:
    old_keys, new_keys = set(old), set(new)
    return {
        "added": sorted(new_keys - old_keys),
        "removed": sorted(old_keys - new_keys),
        "changed": sorted(k for k in old_keys & new_keys if old[k] != new[k]),
    }


def main() -> int:
    eng = json.loads((OUT_ROOT / "eng_v3_oracle_ready.json").read_text(encoding="utf-8"))
    union = sorted(eng["oracle_valid_union_task_ids"])
    violations = set(AUDIT["harness_v3_dep_policy_compliance"].get("violations", {}))

    per_task = {}
    for tid in union:
        old = json.loads((OLD / tid / "record.json").read_text(encoding="utf-8"))
        corr = json.loads((CORRECTED / tid / "record.json").read_text(encoding="utf-8"))
        old_freeze = normalize_freeze((OLD / tid / "freeze.txt").read_text(encoding="utf-8"))
        new_freeze = normalize_freeze((CORRECTED / tid / "freeze.txt").read_text(encoding="utf-8"))
        old_plugins = plugins_from_trace((OLD / tid / "traceconfig.txt").read_text(encoding="utf-8"))
        new_plugins = plugins_from_trace((CORRECTED / tid / "traceconfig.txt").read_text(encoding="utf-8"))

        reasons: list[str] = []
        if old["old_env_repro_status"] != "OK":
            reasons.append("OLD_ENV_UNREPRODUCIBLE")
        pkg_diff = diff_sets(old_freeze, new_freeze)
        if pkg_diff["added"] or pkg_diff["removed"] or pkg_diff["changed"]:
            reasons.append("PACKAGE_SET_DIFF")
        plug_diff = diff_sets({p: "" for p in old_plugins},
                              {p: "" for p in new_plugins})
        if plug_diff["added"] or plug_diff["removed"] or plug_diff["changed"]:
            reasons.append("PLUGIN_SET_DIFF")
        if tid in violations:
            reasons.append("CORRECTED_ENV_FIXES_DECLARED_MISSING_DEPS")
        affected = bool(reasons)
        if not affected:
            reasons.append("EQUIVALENT_POSITIVELY_DEMONSTRATED")

        redis_path = OUT_ROOT / f"p2pu_v3_rediscovery_{tid}.json"
        if not redis_path.exists():
            redis_path = OUT_ROOT / "superseded_env_v31" / "rediscovery" / f"p2pu_v3_rediscovery_{tid}.json"
        redis = json.loads(redis_path.read_text(encoding="utf-8"))
        n_cap200 = len(redis.get("v3_selection", {}).get("cap200_node_ids", []))
        n_cap400 = len(redis.get("v3_selection", {}).get("cap400_node_ids", []))

        per_task[tid] = {
            "old_freeze_sha256": old["freeze_sha256"],
            "new_freeze_sha256": corr["freeze_sha256"],
            "old_freeze_packages": len(old_freeze),
            "new_freeze_packages": len(new_freeze),
            "package_diff": {k: v[:100] for k, v in pkg_diff.items()},
            "plugin_diff": {k: v for k, v in plug_diff.items()},
            "old_env_fingerprint": FINGERPRINTS["per_task"][tid]["execution_environment_fingerprint"],
            "new_env_fingerprint": FINGERPRINTS["per_task"][tid]["execution_environment_fingerprint"],
            "affected": affected,
            "reason": "; ".join(reasons),
            "C4_action": "RERUN" if affected else "KEEP",
            "rediscovery_action": "RERUN" if affected else "KEEP",
            "cap200_action": ("RERUN" if affected and n_cap200 > 0 else
                              ("UNDEFINED_KEEP" if n_cap200 == 0 else "KEEP")),
            "cap400_action": ("RERUN" if affected and n_cap400 > 0 else
                              ("UNDEFINED_KEEP" if n_cap400 == 0 else "KEEP")),
            "n_cap200": n_cap200,
            "n_cap400": n_cap400,
        }
        print(f"{tid} affected={affected} ({reasons[0]}) pkg_delta="
              f"{len(pkg_diff['added'])}/{len(pkg_diff['removed'])}/{len(pkg_diff['changed'])}")

    affected_tasks = sorted(t for t, r in per_task.items() if r["affected"])
    n_p2pu_rerun = sum(0 if per_task[t]["n_cap200"] == 0 else 2 for t in affected_tasks)
    out = {
        "artifact": "environment_rerun_scope",
        "note": "affected = any of OLD_ENV_UNREPRODUCIBLE / PACKAGE_SET_DIFF / "
                "PLUGIN_SET_DIFF / CORRECTED_ENV_FIXES_DECLARED_MISSING_DEPS; "
                "unaffected only when equivalence positively demonstrated.",
        "affected_tasks": affected_tasks,
        "unaffected_tasks": sorted(t for t in per_task if not per_task[t]["affected"]),
        "n_c4_rerun_tasks": len(affected_tasks),
        "n_p2pu_rerun_units": n_p2pu_rerun,
        "per_task": per_task,
    }
    (OUT_ROOT / "environment_rerun_scope.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"wrote environment_rerun_scope.json: affected={len(affected_tasks)} "
          f"c4_rerun={len(affected_tasks)} p2pu_units={n_p2pu_rerun}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
