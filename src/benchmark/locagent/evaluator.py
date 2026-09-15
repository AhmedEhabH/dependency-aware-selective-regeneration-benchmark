"""P5-A — Common evaluator for the LocAgent shared-protocol comparison.

Converts LocAgent-native localization output (found_files / ranked files) into
the SAME unique-predicted-file-set representation we use for our method, then
scores both systems with ONE common evaluator against the hidden observed
change-set proxy (evaluation-only).

ZERO scientific LLM/API calls. The common evaluator is frozen BEFORE any
comparative result.

Protocol rules (P0_TO_P5 fast-track §P5):
- LocAgent found_files / ranked files -> unique predicted file set.
- Freeze comparison policies BEFORE results (e.g. LocAgent predicted merged
  file set exactly as emitted; optionally a fixed Top-K).
- Common metrics on identical tasks: P/R/F1/FNR, TP/FP/FN, valid output rate,
  model calls, prompt/completion/total tokens, cost, latency.
- NEVER mix LocAgent-native Acc@K with our F1 in one performance column.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from benchmark.real_commits import p1_evaluation as p1

COMMON_EVALUATOR_VERSION: str = "locagent-shared-protocol-common-evaluator-1"

# Frozen P1 endpoint pricing snapshot (OpenRouter-routed Qwen3-Coder 480B
# A35B; P1 recorded the DeepInfra `deepinfra/turbo` backend, but P5 did NOT
# prove the backend per call — see LOCAGENT_PROVIDER_ROUTE_NOTE below). The P5
# estimated cost is a NORMALIZED estimate under this frozen snapshot, NOT
# authoritative provider-billed cost. Do NOT use upstream LocAgent
# util/cost_analysis.py: it returns 0 for any model name containing "qwen",
# which would make a paid run appear free.
LOCAGENT_PRICING_SNAPSHOT: dict[str, float] = {
    "prompt_per_token_usd": 0.30 / 1_000_000,
    "completion_per_token_usd": 1.00 / 1_000_000,
}
LOCAGENT_PRICING_SOURCE: str = "real-commit-p1-endpoint_freeze-deepinfra-turbo"

# P5-C provider-route provenance (2026-09-15 correction):
# - The per-call usage ledger records provider="openrouter" (the OpenRouter
#   gateway), NOT the resolved backend provider.
# - Raw logs show BOTH "Upstream error from DeepInfra" (P5-B run,
#   aborted case-3 attempt) AND "Upstream error from Venice" (resumed P5-C
#   run, case 66c70394c9e1), i.e. the backend provider is OpenRouter-ROUTED and
#   was NOT deterministically pinned per call.
# Therefore P5 wording must be "OpenRouter-routed Qwen3-Coder" and must NOT
# claim an unqualified DeepInfra pin for every call. P1's own endpoint freeze
# (DeepInfra `deepinfra/turbo`) is separate evidence and unchanged.
LOCAGENT_PROVIDER_ROUTE_NOTE: str = (
    "OpenRouter-routed qwen/qwen3-coder; backend provider NOT proven per call "
    "(logs show both DeepInfra and Venice upstream errors); cost is a "
    "normalized estimate under the frozen P1 pricing snapshot, not "
    "authoritative provider-billed cost"
)


def estimate_cost_usd(prompt_tokens: int, completion_tokens: int) -> float:
    """Estimated API cost from token usage x the frozen P1 pricing snapshot.

    Authoritative for the shared comparison. Upstream LocAgent's own
    ``calc_cost`` is retained only as a non-authoritative diagnostic.
    """
    est = (
        int(prompt_tokens) * LOCAGENT_PRICING_SNAPSHOT["prompt_per_token_usd"]
        + int(completion_tokens) * LOCAGENT_PRICING_SNAPSHOT["completion_per_token_usd"]
    )
    return round(est, 8)


def locagent_acc_at_k(ranked_files: tuple[str, ...], proxy_paths: set[str], k: int) -> bool:
    """Official LocAgent file-level Acc@K for ONE task.

    Mirrors the pinned upstream evaluator (`evaluation/eval_metric.py`,
    ``acc_at_k``): a task is a hit at K iff the number of correct files among
    the top-K ranked predictions equals ``min(len(gt), K)``, where ``gt`` is
    the ground-truth file set (here: the observed change-set proxy). The
    upstream implementation builds a binary relevance vector of length ``K``
    with ``total_relevant = min(len(gt), K)`` ones and ``relevant`` ones among
    the top-K predictions, then a task counts iff ``relevant ==
    total_relevant``. This is NOT ">=1 hit" and NOT the count of matching file
    items.

    ``ranked_files`` MUST be the ORIGINAL ranked order (never a Python set);
    ``proxy_paths`` is the case's observed change-set proxy.
    """
    correct = sum(1 for f in ranked_files[:k] if f in proxy_paths)
    total = min(len(proxy_paths), k)
    return correct == total


def locagent_hit_at_k(ranked_files: tuple[str, ...], proxy_paths: set[str], k: int) -> bool:
    """Task-level Hit@K for ONE task: fraction-of-tasks with >=1 proxy file
    among the top-K ranked predictions (simple task-level definition). Kept
    distinct from the official ``locagent_acc_at_k`` because the two statistics
    differ when a task contains multiple correct files.
    """
    return any(f in proxy_paths for f in ranked_files[:k])


def locagent_item_hits_at_k(ranked_files: tuple[str, ...], proxy_paths: set[str], k: int) -> int:
    """Number of matching FILE ITEMS among the top-K ranked predictions.

    NOT a task-level accuracy and MUST NOT be labelled Acc@K / Hit@K. The
    historical P5-C reporting bug mislabeled the cross-task sum of these item
    counts as "tasks with >=1 hit" (producing the wrong 4/8/9 values).
    """
    return sum(1 for f in ranked_files[:k] if f in proxy_paths)


def assert_cost_not_zero_for_paid_usage(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    model_route: str = "openrouter/qwen/qwen3-coder",
) -> None:
    """Audit assertion: a Qwen/OpenRouter LocAgent run with non-zero token
    usage must NOT report zero authoritative estimated cost.

    Guards against the upstream ``calc_cost`` qwen-zero bug leaking into the
    shared comparison as a false "free" result.
    """
    total_tokens = int(prompt_tokens) + int(completion_tokens)
    if total_tokens > 0 and float(cost_usd) <= 0.0:
        raise AssertionError(
            f"cost audit: {model_route} run with {total_tokens} tokens reported "
            f"cost {cost_usd} (<=0). A paid Qwen/OpenRouter run must not appear "
            "free. Capture real token usage and use estimate_cost_usd()."
        )


@dataclass(frozen=True)
class LocAgentRawOutput:
    """One LocAgent localization output for one instance."""

    instance_id: str
    found_files: tuple[str, ...] = ()
    ranked_files: tuple[str, ...] = ()
    raw_text: str = ""
    valid: bool = True
    parse_error: str = ""

    def unique_predicted_file_set(self) -> set[str]:
        """Frozen comparison policy #2: exact emitted merged file set."""
        return set(self.found_files) | set(self.ranked_files)


