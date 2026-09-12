"""Controlled encoding ablation core (M1): FULL-v2 vs SPARSE-v2 serialization.

STUDY_ID: scientific-djangocms-controlled-encoding-ablation-01

One common v2-derived ablation schema shared by BOTH arms. The ONLY intended
treatment difference is the SERIALIZATION_POLICY block:

- FULL-v2 policy:  emit exactly one decision for EVERY candidate id (1..144),
  including explicit PRESERVE decisions.
- SPARSE-v2 policy: emit only non-PRESERVE decisions; every omitted id is
  deterministically decoded as PRESERVE (Preserve-by-Omission).

Everything else (model, provider, scenario text, candidate universe, candidate
ordering, candidate ids, repository evidence, common JSON schema, action
vocabulary, reason-code vocabulary, evidence fields, temperature, completion
cap, Graph OFF, scoring logic) is identical between the arms.

Contract highlights:

- ``COMMON_ABLATION_SCHEMA`` allows a variable-length ``decisions`` array
  (0..144 items) and does NOT force Full or Sparse behavior.
- ``build_ablation_prompt`` renders a prompt whose only arm-dependent section
  is the ``[[SERIALIZATION_POLICY]] ... [[/SERIALIZATION_POLICY]]`` block;
  ``strip_serialization_policy`` removes that block so the prompt-control
  proof can compare the two arms byte-for-byte.
- ``encode_full_policy`` / ``encode_sparse_policy`` convert a complete policy
  into each representation; ``decode_full_policy`` / ``decode_sparse_policy``
  convert a model output back into the canonical 144-candidate complete policy.
  Representation equivalence: ``decode_sparse(encode_sparse(pi)) == pi`` for
  complete policies (this is REPRESENTATION EQUIVALENCE, NOT model correctness).
- ``validate_full_v2`` / ``validate_sparse_v2`` implement the arm-specific
  semantic validators.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from benchmark.core.enums import ActionKind
from benchmark.selection.impact_planner_v2 import (
    CandidateIDMap,
    derive_candidate_id_map,
)

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CANDIDATE_UNIVERSE_PATH = (
    _PACKAGE_ROOT
    / "benchmark_data"
    / "external_validity"
    / "djangocms_5_0_0_candidate_universe.json"
)
FROZEN_CANDIDATE_UNIVERSE_COUNT = 144

ABLATION_PLANNER_VERSION: str = "scientific-djangocms-controlled-encoding-ablation-planner-1"
ABLATION_MAX_COMPLETION_TOKENS: int = 4096

# Common action vocabulary (identical for both arms).
ABLATION_ACTION_VOCAB: tuple[str, ...] = (
    "PRESERVE",
    "REGENERATE",
    "VALIDATE",
    "HUMAN_REVIEW",
)
ABLATION_NON_PRESERVE_ACTIONS: tuple[str, ...] = (
    "REGENERATE",
    "VALIDATE",
    "HUMAN_REVIEW",
)

# Frozen reason-code vocabulary (identical for both arms).
ABLATION_REASON_CODES: tuple[str, ...] = (
    "requirement_change",
    "regression",
    "build",
    "static",
    "architecture",
    "test",
    "evidence_conflict",
    "scope_unsafe",
    "no_change",
)

_ACTION_TO_KIND: dict[str, ActionKind] = {
    "PRESERVE": ActionKind.preserve,
    "REGENERATE": ActionKind.regenerate,
    "VALIDATE": ActionKind.validate_only,
    "HUMAN_REVIEW": ActionKind.human_review,
}

# ---------------------------------------------------------------------------
# The ONE common v2-derived ablation schema
# ---------------------------------------------------------------------------

COMMON_ABLATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "decisions": {
            "type": "array",
            "minItems": 0,
            "maxItems": FROZEN_CANDIDATE_UNIVERSE_COUNT,
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1, "maximum": FROZEN_CANDIDATE_UNIVERSE_COUNT},
                    "action": {"type": "string", "enum": list(ABLATION_ACTION_VOCAB)},
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
# Serialization policy blocks (the ONLY intended treatment difference)
# ---------------------------------------------------------------------------

SERIALIZATION_POLICY_FULL: str = """FULL SERIALIZATION POLICY:
- Emit EXACTLY ONE decision for EVERY candidate id in [1, {candidate_count}], including an explicit "PRESERVE" decision for every candidate that should not be regenerated.
- The output MUST contain exactly {candidate_count} decision objects, one per candidate id, each id used exactly once.
- Do NOT omit any candidate id and do NOT invent any id outside [1, {candidate_count}].
"""

SERIALIZATION_POLICY_SPARSE: str = """SPARSE SERIALIZATION POLICY (PRESERVE-BY-OMISSION):
- Emit a decision ONLY for a candidate whose action is NOT "PRESERVE".
- NEVER emit a "PRESERVE" decision.
- Candidate ids that are NOT emitted are deterministically decoded by the harness as "PRESERVE".
- After decoding, every one of the {candidate_count} candidate ids is classified exactly once.
- Never emit an id outside [1, {candidate_count}] and never repeat an id.
"""

_POLICY_OPEN = "[[SERIALIZATION_POLICY]]"
_POLICY_CLOSE = "[[/SERIALIZATION_POLICY]]"

# ---------------------------------------------------------------------------
# Common prompt template (only the serialization-policy block is arm-dependent)
# ---------------------------------------------------------------------------

COMMON_ABLATION_PROMPT_TEMPLATE = """You are an impact planner for a software repository using a common structured policy representation.

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

