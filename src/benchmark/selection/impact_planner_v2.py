"""ImpactPlan-v2: SPARSE AUDITABLE REPRESENTATION (POST-HOC / EXPLORATORY).

v1 (``impact_planner.py``) instructs the model to classify EVERY candidate
explicitly and serialize the full repository-wide action policy (144 decision
objects). v2 is a representation redesign: the model emits ONLY non-PRESERVE
decisions (REGENERATE / VALIDATE / HUMAN_REVIEW) keyed by deterministic frozen
numeric candidate IDs (1..144), and every omitted candidate is decoded
deterministically to PRESERVE.

Design contract (IMPACTPLAN-V2):

- candidate universe V = the frozen 144 djangoCMS paths, unchanged.
- ``candidate_id -> repository_path`` is a deterministic 1..144 mapping derived
  from the frozen candidate-universe artifact (path-sorted), scenario
  independent, hidden-gold independent, persisted as an artifact with its
  SHA-256, identical for every future v2 run.
- The model emits ONLY non-PRESERVE decisions.
- The harness decodes the full policy ``pi : V -> {R, P, V, H}`` so the final
  decoded policy contains EXACTLY 144 candidate decisions, each classified
  exactly once, pairwise-disjoint, no candidate invented, no candidate lost.
- The harness rejects fail-closed on: id < 1, id > 144, unknown id, duplicate
  id, conflicting decision, unsupported action, malformed structured output,
  mapping hash mismatch, or ambiguous decoding.
- Rationale / confidence / reason_codes / evidence are retained for every
  explicitly emitted non-PRESERVE decision.
- Structured output is the EXISTING OpenRouter native JSON-schema mechanism;
  v2 supplies a v2-specific sparse schema.
- ImpactPlan-v2 changes the output representation contract AND the
  corresponding planner instruction together. It is treated as ONE
  representation redesign, NOT a schema-only or prompt-only ablation.
- NO dependency-graph assistance is injected into v2 (graph-based planning is
  a separate possible future treatment).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import (
    ArtifactRef,
    ImpactDecision,
    ImpactPlan,
    LLMResponse,
    TokenUsage,
)
from benchmark.selection.impact_planner import (
    IMPACT_PLAN_MAX_COMPLETION_TOKENS as V1_IMPACT_PLAN_MAX_COMPLETION_TOKENS,
)
from benchmark.selection.impact_planner import (
    IMPACT_PLAN_SCHEMA as V1_IMPACT_PLAN_SCHEMA,
)
from benchmark.selection.impact_planner import (
    PLANNER_PROMPT_TEMPLATE as V1_PLANNER_PROMPT_TEMPLATE,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CANDIDATE_UNIVERSE_PATH = (
    _PACKAGE_ROOT / "benchmark_data" / "external_validity" / "djangocms_5_0_0_candidate_universe.json"
)
FROZEN_CANDIDATE_UNIVERSE_COUNT = 144

PLANNER_VERSION_V2: str = "scientific-wip-impactplan-v2-planner-1"
IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS: int = 4096

V2_ALLOWED_ACTIONS: tuple[str, ...] = ("REGENERATE", "VALIDATE", "HUMAN_REVIEW")

# ---------------------------------------------------------------------------
# v2 sparse structured schema
# ---------------------------------------------------------------------------

IMPACT_PLAN_V2_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "minItems": 0,
            "maxItems": 144,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1, "maximum": 144},
                    "action": {
                        "type": "string",
                        "enum": ["REGENERATE", "VALIDATE", "HUMAN_REVIEW"],
                    },
                    "rationale": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason_codes": {"type": "array", "items": {"type": "string"}},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "source": {"type": "string"},
                                "description": {"type": "string"},
                            },
                            "required": ["source", "description"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "id", "action", "rationale", "confidence",
                    "reason_codes", "evidence",
                ],
                "additionalProperties": False,
            },
        },
        "validation_obligations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "obligation_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "target": {"type": "string"},
                    "reason": {"type": "string"},
                    "evidence_refs": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["obligation_id", "kind", "target", "reason", "evidence_refs"],
                "additionalProperties": False,
            },
        },
        "architecture_checks": {"type": "array", "items": {"type": "string"}},
        "escalation_reason": {"type": "string"},
    },
    "required": [
        "decisions", "validation_obligations",
        "architecture_checks", "escalation_reason",
    ],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# v2 planner prompt (sparse instruction)
# ---------------------------------------------------------------------------

IMPACT_PLAN_V2_PROMPT_TEMPLATE = """You are an impact planner for a software repository using a SPARSE representation.

