"""WP-2 DEV split V2 - unit tests (ZERO API).

Verifies amendment F: deterministic salted split of frozen DEV_TRAIN=120 into
DEV_TRAIN_ENG=40 / DEV_TRAIN_ASSAY_HOLDOUT=80, DEV_VALIDATION untouched, and
freeze artifact hashes.
"""

from __future__ import annotations

import pytest

from benchmark.wp2.dev_split_v2 import (
    DEV_SPLIT_SALT,
    build_dev_split_artifact,
    split_dev_train,
)


def _dev_train_ids(n: int = 120) -> list[str]:
    return [f"saleor-rc-{i:012x}" for i in range(n)]


def test_split_dev_train_40_80() -> None:
    eng, holdout = split_dev_train(_dev_train_ids())
    assert len(eng) == 40
    assert len(holdout) == 80
    assert set(eng).isdisjoint(holdout)


def test_split_dev_train_deterministic() -> None:
    a = split_dev_train(_dev_train_ids())
    b = split_dev_train(_dev_train_ids())
    assert a == b


def test_split_changes_with_salt() -> None:
    eng1, _ = split_dev_train(_dev_train_ids())
    eng2, _ = split_dev_train(_dev_train_ids(), salt="other-salt")
    assert eng1 != eng2


def test_split_requires_frozen_120() -> None:
    with pytest.raises(ValueError, match="120"):
        split_dev_train(_dev_train_ids(119))


def test_split_requires_unique() -> None:
    with pytest.raises(ValueError, match="unique"):
        split_dev_train([f"saleor-rc-{i:012x}" for i in range(60)] * 2)


def test_build_dev_split_artifact_frozen_fields() -> None:
    dev_val = [f"saleor-rc-v{i:012x}" for i in range(30)]
    art = build_dev_split_artifact(dev_train_ids=_dev_train_ids(), dev_validation_ids=dev_val)
    assert art["counts"]["DEV_TRAIN_ENG"] == 40
    assert art["counts"]["DEV_TRAIN_ASSAY_HOLDOUT"] == 80
    assert art["counts"]["DEV_VALIDATION"] == 30
    assert art["salt"] == DEV_SPLIT_SALT
    assert len(art["hashes"]["DEV_TRAIN_ENG_sha256"]) == 64
    # membership disjointness
    eng = set(art["membership"]["DEV_TRAIN_ENG"])
    hold = set(art["membership"]["DEV_TRAIN_ASSAY_HOLDOUT"])
    val = set(art["membership"]["DEV_VALIDATION"])
    assert eng.isdisjoint(hold) and eng.isdisjoint(val) and hold.isdisjoint(val)


def test_build_dev_split_artifact_deterministic() -> None:
    dev_val = [f"saleor-rc-v{i:012x}" for i in range(30)]
    a = build_dev_split_artifact(dev_train_ids=_dev_train_ids(), dev_validation_ids=dev_val)
    b = build_dev_split_artifact(dev_train_ids=_dev_train_ids(), dev_validation_ids=dev_val)
    assert a == b
