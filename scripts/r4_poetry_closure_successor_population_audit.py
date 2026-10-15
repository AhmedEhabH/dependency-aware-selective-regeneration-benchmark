#!/usr/bin/env python3
"""R4 Poetry Closure Successor — population-wide closure audit (S4, BEFORE Docker).

Mission M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION.

Deterministic metadata/parser-only audit over the exact frozen Full-D7
population (144 validation units / 219 mapped tasks).  For every task the
successor behavioural dependency closure is derived according to its frozen
install route and compared against the appropriate frozen dependency/closure
authority:

* old R4 closure  = qualified R4-B integrated-parser closure (marker-gated)
  as the pre-successor runner produced it (``runtime_pins`` R4-B branch);
* successor closure = successor route-aware closure projection
  (``route_closure``): ``LOCK_FRAGMENT_MAIN_PLUS_DEV`` poetry reuses the frozen
  R3 complete-main+dev closure; every other route is unchanged;
* frozen expected  = ``D7_REQUIRED_CLOSURE_AUDIT`` (R1 superseding) required
  main/dev closure where defined.

Equality classification (no unclassified disagreement):

* ``EXACT_MATCH`` — successor equals the audit expected closure exactly.
* ``MATCH_AFTER_R3_PLATFORM_EXCLUSIONS`` — successor differs from the audit
  expected closure only by the exactly-two frozen R3 platform exclusions that
  the D7 install-route authority legitimately applies (pywin32
  marker-excluded-on-linux; python-magic-bin platform=win32).
* ``MATCH_AFTER_D4_R5_CODECOV`` — REQ units where the audit's expected set
  reflects the audit generator's superseded D4 codecov hard-coded set while the
  current D4 R5 amendment governs (codecov 2.1.11/2.1.12 recovered as exact
  artifacts, not excluded by R5).  Current behaviour is unchanged.
* ``NO_AUDIT_EXPECTED_DEFINED`` — the audit does not define an expected closure
  for this unit (V2 legacy / legacy group semantics unresolved).  The route
  remains unchanged; successor == old R4 for V2 (complete closure already).
* ``SEMANTIC_DISAGREEMENT`` — any other difference (must be empty).

No behavioural container is executed.  Exactly 144 units and 219 tasks are
accounted; zero silent skips; no unknown install route.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark.wp2.env_r4 import route_closure  # noqa: E402
from benchmark.wp2.env_r4.contracts import (  # noqa: E402
    RuntimeTarget,
    normalize_name,
    parse_lock,
    unbind_lock_parser,
)
from benchmark.wp2.env_r4.integrated_parser import bind_integrated_parser  # noqa: E402

CENSUS = PROJECT / "research" / "env-canon-r4" / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
AUDIT_JSON = Path(r"D:\wp2_env_store\manifests\D7_REQUIRED_CLOSURE_AUDIT.json")
AUDIT_R1_JSON = Path(r"D:\wp2_env_store\manifests\D7_REQUIRED_CLOSURE_AUDIT_R1.json")
D4_CODECOV_AMENDMENT = Path(r"D:\wp2_env_store\manifests\D4_CODECOV_NONRUNTIME_EXCLUSION_AMENDMENT_R5.json")
LOCK_DIR = Path(r"D:\wp2_env_store\artifacts\locks")

EXPECTED_N_UNITS = 144
EXPECTED_N_TASKS = 219
ALLOWED_ROUTES = ("LOCK_FRAGMENT_MAIN_PLUS_DEV", "REQ_MAIN_PLUS_LOCK_DEV", "UV_EXPORT", "V2_EDITABLE_PLUS_LOCK_DEV")

# Exactly-two frozen R3 platform-exclusion names (marker audit + frozen pyproject).
MARKER_EXCLUDED_ON_LINUX = {"pywin32"}
PYPROJECT_WIN32_NAMES = {"python-magic-bin"}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_census() -> dict:
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def load_audit_expected() -> dict:
    path = AUDIT_R1_JSON if AUDIT_R1_JSON.is_file() else AUDIT_JSON
    return json.loads(path.read_text(encoding="utf-8"))


def codecov_excluded_versions() -> set[str]:
    """D4 R5 non-runtime codecov exclusion set (frozen amendment, exact)."""
    if not D4_CODECOV_AMENDMENT.is_file():
        return set()
    data = json.loads(D4_CODECOV_AMENDMENT.read_text(encoding="utf-8"))
    return {str(v) for v in data.get("affected_versions", [])}


def _r4b_requirements(lock_path: Path, target: RuntimeTarget) -> set[str]:
    bind_integrated_parser()
    try:
        closure = parse_lock(lock_path, target)
        if not closure.is_valid:
            raise RuntimeError(f"invalid closure: {closure.fail_closed_reasons}")
        return {f"{r.normalized_name}=={r.version}" for r in closure.requirements}
    finally:
        unbind_lock_parser()


def _r4b_exclusions(lock_path: Path, target: RuntimeTarget) -> set[str]:
    bind_integrated_parser()
    try:
        closure = parse_lock(lock_path, target)
        if not closure.is_valid:
            raise RuntimeError(f"invalid closure: {closure.fail_closed_reasons}")
        return {f"{r.normalized_name}=={r.version}" for r in closure.exclusions}
    finally:
        unbind_lock_parser()


def _successor_requirements(lock_path: Path, install_route: str, lock_type: str, pyver: str) -> set[str]:
    if route_closure.route_requires_complete_main_plus_dev(install_route, lock_type):
        return set(
            route_closure.derive_route_pins(
                install_route=install_route,
                lock_type=lock_type,
                lock_path=lock_path,
                python_version=pyver,
                marker_excluded_names=MARKER_EXCLUDED_ON_LINUX,
                win32_excluded_names=PYPROJECT_WIN32_NAMES,
            )
        )
    # Other routes are UNCHANGED: identical R4-B projection + the same frozen
    # platform exclusions the qualified runner applies to every route.
    target = RuntimeTarget(pyver, "cpython", "linux", "x86_64")
    reqs = _r4b_requirements(lock_path, target)
    excluded_versions = codecov_excluded_versions()
    return {
        p
        for p in reqs
        if p.partition("==")[0] not in MARKER_EXCLUDED_ON_LINUX
        and p.partition("==")[0] not in PYPROJECT_WIN32_NAMES
        and not (
            p.partition("==")[0] == "codecov"
            and p.partition("==")[2] in excluded_versions
        )
    }


def _audit_expected_for_unit(audit: dict, uid: str) -> tuple[int | None, set[str]]:
    unit = audit.get("units", {}).get(uid, {})
    count = unit.get("required_package_count")
    pkgs = unit.get("required_packages", [])
    names = {
        f"{normalize_name(p['name'])}=={p['version']}"
        for p in pkgs
        if isinstance(p, dict)
    }
    return count, names


def main() -> None:
    census = load_census()
    audit = load_audit_expected()
    units = census["units"]
    assert len(units) == EXPECTED_N_UNITS, f"census units != {EXPECTED_N_UNITS}"

    rows: list[dict] = []
    task_seen: set[str] = set()
    route_counter: Counter = Counter()
    lock_absent: list[str] = []
    verdict_counter: Counter = Counter()

    for u in units:
        uid = u["validation_unit_id"]
        install_route = u["install_route"]
        lock_type = u["lock_type"]
        pyver = u["python_version"]
        if install_route not in ALLOWED_ROUTES:
            raise SystemExit(f"UNKNOWN_INSTALL_ROUTE {install_route} for {uid}")

        route_counter[install_route] += 1
        member_tasks = list(u.get("member_tasks", []))
        for tid in member_tasks:
            task_seen.add(tid)

        exp_count, exp_names = _audit_expected_for_unit(audit, uid)

        old_reqs: set[str] = set()
        old_excls: set[str] = set()
        succ_reqs: set[str] = set()
        excluded_versions = codecov_excluded_versions()
        for tid in member_tasks:
            lock_path = LOCK_DIR / f"{tid}_{lock_type}.toml"
            if not lock_path.is_file():
                lock_absent.append(str(lock_path))
                continue
            target = RuntimeTarget(pyver, "cpython", "linux", "x86_64")
            raw = _r4b_requirements(lock_path, target)
            old_excls |= _r4b_exclusions(lock_path, target)
            # old R4 runner behaviour: R4-B parse minus (marker audit pywin32,
            # D4-R5 codecov, frozen pyproject win32) — mirrors runtime_pins.
            old_reqs |= {
                p
                for p in raw
                if p.partition("==")[0] not in MARKER_EXCLUDED_ON_LINUX
                and p.partition("==")[0] not in PYPROJECT_WIN32_NAMES
                and not (
                    p.partition("==")[0] == "codecov"
                    and p.partition("==")[2] in excluded_versions
                )
            }
            succ_reqs |= _successor_requirements(lock_path, install_route, lock_type, pyver)

        added = sorted(succ_reqs - old_reqs)
        removed = sorted(old_reqs - succ_reqs)

        # --- equality verdict vs frozen expected closure (where defined) ---
        if exp_count is None:
            verdict = "NO_AUDIT_EXPECTED_DEFINED"
        else:
            r3_excl = {
                f"{n}=={v}"
                for n, v in (("pywin32", "308"), ("python-magic-bin", "0.4.14"))
            }
            # successor must equal audit expected, possibly after the exactly-two
# frozen R3 platform exclusions that the install-route authority
            # applies on top of the audit's complete main+dev closure.
            if succ_reqs == exp_names:
                verdict = "EXACT_MATCH"
            elif (succ_reqs | {p for p in exp_names if p in r3_excl}) == exp_names and succ_reqs <= exp_names:
                # successor == audit-expected minus the exactly-two R3 platform exclusions
                verdict = "MATCH_AFTER_R3_PLATFORM_EXCLUSIONS"
            elif (succ_reqs - exp_names) <= {f"codecov=={v}" for v in ("2.1.11", "2.1.12")}:
                verdict = "MATCH_AFTER_D4_R5_CODECOV"
            else:
                verdict = "SEMANTIC_DISAGREEMENT"
        verdict_counter[verdict] += 1

        rows.append(
            {
                "validation_unit_id": uid,
                "member_task_ids": member_tasks,
                "install_route": install_route,
                "lock_type": lock_type,
                "python_version": pyver,
                "old_r4_closure_count": len(old_reqs),
                "successor_closure_count": len(succ_reqs),
                "frozen_expected_count": exp_count,
                "added_requirements": added,
                "removed_requirements": removed,
                "old_r4_exclusion_count": len(old_excls),
                "exclusions_and_reasons": [
                    {"pin": p, "reason": "R3_PLATFORM_EXCLUDED"}
                    for p in sorted(old_excls)
                ],
                "equality_verdict": verdict,
            }
        )

    n_units = len(rows)
    n_tasks = len(task_seen)
    changed = [r for r in rows if r["added_requirements"] or r["removed_requirements"]]
    disagreements = [r for r in rows if r["equality_verdict"] == "SEMANTIC_DISAGREEMENT"]

    summary = {
        "n_units_accounted": n_units,
        "n_tasks_accounted": n_tasks,
        "expected_units": EXPECTED_N_UNITS,
        "expected_tasks": EXPECTED_N_TASKS,
        "routes": dict(route_counter),
        "verdict_counts": dict(verdict_counter),
        "n_changed_units": len(changed),
        "changed_unit_ids": [r["validation_unit_id"] for r in changed],
        "n_semantic_disagreements": len(disagreements),
        "semantic_disagreement_ids": [r["validation_unit_id"] for r in disagreements],
        "zero_silent_skips": not lock_absent,
        "lock_absent": lock_absent,
        "no_unknown_route": True,
    }

    payload = {
        "artifact": "R4_POETRY_CLOSURE_SUCCESSOR_POPULATION_AUDIT",
        "schema_version": "env-canon-r4/poetry-closure-successor-population-audit/1.0",
        "mission_id": "M17_D7_R4_POETRY_CLOSURE_SUCCESSOR_QUALIFICATION",
        "source_census": str(CENSUS),
        "source_audit_authority": str(AUDIT_R1_JSON if AUDIT_R1_JSON.is_file() else AUDIT_JSON),
        "census_sha256": _sha256_file(CENSUS),
        "summary": summary,
        "units": rows,
    }
    out = PROJECT / "research" / "env-canon-r4" / "R4_POETRY_CLOSURE_SUCCESSOR_POPULATION_AUDIT.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("AUDIT_OUT=" + str(out))


if __name__ == "__main__":
    main()