Frozen scenario ({scenario_id}):
Requirement before:
{before}

Requirement after:
{after}

Acceptance criteria (visible, must hold in the final repository):
{acceptance_criteria}

Visible architecture constraints (non-gold, must never be violated):
{architecture_constraints}

Candidate artifacts (frozen deterministic numeric ids 1..{candidate_count}):
{candidates}

Strategy-visible evidence (you may cite these ids):
{evidence}

Validation catalog (permitted, repository-native):
{validation_catalog}

Prior plan failure summary (only during the one bounded expansion):
{prior_summary}

Output ONLY one JSON object conforming EXACTLY to this schema (no prose, no
markdown fences):

{{
  "decisions": [
    {{
      "id": <integer candidate id in [1,{candidate_count}]>,
      "action": "REGENERATE" | "VALIDATE" | "HUMAN_REVIEW",
      "rationale": "<one sentence>",
      "evidence": [{{"source": "<evidence_id or visible source>", "description": "..."}}],
      "confidence": <float in [0,1]>,
      "reason_codes": ["<short code>"]
    }}
  ],
  "validation_obligations": [
    {{
      "obligation_id": "<id>",
      "kind": "changed_requirement" | "regression" | "build" | "static" | "architecture",
      "target": "<repository-native test module or check name>",
      "reason": "<why>",
      "evidence_refs": ["<evidence_id>"]
    }}
  ],
  "architecture_checks": ["<visible architecture obligation to verify>"],
  "escalation_reason": ""
}}

Rules:
- Emit a decision ONLY for a candidate whose action is NOT PRESERVE.
- Candidates that are NOT emitted are decoded deterministically by the harness
  as PRESERVE. Every one of the {candidate_count} candidate ids is classified
  exactly once after decoding.
- REGENERATE only when an edit is justified by the visible requirement and cited
  strategy-visible evidence.
- VALIDATE when no edit is expected but the artifact is inside the validation
  boundary (cite a validation/test/architecture reason).
- HUMAN_REVIEW when evidence is insufficient, conflicting, or the scope is unsafe
  (do NOT confidently regenerate).
- NEVER emit a PRESERVE decision and NEVER emit an id outside [1,{candidate_count}].
- NEVER emit the same candidate id more than once.
- Rationale / confidence / reason_codes / evidence are required for every
  explicitly emitted non-PRESERVE decision.