# ---------------------------------------------------------------------------
# LocAgent-native output parser (found_files / ranked files -> file set)
# ---------------------------------------------------------------------------

_FILE_LINE_RE = re.compile(r"[\"']?([\w./-]+\.py)[\"']?\s*$")


def parse_locagent_found_files(raw_text: str, valid_files: set[str]) -> tuple[str, ...]:
    """Extract a unique, valid ordered list of python file paths from raw text.

    Accepts LocAgent-style outputs: lines ending in ``.py`` optionally with a
    leading ``- `` / ``* `` / numbered prefix, or JSON arrays of file paths.
    Only paths in ``valid_files`` (the case's parent-only candidate universe)
    are retained, so invented/out-of-universe paths fail closed.
    """
    out: list[str] = []
    seen: set[str] = set()
    text = raw_text.strip()
    if text.startswith("[") or text.startswith("{"):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            payload = payload.get("found_files") or payload.get("files") or payload.get("locations")
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, str):
                    cand = item
                elif isinstance(item, dict):
                    cand = item.get("file") or item.get("path") or ""
                else:
                    continue
                if cand in valid_files and cand not in seen:
                    out.append(cand)
                    seen.add(cand)
            return tuple(out)

    for line in text.splitlines():
        line = line.strip().strip("`").strip()
        line = re.sub(r"^[-*\d.\s]+", "", line).strip().strip(":").strip()
        if not line.endswith(".py"):
            continue
        match = _FILE_LINE_RE.search(line)
        if not match:
            continue
        cand = match.group(1)
        if cand in valid_files and cand not in seen:
            out.append(cand)
            seen.add(cand)
    return tuple(out)


