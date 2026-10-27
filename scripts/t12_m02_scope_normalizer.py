#!/usr/bin/env python3
"""T12 M02-D2 — deterministic per-task/per-arm scope extraction + normalization
(OFFLINE, ZERO-OUTCOME-READ, stdlib only).

Mission: T12_M02_D2_INPUT_CONTRACT_20261027 (Track 1.2), Task 1.

The frozen per-arm scope SOURCES are multi-task prediction files or candidate
universes — NOT automatically valid materializer ``--scope-json`` files.  This
module turns one arm + one task into the *precise supported materializer
schema* ``{"scope": [repo-relative canonical paths]}`` (frozen parser lines
1151-1176), deterministically and WITHOUT reading any outcome domain field.

Guarantees:

* EXTRACTION RULES ARE ALLOWLISTS.  Each arm declares exactly ONE extraction
  keypath into its frozen source; only that value list is consumed.  Oracle /
  outcome fields that may coexist in a source (e.g. ``gold``,
  ``<arm>_confusion``, ``classification``) are NEVER consumed: their presence
  is recorded (names only, never values) and a fail-closed guard aborts if the
  allowlisted key is absent or malformed.
* GOLD arm exception is DECLARED, not implicit: the frozen plan designates the
  gold-proxy list as that arm's selector input; it is extracted through its
  own allowlist and never reaches any other arm.
* Every normalized scope artifact carries: arm id, task id, source SHA256,
  extraction rule + version, output SHA256 (frozen canonical scope hash),
  selected path count, and a reproducible audit receipt.

Edge handling (mission Task 1): missing task (fail closed), duplicates
(deduplicated + counted), empty NEG ({"scope": []}), full SELECT_ALL
(candidate universe), derived FULL_REFERENCE (non-test reference change set,
needs the read-only frozen git diff + frozen census test flags).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

_SCRIPTS = Path(__file__).resolve().parent
_schema_spec = importlib.util.spec_from_file_location(
    "t12_m02_materializer_schema", _SCRIPTS / "t12_m02_materializer_schema.py")
assert _schema_spec is not None and _schema_spec.loader is not None
_schema_mod = importlib.util.module_from_spec(_schema_spec)
_schema_spec.loader.exec_module(_schema_mod)
SchemaError = _schema_mod.SchemaError
build_test_path_authority = _schema_mod.build_test_path_authority
canonical_scope_hash = _schema_mod.canonical_scope_hash
canonicalize_scope_paths = _schema_mod.canonicalize_scope_paths
git_name_status_map = _schema_mod.git_name_status_map
sha256_file = _schema_mod.sha256_file

_spec = importlib.util.spec_from_file_location("t12_m02_arm_adapter", _SCRIPTS / "t12_m02_arm_adapter.py")
assert _spec is not None and _spec.loader is not None
_adapt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_adapt)

RULE_VERSION = "t12_m02_scope_rule_v1"
SCHEMA = "t12_m02_scope_normalization_receipt_v1"

# Test-only seam: maps arm_id -> source path, consulted BEFORE the frozen pin
# table (never populated by production code).
SOURCE_PATH_OVERRIDES: dict[str, Path] = {}


class ExtractionError(Exception):
    """Fail-closed scope extraction problem (typed)."""


# --------------------------------------------------------------------------
# Allowlisted extraction definitions
# --------------------------------------------------------------------------

# Known outcome-domain keys that coexist in some sources.  Values are NEVER
# read; only presence is recorded.
ORACLE_KEYS_PER_SOURCE: dict[str, tuple[str, ...]] = {
    "per_task_predictions_r2": ("gold", "gold_in_universe_count", "universe_size",
                                "rmcss_size", "bm25_missing_at_parent"),
    "agentless": ("classification",),
    "wp1b_agent": (),
    "sip_rmcss": (),
    "proxies_gold": ("opened_once",),
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"SOURCE_UNREADABLE: {path}: {exc}") from exc


def _record_holder(source: dict[str, Any], task_id: str) -> Any:
    pt = source.get("per_task")
    if isinstance(pt, dict) and task_id in pt and isinstance(pt[task_id], dict):
        return pt[task_id]
    raise ExtractionError(f"MISSING_TASK_OR_FIELD: per_task[{task_id}] not a dict")


# Extraction accessor per arm.  Each returns (paths: list[str], oracle_present: list[str]).
def _extract_per_task_file(src_path: Path, task_id: str, field: str,
                           source_kind: str) -> tuple[list[str], list[str]]:
    data = _load_json(src_path)
    holder = _record_holder(data, task_id)
    paths = holder.get(field)
    if not isinstance(paths, list):
        raise ExtractionError(f"FIELD_MALFORMED: {field} for {task_id} not a list")
    oracle_present: list[str] = list(
        str(k) for k in ORACLE_KEYS_PER_SOURCE.get(source_kind, ()) if k in holder)
    return [str(p) for p in paths], oracle_present


def _extract_comp_r2(src_path: Path, task_id: str, arm_field: str) -> tuple[list[str], list[str]]:
    data = _load_json(src_path)
    holder = _record_holder(data, task_id)
    paths = holder.get(arm_field)
    if not isinstance(paths, list):
        raise ExtractionError(f"FIELD_MALFORMED: {arm_field} for {task_id} not a list")
    oracle_present: list[str] = []
    for k in ("gold", "gold_in_universe_count", "universe_size", "rmcss_size"):
        if k in holder:
            oracle_present.append(str(k))
    for k in holder:
        if isinstance(k, str) and k.endswith("_confusion"):
            oracle_present.append(str(k))
    return [str(p) for p in paths], sorted(set(oracle_present))


def _extract_agentless(src_path: Path, task_id: str) -> tuple[list[str], list[str]]:
    data = _load_json(src_path)
    records = data.get("records")
    if not isinstance(records, list):
        raise ExtractionError("MISSING_TASK_OR_FIELD: records not a list")
    rec = next((r for r in records if isinstance(r, dict) and r.get("task_id") == task_id), None)
    if rec is None:
        raise ExtractionError(f"MISSING_TASK_OR_FIELD: records has no {task_id}")
    paths = rec.get("prediction_set")
    if not isinstance(paths, list):
        raise ExtractionError(f"FIELD_MALFORMED: prediction_set for {task_id} not a list")
    oracle_present = [k for k in ORACLE_KEYS_PER_SOURCE["agentless"] if k in rec]
    return [str(p) for p in paths], oracle_present


def _extract_gold(src_path: Path, task_id: str) -> tuple[list[str], list[str]]:
    data = _load_json(src_path)
    proxies = data.get("proxies")
    if not isinstance(proxies, dict) or task_id not in proxies:
        raise ExtractionError(f"MISSING_TASK_OR_FIELD: proxies has no {task_id}")
    paths = proxies[task_id]
    if not isinstance(paths, list):
        raise ExtractionError(f"FIELD_MALFORMED: proxies[{task_id}] not a list")
    oracle_present = [k for k in ORACLE_KEYS_PER_SOURCE["proxies_gold"] if k in data]
    return [str(p) for p in paths], oracle_present


def _extract_universe(src_path: Path, _task_id: str) -> tuple[list[str], list[str]]:
    data = _load_json(src_path)
    records = data.get("records")
    if not isinstance(records, list):
        raise ExtractionError("FIELD_MALFORMED: universe records not a list")
    paths = [r["path"] for r in records if isinstance(r, dict) and isinstance(r.get("path"), str)]
    return paths, []


def full_reference_scope(repo: Path, parent: str, target: str,
                         census_records: list[dict[str, Any]]) -> list[str]:
    """FULL_REFERENCE arm scope: ALL non-test reference changes (frozen
    ``materialize_full_reference`` semantics, materialize.py lines 983-1043).

    Uses ONLY the read-only frozen git name-status map + the frozen census
    test-file flags (never filename heuristics).
    """
    git_changes = git_name_status_map(repo, parent, target)
    authority = build_test_path_authority(census_records)
    tests = set(authority["test_paths"])
    if set(git_changes) != set(authority["changed_paths"]):
        raise ExtractionError(
            "CROSS_CHECK_MISMATCH: git name-status does not equal census changed_paths; "
            "refusing to derive FULL_REFERENCE on a non-identical change set"
        )
    return sorted(p for p in git_changes if p not in tests)


# --------------------------------------------------------------------------
# Per-arm rule table
# --------------------------------------------------------------------------

def _rule(accessor: Callable[[Path, str, dict], tuple[list[str], list[str]]],
          source: str, kind: str) -> dict[str, Any]:
    return {"accessor": accessor, "source": source, "kind": kind}


def extraction_rule_for(arm_id: str) -> dict[str, Any]:
    """Declared allowlisted extraction rule per arm (fail closed on unknown)."""
    if arm_id in ("SIP", "RM_CSS"):
        field = "sip_predicted_set" if arm_id == "SIP" else "rmcss_predicted_set"

        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del meta_in
            return _extract_per_task_file(p, t, field, "sip_rmcss")

        src = "research/wp1a/sip_rmcss_per_task_predictions.json"
        return _rule(acc, src, "PREDICTION_FILE")
    if arm_id in ("AGENT",):
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del meta_in
            return _extract_per_task_file(p, t, "selected_paths", "wp1b_agent")

        return _rule(acc, "research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json",
                     "PREDICTION_FILE")
    if arm_id in ("DENSE_K3", "DENSE_K10", "BM25_K3", "BM25_K10", "BM25_TO_CIA_1HOP"):
        arm_field = {
            "DENSE_K3": "DENSE@3_selected",
            "DENSE_K10": "DENSE@10_selected",
            "BM25_K3": "BM25@3_selected",
            "BM25_K10": "BM25@10_selected",
            "BM25_TO_CIA_1HOP": "BM25_TO_CIA_1HOP_selected",
        }[arm_id]

        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del meta_in
            return _extract_comp_r2(p, t, arm_field)

        return _rule(acc, "D:/wp2_comp_baselines/research/competitor-baselines-r2/"
                          "per_task_predictions_r2.json", "PREDICTION_FILE")
    if arm_id == "AGENTLESS_STYLE_ADAPTATION":
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del meta_in
            return _extract_agentless(p, t)

        return _rule(acc, "D:/wp2_agentless_main297/research/competitor-agentless-r1/"
                          "agentless_r1_prediction_freeze.json", "PREDICTION_FILE")
    if arm_id == "GOLD":
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del meta_in
            return _extract_gold(p, t)

        return _rule(acc, "research/saleor-reserve-300-rmcss/"
                          "saleor_reserve_300_proxies.json", "PREDICTION_FILE")
    if arm_id == "SELECT_ALL":
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del t, meta_in
            return _extract_universe(p, "")

        return _rule(acc, "benchmark_data/real_commit_impact_saleor/scientific/<task_id>/public/"
                          "candidate_universe.json", "UNIVERSE_FILE")
    if arm_id == "NEG":
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del p, t, meta_in
            return [], []

        return _rule(acc, "derived-control:empty-scope", "DERIVED_CONTROL")
    if arm_id == "FULL_REFERENCE":
        def acc(p: Path, t: str, meta_in: dict) -> tuple[list[str], list[str]]:
            del p, t
            return full_reference_scope(meta_in["repo"], meta_in["parent"],
                                        meta_in["target"], meta_in["census_records"]), []

        return _rule(acc, "materialize_full_reference", "DERIVED_CONTROL")
    raise ExtractionError(f"UNKNOWN_ARM: {arm_id}")


def resolve_source_path(arm_id: str, base: Path) -> tuple[Path, str | None]:
    """Resolve the frozen source path for an arm (universe <task_id> substituted)."""
    if arm_id in SOURCE_PATH_OVERRIDES:
        return SOURCE_PATH_OVERRIDES[arm_id], None
    pin = _adapt.ARM_SCOPE_SOURCES[arm_id]
    src = pin["source"]
    if pin["kind"] == "DERIVED_CONTROL":
        return Path(src), None
    path = Path(str(src).replace("<task_id>", _adapt.FROZEN_TASK))
    if not path.is_absolute():
        path = base / path
    return path, pin.get("sha256")


# --------------------------------------------------------------------------
# Normalization
# --------------------------------------------------------------------------

def normalize_arm_scope(arm_id: str, task_id: str, *, base: Path,
                        repo: Path, census_records: list[dict[str, Any]],
                        log: Callable[[str], None] | None = None) -> dict[str, Any]:
    """Extract + normalize one arm's scope for the pilot task.

    Returns a full audit receipt dict with the source SHA256, extraction rule,
    normalized (sorted, deduplicated, canonical) path list, canonical scope
    hash, oracle-guard evidence, and selected-path count.  Writes nothing.
    """
    rule = extraction_rule_for(arm_id)
    src_path, pin_sha = resolve_source_path(arm_id, base)
    if rule["kind"] != "DERIVED_CONTROL" and not src_path.is_file():
        raise ExtractionError(f"SOURCE_MISSING: {src_path}")
    source_sha = None if rule["kind"] == "DERIVED_CONTROL" else sha256_file(src_path)
    if source_sha is not None and pin_sha is not None and source_sha != pin_sha:
        raise ExtractionError(
            f"SOURCE_PIN_DRIFT: {src_path} sha256 {source_sha} != pin {pin_sha}"
        )
    meta = {
        "repo": repo, "parent": _adapt.FROZEN_PARENT,
        "target": _adapt.FROZEN_TARGET, "census_records": census_records,
    }
    raw_paths, oracle_present = rule["accessor"](src_path, task_id, meta)
    try:
        unique, dup = canonicalize_scope_paths(raw_paths, context="scope")
    except SchemaError as exc:
        return {
            "schema": SCHEMA, "arm_id": arm_id, "task_id": task_id,
            "status": "REJECTED_INVALID_SCOPE_SPELLING", "reason": str(exc),
            "rule_version": RULE_VERSION,
        }
    scope_hash = canonical_scope_hash(unique)
    out_text = json.dumps({"scope": unique}, sort_keys=True, ensure_ascii=False) + "\n"
    out_sha = hashlib.sha256(out_text.encode("utf-8")).hexdigest()
    if log is not None:
        log(f"arm={arm_id:<26} task={task_id} paths={len(unique):>4} "
            f"dup={dup} hash={scope_hash[:16]} oracle={oracle_present}")
    return {
        "schema": SCHEMA,
        "rule_version": RULE_VERSION,
        "arm_id": arm_id,
        "task_id": task_id,
        "status": "OK",
        "source": str(src_path),
        "source_kind": rule["kind"],
        "source_sha256": source_sha,
        "source_pin_matched": (source_sha == pin_sha) if (source_sha and pin_sha) else None,
        "extraction_keypath_allowlist": _describe_rule(arm_id),
        "oracle_fields_present_never_consumed": oracle_present,
        "selected_path_count": len(unique),
        "duplicate_count": dup,
        "scope_hash": scope_hash,
        "scope_json_sha256": out_sha,
        "scope_json": {"scope": unique},
    }


def _describe_rule(arm_id: str) -> str:
    if arm_id == "SIP":
        return "per_task[task].sip_predicted_set"
    if arm_id == "RM_CSS":
        return "per_task[task].rmcss_predicted_set"
    if arm_id == "AGENT":
        return "per_task[task].selected_paths"
    if arm_id == "DENSE_K3":
        return "per_task[task].DENSE@3_selected"
    if arm_id == "DENSE_K10":
        return "per_task[task].DENSE@10_selected"
    if arm_id == "BM25_K3":
        return "per_task[task].BM25@3_selected"
    if arm_id == "BM25_K10":
        return "per_task[task].BM25@10_selected"
    if arm_id == "BM25_TO_CIA_1HOP":
        return "per_task[task].BM25_TO_CIA_1HOP_selected"
    if arm_id == "AGENTLESS_STYLE_ADAPTATION":
        return "records[task_id=task].prediction_set"
    if arm_id == "GOLD":
        return "proxies[task] (oracle-designated control arm by frozen plan)"
    if arm_id == "SELECT_ALL":
        return "candidate_universe.records[].path (all-file arm)"
    if arm_id == "NEG":
        return "derived-control empty scope"
    if arm_id == "FULL_REFERENCE":
        return "derived git name-status minus census test paths"
    return "UNKNOWN"


def normalize_all_arms(*, base: Path, repo: Path, census_records: list[dict[str, Any]],
                       task_id: str | None = None, arms: list[str] | None = None,
                       log: Callable[[str], None] | None = None) -> list[dict[str, Any]]:
    """Normalize one or all 13 arms; ORDER preserves the frozen first-four.
    Returns receipts (order: given arms list, defaulting to frozen order)."""
    task = task_id or _adapt.FROZEN_TASK
    wanted = arms or [a["arm_id"] for a in _adapt.load_arms()]
    # keep frozen order regardless of caller order for determinism
    frozen = [a["arm_id"] for a in _adapt.load_arms()]
    ordered = [a for a in frozen if a in wanted]
    missing = [a for a in wanted if a not in frozen]
    if missing:
        raise ExtractionError(f"UNKNOWN_ARM: {missing}")
    out = []
    for arm in ordered:
        out.append(normalize_arm_scope(arm, task, base=base, repo=repo,
                                       census_records=census_records, log=log))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="t12_m02_scope_normalizer",
        description="Offline per-task/per-arm scope normalization to the frozen "
                    "materializer --scope-json schema. Writes nothing unless --out is set.")
    ap.add_argument("--out", default=None, help="output directory for scope_<arm>.json + receipts")
    ap.add_argument("--base", default=str(Path.cwd()), help="checkout root for relative sources")
    ap.add_argument("--repo", default=str(_adapt.FROZEN_SOURCE_SALEOR_REPO),
                    help="read-only saleor git cache (FULL_REFERENCE derivation)")
    ap.add_argument("--census", default="research/wp2/wp2_saleor_main297_census_2026-09-22.json",
                    help="frozen census JSON path")
    ap.add_argument("--arms", default=None, help="comma-separated arm ids (default: all 13 frozen)")
    args = ap.parse_args(argv)

    census_path = Path(args.census)
    if not census_path.is_file() and not (Path(args.base) / census_path).is_file():
        print(f"STOP:CENSUS_MISSING: {census_path}", file=sys.stderr)
        return 3
    census_data = json.loads((census_path if census_path.is_file()
                              else Path(args.base) / census_path).read_text(encoding="utf-8"))
    census_records = next(
        (r.get("changed_paths") for r in census_data.get("tasks", [])
         if isinstance(r, dict) and r.get("task_id") == _adapt.FROZEN_TASK), None)
    if census_records is None:
        print("STOP:CENSUS_TASK_MISSING", file=sys.stderr)
        return 3

    arms = args.arms.split(",") if args.arms else None
    receipts = normalize_all_arms(
        base=Path(args.base), repo=Path(args.repo), census_records=census_records,
        arms=arms, log=print)
    ok = [r for r in receipts if r.get("status") == "OK"]
    bad = [r for r in receipts if r.get("status") != "OK"]
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        for r in receipts:
            if r.get("status") == "OK":
                (out / f"scope_{r['arm_id']}.json").write_text(
                    json.dumps({"scope": r["scope_json"]["scope"]}, sort_keys=True,
                               ensure_ascii=False) + "\n", encoding="utf-8")
            (out / f"scope_{r['arm_id']}.receipt.json").write_text(
                json.dumps({k: v for k, v in r.items() if k != "scope_json"},
                           sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        (out / "receipts_summary.json").write_text(
            json.dumps(receipts, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"WROTE_SCOPES {out} ok={len(ok)} rejected={len(bad)}")
    else:
        print(json.dumps(receipts, sort_keys=True, ensure_ascii=False, default=str))
    return 0 if not bad else 4


if __name__ == "__main__":
    sys.exit(main())
