#!/usr/bin/env python3
"""djangoCMS ImpactPlan-v2 PROMPT-EVIDENCE PARITY check (provenance verification only).

TASK: scientific-stagec-djangocms-impactplan-v2-01 — pre-study provenance
verification. ZERO scientific API calls.

Purpose:
1. Reconstruct + persist the FULLY RENDERED historical v1 planner prompt for
   frozen scenario ``djangocms-external-validity-004`` using the historical
   frozen v1 prompt builder (``OpenRouterImpactPlanner._prompt`` /
   ``PLANNER_PROMPT_TEMPLATE``) and the SAME frozen inputs used by the
   historical v1 diagnostic: scenario 004, the 144-path candidate universe,
   artifact descriptors, empty DependencyGraph (no graph assistance), and the
   deterministic strategy-visible evidence configuration
   (``collect_impact_evidence``).
2. Identify the already-stored FULLY RENDERED v2 scenario-004 prompt
   (``reports/scientific-stagec-djangocms-impactplan-v2-costprobe-01/v2_prompt.txt``).
3. Record SHA256 for the rendered v1 and rendered v2 prompts.
4. Extract the strategy-visible evidence block supplied to each and verify
   deterministically whether they are identical (item count + block SHA256).
5. Determine whether semantic-seed evidence was newly introduced in v2 from
   deterministic rendered inputs (NOT from model citations).

This check MUST NOT change the frozen v2 treatment. It writes only NEW
provenance evidence files under the v2 study directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.external_validity import study_runtime as wiring  # noqa: E402
from benchmark.selection import impact_planner as v1  # noqa: E402
from benchmark.selection import impact_planner_v2 as v2  # noqa: E402

STUDY_ID = "scientific-stagec-djangocms-impactplan-v2-01"
STUDY_DIR = _PROJECT_DIR / "reports" / STUDY_ID
PROVENANCE_DIR = STUDY_DIR / "provenance"
SCENARIO_ID = "djangocms-external-validity-004"
COSTPROBE_DIR = (
    _PROJECT_DIR / "reports" / "scientific-stagec-djangocms-impactplan-v2-costprobe-01"
)
STORED_V2_PROMPT = COSTPROBE_DIR / "v2_prompt.txt"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_requirement_change(scenario: Any) -> Any:
    from benchmark.core.models import RequirementChange

    return RequirementChange(
        before=scenario.requirement_before,
        after=scenario.requirement_after,
        acceptance_criteria=tuple(c.description for c in scenario.acceptance_criteria),
    )


def _build_artifact_universe() -> Any:
    from benchmark.core.models import ArtifactUniverse
    from benchmark.repositories.snapshot import resolve_allowed_artifacts

    return ArtifactUniverse(
        artifacts=resolve_allowed_artifacts(
            wiring.PINNED_REPO_ROOT,
            wiring.runtime_universe_paths(),
        )
    )


def _descriptors() -> tuple[Any, ...]:
    from benchmark.selection.dependency_scope import ArtifactDescriptor

    records = wiring.load_frozen_universe_records()
    return tuple(
        ArtifactDescriptor(
            path=str(rec["path"]),
            category="source",
            description="",
            provides_symbols=tuple(rec.get("classes", [])) + tuple(rec.get("functions", [])),
            typical_change_triggers=(),
        )
        for rec in records
    )


def _build_evidence(
    requirement_change: Any,
    artifact_universe: Any,
    descriptors: tuple[Any, ...],
) -> tuple[Any, ...]:
    from benchmark.core.models import DependencyGraph
    from benchmark.selection.impact_evidence import collect_impact_evidence

    return collect_impact_evidence(
        requirement_change,
        artifact_universe,
        descriptors,
        DependencyGraph(),
        workspace_root=wiring.PINNED_REPO_ROOT,
        extra_architecture_constraints=(),
    )


def _build_planner_input(
    requirement_change: Any,
    artifact_universe: Any,
    evidence: tuple[Any, ...],
) -> Any:
    from benchmark.selection.impact_planner import PlannerInput

    return PlannerInput(
        requirement_change=requirement_change,
        artifact_universe=artifact_universe,
        evidence=evidence,
        run_id=f"{requirement_change.after[:32]}_{wiring.PINNED_COMMIT[:8]}",
        scenario_id=requirement_change.after[:64],
        source_commit=wiring.PINNED_COMMIT,
        extra_architecture_constraints=(),
        plan_version="v1",
    )


def _render_v1_prompt(inp: Any) -> str:
    """Render the historical frozen v1 prompt via the frozen v1 builder."""
    planner = v1.OpenRouterImpactPlanner(backend=_NullBackend())
    return planner._prompt(inp)


def _render_v2_prompt(
    requirement_change: Any,
    evidence: tuple[Any, ...],
) -> str:
    mapping = v2.derive_candidate_id_map()
    return v2.build_v2_prompt(
        scenario_id=requirement_change.after[:64],
        before=requirement_change.before,
        after=requirement_change.after,
        acceptance_criteria=tuple(requirement_change.acceptance_criteria),
        architecture_constraints=(),
        mapping=mapping,
        evidence=evidence,
        prior_plan_summary=None,
    )


def _extract_evidence_block(prompt_text: str) -> str:
    """Extract the strategy-visible evidence block from a rendered prompt."""
    header = "Strategy-visible evidence"
    footer = "Validation catalog"
    start = prompt_text.find(header)
    end = prompt_text.find(footer)
    if start < 0 or end < 0:
        raise ValueError("evidence block markers not found in rendered prompt")
    return prompt_text[start:end].rstrip()


def _evidence_item_count(evidence_block: str) -> int:
    return sum(1 for line in evidence_block.splitlines() if line.strip().startswith("- ["))


class _NullBackend:
    """Minimal backend stub; only ``_prompt`` is exercised (no network)."""

    model = "null"
    model_identity = "null"

    @property
    def provider(self) -> str | None:
        return None


def run_parity() -> dict[str, Any]:
    scenario, scenario_path = wiring.load_study_scenario(SCENARIO_ID)
    requirement_change = _build_requirement_change(scenario)
    artifact_universe = _build_artifact_universe()
    descriptors = _descriptors()
    evidence = _build_evidence(requirement_change, artifact_universe, descriptors)

    inp = _build_planner_input(requirement_change, artifact_universe, evidence)
    v1_rendered = _render_v1_prompt(inp)
    v2_rendered = _render_v2_prompt(requirement_change, evidence)

    if not STORED_V2_PROMPT.is_file():
        raise FileNotFoundError(f"stored v2 rendered prompt not found: {STORED_V2_PROMPT}")
    stored_v2_text = STORED_V2_PROMPT.read_text(encoding="utf-8").replace("\r\n", "\n")

    v1_block = _extract_evidence_block(v1_rendered)
    v2_block = _extract_evidence_block(v2_rendered)
    stored_v2_block = _extract_evidence_block(stored_v2_text)

    evidence_items = tuple(
        f"[{e.evidence_id}] {e.evidence_type} {e.artifact_path} {e.direction}: {e.description}"
        for e in evidence
    )
    evidence_source = "collect_impact_evidence (deterministic, frozen v1==v2 pipeline)"

    parity: dict[str, Any] = {
        "study_id": STUDY_ID,
        "check": "PROMPT_EVIDENCE_PARITY",
        "scenario_id": SCENARIO_ID,
        "zero_scientific_calls": True,
        "rendered_v1_prompt_sha256": _sha256_text(v1_rendered),
        "rendered_v2_prompt_sha256": _sha256_text(v2_rendered),
        "stored_v2_prompt_sha256": _sha256_text(stored_v2_text),
        "v2_rendering_reproducible_from_stored": v2_rendered == stored_v2_text,
        "v1_prompt_template_hash": v2.V1_PLANNER_PROMPT_SHA256,
        "v2_prompt_template_hash": v2.V2_PLANNER_PROMPT_SHA256,
        "v1_schema_hash": v2.V1_PLANNER_SCHEMA_SHA256,
        "v2_schema_hash": v2.V2_PLANNER_SCHEMA_SHA256,
        "candidate_id_mapping_sha256": v2.derive_candidate_id_map().sha256,
        "universe_sha256": wiring.frozen_universe_canonical_hash(),
        "visible_scenario_sha256": wiring.visible_input_sha256(scenario_path),
        "evidence": {
            "source": evidence_source,
            "item_count": len(evidence_items),
            "v1_block_sha256": _sha256_text(v1_block),
            "v2_block_sha256": _sha256_text(v2_block),
            "stored_v2_block_sha256": _sha256_text(stored_v2_block),
            "v1_and_v2_blocks_identical": v1_block == v2_block,
            "v2_and_stored_v2_blocks_identical": v2_block == stored_v2_block,
            "evidence_ids": [e.evidence_id for e in evidence],
        },
        "semantic_seed_not_newly_introduced_by_v2": {
            "verified_from_deterministic_rendered_inputs": True,
            "evidence_block_identical_v1_v2": v1_block == v2_block,
            "conclusion": (
                "Scenario-004 v1 and v2 rendered inputs contain the same "
                "strategy-visible evidence block; semantic-seed evidence was "
                "not newly introduced by v2."
            )
            if v1_block == v2_block and v2_block == stored_v2_block
            else "PARITY DOES NOT HOLD",
        },
        "representation_redesign_note": (
            "v2 changes candidate representation (numeric IDs), sparse "
            "planner/output instructions, and the structured-output schema as "
            "ONE representation redesign; prompt and schema effects are NOT "
            "independently isolated."
        ),
        "prompt_token_observation_note": (
            "Historical reported prompt tokens: v1 = 2768 (16K diagnostic), "
            "v2 = 3447 (cost probe). The increase is NOT attributed solely to "
            "numeric candidate IDs."
        ),
        "ran_at": _now_iso(),
    }
    parity["passed"] = bool(
        parity["v2_rendering_reproducible_from_stored"]
        and parity["evidence"]["v1_and_v2_blocks_identical"]
        and parity["evidence"]["v2_and_stored_v2_blocks_identical"]
        and parity["semantic_seed_not_newly_introduced_by_v2"][
            "evidence_block_identical_v1_v2"
        ]
    )

    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    (PROVENANCE_DIR / "v1_rendered_prompt_scenario004.txt").write_text(
        v1_rendered, encoding="utf-8"
    )
    (PROVENANCE_DIR / "v2_rendered_prompt_scenario004.txt").write_text(
        v2_rendered, encoding="utf-8"
    )
    path = PROVENANCE_DIR / "prompt_evidence_parity.json"
    path.write_text(
        json.dumps(parity, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(json.dumps(parity, indent=2, default=str))
    print(f"persisted={path}")
    return parity


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", default=False)
    args = parser.parse_args()
    parity = run_parity()
    if args.check:
        return 0 if parity.get("passed") else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
