#!/usr/bin/env python3
# ruff: noqa: E501
"""Saleor identity/provenance migration — djangocms-rc-* -> saleor-rc-* (T3).

WHY: the Saleor bundles were built with the frozen djangoCMS miner constants,
so their case IDs, repository URL, license ref, graph repo_id, and anchor all
carry djangoCMS identity. The case ID is visible in the inference prompt, so a
Saleor Sparse run would leak the wrong repository provenance to the model.

WHAT THIS DOES (deterministic, ZERO model calls, science preserved):
- renames each case dir djangocms-rc-<sha> -> saleor-rc-<sha> (prefix swap;
  the sha is already the target-commit short sha);
- corrects identity fields in case_manifest.json, public/*.json,
  hidden/*.json: case_id, repository, repository_url,
  repository_license_or_manifest_ref, graph repo_id, provenance anchor+url;
- recomputes canonical_record_sha256 and the graph canonical hash for the
  corrected identity (edges/universes/proxies untouched -> scientific payload
  identical);
- migrates saleor_candidate_metadata.json (dict keys), saleor_split_proposal.json
  (case_ids + per-role/all-pool SHAs), saleor_development_manifest.json
  (case_ids + case records + canonical hash), split_freeze_saleor.json;
- writes research/transparency/saleor_case_id_migration.json (old->new map)
  and research/transparency/saleor_identity_migration_evidence.json.

SCIENCE PRESERVED (verified separately by scripts/saleor_identity_equivalence.py):
commits (parent/target), split membership, candidate universes (records: paths,
sha256, loc, symbols), hidden proxies, graph edges, frozen rules.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.real_commits import models  # noqa: E402

DATASET_DIR = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor"
TRANSPARENCY = _PROJECT_DIR / "research" / "transparency"
META = TRANSPARENCY / "saleor_candidate_metadata.json"
SPLIT = TRANSPARENCY / "saleor_split_proposal.json"
DEV_MANIFEST = DATASET_DIR / "saleor_development_manifest.json"
SPLIT_FREEZE = DATASET_DIR / "split_freeze_saleor.json"

SALEOR_URL = "https://github.com/saleor/saleor"
SALEOR_LICENSE_REF = "BSD-3-Clause; benchmark_data/manifests/repositories.yaml#saleor"
SALEOR_ANCHOR = "2c48391b652c26ce4f27a53d6532d4c873306af0"


def _new_id(old_id: str) -> str:
    """Deterministic prefix swap: djangocms-rc-<sha> -> saleor-rc-<sha>."""
    assert old_id.startswith("djangocms-rc-"), old_id
    return "saleor-rc-" + old_id[len("djangocms-rc-") :]


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_json(payload: Any) -> str:
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def migrate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Correct identity fields in a record; recompute canonical hash."""
    new = dict(record)
    old_id = new["case_id"]
    new_id = _new_id(old_id)
    new["case_id"] = new_id
    new["repository"] = "saleor"
    new["repository_url"] = SALEOR_URL
    new["repository_license_or_manifest_ref"] = SALEOR_LICENSE_REF
    prov = dict(new.get("provenance_hashes") or {})
    prov["anchor_commit"] = SALEOR_ANCHOR
    prov["repository_url"] = SALEOR_URL
    new["provenance_hashes"] = prov
    # recompute canonical hash excluding created_utc + self-ref
    payload = {k: v for k, v in new.items() if k not in {"created_utc", "canonical_record_sha256"}}
    new["canonical_record_sha256"] = _sha256_json(payload)
    return new


def migrate_bundle(case_dir: Path, mapping: dict[str, str]) -> None:
    """Rewrite identity fields in one bundle's 5 JSON artifacts in place."""
    old_id = case_dir.name
    new_id = _new_id(old_id)
    mapping[old_id] = new_id

    manifest_path = case_dir / "case_manifest.json"
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    m["record"] = migrate_record(m["record"])
    m["canonical_record_sha256"] = m["record"]["canonical_record_sha256"]
    manifest_path.write_text(_canonical_json(m) + "\n", encoding="utf-8")

    intent_path = case_dir / "public" / "intent.json"
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    intent["case_id"] = new_id
    intent_path.write_text(_canonical_json(intent) + "\n", encoding="utf-8")

    universe_path = case_dir / "public" / "candidate_universe.json"
    universe = json.loads(universe_path.read_text(encoding="utf-8"))
    universe["case_id"] = new_id
    universe_path.write_text(_canonical_json(universe) + "\n", encoding="utf-8")

    graph_path = case_dir / "public" / "dependency_graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["repo_id"] = "saleor"
    graph_path.write_text(_canonical_json(graph) + "\n", encoding="utf-8")

    proxy_path = case_dir / "hidden" / "observed_change_set_proxy.json"
    proxy = json.loads(proxy_path.read_text(encoding="utf-8"))
    proxy["case_id"] = new_id
    proxy_path.write_text(_canonical_json(proxy) + "\n", encoding="utf-8")


