"""WP-2 census / evaluator-side metadata - unit tests (ZERO API).

Verifies amendment H: deterministic evaluator-side fields (added-in-target
production files, Gold-exists-at-parent hash, scope flags) computed without
modifying frozen predictions.
"""

from __future__ import annotations

from benchmark.wp2.census_metadata_v2 import (
    build_task_metadata,
    gold_existing_at_parent_hash,
    gold_files_exist_at_parent,
    parse_name_status,
    production_files_added_in_target,
    scope_flags,
)


def test_parse_name_status_plain() -> None:
    rows = parse_name_status("M\tsaleor/product/search.py\nA\tsaleor/product/tests/test_x.py\n")
    assert ("M", "saleor/product/search.py") in rows
    assert ("A", "saleor/product/tests/test_x.py") in rows


def test_parse_name_status_rename() -> None:
    rows = parse_name_status("R100\tsaleor/old.py\tsaleor/new.py\n")
    assert ("R100", "saleor/new.py") in rows


def test_production_files_added_in_target() -> None:
    rows = parse_name_status(
        "A\tsaleor/product/models.py\nA\tsaleor/product/tests/test_models.py\nM\tsaleor/product/views.py\n"
    )
    assert production_files_added_in_target(rows) == ["saleor/product/models.py"]


def test_gold_files_exist_at_parent() -> None:
    gold = ["saleor/product/models.py", "saleor/product/new_models.py"]
    parent = {"saleor/product/models.py"}
    assert gold_files_exist_at_parent(gold, parent) == ["saleor/product/models.py"]
    h = gold_existing_at_parent_hash(gold, parent)
    assert len(h) == 64


def test_scope_flags() -> None:
    flags = scope_flags([], ["saleor/a.py"])
    assert flags["rmcss_empty_scope"] is True
    assert flags["agent_empty_scope"] is False
    assert flags["scope_identical"] is False

    flags2 = scope_flags(["saleor/a.py"], ["saleor/a.py"])
    assert flags2["scope_identical"] is True

    flags3 = scope_flags([], [])
    assert flags3["rmcss_empty_scope"] is True
    assert flags3["agent_empty_scope"] is True
    assert flags3["scope_identical"] is True


def test_build_task_metadata_complete() -> None:
    rows = parse_name_status(
        "A\tsaleor/product/models.py\nM\tsaleor/product/views.py\n"
    )
    meta = build_task_metadata(
        task_id="saleor-rc-abc",
        name_status_rows=rows,
        gold_production_files=["saleor/product/models.py", "saleor/product/views.py"],
        parent_files={"saleor/product/views.py"},
        rmcss_paths=["saleor/product/views.py"],
        agent_paths=["saleor/product/views.py", "saleor/product/other.py"],
    )
    assert meta["added_in_target_absent_at_parent"] == ["saleor/product/models.py"]
    assert meta["gold_files_exist_at_parent_count"] == 1
    assert meta["rmcss_empty_scope"] is False
    assert meta["scope_identical"] is False
    assert meta["task_id"] == "saleor-rc-abc"
