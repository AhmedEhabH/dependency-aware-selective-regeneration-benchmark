"""M4A-3 / P1 — REAL-COMMIT FULL-v2 vs SPARSE-v2 held-out evaluation core.

STUDY_ID: real-commit-p1-full-v2-vs-sparse-v2-01

ZERO scientific LLM/API calls in this milestone. The P1 protocol is frozen
BEFORE any model result (see reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md). This
module implements the deterministic, auditable harness:

- per-case candidate ID map derived from the frozen PUBLIC parent-only
  candidate universe (path-sorted, scenario/gold independent);
- FULL-v2 and SPARSE-v2 prompts that share the SAME semantic contract and
  differ ONLY in the serialization-policy block (prompt-control proof);
- fail-closed decode/validate for both arms parameterized by the per-case
  candidate count;
- hidden observed-change-set proxy used evaluation-only (never exposed to a
  prompt);
- deterministic selection metrics (P/R/F1/FNR) against the proxy;
- frozen 60-cell manifest shape (N_heldout × 2 arms × 3 repetitions);
- six ZERO-API gates + independent audit.

Scientific discipline: the historical diff is an OBSERVED CHANGE-SET PROXY,
never semantic ground truth. Independent task = historical change; repeated
model calls are nested observations, not independent tasks.
"""

# ruff: noqa: E501
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

P1_PROTOCOL_VERSION: str = "real-commit-p1-v1.0.0"
P1_PLANNER_VERSION: str = "real-commit-p1-planner-1"
P1_MAX_COMPLETION_TOKENS: int = 16384
P1_TEMPERATURE: float = 0.0
P1_REPETITIONS: int = 3

# Frozen primary scientific model for P1 (same semantic contract both arms).
P1_MODEL: str = "qwen/qwen3-coder"
P1_MODEL_HUMAN: str = "Qwen3-Coder-480B-A35B-Instruct"
P1_PROVIDER_TAG: str = "deepinfra/turbo"

# Action vocabulary (identical for both arms).
P1_ACTION_VOCAB: tuple[str, ...] = (
    "PRESERVE",
    "REGENERATE",
    "VALIDATE",
    "HUMAN_REVIEW",
)
P1_NON_PRESERVE_ACTIONS: tuple[str, ...] = (
    "REGENERATE",
    "VALIDATE",
    "HUMAN_REVIEW",
)

# Frozen reason-code vocabulary (identical for both arms).
P1_REASON_CODES: tuple[str, ...] = (
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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_text(canonical)


# ---------------------------------------------------------------------------
# Per-case public-bundle loading (parent-only, hidden proxy kept separate)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P1CaseBundle:
    """Deterministic per-case public bundle for P1 inference input.

    Only PARENT-commit visible artifacts are present:
    - candidate universe (production Python paths at parent);
    - dependency graph (parent-only);
    - natural-language intent (normalized commit message);
    - repository identity + parent commit SHA.

    The hidden observed-change proxy is NEVER part of this bundle.
    """

    case_id: str
    repository: str
    repository_url: str
    parent_commit: str
    target_commit: str
    intent_text: str
    candidate_paths: tuple[str, ...]
    candidate_records: tuple[dict[str, Any], ...]
    graph_edges: tuple[tuple[str, str], ...]
    public_bundle_sha256: str


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_case_public_bundle(dataset_dir: Path, case_id: str) -> P1CaseBundle:
    """Load one frozen scientific case's PUBLIC bundle (parent-only inputs)."""
    case_dir = dataset_dir / "scientific" / case_id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"case dir not found: {case_dir}")

    manifest = _read_json(case_dir / "case_manifest.json")
    record = manifest["record"]
    intent = _read_json(case_dir / "public" / "intent.json")
    universe = _read_json(case_dir / "public" / "candidate_universe.json")
    graph = _read_json(case_dir / "public" / "dependency_graph.json")

    records = universe.get("records", [])
    paths = tuple(str(r["path"]) for r in records)
    edges = tuple(
        (str(src), str(dst))
        for src, dst in graph.get("edges", [])
    )

    payload = {
        "case_id": case_id,
        "parent_commit": record.get("parent_commit"),
        "target_commit": record.get("target_commit"),
        "intent_text": intent.get("intent_text"),
        "candidate_paths": list(paths),
        "graph_edges": [list(e) for e in edges],
    }
    return P1CaseBundle(
        case_id=case_id,
        repository=record.get("repository", ""),
        repository_url=record.get("repository_url", ""),
        parent_commit=record.get("parent_commit", ""),
        target_commit=record.get("target_commit", ""),
        intent_text=intent.get("intent_text", ""),
        candidate_paths=paths,
        candidate_records=tuple(records),
        graph_edges=edges,
        public_bundle_sha256=sha256_json(payload),
    )


