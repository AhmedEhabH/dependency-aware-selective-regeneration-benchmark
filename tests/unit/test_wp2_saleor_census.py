"""WP-2 zero-API Saleor MAIN_297 census tests.

Deterministic classifier unit tests + manifest-scope invariants. These are
ZERO-API: no Saleor test runs, no git subprocesses, no network.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.wp2_saleor_e2e_census import (  # noqa: E402
    is_config_or_infra_path,
    is_migration_path,
    is_test_path,
)

CALIBRATION_IDS = {
    "saleor-rc-349d46d906ad",
    "saleor-rc-b05633dae118",
    "saleor-rc-d52a55471bfc",
}


def _manifest_ids() -> set[str]:
    data = json.loads(
        (PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json").read_text(encoding="utf-8")
    )
    return set(data["task_ids"])


def test_manifest_has_exactly_297_unique_ids() -> None:
    ids = _manifest_ids()
    assert len(ids) == 297
    data = json.loads(
        (PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json").read_text(encoding="utf-8")
    )
    assert len(data["task_ids"]) == len(set(data["task_ids"]))


def test_manifest_excludes_calibration_ids() -> None:
    assert not (_manifest_ids() & CALIBRATION_IDS)


def test_manifest_nested_main50_first_50() -> None:
    main50 = json.loads(
        (PROJECT_DIR / "research" / "wp1b" / "wp1b_main_50_manifest.json").read_text(encoding="utf-8")
    )
    main297 = json.loads(
        (PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json").read_text(encoding="utf-8")
    )
    assert main50["task_ids"] == main297["task_ids"][:50]


def test_is_test_path_rules() -> None:
    assert is_test_path("saleor/product/tests/test_tasks.py")
    assert is_test_path("saleor/tests/fixtures.py")
    assert is_test_path("saleor/graphql/order/tests/test_fulfillment.py")
    assert not is_test_path("saleor/product/search.py")
    assert not is_test_path("saleor/core/languages.py")


def test_is_migration_path_rule() -> None:
    assert is_migration_path("saleor/product/migrations/0142_auto_20210304_1052.py")
    assert not is_migration_path("saleor/product/models.py")


def test_is_config_or_infra_path_rules() -> None:
    assert is_config_or_infra_path("pyproject.toml")
    assert is_config_or_infra_path("setup.cfg")
    assert is_config_or_infra_path("requirements.txt")
    assert is_config_or_infra_path("Dockerfile")
    assert is_config_or_infra_path(".env.example")
    assert is_config_or_infra_path(".github/workflows/test.yml")
    assert is_config_or_infra_path("manage.py")
    assert not is_config_or_infra_path("saleor/product/search.py")
    assert not is_config_or_infra_path("saleor/product/models.py")


def test_census_output_counts_reconcile() -> None:
    out = PROJECT_DIR / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    assert len(tasks) == 297
    assert len({t["task_id"] for t in tasks}) == 297
    assert all(t["status"] == "OK" for t in tasks)
    assert all(t["f2p_candidacy"] != "F2P_CONFIRMED" for t in tasks)
    s = data["summary"]["counts_by_f2p_candidacy"]
    assert sum(s.values()) == 297
    assert s.get("F2P_CONFIRMED", 0) == 0
    totals = data["summary"]["totals"]
    assert totals["n_changed"] == sum(t["n_changed"] for t in tasks)
    assert totals["n_test"] == sum(t["n_test"] for t in tasks)
    assert totals["n_test_added"] == sum(t["n_test_added"] for t in tasks)
    assert totals["n_test_modified"] == sum(t["n_test_modified"] for t in tasks)
    assert totals["n_test_deleted"] == sum(t["n_test_deleted"] for t in tasks)
    assert totals["n_migration"] == sum(t["n_migration"] for t in tasks)
    assert totals["n_config_or_infra"] == sum(t["n_config_or_infra"] for t in tasks)


def test_census_output_ids_all_in_manifest() -> None:
    manifest = _manifest_ids()
    data = json.loads(
        (PROJECT_DIR / "research" / "wp2" / "wp2_saleor_main297_census_2026-09-22.json").read_text(
            encoding="utf-8"
        )
    )
    out_ids = {t["task_id"] for t in data["tasks"]}
    assert out_ids == manifest