- Keep validation obligations separate from artifact actions.
"""


# ---------------------------------------------------------------------------
# Hash helpers + v1/v2 prompt & schema identity
# ---------------------------------------------------------------------------


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_text(canonical)


V1_PLANNER_PROMPT_SHA256: str = sha256_text(V1_PLANNER_PROMPT_TEMPLATE)
V1_PLANNER_SCHEMA_SHA256: str = sha256_json(V1_IMPACT_PLAN_SCHEMA)
V2_PLANNER_PROMPT_SHA256: str = sha256_text(IMPACT_PLAN_V2_PROMPT_TEMPLATE)
V2_PLANNER_SCHEMA_SHA256: str = sha256_json(IMPACT_PLAN_V2_SCHEMA)


def impact_plan_v2_identity() -> dict[str, str]:
    """Persistable v1+v2 prompt/schema hashes (evidence provenance)."""
    return {
        "v1_planner_prompt_sha256": V1_PLANNER_PROMPT_SHA256,
        "v1_planner_schema_sha256": V1_PLANNER_SCHEMA_SHA256,
        "v1_default_cap": str(V1_IMPACT_PLAN_MAX_COMPLETION_TOKENS),
        "v2_planner_prompt_sha256": V2_PLANNER_PROMPT_SHA256,
        "v2_planner_schema_sha256": V2_PLANNER_SCHEMA_SHA256,
        "v2_completion_cap": str(IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS),
    }


# ---------------------------------------------------------------------------
# Frozen deterministic candidate ID mapping (1..144)
# ---------------------------------------------------------------------------

V2_CANDIDATE_ID_MAP_ARTIFACT = (
    CANDIDATE_UNIVERSE_PATH.parent / "impactplan_v2_candidate_id_map.json"
)


def load_frozen_universe_records() -> list[dict[str, Any]]:
    """Load the frozen candidate universe records (single source of truth)."""
    if not CANDIDATE_UNIVERSE_PATH.is_file():
        raise FileNotFoundError(
            f"candidate universe not found: {CANDIDATE_UNIVERSE_PATH}"
        )
    with CANDIDATE_UNIVERSE_PATH.open(encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        raise ValueError("candidate universe JSON must be a list of records")
    if len(records) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise ValueError(
            f"candidate universe has {len(records)} records, expected "
            f"{FROZEN_CANDIDATE_UNIVERSE_COUNT}"
        )
    return records


@dataclass(frozen=True)
class CandidateIDMap:
    id_to_path: tuple[tuple[int, str], ...]
    path_to_id: tuple[tuple[str, int], ...]
    sha256: str
    universe_canonical_sha256: str

    def __post_init__(self) -> None:
        if len(self.id_to_path) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
            raise ValueError(
                f"candidate ID map has {len(self.id_to_path)} entries, "
                f"expected {FROZEN_CANDIDATE_UNIVERSE_COUNT}"
            )
        ids = [i for i, _ in self.id_to_path]
        if ids != list(range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1)):
            raise ValueError("candidate ID map ids must be exactly 1..144 in order")
        paths = [p for _, p in self.id_to_path]
        if len(set(paths)) != len(paths):
            raise ValueError("candidate ID map contains duplicate paths")

    def path_for(self, candidate_id: int) -> str:
        for i, p in self.id_to_path:
            if i == candidate_id:
                return p
        raise KeyError(f"candidate id {candidate_id} not in frozen mapping")

    def id_for(self, path: str) -> int:
        for p, i in self.path_to_id:
            if p == path:
                return i
        raise KeyError(f"path {path!r} not in frozen mapping")

    def paths(self) -> tuple[str, ...]:
        return tuple(p for _, p in self.id_to_path)


def build_candidate_id_map(
    records: list[dict[str, Any]],
) -> CandidateIDMap:
    """Deterministic 1..144 mapping, path-sorted, scenario/gold independent."""
    paths = sorted(str(rec["path"]) for rec in records)
    if len(paths) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise ValueError(
            f"candidate universe has {len(paths)} records, expected "
            f"{FROZEN_CANDIDATE_UNIVERSE_COUNT}"
        )
    id_to_path = tuple((idx + 1, path) for idx, path in enumerate(paths))
    path_to_id = tuple((path, idx + 1) for idx, path in enumerate(paths))
    canonical = json.dumps(
        [{"id": i, "path": p} for i, p in id_to_path],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    universe_canonical = json.dumps(
        records, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return CandidateIDMap(
        id_to_path=id_to_path,
        path_to_id=path_to_id,
        sha256=sha256_text(canonical),
        universe_canonical_sha256=sha256_text(universe_canonical),
    )


def derive_candidate_id_map() -> CandidateIDMap:
    return build_candidate_id_map(load_frozen_universe_records())


def load_candidate_id_map_artifact() -> dict[str, Any]:
    if not V2_CANDIDATE_ID_MAP_ARTIFACT.is_file():
        raise FileNotFoundError(f"v2 candidate ID map artifact not found: {V2_CANDIDATE_ID_MAP_ARTIFACT}")
    with V2_CANDIDATE_ID_MAP_ARTIFACT.open(encoding="utf-8") as f:
        payload: Any = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError("v2 candidate ID map artifact must be a JSON object")
    return payload


def verify_candidate_id_map_artifact() -> dict[str, Any]:
    """Fail-closed check that the persisted artifact == deterministic mapping."""
    errors: list[str] = []
    artifact = load_candidate_id_map_artifact()
    derived = derive_candidate_id_map()
    entries = artifact.get("mapping")
    if not isinstance(entries, list) or len(entries) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        errors.append(f"artifact mapping must have {FROZEN_CANDIDATE_UNIVERSE_COUNT} entries")
    else:
        artifact_pairs = tuple((int(e["id"]), str(e["path"])) for e in entries)
        if artifact_pairs != derived.id_to_path:
            errors.append("artifact mapping != deterministic derived mapping")
    if artifact.get("mapping_sha256") != derived.sha256:
        errors.append("artifact mapping_sha256 mismatch")
    if artifact.get("universe_canonical_sha256") != derived.universe_canonical_sha256:
        errors.append("artifact universe hash mismatch")
    return {
        "artifact_path": str(V2_CANDIDATE_ID_MAP_ARTIFACT),
        "entry_count": len(entries) if isinstance(entries, list) else None,
        "derived_sha256": derived.sha256,
        "artifact_sha256": artifact.get("mapping_sha256"),
        "universe_sha256": derived.universe_canonical_sha256,
        "passed": not errors,
        "errors": errors,
    }


# ---------------------------------------------------------------------------
# Fail-closed sparse decode
# ---------------------------------------------------------------------------

_V2_ACTION_TO_KIND: dict[str, ActionKind] = {
    "REGENERATE": ActionKind.regenerate,
    "VALIDATE": ActionKind.validate_only,
    "HUMAN_REVIEW": ActionKind.human_review,
}


class ImpactPlanV2Error(RuntimeError):
    """Raised when a v2 sparse output cannot be decoded fail-closed."""


@dataclass(frozen=True)
class DecodedV2Policy:
    action_by_id: tuple[tuple[int, ActionKind], ...]
    decoded_preserve_ids: tuple[int, ...]
    emitted_decision_count: int
    invalid_ids: tuple[int, ...]
    duplicate_ids: tuple[int, ...]
    conflicts: tuple[str, ...]

    def action_for(self, candidate_id: int) -> ActionKind:
        for i, a in self.action_by_id:
            if i == candidate_id:
                return a
        raise KeyError(candidate_id)


def _raw_decision_items(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(parsed, dict):
        raise ImpactPlanV2Error("malformed structured output: not a JSON object")
    raw = parsed.get("decisions")
    if raw is None:
        raise ImpactPlanV2Error("malformed structured output: missing 'decisions'")
    if not isinstance(raw, list):
        raise ImpactPlanV2Error("malformed structured output: 'decisions' is not a list")
    items: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ImpactPlanV2Error("malformed structured output: decision item is not an object")
        items.append(item)
    return items


def decode_v2_policy(
    parsed: dict[str, Any],
    mapping: CandidateIDMap,
    candidate_paths: tuple[str, ...],
) -> DecodedV2Policy:
    """Deterministic fail-closed sparse decode: omitted candidate => PRESERVE.

    Raises :class:`ImpactPlanV2Error` on any representation violation (id out of
    range, unknown id, duplicate, conflicting decision, unsupported action,
    malformed item, ambiguous decoding).
    """
    items = _raw_decision_items(parsed)
    id_actions: dict[int, ActionKind] = {}
    invalid: list[int] = []
    duplicates: list[int] = []
    conflicts: list[str] = []

    for idx, item in enumerate(items):
        try:
            raw_id = item.get("id")
        except AttributeError as exc:  # pragma: no cover - defensive
            raise ImpactPlanV2Error("malformed structured output: decision item has no 'id'") from exc
        if not isinstance(raw_id, int) or isinstance(raw_id, bool):
            raise ImpactPlanV2Error(
                f"malformed structured output: decision id must be an integer (index {idx})"
            )
        action_str = str(item.get("action") or "").strip().upper()
        if action_str not in V2_ALLOWED_ACTIONS:
            raise ImpactPlanV2Error(f"unsupported action {action_str!r} (index {idx})")
        if raw_id < 1:
            invalid.append(raw_id)
            continue
        if raw_id > FROZEN_CANDIDATE_UNIVERSE_COUNT:
            invalid.append(raw_id)
            continue
        try:
            mapping.path_for(raw_id)
        except KeyError:
            invalid.append(raw_id)
            continue
        action = _V2_ACTION_TO_KIND[action_str]
        if raw_id in id_actions:
            duplicates.append(raw_id)
            if id_actions[raw_id] != action:
                conflicts.append(
                    f"id {raw_id}: {id_actions[raw_id].value} vs {action.value}"
                )
            continue
        id_actions[raw_id] = action

    if invalid:
        raise ImpactPlanV2Error(f"invalid candidate ids: {sorted(set(invalid))}")
    if conflicts:
        raise ImpactPlanV2Error(f"conflicting decisions: {sorted(set(conflicts))}")
    if duplicates:
        raise ImpactPlanV2Error(f"duplicate candidate ids: {sorted(set(duplicates))}")

    if len(id_actions) > len(candidate_paths):
        raise ImpactPlanV2Error("decoded policy larger than candidate universe (ambiguous)")

    decoded = sorted(id_actions.keys())
    preserved = [i for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1) if i not in id_actions]
    full: list[tuple[int, ActionKind]] = []
    for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1):
        full.append((i, id_actions.get(i, ActionKind.preserve)))
    if len(full) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise ImpactPlanV2Error("decoded policy must contain exactly 144 candidate decisions")
    return DecodedV2Policy(
        action_by_id=tuple(full),
        decoded_preserve_ids=tuple(preserved),
        emitted_decision_count=len(decoded),
        invalid_ids=tuple(sorted(set(invalid))),
        duplicate_ids=tuple(sorted(set(duplicates))),
        conflicts=tuple(sorted(set(conflicts))),
    )


# ---------------------------------------------------------------------------
# ImpactPlan reconstruction (reuses v1 invariant gate)
# ---------------------------------------------------------------------------


def _decision_detail(
    items: list[dict[str, Any]],
    candidate_id: int,
    *,
    field: str,
    default: Any,
) -> Any:
    for item in items:
        if int(item.get("id", -1)) == candidate_id:
            return item.get(field, default)
    return default


def impact_plan_v2_from_json(
    parsed: dict[str, Any],
    *,
    mapping: CandidateIDMap,
    run_id: str,
    scenario_id: str,
    source_commit: str,
    parent_plan_hash: str | None = None,
    token_usage: TokenUsage | None = None,
    model_calls: int = 0,
    latency_seconds: float = 0.0,
) -> ImpactPlan:
    """Build the full 144-decision ImpactPlan from the sparse v2 output."""
    items = _raw_decision_items(parsed)
    policy = decode_v2_policy(parsed, mapping, mapping.paths())

    path_for = mapping.path_for

    decisions: list[ImpactDecision] = []
    for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1):
        action = policy.action_for(i)
        path = path_for(i)
        evidence_raw = _decision_detail(items, i, field="evidence", default=[])
        from benchmark.core.models import SupportingEvidence

        evidence = tuple(
            SupportingEvidence(
                description=str(ev.get("description") or ev.get("source") or "evidence"),
                source=str(ev.get("source") or "planner_v2"),
            )
            for ev in (evidence_raw if isinstance(evidence_raw, list) else [])
            if isinstance(ev, dict)
        )
        conf_raw = _decision_detail(items, i, field="confidence", default=None)
        if isinstance(conf_raw, (int, float)) and not isinstance(conf_raw, bool):
            confidence = max(0.0, min(1.0, float(conf_raw)))
        else:
            confidence = 0.6
        decisions.append(
            ImpactDecision(
                artifact=ArtifactRef(path=path, artifact_type=ArtifactType.source),
                action=action,
                rationale=str(
                    _decision_detail(items, i, field="rationale", default="planner v2 decision")
                ),
                supporting_evidence=evidence,
                confidence=confidence,
                reason_codes=tuple(
                    str(x)
                    for x in (_decision_detail(items, i, field="reason_codes", default=[]) or [])
                ),
            )
        )

    from benchmark.selection.impact_planner import compute_plan_hash

    raw_obligations = parsed.get("validation_obligations", [])
    from benchmark.core.models import ValidationObligation

    obligations: list[ValidationObligation] = []
    if isinstance(raw_obligations, list):
        for idx, ob in enumerate(raw_obligations):
            if isinstance(ob, dict):
                obligations.append(
                    ValidationObligation(
                        obligation_id=str(ob.get("obligation_id") or f"obligation-{idx}"),
                        kind=str(ob.get("kind") or "regression"),
                        target=str(ob.get("target") or ""),
                        reason=str(ob.get("reason") or ""),
                        evidence_refs=tuple(str(x) for x in (ob.get("evidence_refs") or [])),
                    )
                )

    plan = ImpactPlan(
        run_id=run_id,
        scenario_id=scenario_id,
        source_commit=source_commit,
        planner_version=PLANNER_VERSION_V2,
        plan_version="v2",
        parent_plan_hash=parent_plan_hash,
        decisions=tuple(decisions),
        context_set=(),
        validation_obligations=tuple(obligations),
        architecture_checks=tuple(str(x) for x in (parsed.get("architecture_checks") or [])),
        escalation_reason=str(parsed.get("escalation_reason") or ""),
        planner_token_usage=token_usage,
        planner_model_calls=model_calls,
        planner_latency_seconds=latency_seconds,
    )
    return ImpactPlan(**{**plan.__dict__, "plan_hash": compute_plan_hash(plan)})


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def build_v2_prompt(
    *,
    scenario_id: str,
    before: str,
    after: str,
    acceptance_criteria: tuple[str, ...],
    architecture_constraints: tuple[str, ...],
    mapping: CandidateIDMap,
    evidence: tuple[Any, ...] = (),
    prior_plan_summary: str | None = None,
) -> str:
    candidates = "\n".join(f"- {i}. {p}" for i, p in mapping.id_to_path)
    return IMPACT_PLAN_V2_PROMPT_TEMPLATE.format(
        scenario_id=scenario_id,
        before=before,
        after=after,
        acceptance_criteria=(
            "\n".join(f"- {c}" for c in acceptance_criteria) or "- (none declared)"
        ),
        architecture_constraints=(
            "\n".join(f"- {c}" for c in architecture_constraints) or "- (none declared)"
        ),
        candidate_count=FROZEN_CANDIDATE_UNIVERSE_COUNT,
        candidates=candidates,
        evidence="\n".join(
            f"- [{e.evidence_id}] {e.evidence_type} {e.artifact_path} {e.direction}: {e.description}"
            for e in evidence
        ) or "- (none)",
        validation_catalog="- (permitted repository-native test modules only)",
        prior_summary=prior_plan_summary or "- (none)",
    )


# ---------------------------------------------------------------------------
# Planners
# ---------------------------------------------------------------------------


class MockImpactPlannerV2:
    """Deterministic sparse planner for tests/dry-runs (no model calls)."""

    def __init__(
        self,
        r_paths: frozenset[str] = frozenset(),
        v_paths: frozenset[str] = frozenset(),
        h_paths: frozenset[str] = frozenset(),
    ) -> None:
        if not r_paths.isdisjoint(v_paths):
            raise ValueError("r_paths and v_paths must be disjoint")
        if not r_paths.isdisjoint(h_paths):
            raise ValueError("r_paths and h_paths must be disjoint")
        if not v_paths.isdisjoint(h_paths):
            raise ValueError("v_paths and h_paths must be disjoint")
        self._r_paths = frozenset(r_paths)
        self._v_paths = frozenset(v_paths)
        self._h_paths = frozenset(h_paths)
        self._token_usage = TokenUsage(0, 0, 0)
        self._model_calls = 0
        self._latency = 0.0
        self._raw_response_hashes: list[str] = []
        self._last_finish_reason = ""
        self._last_prompt: str = ""

    @property
    def last_prompt(self) -> str:
        return self._last_prompt

    @property
    def token_usage(self) -> TokenUsage:
        return self._token_usage

    @property
    def model_calls(self) -> int:
        return self._model_calls

    @property
    def latency_seconds(self) -> float:
        return self._latency

    @property
    def raw_response_hashes(self) -> list[str]:
        return list(self._raw_response_hashes)

    @property
    def last_finish_reason(self) -> str:
        return self._last_finish_reason

    def plan(self, inp: Any) -> ImpactPlan:
        mapping = derive_candidate_id_map()
        parsed_items: list[dict[str, Any]] = []
        for path, action in (
            *((p, ActionKind.regenerate) for p in sorted(self._r_paths)),
            *((p, ActionKind.validate_only) for p in sorted(self._v_paths)),
            *((p, ActionKind.human_review) for p in sorted(self._h_paths)),
        ):
            parsed_items.append(
                {
                    "id": mapping.id_for(path),
                    "action": {
                        ActionKind.regenerate: "REGENERATE",
                        ActionKind.validate_only: "VALIDATE",
                        ActionKind.human_review: "HUMAN_REVIEW",
                    }[action],
                    "rationale": f"mock planner v2: {action.value}",
                    "confidence": 0.9,
                    "reason_codes": ["mock_v2"],
                    "evidence": [
                        {"source": "mock_planner_v2_deterministic", "description": f"mock v2 {action.value}"}
                    ],
                }
            )
        parsed = {
            "decisions": parsed_items,
            "validation_obligations": [],
            "architecture_checks": list(getattr(inp, "extra_architecture_constraints", ()) or ()),
            "escalation_reason": "",
        }
        return impact_plan_v2_from_json(
            parsed,
            mapping=mapping,
            run_id=inp.run_id,
            scenario_id=inp.scenario_id,
            source_commit=inp.source_commit,
            parent_plan_hash=getattr(inp, "parent_plan_hash", None),
            token_usage=self._token_usage,
            model_calls=self._model_calls,
            latency_seconds=self._latency,
        )


class OpenRouterImpactPlannerV2:
    """Structured sparse v2 planner through the existing OpenRouter backend."""

    def __init__(self, backend: Any) -> None:
        self._backend = backend
        self._token_usage = TokenUsage(0, 0, 0)
        self._model_calls = 0
        self._latency = 0.0
        self._raw_response_hashes: list[str] = []
        self._last_finish_reason: str = ""
        self._last_prompt: str = ""

    @property
    def last_prompt(self) -> str:
        return self._last_prompt

    @property
    def token_usage(self) -> TokenUsage:
        return self._token_usage

    @property
    def model_calls(self) -> int:
        return self._model_calls

    @property
    def latency_seconds(self) -> float:
        return self._latency

    @property
    def raw_response_hashes(self) -> list[str]:
        return list(self._raw_response_hashes)

    @property
    def last_finish_reason(self) -> str:
        return self._last_finish_reason

    def _prompt(self, inp: Any) -> str:
        return build_v2_prompt(
            scenario_id=inp.scenario_id,
            before=inp.requirement_change.before,
            after=inp.requirement_change.after,
            acceptance_criteria=tuple(inp.requirement_change.acceptance_criteria),
            architecture_constraints=tuple(getattr(inp, "extra_architecture_constraints", ()) or ()),
            mapping=derive_candidate_id_map(),
            evidence=tuple(inp.evidence),
            prior_plan_summary=getattr(inp, "prior_plan_summary", None),
        )

    def plan(self, inp: Any) -> ImpactPlan:
        import time

        prompt = self._prompt(inp)
        self._last_prompt = prompt
        start = time.monotonic()
        response, native_structured = _generate_v2(self._backend, prompt)
        elapsed = time.monotonic() - start
        self._model_calls += 1
        tu = response.token_usage
        self._last_finish_reason = response.finish_reason or ""
        if getattr(response, "text", ""):
            self._raw_response_hashes.append(
                hashlib.sha256(response.text.encode("utf-8")).hexdigest()
            )
        if tu:
            self._token_usage = TokenUsage(
                prompt_tokens=self._token_usage.prompt_tokens + tu.prompt_tokens,
                completion_tokens=self._token_usage.completion_tokens + tu.completion_tokens,
                total_tokens=self._token_usage.total_tokens + tu.total_tokens,
            )
        self._latency += elapsed

        parsed: dict[str, Any]
        try:
            if native_structured:
                parsed_raw: Any = json.loads(response.text)
                if not isinstance(parsed_raw, dict):
                    raise ValueError("structured planner v2 response is not an object")
                parsed = parsed_raw
            else:
                from benchmark.selection.impact_planner import _extract_json_object

                parsed = _extract_json_object(response.text)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ImpactPlanV2Error(
                f"planner v2 response not JSON (finish_reason={response.finish_reason or 'unknown'}): {exc}"
            ) from exc
        if response.finish_reason == "length":
            raise ImpactPlanV2Error(
                "planner v2 response truncated: finish_reason=length; "
                f"configured_completion_cap={IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS}"
            )

        return impact_plan_v2_from_json(
            parsed,
            mapping=derive_candidate_id_map(),
            run_id=inp.run_id,
            scenario_id=inp.scenario_id,
            source_commit=inp.source_commit,
            parent_plan_hash=getattr(inp, "parent_plan_hash", None),
            token_usage=self._token_usage,
            model_calls=self._model_calls,
            latency_seconds=self._latency,
        )


def _generate_v2(backend: Any, prompt: str) -> tuple[LLMResponse, bool]:
    import asyncio

    native_structured = callable(getattr(backend, "generate_structured", None))

    async def _run() -> LLMResponse:
        if native_structured:
            resp: Any = await backend.generate_structured(
                prompt=prompt,
                schema_name="impact_plan_v2",
                schema=IMPACT_PLAN_V2_SCHEMA,
                temperature=0.0,
                max_tokens=IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS,
            )
        else:
            resp = await backend.generate(
                prompt=prompt,
                temperature=0.0,
                max_tokens=IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS,
            )
        assert isinstance(resp, LLMResponse)
        return resp

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_run())
    assert isinstance(result, LLMResponse)
    return result, native_structured
