#!/usr/bin/env python3
"""WP2 M16 amendment R2A (brain-authored): R2 adapter-verifier historical-schema rule. ZERO model API.

Trigger (2026-10-02): the first resource dry-run (plan WP2_M16_V1_DRYRUN) stopped at R02_ADAPTER_VERIFY
before any Docker work with `KeyError: 'dev_test_closure'`. The R2 verifier of the M16 kit
(tag wp2-m16-v1-kit-2026-10-02) assumed that every record of the frozen ENG Phase-5 file
research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl (Harness V3, 2026-09-26) carries
`manifest.dev_test_closure`, a field of the later V3.1 historical dev/test closure (2026-09-27).

Rule M16_R2A_ENG_IDENTITY_HIST_SCHEMA_V1 (applied by scripts/wp2_m16_run.py::adapter_verify):
 1. REQUIRED for EVERY historical ENG record (no status is exempt):
      frozen closure == adapted closure (canonical sha)   <- the reviewer-approved R2 ENG identity test
      frozen lookup  == adapted lookup (parent, target, era)
      install mode of the target manifests == recorded manifest.install_mode
      lock signature of the target manifests == recorded manifest.lockfile_sha256
 2. ADDITIONAL provenance only where the historical record itself carries manifest.dev_test_closure:
      every recorded brief key (mechanism, n_pins, pins_sha256, n_unsupported) equals the adapted closure.
    A record without the field is NOT_RECORDED. Nothing is backfilled, inferred, or written to history.
 3. Fail-closed schema: an unparsable line, a non-object line, a missing task_id, a missing target_commit /
    manifest / manifest.install_mode / manifest.lockfile_sha256, a recorded closure that is neither absent,
    null nor a dict carrying 'mechanism', or an empty file is a violation (STOP 35, report written first).
 4. The per-record schema, the per-status coverage and the duplicates are reported (historical_schema).
The MAIN checks (all 220 rows, lookup/era, commits, declared dev group -> mechanism != none) are unchanged.
This module is pure: no I/O, no frozen imports, no network.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Callable

RULE_ID = "M16_R2A_ENG_IDENTITY_HIST_SCHEMA_V1"
TAG = "wp2-m16-v1-r2a-2026-10-02"
HIST_REL = "research/wp2/harness_v3_2026-09-26/phase5_c4_v3_per_task.jsonl"
BRIEF_KEYS = ("mechanism", "n_pins", "pins_sha256", "n_unsupported")
REQUIRED_TOP = ("task_id", "target_commit", "manifest")
REQUIRED_MANIFEST = ("install_mode", "lockfile_sha256")
RECORDED, ABSENT, NULL, UNKNOWN = "RECORDED", "NOT_RECORDED_ABSENT", "NOT_RECORDED_NULL", "UNKNOWN_SCHEMA"


def rule_constants_sha() -> str:
    c = {"rule_id": RULE_ID, "tag": TAG, "hist": HIST_REL, "brief_keys": list(BRIEF_KEYS),
         "required_top": list(REQUIRED_TOP), "required_manifest": list(REQUIRED_MANIFEST)}
    return hashlib.sha256(json.dumps(c, sort_keys=True).encode("utf-8")).hexdigest()


def closure_state(rec: dict) -> tuple[str, Any]:
    """Classify the historical manifest.dev_test_closure of one record (never modifies it)."""
    m = rec.get("manifest")
    if not isinstance(m, dict) or "dev_test_closure" not in m:
        return ABSENT, None
    c = m["dev_test_closure"]
    if c is None:
        return NULL, None
    if isinstance(c, dict) and "mechanism" in c:
        return RECORDED, c
    return UNKNOWN, c


def status_of(rec: dict) -> str:
    s = rec.get("status")
    return s if isinstance(s, str) and s else "<no status>"


def _signature(rec: dict) -> dict:
    m = rec.get("manifest")
    state, c = closure_state(rec)
    return {"status": status_of(rec), "top_keys": sorted(rec), "closure": state,
            "manifest_keys": sorted(m) if isinstance(m, dict) else None,
            "closure_keys": sorted(c) if isinstance(c, dict) else None}


def parse_history(text: str) -> tuple[dict[str, dict], dict]:
    """Parse the frozen JSONL exactly as the kit did (last record of a task wins) and census its schema.
    Returns (records by task_id, census). census['fatal'] lists fail-closed schema violations."""
    records: dict[str, dict] = {}
    lines: dict[str, list[int]] = {}
    per_line: list[dict] = []
    fatal: list[str] = []
    n_lines = 0
    for i, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        n_lines += 1
        try:
            r = json.loads(raw)
        except ValueError as exc:
            fatal.append(f"line {i}: not JSON ({exc.__class__.__name__})")
            continue
        if not isinstance(r, dict):
            fatal.append(f"line {i}: not a JSON object")
            continue
        t = r.get("task_id")
        if not isinstance(t, str) or not t:
            fatal.append(f"line {i}: missing task_id")
            continue
        sig = _signature(r)
        per_line.append({"line": i, "task_id": t, **sig})
        missing = [k for k in REQUIRED_TOP if k not in r or r[k] in (None, "")]
        m = r.get("manifest")
        if isinstance(m, dict):
            missing += [f"manifest.{k}" for k in REQUIRED_MANIFEST if not isinstance(m.get(k), str) or not m[k]]
        elif "manifest" not in missing:
            missing.append("manifest(not an object)")
        if missing:
            fatal.append(f"line {i} task {t}: missing {missing}")
        if sig["closure"] == UNKNOWN:
            fatal.append(f"line {i} task {t}: manifest.dev_test_closure has an unknown shape")
        records[t] = r
        lines.setdefault(t, []).append(i)
    if not records and not fatal:
        fatal.append("historical file has no records")
    eff = {t: _signature(r) for t, r in records.items()}
    by_status: dict[str, dict[str, int]] = {}
    for sig in eff.values():
        row = by_status.setdefault(sig["status"], {"n": 0, RECORDED: 0, ABSENT: 0, NULL: 0, UNKNOWN: 0})
        row["n"] += 1
        row[sig["closure"]] += 1
    shapes = Counter(json.dumps({k: sig[k] for k in ("top_keys", "manifest_keys", "closure_keys")},
                                sort_keys=True) for sig in eff.values())
    census = {
        "rule_id": RULE_ID, "path": HIST_REL, "n_nonblank_lines": n_lines, "n_tasks": len(records),
        "duplicates": {t: ls for t, ls in sorted(lines.items()) if len(ls) > 1},
        "effective_record": "last record of a task_id wins (unchanged kit semantics)",
        "closure_state_counts": dict(Counter(sig["closure"] for sig in eff.values())),
        "by_status": dict(sorted(by_status.items())),
        "tasks_with_recorded_closure": sorted(t for t, s in eff.items() if s["closure"] == RECORDED),
        "tasks_without_recorded_closure": sorted(t for t, s in eff.items() if s["closure"] in (ABSENT, NULL)),
        "record_shapes": [{"n": n, **json.loads(k)} for k, n in sorted(shapes.items())],
        "per_line": per_line, "fatal": fatal}
    return records, census


def eng_check(rec: dict, *, frozen_closure: dict, adapted_closure: dict, frozen_lookup: dict,
              adapted_lookup: dict, install_mode: str, lock_signature: str,
              sha_obj: Callable[[Any], str], brief: Callable[[dict], dict]) -> dict:
    """Pure R2A check of one historical ENG record. Returns the report row with its violations."""
    state, recorded = closure_state(rec)
    b = brief(adapted_closure)
    same = sha_obj(frozen_closure) == sha_obj(adapted_closure)
    lk_same = frozen_lookup == adapted_lookup
    m = rec.get("manifest") if isinstance(rec.get("manifest"), dict) else {}
    mode_rec, lock_rec = m.get("install_mode"), m.get("lockfile_sha256")
    mode_ok = isinstance(mode_rec, str) and install_mode == mode_rec
    lock_ok = isinstance(lock_rec, str) and lock_signature == lock_rec
    keys: list[str] = []
    mism: dict[str, list] = {}
    if state == RECORDED:
        keys = [k for k in BRIEF_KEYS if k in recorded]
        mism = {k: [recorded[k], b.get(k)] for k in keys if recorded[k] != b.get(k)}
        prov = "MATCH" if not mism else "MISMATCH"
    else:
        prov = state
    v: list[str] = []
    if not same:
        v.append("CLOSURE_FROZEN_ADAPTED_DIFFER")
    if not lk_same:
        v.append("LOOKUP_FROZEN_ADAPTED_DIFFER")
    if not mode_ok:
        v.append("INSTALL_MODE_NOT_RECORDED" if not isinstance(mode_rec, str) else "INSTALL_MODE_DIFFERS_FROM_RECORD")
    if not lock_ok:
        v.append("LOCKFILE_SHA_NOT_RECORDED" if not isinstance(lock_rec, str) else "LOCKFILE_SHA_DIFFERS_FROM_RECORD")
    if prov == "MISMATCH":
        v.append(f"RECORDED_CLOSURE_MISMATCH:{sorted(mism)}")
    if prov == UNKNOWN:
        v.append("RECORDED_CLOSURE_UNKNOWN_SCHEMA")
    return {"status": status_of(rec), "closure_identical": same, "recorded_closure": prov,
            "recorded_closure_keys_compared": keys, "recorded_closure_mismatch": mism,
            "lookup_identical": lk_same, "install_mode_matches_record": mode_ok,
            "lockfile_sha_matches_record": lock_ok, "violations": v}


def provenance_coverage(eng: dict[str, dict]) -> dict:
    c = Counter(r["recorded_closure"] for r in eng.values())
    return {"n_eng": len(eng), "identity_tested": len(eng), "recorded_closure_counts": dict(c),
            "recorded_closure_compared": c.get("MATCH", 0) + c.get("MISMATCH", 0)}


def record_problems(rec: dict, *, kit_commit: str, design_sha: str, files_lf_sha: dict[str, str]) -> list[str]:
    """Pure check of the static R2A amendment record against the repository (used by the guard).
    files_lf_sha: working-tree LF sha256 of every amended/added file named in the record."""
    bad = []
    if rec.get("rule_id") != RULE_ID or rec.get("tag") != TAG:
        bad.append("rule id / tag drift")
    if rec.get("rule_constants_sha256") != rule_constants_sha():
        bad.append("rule constants drift")
    a = rec.get("amends", {})
    if a.get("kit_commit") != kit_commit:
        bad.append(f"amends kit commit {a.get('kit_commit')} != kit tag commit {kit_commit}")
    if a.get("design_artifact_sha256") != design_sha:
        bad.append("design artifact drift")
    for f, h in rec.get("amended_files", {}).items():
        if files_lf_sha.get(f) != h.get("r2a_lf_sha256"):
            bad.append(f"amended file drift {f}")
    for f, h in rec.get("added_files", {}).items():
        if files_lf_sha.get(f) != h:
            bad.append(f"added file drift {f}")
    return bad