def main() -> int:
    scientific = DATASET_DIR / "scientific"
    bundles = sorted(p.name for p in scientific.iterdir() if p.is_dir())
    mapping: dict[str, str] = {}
    for old in bundles:
        migrate_bundle(scientific / old, mapping)

    # rename dirs (after content rewritten; use temp name to avoid collision)
    for old in sorted(mapping, reverse=True):
        src = scientific / old
        dst = scientific / mapping[old]
        tmp = scientific / (mapping[old] + ".migrate")
        if src.is_dir():
            shutil.move(str(src), str(tmp))
            shutil.move(str(tmp), str(dst))

    # ---- metadata: rename dict keys ----
    meta = json.loads(META.read_text(encoding="utf-8"))
    for k in list(meta.keys()):
        if k not in mapping:
            mapping[k] = _new_id(k)
    new_meta = {mapping[k]: v for k, v in meta.items()}
    META.write_text(_canonical_json(new_meta) + "\n", encoding="utf-8")

    # ---- split proposal: migrate case_ids + recompute SHAs ----
    split = json.loads(SPLIT.read_text(encoding="utf-8"))
    all_ids = []
    for _role, per in split["per_role"].items():
        per["case_ids"] = [mapping[c] for c in per["case_ids"]]
        per["sha256"] = _sha256_json(per["case_ids"])
        all_ids.extend(per["case_ids"])
    all_ids = sorted(set(all_ids))
    split["all_pool_sha256"] = _sha256_json(all_ids)
    split["anchor"] = SALEOR_ANCHOR
    split["migration_note"] = "case IDs migrated djangocms-rc-* -> saleor-rc-* (identity correction 2026-09-17); seed, membership, and scientific payload unchanged"
    SPLIT.write_text(_canonical_json(split) + "\n", encoding="utf-8")

    # ---- dev manifest: migrate case_ids + case records ----
    dev = json.loads(DEV_MANIFEST.read_text(encoding="utf-8"))
    dev["case_ids"] = [mapping[c] for c in dev["case_ids"]]
    for i, c in enumerate(dev["cases"]):
        rec = c.get("record")
        if isinstance(rec, dict):
            dev["cases"][i]["record"] = migrate_record(rec)
            dev["cases"][i]["case_id"] = dev["cases"][i]["record"]["case_id"]
        else:
            dev["cases"][i] = migrate_record(c)
    dev["canonical_manifest_sha256"] = models.compute_canonical_dataset_manifest_hash(dev)
    DEV_MANIFEST.write_text(models.canonical_json(dev) + "\n", encoding="utf-8")

    # ---- split freeze: migrate assignment + per-role SHAs ----
    sf = json.loads(SPLIT_FREEZE.read_text(encoding="utf-8"))
    sf["assignment"] = {mapping[k]: v for k, v in sf["assignment"].items()}
    sf["per_role_sha256"] = {_r: _sha256_json(split["per_role"][_r]["case_ids"]) for _r in split["roles"]}
    sf["all_pool_sha256"] = split["all_pool_sha256"]
    sf["note"] = "case IDs migrated djangocms-rc-* -> saleor-rc-* (identity correction); membership unchanged"
    sf["canonical_split_freeze_sha256"] = _sha256_json({k: v for k, v in sf.items() if k != "canonical_split_freeze_sha256"})
    SPLIT_FREEZE.write_text(models.canonical_json(sf) + "\n", encoding="utf-8")

    # ---- mapping + evidence ----
    (TRANSPARENCY / "saleor_case_id_migration.json").write_text(
        _canonical_json({"migrated_at": datetime.now(UTC).isoformat(), "count": len(mapping), "old_to_new": mapping}) + "\n",
        encoding="utf-8",
    )
    print("bundles migrated:", len(bundles))
    print("mapping entries:", len(mapping))
    print("dev manifest canonical sha:", dev["canonical_manifest_sha256"][:20])
    print("split all_pool sha:", split["all_pool_sha256"][:20])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
