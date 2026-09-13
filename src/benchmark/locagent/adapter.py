"""P5-A — LocAgent shared-protocol adapter (engineering readiness).

P5-A COMPARISON-READY engineering layer. ZERO scientific LLM/API calls in this
milestone. This module adapts our RealCommitImpactDataset-v1 PUBLIC bundles to
the upstream LocAgent SWE-bench-like input format so both systems can later be
scored with ONE common evaluator on the SAME real-commit cases.

Upstream (frozen): https://github.com/gersteinlab/LocAgent
Pinned upstream commit: 4935b557326c154bad8e8dcf3747cc8d32d1f387

Adapter input mapping (per real-commit case, PARENT-ONLY):
- instance_id       -> real-commit case_id (e.g. djangocms-rc-8d50660e7bcf)
- repo              -> repository identity (djangocms / djangocms__djangocms)
- base_commit       -> parent commit SHA
- problem_statement -> normalized commit intent (visible)
- patch             -> NEVER the hidden target patch. If the upstream loader
                       requires the field syntactically, it is set to an
                       empty/non-informative value and a leakage test proves it
                       is not used to guide localization.

NEVER exposed to any LocAgent input:
- target diff / target commit file list / observed-change proxy / gold labels.

Common output conversion (later): LocAgent found_files / ranked files ->
unique predicted file set, scored by the common evaluator
(``src/benchmark/locagent/evaluator.py``).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.real_commits import p1_evaluation as p1

LOCAGENT_REPOSITORY_URL: str = "https://github.com/gersteinlab/LocAgent"
LOCAGENT_PINNED_COMMIT: str = "4935b557326c154bad8e8dcf3747cc8d32d1f387"
LOCAGENT_PINNED_DATE: str = "2026-08-12"
LOCAGENT_LICENSE: str = "Apache-2.0"
ADAPTER_VERSION: str = "locagent-shared-protocol-adapter-1"

# SWE-bench-like fields LocAgent reads from a dataset instance.
LOCAGENT_INPUT_FIELDS: tuple[str, ...] = (
    "instance_id",
    "repo",
    "base_commit",
    "problem_statement",
    "patch",
)

# Hidden-proxy markers that must NEVER appear in a LocAgent input bundle.
_HIDDEN_MARKERS: tuple[str, ...] = (
    "observed_change_set_proxy",
    "observed-change-set",
    "changed_paths",
    "change_statuses",
    "statuses",
    "target_diff",
    "target_commit_diff",
    "hidden/",
    "proxy_sha256",
    "gold",
    "gold_patch",
    "test_patch",
)


@dataclass(frozen=True)
class LocAgentInput:
    """One LocAgent SWE-bench-like instance (parent-only, leakage-free)."""

    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    patch: str = ""
    source_case_id: str = ""
    split: str = ""
    candidate_count: int = 0

    @property
    def input_sha256(self) -> str:
        return p1.sha256_json(self.to_swebench_dict())

    def to_swebench_dict(self) -> dict[str, str]:
        """Serializable LocAgent-compatible instance (patch is EMPTY)."""
        return {
            "instance_id": self.instance_id,
            "repo": self.repo,
            "base_commit": self.base_commit,
            "problem_statement": self.problem_statement,
            "patch": self.patch,
        }


@dataclass
class LocAgentAdapter:
    """Build leakage-free LocAgent inputs from real-commit public bundles."""

    dataset_dir: Path
    repo_slug: str = "djangocms__djangocms"

    def _case_dir(self, case_id: str) -> Path:
        for sub in ("scientific", "miner_dev"):
            candidate = self.dataset_dir / sub / case_id
            if candidate.is_dir():
                return candidate
        raise FileNotFoundError(f"case dir not found for {case_id}")

    def build_input(self, case_id: str) -> LocAgentInput:
        bundle = self._load_public_bundle(case_id)
        split = self._split_for(case_id)
        instance = LocAgentInput(
            instance_id=bundle["case_id"],
            repo=self.repo_slug,
            base_commit=bundle["parent_commit"],
            problem_statement=bundle["intent_text"],
            patch="",  # NEVER the hidden target patch (proved by leakage tests)
            source_case_id=case_id,
            split=split,
            candidate_count=len(bundle["candidate_paths"]),
        )
        return instance

    def _load_public_bundle(self, case_id: str) -> dict[str, Any]:
        case_dir = self._case_dir(case_id)
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        universe = json.loads(
            (case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8")
        )
        parent = intent.get("parent_commit")
        if not isinstance(parent, str) or not parent:
            parent = self._parent_from_manifest(case_dir, case_id)
        return {
            "case_id": case_id,
            "parent_commit": parent,
            "intent_text": str(intent.get("intent_text") or ""),
            "candidate_paths": [str(r["path"]) for r in universe.get("records", [])],
        }

    def _parent_from_manifest(self, case_dir: Path, case_id: str) -> str:
        del case_id  # manifest is the source; case_id kept for interface clarity
        manifest = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        record = manifest.get("record") or {}
        return str(record.get("parent_commit") or "")

    def _split_for(self, case_id: str) -> str:
        split_freeze = json.loads(
            (self.dataset_dir / "split_freeze.json").read_text(encoding="utf-8")
        )
        per_split = split_freeze.get("per_split") or {}
        for split, per in per_split.items():
            member_ids = per.get("case_ids") or []
            if case_id in member_ids:
                return str(split)
        return "MINER_DEV"

    # ------------------------------------------------------------------
    # Leakage barrier (fail-closed)
    # ------------------------------------------------------------------

    def leakage_errors(self, instance: LocAgentInput) -> list[str]:
        """Return hidden-proxy leakage markers found in a LocAgent input."""
        errors: list[str] = []
        payload = instance.to_swebench_dict()
        for marker in _HIDDEN_MARKERS:
            for field, value in payload.items():
                if marker in value:
                    errors.append(f"{field} contains marker {marker!r}")
        if instance.patch != "":
            errors.append("patch must be EMPTY/non-informative for the adapter")
        return errors

    def assert_no_leakage(self, instance: LocAgentInput) -> None:
        errors = self.leakage_errors(instance)
        if errors:
            raise AssertionError(f"LocAgent input leakage: {errors}")


def upstream_pin_check() -> dict[str, Any]:
    """Deterministic check of the frozen upstream pin metadata."""
    return {
        "repository_url": LOCAGENT_REPOSITORY_URL,
        "pinned_commit": LOCAGENT_PINNED_COMMIT,
        "pinned_date": LOCAGENT_PINNED_DATE,
        "license": LOCAGENT_LICENSE,
        "adapter_version": ADAPTER_VERSION,
        "pin_length_ok": len(LOCAGENT_PINNED_COMMIT) == 40,
        "input_fields": list(LOCAGENT_INPUT_FIELDS),
        "no_vendoring": True,
    }


def build_dryrun_manifest(
    dataset_dir: Path, case_ids: list[str]
) -> list[dict[str, Any]]:
    """Zero-API dry-run manifest: one LocAgent input per requested case."""
    adapter = LocAgentAdapter(dataset_dir)
    rows: list[dict[str, Any]] = []
    for cid in case_ids:
        instance = adapter.build_input(cid)
        adapter.assert_no_leakage(instance)
        rows.append(
            {
                "case_id": cid,
                "split": instance.split,
                "instance_id": instance.instance_id,
                "repo": instance.repo,
                "base_commit": instance.base_commit,
                "problem_statement_chars": len(instance.problem_statement),
                "patch_chars": len(instance.patch),
                "input_sha256": instance.input_sha256,
                "candidate_count": instance.candidate_count,
                "upstream_pinned_commit": LOCAGENT_PINNED_COMMIT,
                "adapter_version": ADAPTER_VERSION,
            }
        )
    return rows
