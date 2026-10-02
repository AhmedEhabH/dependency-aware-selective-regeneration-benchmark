#!/usr/bin/env python3
"""WP2 M16 R2 - MAIN input adapter (brain-authored). ZERO model API, ZERO Docker.

The frozen V3 code reads its task inputs from DEV-only files: commits from the DEV census
(benchmark.wp2.e2e.scopes.CENSUS, phase5/P2P-U task_commits), the era key and the locked
dev/test closure from files under `harness_v3.PROJECT` (dev census + DEV unchanged-test
inventory), and P2P-U inventory rows from a module global. For a MAIN task these lookups
fail or - worst case - silently return `mechanism = none` (no dev/test group installed).

R2 changes INPUTS ONLY. It builds a "shadow root" that contains exactly the two files the
frozen functions read, at the exact relative paths they read, holding the frozen DEV rows
UNCHANGED plus MAIN rows built from frozen MAIN artifacts (commits from the MAIN census,
era from the frozen Linux-v2 per-task record, associated unchanged-test files from the
frozen MAIN inventory). Inside `main_inputs()` the frozen modules are pointed at it:
    scopes.CENSUS            <- union census (dict, same schema)
    harness_v3.PROJECT       <- shadow root   (v31_dev_closure, _era_for)
    p2pu.V2_ROOT / INVENTORY <- shadow v2 dir / union inventory
    p2pu.OUT_ROOT            <- the M16 evaluator-set directory (never the historical one)
and the evaluator module is wrapped by `EvProxy` whose PROJECT is the shadow root (era).
No frozen function body is changed; DEV rows are byte-identical, so every DEV/ENG call
returns what it returned before (verified in Q02 against stored historical records).

Fail-closed (Q02): every MAIN task in the frozen 220 must have commits, an era, target
manifests, a dev/test closure whose note is not "task not in census"/"no target manifests
found", and `mechanism != "none"` whenever its target manifests declare a dev/test group.
Any violation is a STOP (exit 35), never a warning or fallback.
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

MAIN_CENSUS = "research/wp2/wp2_saleor_main297_census_2026-09-22.json"
ORACLE_SELECTION = "research/wp2/wp2_oracle_confirmation_selection_2026-09-22.json"
PER_TASK_V2 = "research/wp2/oracle_confirmation_linux_v2_2026-09-23/per_task_v2.jsonl"
MAIN_INVENTORY = ("research/wp2/oracle_confirmation_linux_v2_2026-09-23/"
                  "wp2_unchanged_p2p_candidate_inventory_v1_final_2026-09-25.json")
DEV_CENSUS = "research/wp2/oracle_confirmation_linux_v2_2026-09-23/dev_census_2026-09-23.json"
DEV_INVENTORY = "research/wp2/wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json"
ERAS = ("py38", "py39", "py312")
ADAPTER_VERSION = "m16-r2-main-input-adapter-v1"
MECHANISM_NONE_NOTES = ("task not in census", "no target manifests found")


class AdapterError(RuntimeError):
    """R2 fail-closed violation (exit 35)."""


def _load(p: Path) -> Any:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _canon(x: Any) -> str:
    return json.dumps(x, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha_obj(x: Any) -> str:
    return hashlib.sha256(_canon(x).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ frozen MAIN inputs
def frame_220(project: Path) -> list[str]:
    sel = _load(project / ORACLE_SELECTION)
    ids = [r["task_id"] for r in sel["selection"]["tasks"]]
    if len(ids) != 220 or len(set(ids)) != 220 or sel.get("status") != "FROZEN_BEFORE_ORACLE_EXECUTION":
        raise AdapterError("frozen oracle selection is not the 220-task frame")
    return sorted(ids)


def main_rows(project: Path) -> dict[str, dict]:
    """task_id -> {task_id, parent_commit, target_commit, era_key} for the frozen 220."""
    census = {t["task_id"]: t for t in _load(project / MAIN_CENSUS)["tasks"]}
    eras = {}
    for line in (project / PER_TASK_V2).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            eras[r["task_id"]] = r.get("era_key")
    out = {}
    for t in frame_220(project):
        c = census.get(t)
        if not c or not c.get("parent_commit") or not c.get("target_commit"):
            raise AdapterError(f"MAIN census row missing for {t}")
        if eras.get(t) not in ERAS:
            raise AdapterError(f"era missing for {t}: {eras.get(t)!r}")
        out[t] = {"task_id": t, "parent_commit": c["parent_commit"],
                  "target_commit": c["target_commit"], "era_key": eras[t]}
    return out


def build_shadow(project: Path, shadow_root: Path) -> dict:
    """Write the two shadow files (DEV rows unchanged + MAIN rows). Returns hashes."""
    dev_census = _load(project / DEV_CENSUS)
    dev_inv = _load(project / DEV_INVENTORY)
    dev_ids = {t["task_id"] for t in dev_census["tasks"]}
    rows = main_rows(project)
    if dev_ids & set(rows):
        raise AdapterError("DEV and MAIN overlap; the union census would be ambiguous")
    minv = {r["task_id"]: r for r in _load(project / MAIN_INVENTORY)["tasks"]}
    main_census = sorted(_load(project / MAIN_CENSUS)["tasks"], key=lambda r: r["task_id"])
    if dev_ids & {r["task_id"] for r in main_census}:
        raise AdapterError("DEV and MAIN_297 overlap")
    census = copy.deepcopy(dev_census)
    census["tasks"] = list(dev_census["tasks"]) + [
        {"task_id": r["task_id"], "parent_commit": r["parent_commit"], "target_commit": r["target_commit"],
         "m16_source": MAIN_CENSUS} for r in main_census]
    census["m16_adapter_note"] = (f"{ADAPTER_VERSION}: frozen DEV census rows unchanged + MAIN_297 rows "
                                  "(task_id, parent_commit, target_commit); era/inventory rows only for "
                                  "the frozen 220")
    inv = copy.deepcopy(dev_inv)
    main_inv_rows = []
    for t, r in sorted(rows.items()):
        m = minv.get(t)
        if m is None:
            raise AdapterError(f"MAIN unchanged-test inventory row missing for {t}")
        row = copy.deepcopy(m)
        row["era_key"] = r["era_key"]
        row["parent_commit"] = r["parent_commit"]
        row["m16_source"] = MAIN_INVENTORY
        main_inv_rows.append(row)
    inv["tasks"] = list(dev_inv["tasks"]) + main_inv_rows
    inv["m16_adapter_note"] = (f"{ADAPTER_VERSION}: frozen DEV inventory rows unchanged + MAIN rows "
                               "(frozen MAIN inventory row + era_key from per_task_v2)")
    files = {DEV_CENSUS: census, DEV_INVENTORY: inv}
    hashes = {}
    for rel, obj in files.items():
        p = shadow_root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
        p.write_text(text, encoding="utf-8", newline="\n")
        hashes[rel] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    readme = {"artifact": "m16_adapter_shadow_root", "version": ADAPTER_VERSION,
              "purpose": "input-only shim read by frozen V3 functions at their hard-coded paths",
              "files": hashes, "n_dev_rows": len(dev_census["tasks"]), "n_main_census_rows": len(main_census),
              "n_main_frame_rows": len(rows)}
    (shadow_root / "M16_SHADOW_README.json").write_text(
        json.dumps(readme, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return readme


def load_shadow(shadow_root: Path) -> tuple[dict, dict]:
    return _load(shadow_root / DEV_CENSUS), _load(shadow_root / DEV_INVENTORY)


# ------------------------------------------------------------------ patching
class EvProxy:
    """The frozen evaluator module with PROJECT redirected to the shadow root (era lookup)."""

    def __init__(self, ev: Any, shadow_root: Path) -> None:
        object.__setattr__(self, "_ev", ev)
        object.__setattr__(self, "PROJECT", shadow_root)

    def __getattr__(self, name: str) -> Any:
        return getattr(object.__getattribute__(self, "_ev"), name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(object.__getattribute__(self, "_ev"), name, value)


@contextlib.contextmanager
def main_inputs(shadow_root: Path, p2pu_out: Path | None = None) -> Iterator[dict]:
    """Point the frozen modules at the shadow inputs for the duration of the block."""
    import benchmark.wp2.e2e.scopes as scopes
    import benchmark.wp2.harness_v3 as hv3
    census, inv = load_shadow(shadow_root)
    saved: list[tuple[Any, str, Any]] = [(scopes, "CENSUS", scopes.CENSUS), (hv3, "PROJECT", hv3.PROJECT)]
    scopes.CENSUS = census
    hv3.PROJECT = shadow_root
    p2pu = None
    if p2pu_out is not None:
        import scripts.wp2_m10b_p2pu_v3_eng as p2pu
        for name in ("V2_ROOT", "INVENTORY", "OUT_ROOT"):
            saved.append((p2pu, name, getattr(p2pu, name)))
        p2pu.V2_ROOT = shadow_root / Path(DEV_CENSUS).parent
        p2pu.INVENTORY = inv
        p2pu_out.mkdir(parents=True, exist_ok=True)
        p2pu.OUT_ROOT = p2pu_out
    try:
        yield {"scopes": scopes, "harness_v3": hv3, "p2pu": p2pu}
    finally:
        for mod, name, val in reversed(saved):
            setattr(mod, name, val)


def clear_closure_cache(task_ids: list[str] | None = None) -> None:
    import benchmark.wp2.harness_v3 as hv3
    if task_ids is None:
        hv3._DEV_CLOSURE_CACHE.clear()
    else:
        for t in task_ids:
            hv3._DEV_CLOSURE_CACHE.pop(t, None)


# ------------------------------------------------------------------ fail-closed checks
def declares_dev_group(manifests: dict[str, str]) -> bool:
    """Target manifests declare a dev/test group (frozen dep_compiler predicates)."""
    from benchmark.wp2.dep_compiler import pyproject_dev_group_names
    py = manifests.get("pyproject.toml", "")
    if py and (pyproject_dev_group_names(py) or "[dependency-groups]" in py
               or "[tool.poetry.group.dev.dependencies]" in py
               or "[tool.poetry.dev-dependencies]" in py):
        return True
    return bool(manifests.get("requirements_dev.txt") or manifests.get("requirements-test.txt"))


def closure_brief(c: dict) -> dict:
    return {"mechanism": c.get("mechanism"), "n_pins": len(c.get("pins", [])),
            "pins_sha256": c.get("pins_sha256"), "n_unsupported": len(c.get("unsupported", [])),
            "era_key": c.get("era_key"), "python_version": c.get("python_version"),
            "note": c.get("note", "")}


def check_main_closure(task_id: str, era_expected: str, manifests: dict[str, str],
                       closure: dict) -> list[str]:
    """Pure fail-closed predicate for one MAIN task (unit-tested). Returns violations."""
    bad = []
    if not manifests:
        bad.append("NO_TARGET_MANIFESTS")
    if closure.get("note") in MECHANISM_NONE_NOTES:
        bad.append(f"CLOSURE_NOTE:{closure.get('note')}")
    if closure.get("era_key") != era_expected:
        bad.append(f"ERA_MISMATCH:{closure.get('era_key')}!={era_expected}")
    if manifests and declares_dev_group(manifests) and closure.get("mechanism") == "none":
        bad.append("DEV_GROUP_DECLARED_BUT_MECHANISM_NONE")
    if closure.get("mechanism") not in ("uv", "poetry", "requirements", "none"):
        bad.append(f"UNKNOWN_MECHANISM:{closure.get('mechanism')}")
    return bad
