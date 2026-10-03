"""M17 P08 - selector firewall / static-import tests (zero network, zero Docker).

Asserts that the M17 adapter and the P01/P04 generators never open selector
prediction files and never import selector-derived scope builders.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m17_adapter as ad  # noqa: E402

M17_FILES = [
    P / "scripts/wp2_m17_adapter.py",
    P / "scripts/wp2_m17_p01_census.py",
    P / "scripts/wp2_m17_p04_qualification.py",
]

SELECTOR_PATHS = (
    "research/wp1a/sip_rmcss_per_task_predictions.json",
    "research/wp1b/main-297-2026-09-22",
    "research/wp1b/variance-15x3-2026-09-22",
    "research/stage5-v2-final/deployment_artifact.json",
)

SELECTOR_IMPORTS = ("build_arm_scopes", "sip_rmcss", "wp1b_agent_predictions")


@pytest.mark.parametrize("f", M17_FILES, ids=lambda p: p.name)
def test_no_selector_path_referenced(f: Path):
    src = f.read_text(encoding="utf-8")
    # Allow the adapter's own blocklist constant; anything else must not name them.
    lines = src.splitlines()
    in_block = False
    stripped: list[str] = []
    for line in lines:
        if "SELECTOR_BLOCKED_PATHS = (" in line:
            in_block = True
            continue
        if in_block and ")" in line:
            in_block = False
            continue
        if not in_block:
            stripped.append(line)
    joined = "\n".join(stripped)
    for s in SELECTOR_PATHS:
        assert s not in joined, f"{f.name} references {s}"


@pytest.mark.parametrize("f", M17_FILES, ids=lambda p: p.name)
def test_no_selector_import(f: Path):
    tree = ast.parse(f.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.ImportFrom, ast.Import)):
            for alias in node.names:
                assert alias.name not in SELECTOR_IMPORTS, f"{f.name} imports {alias.name}"


def test_adapter_static_guard_pass():
    src = (P / "scripts/wp2_m17_adapter.py").read_text(encoding="utf-8")
    assert ad.static_selector_guard(src) is True


def test_adapter_static_guard_rejects_usage():
    assert ad.static_selector_guard("x = load_json('research/wp1a/sip_rmcss_per_task_predictions.json')") is False
    assert ad.static_selector_guard("from benchmark.wp2.e2e.scopes import build_arm_scopes") is False


def test_p01_generator_never_opens_selector_files(tmp_path):
    # The P01 generator reads only census/selection/pertask/SUMMARY + git cache.
    src = (P / "scripts/wp2_m17_p01_census.py").read_text(encoding="utf-8")
    for s in SELECTOR_PATHS:
        assert s not in src


def test_p04_generator_never_opens_selector_files(tmp_path):
    src = (P / "scripts/wp2_m17_p04_qualification.py").read_text(encoding="utf-8")
    for s in SELECTOR_PATHS:
        assert s not in src