Action vocabulary (identical for every policy representation):
- PRESERVE: no action; keep the candidate unchanged.
- REGENERATE: candidate requires an edit justified by the visible requirement and cited evidence.
- VALIDATE: no edit expected but the candidate is inside the validation boundary (cite a validation/architecture reason).
- HUMAN_REVIEW: evidence is insufficient, conflicting, or the scope is unsafe (do NOT confidently regenerate).

Reason-code vocabulary (identical for every policy representation):
{reason_codes}

Output ONLY one JSON object conforming EXACTLY to this schema (no prose, no markdown fences):

{{
  "decisions": [
    {{
      "id": <integer candidate id in [1,{candidate_count}]>,
      "action": "PRESERVE" | "REGENERATE" | "VALIDATE" | "HUMAN_REVIEW",
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

[[SERIALIZATION_POLICY]]
{serialization_policy}
[[/SERIALIZATION_POLICY]]
"""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_text(canonical)


# Frozen identity hashes.
COMMON_SCHEMA_SHA256: str = sha256_json(COMMON_ABLATION_SCHEMA)
COMMON_TEMPLATE_SHA256: str = sha256_text(COMMON_ABLATION_PROMPT_TEMPLATE)
FULL_POLICY_TEMPLATE_SHA256: str = sha256_text(SERIALIZATION_POLICY_FULL)
SPARSE_POLICY_TEMPLATE_SHA256: str = sha256_text(SERIALIZATION_POLICY_SPARSE)
REASON_CODES_SHA256: str = sha256_json(list(ABLATION_REASON_CODES))


def common_ablation_identity() -> dict[str, str]:
    """Persistable identity block (hashes) for provenance."""
    return {
        "common_schema_sha256": COMMON_SCHEMA_SHA256,
        "common_template_sha256": COMMON_TEMPLATE_SHA256,
        "full_policy_template_sha256": FULL_POLICY_TEMPLATE_SHA256,
        "sparse_policy_template_sha256": SPARSE_POLICY_TEMPLATE_SHA256,
        "reason_codes_sha256": REASON_CODES_SHA256,
        "action_vocab": list(ABLATION_ACTION_VOCAB),
        "non_preserve_actions": list(ABLATION_NON_PRESERVE_ACTIONS),
        "candidate_count": str(FROZEN_CANDIDATE_UNIVERSE_COUNT),
        "completion_cap": str(ABLATION_MAX_COMPLETION_TOKENS),
        "planner_version": ABLATION_PLANNER_VERSION,
    }


# ---------------------------------------------------------------------------
# Prompt building + prompt-control proof
# ---------------------------------------------------------------------------


def build_ablation_prompt(
    *,
    scenario_id: str,
    before: str,
    after: str,
    acceptance_criteria: Iterable[str],
    architecture_constraints: Iterable[str],
    serialization_policy: str,
    mapping: CandidateIDMap,
    evidence: Iterable[Any] = (),
) -> str:
    """Render the common ablation prompt with the given serialization policy.

    Every field other than ``serialization_policy`` is shared verbatim by both
    arms, so the only arm-dependent content is the policy block.
    """
    candidates = "\n".join(f"- {i}. {p}" for i, p in mapping.id_to_path)
    return COMMON_ABLATION_PROMPT_TEMPLATE.format(
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
        reason_codes="\n".join(f"- {c}" for c in ABLATION_REASON_CODES),
        serialization_policy=serialization_policy.format(
            candidate_count=FROZEN_CANDIDATE_UNIVERSE_COUNT
        ),
    )


def render_full_prompt(
    *,
    scenario_id: str,
    before: str,
    after: str,
    acceptance_criteria: Iterable[str],
    architecture_constraints: Iterable[str],
    mapping: CandidateIDMap,
    evidence: Iterable[Any] = (),
) -> str:
    return build_ablation_prompt(
        scenario_id=scenario_id,
        before=before,
        after=after,
        acceptance_criteria=acceptance_criteria,
        architecture_constraints=architecture_constraints,
        serialization_policy=SERIALIZATION_POLICY_FULL,
        mapping=mapping,
        evidence=evidence,
    )


def render_sparse_prompt(
    *,
    scenario_id: str,
    before: str,
    after: str,
    acceptance_criteria: Iterable[str],
    architecture_constraints: Iterable[str],
    mapping: CandidateIDMap,
    evidence: Iterable[Any] = (),
) -> str:
    return build_ablation_prompt(
        scenario_id=scenario_id,
        before=before,
        after=after,
        acceptance_criteria=acceptance_criteria,
        architecture_constraints=architecture_constraints,
        serialization_policy=SERIALIZATION_POLICY_SPARSE,
        mapping=mapping,
        evidence=evidence,
    )


def strip_serialization_policy(prompt: str) -> str:
    """Remove the serialization-policy block, returning the shared skeleton.

    Used by the prompt-control proof: after stripping, FULL and SPARSE rendered
    prompts for the same scenario MUST be byte-identical.
    """
    start = prompt.find(_POLICY_OPEN)
    end = prompt.find(_POLICY_CLOSE)
    if start < 0 or end < 0 or end <= start:
        raise ValueError("serialization policy block markers not found")
    end += len(_POLICY_CLOSE)
    return prompt[:start] + prompt[end:]


def prompt_control_proof(
    full_prompt: str, sparse_prompt: str
) -> dict[str, Any]:
    """Deterministic proof that the ONLY difference is the policy block."""
    stripped_full = strip_serialization_policy(full_prompt)
    stripped_sparse = strip_serialization_policy(sparse_prompt)
    return {
        "PROMPT_CONTROLLED_DIFF": "PASS" if stripped_full == stripped_sparse else "FAIL",
        "stripped_full_sha256": sha256_text(stripped_full),
        "stripped_sparse_sha256": sha256_text(stripped_sparse),
        "byte_identical_after_policy_strip": stripped_full == stripped_sparse,
    }


# ---------------------------------------------------------------------------
# Complete policy representation (canonical 144-candidate policy)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletePolicy:
    """Canonical complete policy: id (1..144) -> action string.

    This is the SAME canonical representation both arms decode into before
    hidden-gold scoring.
    """

    action_by_id: tuple[tuple[int, str], ...]

    def __post_init__(self) -> None:
        ids = [i for i, _ in self.action_by_id]
        if len(ids) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
            raise ValueError(
                f"complete policy must have {FROZEN_CANDIDATE_UNIVERSE_COUNT} entries"
            )
        if ids != list(range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1)):
            raise ValueError("complete policy ids must be exactly 1..144 in order")
        if len(set(a for _, a in self.action_by_id)) == 0:
            raise ValueError("empty action set")
        for _, action in self.action_by_id:
            if action not in ABLATION_ACTION_VOCAB:
                raise ValueError(f"unknown action {action!r} in complete policy")

    def action_for(self, candidate_id: int) -> str:
        for i, a in self.action_by_id:
            if i == candidate_id:
                return a
        raise KeyError(candidate_id)

    def to_dict(self) -> dict[int, str]:
        return dict(self.action_by_id)

    def write_set_ids(self) -> list[int]:
        """Ids whose action is REGENERATE (the reconstructed write set)."""
        return [i for i, a in self.action_by_id if a == "REGENERATE"]


def complete_policy_from_actions(actions: Mapping[int, str]) -> CompletePolicy:
    """Build a CompletePolicy from an id->action mapping (missing => PRESERVE)."""
    rows: list[tuple[int, str]] = []
    for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1):
        rows.append((i, actions.get(i, "PRESERVE")))
    return CompletePolicy(action_by_id=tuple(rows))


# ---------------------------------------------------------------------------
# Encoding (complete policy -> arm representation)
# ---------------------------------------------------------------------------

_DEFAULT_DECISION = {
    "rationale": "no change required",
    "confidence": 0.9,
    "reason_codes": ["no_change"],
    "evidence": [{"source": "policy", "description": "preserved by default"}],
}


def encode_full_policy(policy: CompletePolicy, mapping: CandidateIDMap) -> list[dict[str, Any]]:
    """Encode a complete policy as FULL-v2: one decision per id incl. PRESERVE."""
    rows: list[dict[str, Any]] = []
    for i, action in policy.action_by_id:
        if action == "PRESERVE":
            rows.append(
                {
                    "id": i,
                    "action": "PRESERVE",
                    **_DEFAULT_DECISION,
                }
            )
        else:
            rows.append(
                {
                    "id": i,
                    "action": action,
                    "rationale": f"{action.lower()} decision for id {i}",
                    "confidence": 0.9,
                    "reason_codes": ["requirement_change"],
                    "evidence": [{"source": "policy", "description": action.lower()}],
                }
            )
    return rows


def encode_sparse_policy(policy: CompletePolicy, mapping: CandidateIDMap) -> list[dict[str, Any]]:
    """Encode a complete policy as SPARSE-v2: only non-PRESERVE decisions."""
    rows: list[dict[str, Any]] = []
    for i, action in policy.action_by_id:
        if action == "PRESERVE":
            continue
        rows.append(
            {
                "id": i,
                "action": action,
                "rationale": f"{action.lower()} decision for id {i}",
                "confidence": 0.9,
                "reason_codes": ["requirement_change"],
                "evidence": [{"source": "policy", "description": action.lower()}],
            }
        )
    return rows


def sparse_payload_for(policy: CompletePolicy, mapping: CandidateIDMap) -> dict[str, Any]:
    return {
        "decisions": encode_sparse_policy(policy, mapping),
        "validation_obligations": [],
        "architecture_checks": [],
        "escalation_reason": "",
    }


def full_payload_for(policy: CompletePolicy, mapping: CandidateIDMap) -> dict[str, Any]:
    return {
        "decisions": encode_full_policy(policy, mapping),
        "validation_obligations": [],
        "architecture_checks": [],
        "escalation_reason": "",
    }


# ---------------------------------------------------------------------------
# Decoding (arm output -> canonical complete policy), fail-closed
# ---------------------------------------------------------------------------


class AblationDecodeError(RuntimeError):
    """Raised when an ablation output cannot be decoded fail-closed."""


def _raw_decision_items(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(parsed, dict):
        raise AblationDecodeError("malformed structured output: not a JSON object")
    raw = parsed.get("decisions")
    if raw is None:
        raise AblationDecodeError("malformed structured output: missing 'decisions'")
    if not isinstance(raw, list):
        raise AblationDecodeError("malformed structured output: 'decisions' is not a list")
    return [item for item in raw if isinstance(item, dict)]


def _validate_item_fields(item: dict[str, Any], idx: int) -> str:
    """Validate the common semantic invariants of one decision row."""
    raw_id = item.get("id")
    if not isinstance(raw_id, int) or isinstance(raw_id, bool):
        raise AblationDecodeError(
            f"malformed structured output: decision id must be an integer (index {idx})"
        )
    action_str = str(item.get("action") or "").strip().upper()
    if action_str not in ABLATION_ACTION_VOCAB:
        raise AblationDecodeError(f"unsupported action {action_str!r} (index {idx})")
    if raw_id < 1 or raw_id > FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise AblationDecodeError(f"id out of range {raw_id} (index {idx})")
    return action_str


def _assemble_policy(
    id_actions: dict[int, str], *, non_preserve_only: bool
) -> CompletePolicy:
    rows: list[tuple[int, str]] = []
    for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1):
        action = id_actions.get(i, "PRESERVE")
        if non_preserve_only and action == "PRESERVE":
            # omitted ids always decode as PRESERVE (sparse semantics)
            pass
        rows.append((i, action))
    if len(rows) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        raise AblationDecodeError("decoded policy must contain exactly 144 candidates")
    return CompletePolicy(action_by_id=tuple(rows))


def decode_full_policy(parsed: dict[str, Any]) -> CompletePolicy:
    """Decode a FULL-v2 output fail-closed.

    Requires exactly 144 unique candidate ids, every candidate represented
    once, no unknown id.
    """
    items = _raw_decision_items(parsed)
    id_actions: dict[int, str] = {}
    for idx, item in enumerate(items):
        action_str = _validate_item_fields(item, idx)
        raw_id = int(item["id"])
        if raw_id in id_actions:
            raise AblationDecodeError(f"duplicate candidate id {raw_id} (index {idx})")
        id_actions[raw_id] = action_str
    if len(id_actions) != FROZEN_CANDIDATE_UNIVERSE_COUNT:
        missing = sorted(
            set(range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1)) - set(id_actions)
        )
        raise AblationDecodeError(
            f"FULL-v2 output must contain exactly {FROZEN_CANDIDATE_UNIVERSE_COUNT} "
            f"unique ids; missing={missing[:10]}"
        )
    return _assemble_policy(id_actions, non_preserve_only=False)


def decode_sparse_policy(parsed: dict[str, Any]) -> CompletePolicy:
    """Decode a SPARSE-v2 output fail-closed.

    Requires zero or more unique candidate ids, NO explicit PRESERVE rows, only
    R/V/H rows, no unknown id; omitted ids reconstruct as PRESERVE.
    """
    items = _raw_decision_items(parsed)
    id_actions: dict[int, str] = {}
    for idx, item in enumerate(items):
        action_str = _validate_item_fields(item, idx)
        raw_id = int(item["id"])
        if action_str == "PRESERVE":
            raise AblationDecodeError(
                f"SPARSE-v2 output must NOT contain explicit PRESERVE rows (index {idx})"
            )
        if raw_id in id_actions:
            raise AblationDecodeError(f"duplicate candidate id {raw_id} (index {idx})")
        id_actions[raw_id] = action_str
    return _assemble_policy(id_actions, non_preserve_only=True)


# ---------------------------------------------------------------------------
# Semantic validators (arm-specific, before hidden-gold scoring)
# ---------------------------------------------------------------------------


def validate_full_v2(parsed: dict[str, Any]) -> dict[str, Any]:
    """FULL-v2 valid output: exactly 144 unique ids, every candidate once."""
    errors: list[str] = []
    try:
        policy = decode_full_policy(parsed)
        valid = True
    except AblationDecodeError as exc:
        policy = None
        valid = False
        errors.append(str(exc))
    return {
        "valid": valid,
        "errors": errors,
        "policy": policy,
        "decoded_candidate_count": len(policy.action_by_id) if policy else 0,
        "decoded_write_set_ids": policy.write_set_ids() if policy else [],
    }


def validate_sparse_v2(parsed: dict[str, Any]) -> dict[str, Any]:
    """SPARSE-v2 valid output: only R/V/H rows, omitted => PRESERVE."""
    errors: list[str] = []
    try:
        policy = decode_sparse_policy(parsed)
        valid = True
    except AblationDecodeError as exc:
        policy = None
        valid = False
        errors.append(str(exc))
    return {
        "valid": valid,
        "errors": errors,
        "policy": policy,
        "decoded_candidate_count": len(policy.action_by_id) if policy else 0,
        "decoded_write_set_ids": policy.write_set_ids() if policy else [],
    }


# ---------------------------------------------------------------------------
# Representation-equivalence property tests (ZERO API)
# ---------------------------------------------------------------------------


def _random_policy(rng: Any) -> CompletePolicy:
    actions = list(ABLATION_ACTION_VOCAB)
    rows: list[tuple[int, str]] = []
    for i in range(1, FROZEN_CANDIDATE_UNIVERSE_COUNT + 1):
        rows.append((i, actions[rng.randrange(len(actions))]))
    return CompletePolicy(action_by_id=tuple(rows))


def representation_equivalence_checks() -> dict[str, Any]:
    """Deterministic property tests proving decode_sparse(encode_sparse(pi)) == pi.

    Also proves the full-v2 round trip and that malformed sparse inputs
    (duplicate ids, unknown ids, explicit PRESERVE rows) fail closed.
    """
    mapping = derive_candidate_id_map()
    checks: list[dict[str, Any]] = []
    rng = __import__("random").Random(20260912)

    def _roundtrip_sparse(policy: CompletePolicy, label: str) -> dict[str, Any]:
        payload = sparse_payload_for(policy, mapping)
        try:
            decoded = decode_sparse_policy(payload)
            ok = decoded.to_dict() == policy.to_dict()
        except AblationDecodeError as exc:
            ok = False
            decoded = None
        return {
            "label": label,
            "D_s(E_s(pi)) == pi": ok,
            "details": f"decoded==original: {ok}",
        }

    # 1. all PRESERVE
    all_preserve = complete_policy_from_actions({})
    checks.append(_roundtrip_sparse(all_preserve, "all_preserve"))
    # 2. one non-PRESERVE
    one = complete_policy_from_actions({1: "REGENERATE"})
    checks.append(_roundtrip_sparse(one, "one_non_preserve"))
    # 3. mixed R / V / H
    mixed = complete_policy_from_actions(
        {2: "REGENERATE", 5: "VALIDATE", 9: "HUMAN_REVIEW", 12: "REGENERATE"}
    )
    checks.append(_roundtrip_sparse(mixed, "mixed_R_V_H"))
    # 4. all non-PRESERVE
    all_non = complete_policy_from_actions(
        {i: "REGENERATE" if i % 3 != 0 else "VALIDATE" for i in range(1, 145)}
    )
    checks.append(_roundtrip_sparse(all_non, "all_non_preserve"))
    # 5. random generated policies
    random_ok = True
    for seed in range(5):
        rng = __import__("random").Random(seed + 1)
        policy = _random_policy(rng)
        res = _roundtrip_sparse(policy, f"random_{seed}")
        random_ok = random_ok and res["D_s(E_s(pi)) == pi"]
        checks.append(res)
    # 6. duplicate ids must fail closed (sparse)
    dup = {"decisions": [{"id": 1, "action": "REGENERATE"}, {"id": 1, "action": "VALIDATE"}]}
    try:
        decode_sparse_policy(dup)
        dup_ok = False
    except AblationDecodeError:
        dup_ok = True
    checks.append({"label": "duplicate_ids_rejected", "D_s(E_s(pi)) == pi": dup_ok,
                   "details": "duplicate ids fail closed"})
    # 7. unknown ids must fail closed (sparse)
    unk = {"decisions": [{"id": 999, "action": "REGENERATE"}]}
    try:
        decode_sparse_policy(unk)
        unk_ok = False
    except AblationDecodeError:
        unk_ok = True
    checks.append({"label": "unknown_ids_rejected", "D_s(E_s(pi)) == pi": unk_ok,
                   "details": "unknown ids fail closed"})
    # 8. explicit PRESERVE rows must fail closed (sparse)
    pres = {"decisions": [{"id": 1, "action": "PRESERVE"}]}
    try:
        decode_sparse_policy(pres)
        pres_ok = False
    except AblationDecodeError:
        pres_ok = True
    checks.append({"label": "explicit_preserve_rejected_sparse", "D_s(E_s(pi)) == pi": pres_ok,
                   "details": "sparse must not contain explicit PRESERVE rows"})
    # 9. full-v2 round trip
    full_ok = True
    try:
        payload = full_payload_for(mixed, mapping)
        decoded_full = decode_full_policy(payload)
        full_ok = decoded_full.to_dict() == mixed.to_dict()
    except AblationDecodeError:
        full_ok = False
    checks.append({"label": "full_v2_roundtrip", "D_s(E_s(pi)) == pi": full_ok,
                   "details": "decode_full(encode_full(pi)) == pi"})
    # 10. full-v2 must reject incomplete outputs
    incomplete = {"decisions": [{"id": 1, "action": "REGENERATE"}]}
    try:
        decode_full_policy(incomplete)
        full_incomplete_ok = False
    except AblationDecodeError:
        full_incomplete_ok = True
    checks.append({"label": "full_incomplete_rejected", "D_s(E_s(pi)) == pi": full_incomplete_ok,
                   "details": "full output missing ids fails closed"})

    all_pass = all(c["D_s(E_s(pi)) == pi"] for c in checks)
    return {
        "REPRESENTATION_EQUIVALENCE": "PASS" if all_pass else "FAIL",
        "all_pass": all_pass,
        "checks": checks,
    }