def load_hidden_proxy_paths(dataset_dir: Path, case_id: str) -> tuple[str, ...]:
    """Load the hidden observed-change proxy paths (evaluation-only)."""
    case_dir = dataset_dir / "scientific" / case_id
    proxy = _read_json(case_dir / "hidden" / "observed_change_set_proxy.json")
    return tuple(sorted(str(p) for p in proxy.get("paths", [])))


def held_out_case_ids(dataset_dir: Path) -> tuple[str, ...]:
    """Frozen HELD_OUT_TEST membership (ordered, from split_freeze.json)."""
    split_freeze = _read_json(dataset_dir / "split_freeze.json")
    return tuple(sorted(split_freeze["per_split"]["HELD_OUT_TEST"]["case_ids"]))


# ---------------------------------------------------------------------------
# Per-case candidate ID map (path-sorted, deterministic, proxy independent)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class P1CandidateMap:
    id_to_path: tuple[tuple[int, str], ...]
    sha256: str

    def __post_init__(self) -> None:
        ids = [i for i, _ in self.id_to_path]
        if ids != list(range(1, len(self.id_to_path) + 1)):
            raise ValueError("P1 candidate IDs must be exactly 1..N in order")
        paths = [p for _, p in self.id_to_path]
        if len(set(paths)) != len(paths):
            raise ValueError("P1 candidate map contains duplicate paths")

    def path_for(self, candidate_id: int) -> str:
        for i, p in self.id_to_path:
            if i == candidate_id:
                return p
        raise KeyError(f"candidate id {candidate_id} not in mapping")

    def paths(self) -> tuple[str, ...]:
        return tuple(p for _, p in self.id_to_path)


def build_p1_candidate_map(candidate_paths: Iterable[str]) -> P1CandidateMap:
    paths = sorted(set(str(p) for p in candidate_paths))
    id_to_path = tuple((idx + 1, path) for idx, path in enumerate(paths))
    canonical = json.dumps(
        [{"id": i, "path": p} for i, p in id_to_path],
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return P1CandidateMap(id_to_path=id_to_path, sha256=sha256_text(canonical))


# ---------------------------------------------------------------------------
# Common P1 schema (parameterized by the per-case candidate count)
# ---------------------------------------------------------------------------


def p1_common_schema(candidate_count: int) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "minItems": 0,
                "maxItems": candidate_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "minimum": 1, "maximum": candidate_count},
                        "action": {"type": "string", "enum": list(P1_ACTION_VOCAB)},
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
# Serialization policies (ONLY intended treatment difference)
# ---------------------------------------------------------------------------

P1_SERIALIZATION_POLICY_FULL = """FULL SERIALIZATION POLICY:
- Emit EXACTLY ONE decision for EVERY candidate id in [1, {candidate_count}], including an explicit "PRESERVE" decision for every candidate that should not be regenerated.
- The output MUST contain exactly {candidate_count} decision objects, one per candidate id, each id used exactly once.
- Do NOT omit any candidate id and do NOT invent any id outside [1, {candidate_count}].
"""

P1_SERIALIZATION_POLICY_SPARSE = """SPARSE SERIALIZATION POLICY (PRESERVE-BY-OMISSION):
- Emit a decision ONLY for a candidate whose action is NOT "PRESERVE".
- NEVER emit a "PRESERVE" decision.
- Candidate ids that are NOT emitted are deterministically decoded by the harness as "PRESERVE".
- After decoding, every one of the {candidate_count} candidate ids is classified exactly once.
- Never emit an id outside [1, {candidate_count}] and never repeat an id.
"""

_POLICY_OPEN = "[[SERIALIZATION_POLICY]]"
_POLICY_CLOSE = "[[/SERIALIZATION_POLICY]]"

