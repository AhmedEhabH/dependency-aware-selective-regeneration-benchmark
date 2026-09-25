"""WP-2 DEV split V2 - deterministic salted split of DEV_TRAIN (amendment F).

Frozen before any candidate generation: the frozen ``DEV_TRAIN=120`` is split
into ``DEV_TRAIN_ENG`` (≈40) and ``DEV_TRAIN_ASSAY_HOLDOUT`` (≈80) using a
deterministic salted SHA-256 rank procedure. ``DEV_VALIDATION=30`` is separate
and untouched. INTERNAL_TEST and RESERVE are never referenced here.

This mission does NOT run generation or Smoke/Pilot on DEV (amendment F/G/K).
"""
from __future__ import annotations

import hashlib
import json

DEV_SPLIT_VERSION = "dev-split-v2-2026-09-23"
DEV_SPLIT_SALT = "wp2-dev-train-eng-v1-2026-09-23"
DEV_TRAIN_ENG_TARGET = 40
DEV_TRAIN_ASSAY_HOLDOUT_TARGET = 80


def _rank(task_id: str, salt: str = DEV_SPLIT_SALT) -> str:
    return hashlib.sha256(f"{salt}|{task_id}".encode()).hexdigest()


def split_dev_train(
    dev_train_ids: list[str],
    salt: str = DEV_SPLIT_SALT,
    eng_target: int = DEV_TRAIN_ENG_TARGET,
) -> tuple[list[str], list[str]]:
    """Deterministic split: first ``eng_target`` by salted rank -> ENG; the rest
    -> ASSAY_HOLDOUT.

    Returns (eng_ids, assay_holdout_ids), each sorted by rank. Raises
    ValueError if the input does not match the frozen DEV_TRAIN size (120).
    """
    if len(dev_train_ids) != 120:
        raise ValueError(
            f"DEV_TRAIN must be the frozen 120 tasks, got {len(dev_train_ids)}"
        )
    if len(set(dev_train_ids)) != len(dev_train_ids):
        raise ValueError("DEV_TRAIN ids must be unique")
    ordered = sorted(dev_train_ids, key=lambda t: _rank(t, salt))
    return ordered[:eng_target], ordered[eng_target:]


def build_dev_split_artifact(
    *,
    dev_train_ids: list[str],
    dev_validation_ids: list[str],
    salt: str = DEV_SPLIT_SALT,
    eng_target: int = DEV_TRAIN_ENG_TARGET,
) -> dict:
    """Build the frozen DEV split artifact with algorithm, salt, membership and
    hashes (amendment F)."""
    eng, holdout = split_dev_train(dev_train_ids, salt=salt, eng_target=eng_target)

    def role_sha(ids: list[str]) -> str:
        payload = json.dumps(sorted(ids), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    return {
        "artifact": "wp2_dev_split_v2",
        "version": DEV_SPLIT_VERSION,
        "date": "2026-09-23",
        "algorithm": f"sha256(salt|task_id) rank ascending; first {eng_target} -> ENG; rest -> ASSAY_HOLDOUT",
        "salt": salt,
        "counts": {
            "DEV_TRAIN": len(dev_train_ids),
            "DEV_TRAIN_ENG": len(eng),
            "DEV_TRAIN_ASSAY_HOLDOUT": len(holdout),
            "DEV_VALIDATION": len(dev_validation_ids),
        },
        "membership": {
            "DEV_TRAIN_ENG": sorted(eng),
            "DEV_TRAIN_ASSAY_HOLDOUT": sorted(holdout),
            "DEV_VALIDATION": sorted(dev_validation_ids),
        },
        "hashes": {
            "DEV_TRAIN_ENG_sha256": role_sha(eng),
            "DEV_TRAIN_ASSAY_HOLDOUT_sha256": role_sha(holdout),
            "DEV_VALIDATION_sha256": role_sha(dev_validation_ids),
            "all_eng_holdout_validation_sha256": role_sha(
                sorted(eng + holdout + dev_validation_ids)
            ),
        },
        "status": "FROZEN",
    }