def parse_locagent_raw_output(raw_text: str, valid_files: set[str]) -> LocAgentRawOutput:
    """Parse + validate one LocAgent raw output against the candidate universe."""
    if not raw_text.strip():
        return LocAgentRawOutput(
            instance_id="", raw_text=raw_text, valid=False, parse_error="empty output"
        )
    found = parse_locagent_found_files(raw_text, valid_files)
    if not found:
        return LocAgentRawOutput(
            instance_id="", raw_text=raw_text, valid=False,
            parse_error="no valid candidate-universe file paths found",
        )
    return LocAgentRawOutput(
        instance_id="", found_files=found, ranked_files=found, raw_text=raw_text, valid=True
    )


# ---------------------------------------------------------------------------
# Common scoring (both systems scored identically)
# ---------------------------------------------------------------------------


def common_evaluator(
    *,
    predicted_file_set: set[str],
    proxy_paths: set[str],
    valid_output: bool = True,
    model_calls: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    cost_usd: float = 0.0,
    latency_s: float = 0.0,
    native_ranked_files: tuple[str, ...] = (),
    policy: str = "exact_emitted_file_set",
) -> dict[str, Any]:
    """Score one system output with the common evaluator.

    ``policy`` is frozen: for P5-A the only comparison policy is the exact
    emitted merged file set (``exact_emitted_file_set``). A fixed Top-K policy
    can be added later but is never chosen after seeing hidden targets.
    """
    metrics = p1.p1_selection_metrics(predicted_file_set, proxy_paths)
    if (prompt_tokens + completion_tokens) > 0 and float(cost_usd) <= 0.0:
        cost_usd = estimate_cost_usd(prompt_tokens, completion_tokens)
        cost_source = "estimated:frozen-p1-pricing"
    elif float(cost_usd) > 0.0:
        cost_source = "estimated:frozen-p1-pricing"
    else:
        cost_source = "unset"
    return {
        "evaluator_version": COMMON_EVALUATOR_VERSION,
        "policy": policy,
        "valid_output": bool(valid_output),
        "predicted_file_count": len(predicted_file_set),
        "proxy_size": len(proxy_paths),
        "tp": metrics["tp"],
        "fp": metrics["fp"],
        "fn": metrics["fn"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "fnr": metrics["fnr"],
        "full_recall": metrics["full_recall"],
        "model_calls": model_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": cost_usd,
        "cost_source": cost_source,
        "latency_s": latency_s,
        "native_ranked_file_count": len(native_ranked_files),
        "note": "native Acc@K reported separately; never mixed with F1",
    }


def pair_common_results(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate ONLY after task-level results exist (paired per task)."""
    if not task_results:
        return {"task_count": 0}
    return {
        "task_count": len(task_results),
        "mean_precision": sum(r["precision"] for r in task_results) / len(task_results),
        "mean_recall": sum(r["recall"] for r in task_results) / len(task_results),
        "mean_f1": sum(r["f1"] for r in task_results) / len(task_results),
        "mean_fnr": sum(r["fnr"] for r in task_results) / len(task_results),
        "valid_output_rate": sum(bool(r["valid_output"]) for r in task_results) / len(task_results),
    }
