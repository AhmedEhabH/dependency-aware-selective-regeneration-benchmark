"""WP-2 Mission-12 E2E Smoke v2 - episode generator (F01-F05 + interface v2).

v2 pipeline fixes the five verified v1 instrument defects:
  F01 (DF1) replay guard: a replay call cannot be persisted into a paid
          episodes root; tests isolate to tmp_path.
  F02 (DF2) full-context repair: four-message request
          [system, original_user, previous_assistant_output, repair_instruction].
  F03 (DF3) run-level on-disk response cache keyed by canonical request_sha;
          repair carries its own request_sha and never overwrites the initial.
  F04 (DF4) real provider finish_reason propagated; length -> TRUNCATED
          (consumes the single repair).
  F05 (DF5) raw response text persisted immediately:
          episodes/<task>/<arm>/calls/<n>_<kind>.txt + sha256.

Interface v2: envelope extraction (I01), SEARCH matching ladder (I02),
SEARCH_ELLIPSIS (I03).
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.generate import _parent_texts, _raw_scope, _record_ledger
from benchmark.wp2.e2e.llm_client import CallResult
from benchmark.wp2.e2e.patch_format import (
    apply_patch_v2,
    parse_multi_file_patch_v2,
    unified_diff,
)
from benchmark.wp2.e2e.prompt import (
    build_prompt,
    build_repair_messages,
)
from benchmark.wp2.e2e.pycompile import py_compile_in_era
from benchmark.wp2.e2e.response_cache import ResponseCache
from benchmark.wp2.e2e.scopes import editable_filter
from benchmark.wp2.e2e.spec import (
    INTERFACE_VERSION,
    MAX_REPAIRS,
    MAX_TOKENS,
    MODEL,
    SMOKE_VERSION_V2,
    TEMPERATURE,
    TOP_P,
    spec_sha256,
)
from benchmark.wp2.e2e.task_inputs import load_task_input
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT_V2 = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"
ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
PROVIDER = "deepinfra/turbo"


class ReplayInPaidEvidenceError(RuntimeError):
    """F01: a replay (test/control) call must never enter a paid evidence root."""


def _sha(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _build_request(messages: list[dict[str, Any]], model: str = MODEL,
                   route: str = ROUTE, provider: str = PROVIDER,
                   temperature: float = TEMPERATURE, top_p: float = TOP_P,
                   max_tokens: int = MAX_TOKENS) -> dict:
    return {"model": model, "route": route, "provider": provider,
            "temperature": temperature, "top_p": top_p, "max_tokens": max_tokens,
            "messages": messages}


def _cache_entry_from_call(call: CallResult, request: dict, request_sha: str,
                           provider_call: bool, raw_file: str) -> dict:
    return {
        "request": request,
        "request_sha": request_sha,
        "provider_call": provider_call,
        "raw_file": raw_file,
        "text": call.text,
        "response_sha256": hashlib.sha256(call.text.encode("utf-8")).hexdigest(),
        "finish_reason": call.finish_reason,
        "prompt_tokens": call.prompt_tokens,
        "completion_tokens": call.completion_tokens,
        "cost_usd": call.cost_usd,
        "route": call.route,
        "provider": call.provider,
        "request_id": call.request_id,
    }


def _call_from_cache(entry: dict) -> CallResult:
    return CallResult(
        text=entry["text"], finish_reason=entry["finish_reason"],
        prompt_tokens=entry["prompt_tokens"], completion_tokens=entry["completion_tokens"],
        cost_usd=0.0, route=entry["route"], provider=entry["provider"],
        latency_s=0.0, request_id=entry["request_id"])


def _persist_raw(root: Path, task_id: str, arm: str, index: int, kind: str,
                 text: str) -> tuple[Path, str]:
    """F05: write calls/<n>_<kind>.txt immediately; return (path, sha256)."""
    d = root / "episodes" / task_id / arm / "calls"
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{index}_{kind}.txt"
    p.write_text(text, encoding="utf-8", newline="")
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    if digest != hashlib.sha256(text.encode("utf-8")).hexdigest():
        raise RuntimeError("F05 raw persistence hash mismatch")
    return p, digest


def _is_paid_episodes_root(base: Path) -> bool:
    """True if base resolves under a paid Smoke evidence episodes dir (v1 or v2)."""
    parts = [p.lower() for p in base.parts]
    return "episodes" in parts and any(
        f"e2e_smoke_eng_{ver}" in parts for ver in ("v1", "v2")
    )


def _persist_episode_v2(root: Path, rec: dict, diffs: list[str],
                        final_texts: dict[str, str]) -> None:
    """F01 guard + persist episode.json under the given root."""
    calls = rec.get("calls", [])
    replay = [c for c in calls if c.get("route") == "replay"]
    base = root / "episodes" / rec["task_id"] / rec["arm"]
    if replay and _is_paid_episodes_root(base):
        raise ReplayInPaidEvidenceError(
            f"replay route blocked from paid evidence root {base}: {replay}")
    base.mkdir(parents=True, exist_ok=True)
    (base / "episode.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    if rec["status"] == "APPLIED":
        if diffs:
            (base / "final_diff.patch").write_text(diffs[0], encoding="utf-8", newline="")
        for path, text in (final_texts or {}).items():
            p = base / "final_files" / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8", newline="")


def _validate_v2(text: str, editable: list[str], parent_texts: dict[str, str],
                 finish_reason: str, era_key: str) -> tuple[list[str], dict[str, str], list[dict], dict]:
    """Interface-v2 validation. Returns (errors, final_texts, block_results, stats)."""
    if finish_reason == "length":
        return ["TRUNCATED"], {}, [], {"finish_reason": "length"}
    try:
        sections, stats = parse_multi_file_patch_v2(text)
    except ValueError as exc:
        return [str(exc)], {}, [], {"envelope": {}}
    edited_paths = [p for p, _ in sections]
    if not edited_paths:
        return ["NO_BLOCKS"], {}, [], stats
    errors: list[str] = []
    for p in edited_paths:
        if is_test_path_v2(p):
            errors.append(f"TEST_PATH:{p}")
        if p not in editable:
            errors.append(f"OUT_OF_SCOPE_FILE:{p}")
    if errors:
        return errors, {}, [], stats
    try:
        final, block_results = apply_patch_v2(parent_texts, sections, set(editable))
    except ValueError as exc:
        return [str(exc)], {}, [], stats
    edited_py = {p: final[p] for p in edited_paths if p.endswith(".py")}
    if edited_py:
        pres = py_compile_in_era(era_key, edited_py)
        for p, st in pres.items():
            if st != "ok":
                errors.append(f"PY_COMPILE:{p}")
    return errors, final, block_results, stats


def _component_hashes(messages: list[dict[str, Any]]) -> dict[str, str]:
    """D2.2: sha256 of every message component of a request."""
    out: dict[str, str] = {}
    for i, m in enumerate(messages, start=1):
        out[f"message_{i}_{m.get('role', '')}"] = hashlib.sha256(
            str(m.get("content", "")).encode("utf-8")).hexdigest()
    return out


def run_episode_v2(task_id: str, arm: str, client: Any, ledger: Any,
                   cache: ResponseCache, root: Path = E2E_ROOT_V2) -> dict:
    """Run one (task, arm) episode with the v2 pipeline. Root may be a paid
    episodes root or a controls root; the replay guard enforces F01."""
    scope = editable_filter(task_id, _raw_scope(task_id, arm))
    if not scope["editable"]:
        rec = {
            "smoke_version": SMOKE_VERSION_V2, "interface_version": INTERFACE_VERSION,
            "task_id": task_id, "arm": arm, "status": "NO_SCOPE",
            "editable_set": [], "excluded": scope,
            "calls": [], "validation": {}, "repair_used": False,
            "edited_files": [], "diff_sha256": "", "envelope": {},
            "whitespace_tolerant_blocks": [], "flags": [],
            "spec_sha256": spec_sha256(), "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "episode_sha256": "",
        }
        rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
        _persist_episode_v2(root, rec, [], {})
        return rec

    ti = load_task_input(task_id)
    parent_texts = _parent_texts(task_id, scope["editable"])
    system, user, prompt_sha = build_prompt(ti, scope["editable"], parent_texts, scope)
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    request = _build_request(messages)
    request_sha = ResponseCache.request_sha(**request)
    calls: list[dict] = []
    block_results: list[dict] = []
    envelope: dict = {}
    provider_calls = 0
    actual_cost = 0.0

    entry = cache.get(request_sha)
    if entry is None:
        call = client.generate_messages(messages)
        provider_calls += 1
        actual_cost += call.cost_usd
        idx = 1
        raw_path, raw_sha = _persist_raw(root, task_id, arm, idx, "initial", call.text)
        entry = _cache_entry_from_call(call, request, request_sha, True, str(raw_path))
        entry["raw_sha256"] = raw_sha
        cache.put(request_sha, entry)
        _record_ledger(ledger, call, task_id, arm, "initial")
        calls.append(_call_entry_v2(entry, "initial", idx))
    else:
        calls.append(_call_entry_v2(entry, "initial_reused", 0))

    text = entry["text"]
    errors, final, block_results, stats = _validate_v2(
        text, scope["editable"], parent_texts, entry["finish_reason"], ti.era_key)
    if stats.get("envelope"):
        envelope = stats["envelope"]
    repair_used = False
    final_texts: dict[str, str] = {}
    diffs: list[str] = []

    if errors and MAX_REPAIRS >= 1:
        hint_ellipsis = any("SEARCH_ELLIPSIS" in e or "SEARCH_ERROR" in e for e in errors)
        repair_messages = build_repair_messages(system, user, text, errors, hint_ellipsis)
        repair_request = _build_request(repair_messages)
        repair_sha = ResponseCache.request_sha(**repair_request)
        entry2 = cache.get(repair_sha)
        if entry2 is None:
            call2 = client.generate_messages(repair_messages)
            provider_calls += 1
            actual_cost += call2.cost_usd
            idx = 2
            raw2_path, raw2_sha = _persist_raw(root, task_id, arm, idx, "repair", call2.text)
            entry2 = _cache_entry_from_call(call2, repair_request, repair_sha, True, str(raw2_path))
            entry2["raw_sha256"] = raw2_sha
            cache.put(repair_sha, entry2)
            _record_ledger(ledger, call2, task_id, arm, "repair")
            calls.append(_call_entry_v2(entry2, "repair", idx))
        else:
            calls.append(_call_entry_v2(entry2, "repair_reused", 0))
        errors2, final2, block_results2, stats2 = _validate_v2(
            entry2["text"], scope["editable"], parent_texts,
            entry2["finish_reason"], ti.era_key)
        if stats2.get("envelope"):
            envelope = stats2["envelope"]
        repair_used = True
        if block_results2:
            block_results = block_results2
        if not errors2:
            errors, final = errors2, final2

    status = "APPLIED" if not errors else "INVALID_AFTER_REPAIR"
    edited_files: list[str] = []
    if not final:
        final_texts = {}
    else:
        edited_files = sorted(final.keys())
        final_texts = final
        diffs = [unified_diff(parent_texts, final)]

    validation = {"initial": errors, "repair": errors2 if repair_used else []}
    whitespace_tolerant = [b for b in block_results if b.get("mode") == "WHITESPACE_TOLERANT"]
    rec = {
        "smoke_version": SMOKE_VERSION_V2, "interface_version": INTERFACE_VERSION,
        "task_id": task_id, "arm": arm, "status": status,
        "editable_set": scope["editable"], "excluded": scope,
        "prompt_sha256": prompt_sha,
        "request_sha_initial": request_sha,
        "request_sha_repair": repair_sha if repair_used else "",
        "repair_component_hashes": (_component_hashes(repair_messages)
                                    if repair_used else {}),
        "repair_request_sha256": (hashlib.sha256(
            json.dumps(repair_request, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest() if repair_used else ""),
        "reused_identical_prompt": False,
        "calls": calls, "validation": validation,
        "repair_used": repair_used,
        "edited_files": edited_files,
        "diff_sha256": _sha(diffs) if diffs else "",
        "envelope": envelope,
        "whitespace_tolerant_blocks": whitespace_tolerant,
        "flags": [], "spec_sha256": spec_sha256(),
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "episode_sha256": "",
    }
    rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
    _persist_episode_v2(root, rec, diffs, final_texts)
    rec["_provider_calls"] = provider_calls
    rec["_actual_cost"] = actual_cost
    return rec


def _call_entry_v2(entry: dict, kind: str, index: int) -> dict:
    return {
        "kind": kind, "index": index,
        "request_id": entry.get("request_id", ""),
        "route": entry.get("route", ""),
        "provider": entry.get("provider", ""),
        "prompt_tokens": entry.get("prompt_tokens", 0),
        "completion_tokens": entry.get("completion_tokens", 0),
        "cost_usd_actual": entry.get("cost_usd", 0.0),
        "cost_usd_nominal": entry.get("cost_usd", 0.0),
        "finish_reason": entry.get("finish_reason", ""),
        "response_sha256": entry.get("response_sha256", ""),
        "request_sha": entry.get("request_sha", ""),
        "provider_call": entry.get("provider_call", False),
        "raw_file": entry.get("raw_file", ""),
        "raw_sha256": entry.get("raw_sha256", ""),
    }