P1_COMMON_PROMPT_TEMPLATE = """You are an impact planner for a software repository using a common structured policy representation.

Frozen real historical change ({case_id}):
Commit intent (normalized commit message):
{intent}

Candidate artifacts at the PARENT commit (frozen deterministic numeric ids 1..{candidate_count}):
{candidates}

Parent-only dependency graph edges (may be used for context):
{graph_edges}

Action vocabulary (identical for every policy representation):
- PRESERVE: no action; keep the candidate unchanged.
- REGENERATE: candidate requires an edit justified by the visible intent and cited evidence.
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


def build_p1_prompt(
    *,
    case: P1CaseBundle,
    serialization_policy: str,
    mapping: P1CandidateMap,
) -> str:
    candidates = "\n".join(f"- {i}. {p}" for i, p in mapping.id_to_path)
    return P1_COMMON_PROMPT_TEMPLATE.format(
        case_id=case.case_id,
        intent=case.intent_text,
        candidate_count=len(mapping.id_to_path),
        candidates=candidates,
        graph_edges=(
            "\n".join(f"- {src} -> {dst}" for src, dst in case.graph_edges[:200])
            or "- (none)"
        ),
        reason_codes="\n".join(f"- {c}" for c in P1_REASON_CODES),
        serialization_policy=serialization_policy.format(
            candidate_count=len(mapping.id_to_path)
        ),
    )


def render_p1_full_prompt(*, case: P1CaseBundle, mapping: P1CandidateMap) -> str:
    return build_p1_prompt(
        case=case,
        serialization_policy=P1_SERIALIZATION_POLICY_FULL,
        mapping=mapping,
    )


def render_p1_sparse_prompt(*, case: P1CaseBundle, mapping: P1CandidateMap) -> str:
    return build_p1_prompt(
        case=case,
        serialization_policy=P1_SERIALIZATION_POLICY_SPARSE,
        mapping=mapping,
    )


def strip_serialization_policy(prompt: str) -> str:
    start = prompt.find(_POLICY_OPEN)
    end = prompt.find(_POLICY_CLOSE)
    if start < 0 or end < 0 or end <= start:
        raise ValueError("serialization policy block markers not found")
    end += len(_POLICY_CLOSE)
    return prompt[:start] + prompt[end:]


def prompt_control_proof(full_prompt: str, sparse_prompt: str) -> dict[str, Any]:
    stripped_full = strip_serialization_policy(full_prompt)
    stripped_sparse = strip_serialization_policy(sparse_prompt)
    return {
        "PROMPT_CONTROLLED_DIFF": "PASS" if stripped_full == stripped_sparse else "FAIL",
        "stripped_full_sha256": sha256_text(stripped_full),
        "stripped_sparse_sha256": sha256_text(stripped_sparse),
        "byte_identical_after_policy_strip": stripped_full == stripped_sparse,
    }


# ---------------------------------------------------------------------------
# Decode / validate (fail-closed, parameterized per case)
# ---------------------------------------------------------------------------


class P1DecodeError(RuntimeError):
    """Raised when a P1 arm output cannot be decoded fail-closed."""


def _raw_decision_items(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(parsed, dict):
        raise P1DecodeError("malformed structured output: not a JSON object")
    raw = parsed.get("decisions")
    if raw is None:
        raise P1DecodeError("malformed structured output: missing 'decisions'")
    if not isinstance(raw, list):
        raise P1DecodeError("malformed structured output: 'decisions' is not a list")
    return [item for item in raw if isinstance(item, dict)]


def _validate_item_fields(item: dict[str, Any], idx: int, candidate_count: int) -> str:
    raw_id = item.get("id")
    if not isinstance(raw_id, int) or isinstance(raw_id, bool):
        raise P1DecodeError(
            f"malformed structured output: decision id must be an integer (index {idx})"
        )
    action_str = str(item.get("action") or "").strip().upper()
    if action_str not in P1_ACTION_VOCAB:
        raise P1DecodeError(f"unsupported action {action_str!r} (index {idx})")
    if raw_id < 1 or raw_id > candidate_count:
        raise P1DecodeError(f"id out of range {raw_id} (index {idx})")
    return action_str


def _assemble_policy(
    id_actions: dict[int, str], *, candidate_count: int, non_preserve_only: bool
) -> tuple[tuple[int, str], ...]:
    rows: list[tuple[int, str]] = []
    for i in range(1, candidate_count + 1):
        action = id_actions.get(i, "PRESERVE")
        if non_preserve_only and action == "PRESERVE":
            pass
        rows.append((i, action))
    if len(rows) != candidate_count:
        raise P1DecodeError(f"decoded policy must contain exactly {candidate_count} candidates")
    return tuple(rows)


def decode_p1_full(parsed: dict[str, Any], *, candidate_count: int) -> tuple[tuple[int, str], ...]:
    items = _raw_decision_items(parsed)
    id_actions: dict[int, str] = {}
    for idx, item in enumerate(items):
        action_str = _validate_item_fields(item, idx, candidate_count)
        raw_id = int(item["id"])
        if raw_id in id_actions:
            raise P1DecodeError(f"duplicate candidate id {raw_id} (index {idx})")
        id_actions[raw_id] = action_str
    if len(id_actions) != candidate_count:
        missing = sorted(set(range(1, candidate_count + 1)) - set(id_actions))
        raise P1DecodeError(
            f"FULL-v2 output must contain exactly {candidate_count} unique ids; missing={missing[:10]}"
        )
    return _assemble_policy(id_actions, candidate_count=candidate_count, non_preserve_only=False)


def decode_p1_sparse(parsed: dict[str, Any], *, candidate_count: int) -> tuple[tuple[int, str], ...]:
    items = _raw_decision_items(parsed)
    id_actions: dict[int, str] = {}
    for idx, item in enumerate(items):
        action_str = _validate_item_fields(item, idx, candidate_count)
        raw_id = int(item["id"])
        if action_str == "PRESERVE":
            raise P1DecodeError(
                f"SPARSE-v2 output must NOT contain explicit PRESERVE rows (index {idx})"
            )
        if raw_id in id_actions:
            raise P1DecodeError(f"duplicate candidate id {raw_id} (index {idx})")
        id_actions[raw_id] = action_str
    return _assemble_policy(id_actions, candidate_count=candidate_count, non_preserve_only=True)


def validate_p1_full(parsed: dict[str, Any], *, candidate_count: int) -> dict[str, Any]:
    errors: list[str] = []
    try:
        policy = decode_p1_full(parsed, candidate_count=candidate_count)
        valid = True
    except P1DecodeError as exc:
        policy = None
        valid = False
        errors.append(str(exc))
    return {
        "valid": valid,
        "errors": errors,
        "policy": policy,
        "decoded_candidate_count": len(policy) if policy else 0,
        "decoded_write_set_ids": [i for i, a in (policy or []) if a == "REGENERATE"],
    }


def validate_p1_sparse(parsed: dict[str, Any], *, candidate_count: int) -> dict[str, Any]:
    errors: list[str] = []
    try:
        policy = decode_p1_sparse(parsed, candidate_count=candidate_count)
        valid = True
    except P1DecodeError as exc:
        policy = None
        valid = False
        errors.append(str(exc))
    return {
        "valid": valid,
        "errors": errors,
        "policy": policy,
        "decoded_candidate_count": len(policy) if policy else 0,
        "decoded_write_set_ids": [i for i, a in (policy or []) if a == "REGENERATE"],
    }


# ---------------------------------------------------------------------------
# Raw-response parsing (persisted provider bytes -> serialized decision count)
# ---------------------------------------------------------------------------


def serialized_decision_count_from_raw(raw_text: str) -> tuple[int, list[str]]:
    """Count explicit decision rows serialized by the model from a persisted
    raw provider response (``choices[0].message.content`` JSON payload).

    Returns ``(serialized_decision_count, errors)``. This is the authoritative
    serialized-record source; ``decoded_write_set_ids`` counts only REGENERATE
    rows and is NOT a serialized decision count.
    """
    errors: list[str] = []
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return 0, [f"raw provider response is not valid JSON: {exc}"]
    if not isinstance(parsed, dict):
        return 0, ["raw provider response is not a JSON object"]
    choices = parsed.get("choices") or []
    if not choices:
        return 0, ["raw provider response has no choices"]
    choice = choices[0]
    if not isinstance(choice, dict):
        return 0, ["first choice is not an object"]
    message = choice.get("message") or {}
    content = message.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        return 0, ["assistant content is empty"]
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        return 0, [f"assistant content is not valid JSON: {exc}"]
    if not isinstance(payload, dict):
        return 0, ["assistant content is not a JSON object"]
    decisions = payload.get("decisions")
    if not isinstance(decisions, list):
        return 0, ["payload has no 'decisions' list"]
    return len(decisions), errors


def raw_decision_items(raw_text: str) -> list[dict[str, Any]]:
    """Extract the explicit decision items from a persisted raw response."""
    parsed = json.loads(raw_text)
    content = parsed["choices"][0]["message"]["content"]
    payload = json.loads(content)
    items = payload.get("decisions")
    if not isinstance(items, list):
        raise P1DecodeError("payload has no 'decisions' list")
    return [item for item in items if isinstance(item, dict)]


# ---------------------------------------------------------------------------
# Metrics (predicted REGENERATE file set vs hidden observed-change proxy)
# ---------------------------------------------------------------------------


def p1_selection_metrics(predicted_regenerate: set[str], proxy: set[str]) -> dict[str, Any]:
    tp = len(predicted_regenerate & proxy)
    fn = len(proxy - predicted_regenerate)
    fp = len(predicted_regenerate - proxy)
    predicted_size = len(predicted_regenerate)
    precision = tp / predicted_size if predicted_size else 0.0
    recall = tp / len(proxy) if proxy else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fnr = fn / len(proxy) if proxy else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fnr": fnr,
        "full_recall": bool(proxy and recall >= 1.0),
        "proxy_size": len(proxy),
        "predicted_size": predicted_size,
    }


# ---------------------------------------------------------------------------
# Fixture / dry-run payloads (deterministic, ZERO API)
# ---------------------------------------------------------------------------


def _default_decision(action: str, candidate_id: int) -> dict[str, Any]:
    if action == "PRESERVE":
        return {
            "id": candidate_id,
            "action": "PRESERVE",
            "rationale": "no change required",
            "confidence": 0.9,
            "reason_codes": ["no_change"],
            "evidence": [{"source": "policy", "description": "preserved by default"}],
        }
    return {
        "id": candidate_id,
        "action": action,
        "rationale": f"{action.lower()} decision for id {candidate_id}",
        "confidence": 0.9,
        "reason_codes": ["requirement_change"],
        "evidence": [{"source": "policy", "description": action.lower()}],
    }


def fixture_payload_for_arm(
    *,
    arm: str,
    mapping: P1CandidateMap,
    proxy_paths: set[str],
) -> dict[str, Any]:
    policy_rows: dict[int, str] = {}
    for i, path in mapping.id_to_path:
        policy_rows[i] = "REGENERATE" if path in proxy_paths else "PRESERVE"
    if arm == "full_v2":
        decisions = [_default_decision(policy_rows[i], i) for i in range(1, len(mapping.id_to_path) + 1)]
    else:
        decisions = [
            _default_decision(policy_rows[i], i)
            for i in range(1, len(mapping.id_to_path) + 1)
            if policy_rows[i] != "PRESERVE"
        ]
    return {
        "decisions": decisions,
        "validation_obligations": [],
        "architecture_checks": [],
        "escalation_reason": "",
    }


# ---------------------------------------------------------------------------
# Frozen manifest shape (N_heldout × 2 arms × 3 repetitions)
# ---------------------------------------------------------------------------


def build_p1_manifest(
    dataset_dir: Path,
    *,
    repetitions: int = P1_REPETITIONS,
) -> list[dict[str, Any]]:
    case_ids = held_out_case_ids(dataset_dir)
    rows: list[dict[str, Any]] = []
    for case_id in case_ids:
        bundle = load_case_public_bundle(dataset_dir, case_id)
        mapping = build_p1_candidate_map(bundle.candidate_paths)
        for arm in ("full_v2", "sparse_v2"):
            for rep in range(1, repetitions + 1):
                rows.append(
                    {
                        "run_id": f"p1-{case_id}-{arm}-r{rep}",
                        "case_id": case_id,
                        "repetition": rep,
                        "arm": arm,
                        "serialization_policy": arm,
                        "expected_model": P1_MODEL,
                        "provider_tag": P1_PROVIDER_TAG,
                        "temperature": P1_TEMPERATURE,
                        "max_completion_tokens": P1_MAX_COMPLETION_TOKENS,
                        "candidate_count": len(mapping.id_to_path),
                        "candidate_map_sha256": mapping.sha256,
                        "public_bundle_sha256": bundle.public_bundle_sha256,
                        "protocol_version": P1_PROTOCOL_VERSION,
                    }
                )
    return rows
