"""WP-1 preflight A1 - no tracked artifact may be mutated by the test suite.

A preregistration file must never change when someone runs the tests. This test
snapshots the SHA-256 of every file under ``artifacts/`` and ``research/wp1a/``,
then runs the four generator entry points that the WP-1 tests call IN-PROCESS
with ``--out`` redirected to a pytest ``tmp_path``, and asserts every snapshot
is unchanged.

The four generator entry points are the scripts invoked by
``tests/unit/test_wp1a_audit_acceptance.py``,
``tests/unit/test_wp1b_closure_recompute.py`` and
``tests/unit/test_wp1b_variance_substudy.py``:

1. scripts/wp1a_independent_audit.py        -> wp1a_independent_audit.json
2. scripts/wp1a_acceptance_report.py        -> wp1a_acceptance_report.json
3. scripts/wp1b_closure_recompute.py        -> wp1a_wp1b_closure_recomputation.json
                                             + wp1b_completion_cap_truncation_evidence.json
4. scripts/wp1b_variance_substudy_selection.py -> wp1b_variance_substudy_preregistration_2026-09-21.json

The scripts accept ``--out <dir>``; when given they write their NEW output(s)
into ``<dir>`` and leave every tracked path untouched. Default (human-run)
behaviour without ``--out`` is unchanged.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

TRACKED_DIRS = (
    PROJECT_DIR / "artifacts",
    PROJECT_DIR / "research" / "wp1a",
)

# wp1a_independent_audit reads the FULL-only per-case candidate_universe.json
# (excluded from the TRUE LIGHT export). Skip on a LIGHT checkout instead of
# failing; on the FULL checkout these must run and pass.
_FULL_ONLY_UNIVERSE = (
    PROJECT_DIR
    / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
    / "saleor-rc-0179b331be38" / "public" / "candidate_universe.json"
)

GENERATOR_SCRIPTS = (
    "wp1a_independent_audit.py",
    "wp1a_acceptance_report.py",
    "wp1b_closure_recompute.py",
    "wp1b_variance_substudy_selection.py",
)

# The acceptance report reads the audit output; run order matters within this
# test so the acceptance report can read the audit from the same tmp_path.
_RUN_ORDER = (
    "wp1a_independent_audit.py",
    "wp1a_acceptance_report.py",
    "wp1b_closure_recompute.py",
    "wp1b_variance_substudy_selection.py",
)


def _load_script(name: str):
    path = PROJECT_DIR / "scripts" / name
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name[:-3]] = module
    spec.loader.exec_module(module)
    return module


def _snapshot() -> dict[str, str]:
    snap: dict[str, str] = {}
    for directory in TRACKED_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                rel = path.relative_to(PROJECT_DIR).as_posix()
                snap[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snap


def _run_generator(module, name: str, out_dir: Path) -> None:
    main = getattr(module, "main", None)
    assert callable(main), f"{name} has no callable main()"
    rc = main(out_dir=out_dir)
    assert rc == 0, f"{name} main() returned nonzero exit {rc}"


def test_four_generator_entry_points_do_not_mutate_tracked_artifacts(tmp_path: Path) -> None:
    if not _FULL_ONLY_UNIVERSE.is_file():
        pytest.skip(f"requires FULL export: {_FULL_ONLY_UNIVERSE}")
    before = _snapshot()
    modules = {name: _load_script(name) for name in GENERATOR_SCRIPTS}
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in _RUN_ORDER:
        _run_generator(modules[name], name, out_dir)
    after = _snapshot()
    assert after == before, "running the WP-1 generator entry points mutated a tracked artifact"


def test_generators_write_into_tmp_path_when_out_given(tmp_path: Path) -> None:
    if not _FULL_ONLY_UNIVERSE.is_file():
        pytest.skip(f"requires FULL export: {_FULL_ONLY_UNIVERSE}")
    modules = {name: _load_script(name) for name in GENERATOR_SCRIPTS}
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in _RUN_ORDER:
        _run_generator(modules[name], name, out_dir)
    expected_files = {
        "wp1a_independent_audit.json",
        "wp1a_acceptance_report.json",
        "wp1a_wp1b_closure_recomputation.json",
        "wp1b_completion_cap_truncation_evidence.json",
        "wp1b_variance_substudy_preregistration_2026-09-21.json",
    }
    written = {p.name for p in out_dir.iterdir()}
    assert expected_files <= written, f"missing outputs: {expected_files - written}"


@pytest.mark.parametrize("name", GENERATOR_SCRIPTS)
def test_generator_script_has_main_function(name: str) -> None:
    module = _load_script(name)
    assert callable(getattr(module, "main", None))
