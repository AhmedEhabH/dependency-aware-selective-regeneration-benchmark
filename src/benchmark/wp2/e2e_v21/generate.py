"""Mission-12B v2.1 - generation driver module (T2).

v2.1 fork of the frozen v2 episode generator. Key differences (frozen policy):
- uses the v21 TRANSPORT_V21 client (HOLD-gated, 4 attempts, pacing);
- v21 cache ONLY (historical v2 cache is never read or written);
- ledger fsync after every provider call;
- raw responses persisted immediately;
- partial failure preserves all earlier successful-call evidence;
- a transport failure produces a GENERATION_FAIL episode record that NEVER
  replaces an existing calls list with [] (partial success is kept);
- one repair maximum (unchanged Interface-v2 semantics);
- generator-equivalent scope loader (AGENT scopes read from 'per_task');
- no evaluation in this module.

Reuses frozen v2 instrument helpers (patch parsing, prompt, pycompile,
validation, response cache) WITHOUT modifying them and WITHOUT touching any
v2 evidence path.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from benchmark.wp2.e2e.generate import _parent_texts, _raw_scope, _record_ledger
from benchmark.wp2.e2e.generate_v2 import (
    _cache_entry_from_call,
    _component_hashes,
    _persist_raw,
    _validate_v2,
)
from benchmark.wp2.e2e.patch_format import unified_diff
from benchmark.wp2.e2e.prompt import build_prompt, build_repair_messages
from benchmark.wp2.e2e.response_cache import ResponseCache
from benchmark.wp2.e2e.scopes import editable_filter
from benchmark.wp2.e2e.spec import (
    INTERFACE_VERSION,
    MAX_REPAIRS,
    MAX_TOKENS,
    MODEL,
    TEMPERATURE,
    TOP_P,
    spec_sha256,
)
from benchmark.wp2.e2e.task_inputs import load_task_input
from benchmark.wp2.e2e_v21.transport import (
    HOLD_ACTIVE,
    GenerationFail,
    NonRetryableError,
    V21HttpClient,
)

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT_V21 = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v21"
ROUTE = "openrouter:qwen/qwen3-coder@deepinfra/turbo"
PROVIDER = "deepinfra/turbo"
SMOKE_VERSION_V21 = "wp2-e2e-smoke-eng-v21"


class ReplayInPaidEvidenceError(RuntimeError):
    """A replay (test/control) call must never enter the paid v21 episodes root."""


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


def _call_entry_v21(entry: dict, kind: str, index: int) -> dict:
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


def _persist_episode_v21(root: Path, rec: dict, diffs: list[str],
                         final_texts: dict[str, str],
                         subdir: str = "episodes",
                         label: str | None = None) -> None:
    """Persist episode.json under the v21 evidence root (replay guard).

    ``subdir`` is 'episodes' for the main run and 'variance' for variance
    replicates. ``label`` distinguishes replicates (e.g. var_r1) so r1 can
    never overwrite r2.

    F01 guard: a replay (test/control) call may only be persisted under a
    non-paid subdir (e.g. 'controls'); it is blocked from the paid 'episodes'
    root.
    """
    calls = rec.get("calls", [])
    replay = [c for c in calls if c.get("route") == "replay"]
    if replay and subdir == "episodes":
        raise ReplayInPaidEvidenceError(
            f"replay route blocked from v21 paid evidence root: {replay}")
    arm_dir = label or rec["arm"]
    base = root / subdir / rec["task_id"] / arm_dir
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


def _generation_fail_rec(task_id: str, arm: str, calls: list[dict],
                         terminal_reason: str) -> dict:
    """GENERATION_FAIL record. NEVER replaces an existing calls list with []."""
    return {
        "smoke_version": SMOKE_VERSION_V21, "interface_version": INTERFACE_VERSION,
        "task_id": task_id, "arm": arm, "status": "GENERATION_FAIL",
        "editable_set": [], "excluded": {},
        "prompt_sha256": "", "request_sha_initial": "", "request_sha_repair": "",
        "repair_component_hashes": {}, "repair_request_sha256": "",
        "reused_identical_prompt": False,
        "calls": calls, "validation": {}, "repair_used": False,
        "edited_files": [], "diff_sha256": "", "envelope": {},
        "whitespace_tolerant_blocks": [], "flags": ["TRANSPORT_FAIL", terminal_reason],
        "spec_sha256": spec_sha256(), "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "episode_sha256": "",
    }


def run_episode_v21(task_id: str, arm: str, client: V21HttpClient, ledger: Any,
                    cache: ResponseCache, root: Path = E2E_ROOT_V21,
                    subdir: str = "episodes", label: str | None = None) -> dict:
    """Run one (task, arm) episode with the v2.1 pipeline (T2).

    ``subdir`` selects the evidence subdirectory ('episodes' for main,
    'variance' for variance replicates). ``label`` distinguishes replicate
    paths (var_r1 / var_r2) so r1 can never overwrite r2.

    Transport failures become GENERATION_FAIL records that preserve any
    successful calls already made. NO_SCOPE episodes make 0 provider calls.
    """
    scope = editable_filter(task_id, _raw_scope(task_id, arm))
    if not scope["editable"]:
        rec = {
            "smoke_version": SMOKE_VERSION_V21, "interface_version": INTERFACE_VERSION,
            "task_id": task_id, "arm": arm, "status": "NO_SCOPE",
            "editable_set": [], "excluded": scope,
            "calls": [], "validation": {}, "repair_used": False,
            "edited_files": [], "diff_sha256": "", "envelope": {},
            "whitespace_tolerant_blocks": [], "flags": [],
            "spec_sha256": spec_sha256(), "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "episode_sha256": "",
        }
        rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
        _persist_episode_v21(root, rec, [], {}, subdir, label)
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

    # ---- initial call ------------------------------------------------------
    arm_dir = label or arm
    try:
        entry = cache.get(request_sha)
        if entry is None:
            call = client.generate_messages(messages)
            provider_calls += 1
            actual_cost += call.cost_usd
            idx = 1
            raw_path, raw_sha = _persist_raw(root, task_id, arm_dir, idx, "initial",
                                             call.text, episodes_subdir=subdir)
            entry = _cache_entry_from_call(call, request, request_sha, True, str(raw_path))
            entry["raw_sha256"] = raw_sha
            cache.put(request_sha, entry)
            _record_ledger(ledger, call, task_id, arm, "initial")
            calls.append(_call_entry_v21(entry, "initial", idx))
        else:
            calls.append(_call_entry_v21(entry, "initial_reused", 0))
    except (HOLD_ACTIVE, GenerationFail, NonRetryableError) as exc:
        rec = _generation_fail_rec(task_id, arm, calls, f"{type(exc).__name__}: {exc}")
        rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
        _persist_episode_v21(root, rec, [], {}, subdir, label)
        rec["_provider_calls"] = provider_calls
        rec["_actual_cost"] = actual_cost
        return rec

    text = entry["text"]
    errors, final, block_results, stats = _validate_v2(
        text, scope["editable"], parent_texts, entry["finish_reason"], ti.era_key)
    if stats.get("envelope"):
        envelope = stats["envelope"]
    repair_used = False
    final_texts: dict[str, str] = {}
    diffs: list[str] = []

    # ---- repair (max 1) -----------------------------------------------------
    if errors and MAX_REPAIRS >= 1:
        hint_ellipsis = any("SEARCH_ELLIPSIS" in e or "SEARCH_ERROR" in e for e in errors)
        repair_messages = build_repair_messages(system, user, text, errors, hint_ellipsis)
        repair_request = _build_request(repair_messages)
        repair_sha = ResponseCache.request_sha(**repair_request)
        try:
            entry2 = cache.get(repair_sha)
            if entry2 is None:
                call2 = client.generate_messages(repair_messages)
                provider_calls += 1
                actual_cost += call2.cost_usd
                idx = 2
                raw2_path, raw2_sha = _persist_raw(root, task_id, arm_dir, idx, "repair",
                                                   call2.text, episodes_subdir=subdir)
                entry2 = _cache_entry_from_call(call2, repair_request, repair_sha, True, str(raw2_path))
                entry2["raw_sha256"] = raw2_sha
                cache.put(repair_sha, entry2)
                _record_ledger(ledger, call2, task_id, arm, "repair")
                calls.append(_call_entry_v21(entry2, "repair", idx))
            else:
                calls.append(_call_entry_v21(entry2, "repair_reused", 0))
        except (HOLD_ACTIVE, GenerationFail, NonRetryableError) as exc:
            # partial success preserved: the initial call record stays in calls
            rec = _generation_fail_rec(task_id, arm, calls, f"{type(exc).__name__}: {exc}")
            rec["prompt_sha256"] = prompt_sha
            rec["request_sha_initial"] = request_sha
            rec["request_sha_repair"] = repair_sha
            rec["repair_component_hashes"] = _component_hashes(repair_messages)
            rec["repair_request_sha256"] = hashlib.sha256(
                json.dumps(repair_request, sort_keys=True, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            rec["validation"] = {"initial": errors}
            rec["repair_used"] = True
            rec["editable_set"] = scope["editable"]
            rec["excluded"] = scope
            rec["envelope"] = envelope
            rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
            _persist_episode_v21(root, rec, [], {}, subdir, label)
            rec["_provider_calls"] = provider_calls
            rec["_actual_cost"] = actual_cost
            return rec
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
        "smoke_version": SMOKE_VERSION_V21, "interface_version": INTERFACE_VERSION,
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
    _persist_episode_v21(root, rec, diffs, final_texts, subdir, label)
    rec["_provider_calls"] = provider_calls
    rec["_actual_cost"] = actual_cost
    return rec
