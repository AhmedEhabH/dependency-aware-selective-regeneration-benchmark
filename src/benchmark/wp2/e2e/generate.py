"""WP-2 Mission-11 E2E Smoke - episode generator (B8).

Runs one (task, arm) episode: build prompt -> (reuse identical prompt if seen)
-> call client -> validate (D33) -> repair once (D34) -> persist.
Never reads evaluator-only data. Never edits test paths / creates files.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from benchmark.wp2.e2e.llm_client import Ledger
from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch, unified_diff
from benchmark.wp2.e2e.prompt import build_prompt, build_repair_prompt
from benchmark.wp2.e2e.pycompile import py_compile_in_era
from benchmark.wp2.e2e.scopes import editable_filter
from benchmark.wp2.e2e.spec import MAX_REPAIRS, SMOKE_VERSION, spec_sha256
from benchmark.wp2.e2e.task_inputs import load_task_input
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"


def _sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


class _PromptResponseCache:
    def __init__(self) -> None:
        self._map: dict[str, str] = {}

    def get(self, sha: str) -> str | None:
        return self._map.get(sha)

    def put(self, sha: str, text: str) -> None:
        self._map[sha] = text


def validate_output(text: str, editable: list[str], parent_texts: dict[str, str],
                    finish_reason: str, era_key: str) -> tuple[list[str], dict[str, str]]:
    """D33 validator. Returns (errors, final_texts)."""
    errors: list[str] = []
    if finish_reason == "length":
        errors.append("TRUNCATED")
        return errors, {}
    try:
        sections = parse_multi_file_patch(text)
    except ValueError as exc:
        return [str(exc)], {}
    edited_paths = [p for p, _ in sections]
    if not edited_paths:
        return ["NO_BLOCKS"], {}
    for p in edited_paths:
        if is_test_path_v2(p):
            errors.append(f"TEST_PATH:{p}")
        if p not in editable:
            errors.append(f"OUT_OF_SCOPE_FILE:{p}")
    if errors:
        return errors, {}
    try:
        final = apply_patch(parent_texts, sections, set(editable))
    except ValueError as exc:
        return [str(exc)], {}
    # py_compile the edited .py files
    edited_py = {p: final[p] for p in edited_paths if p.endswith(".py")}
    if edited_py:
        pres = py_compile_in_era(era_key, edited_py)
        for p, st in pres.items():
            if st != "ok":
                errors.append(f"PY_COMPILE:{p}")
    return errors, final


def run_episode(task_id: str, arm: str, client, ledger: Ledger,
                cache: _PromptResponseCache | None = None) -> dict:
    if cache is None:
        cache = _PromptResponseCache()
    scope = editable_filter(task_id, _raw_scope(task_id, arm))
    if not scope["editable"]:
        return _episode(task_id, arm, "NO_SCOPE", scope, [], {}, [], [], [], None)
    ti = load_task_input(task_id)
    system, user, prompt_sha = build_prompt(ti, scope["editable"], _parent_texts(task_id, scope["editable"]), scope)
    reused = False
    response = cache.get(prompt_sha)
    if response is None:
        call = client.generate(system, user)
        response = call.text
        cache.put(prompt_sha, response)
        calls = [_call_entry(call, "initial")]
        _record_ledger(ledger, call, task_id, arm, "initial")
    else:
        reused = True
        calls = []
    errors, final = validate_output(response, scope["editable"],
                                    _parent_texts(task_id, scope["editable"]),
                                    "stop", ti.era_key)
    repair_used = False
    if errors and MAX_REPAIRS >= 1:
        repair_user = build_repair_prompt(response, errors)
        call2 = client.generate(system, repair_user)
        response2 = call2.text
        cache.put(prompt_sha, response2)
        calls.append(_call_entry(call2, "repair"))
        _record_ledger(ledger, call2, task_id, arm, "repair")
        errors2, final2 = validate_output(response2, scope["editable"],
                                          _parent_texts(task_id, scope["editable"]),
                                          "stop", ti.era_key)
        repair_used = True
        if not errors2:
            errors, final = errors2, final2
        else:
            final = {}
    status = "APPLIED" if not errors else "INVALID_AFTER_REPAIR"
    if not final:
        repair_errors = errors2 if repair_used else errors
        return _episode(task_id, arm, status, scope, [prompt_sha], calls,
                        {"initial": errors, "repair": repair_errors}, [], [], reused)
    diff = unified_diff(_parent_texts(task_id, scope["editable"]), final)
    return _episode(task_id, arm, status, scope, [prompt_sha], calls,
                    {"initial": errors, "repair": [] if not repair_used else []},
                    list(final), [diff], reused, final_texts=final)


def _raw_scope(task_id: str, arm: str) -> list[str]:
    from benchmark.wp2.e2e.scopes import build_arm_scopes
    if arm == "AGENT_HARD":
        agent_file = E2E_ROOT / "scopes" / "agent_scopes_dev_eng.json"
        if agent_file.exists():
            d = json.loads(agent_file.read_text(encoding="utf-8"))
            return sorted(d.get("per_task", {}).get(task_id, {}).get("selected_paths", []))
        return []
    res = build_arm_scopes(task_id, arm)
    return res.get("raw", [])


def _parent_texts(task_id: str, paths: list[str]) -> dict[str, str]:
    import subprocess

    from benchmark.wp2.e2e.scopes import commits_of
    parent, _ = commits_of(task_id)
    out = {}
    for p in paths:
        r = subprocess.run(["git", "-C", str(PROJECT / "dist/pilot-repo-cache/saleor"),
                            "show", f"{parent}:{p}"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            out[p] = r.stdout
    return out


def _call_entry(call, kind: str) -> dict:
    return {"kind": kind, "request_id": call.request_id, "route": call.route,
            "provider": call.provider, "prompt_tokens": call.prompt_tokens,
            "completion_tokens": call.completion_tokens,
            "cost_usd_actual": call.cost_usd, "cost_usd_nominal": call.cost_usd,
            "finish_reason": call.finish_reason, "latency_s": call.latency_s,
            "response_sha256": hashlib.sha256(call.text.encode("utf-8")).hexdigest()}


def _record_ledger(ledger: Ledger, call, task_id: str, arm: str, kind: str) -> None:
    if ledger is None:
        return
    ledger.record({"stage": "SMOKE", "task_id": task_id, "arm": arm, "kind": kind,
                   "cost_usd": call.cost_usd, "prompt_tokens": call.prompt_tokens,
                   "completion_tokens": call.completion_tokens, "request_id": call.request_id})


class ReplayInPaidEvidenceError(RuntimeError):
    """F01: a replay (test/control) call must never enter a paid evidence root."""


def _is_paid_episodes_root(base: Path) -> bool:
    """True if base resolves under a paid Smoke evidence episodes dir (v1 or v2)."""
    parts = [p.lower() for p in base.parts]
    return "episodes" in parts and any(
        f"e2e_smoke_eng_{ver}" in parts for ver in ("v1", "v2")
    )


def _persist_episode(rec: dict, diffs: list[str], final_texts: dict[str, str]) -> None:
    """B8 step 6: persist episode.json for every status; final artifacts for APPLIED.

    F01 guard: a replay call must never be persisted into a paid Smoke evidence
    root (v1 or v2 episodes dir). Control labels persist under controls/.
    """
    base = E2E_ROOT / "episodes" / rec["task_id"] / rec["arm"]
    replay = [c for c in rec.get("calls", []) if c.get("route") == "replay"]
    if replay and _is_paid_episodes_root(base):
        raise ReplayInPaidEvidenceError(
            f"replay route blocked from paid evidence root {base}: {replay}")
    base.mkdir(parents=True, exist_ok=True)
    (base / "episode.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    if rec["status"] == "APPLIED":
        if diffs:
            (base / "final_diff.patch").write_text(diffs[0], encoding="utf-8", newline="")
        if final_texts:
            fdir = base / "final_files"
            fdir.mkdir(parents=True, exist_ok=True)
            for path, text in final_texts.items():
                p = fdir / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8", newline="")


def _episode(task_id, arm, status, scope, prompt_shas, calls, validation,
             edited_files, diffs, reused=False, repair_used=False, final_texts=None) -> dict:
    rec = {
        "smoke_version": SMOKE_VERSION, "task_id": task_id, "arm": arm,
        "status": status, "editable_set": scope.get("editable", []),
        "excluded": {"LARGE_FILE_EXCLUDED": scope.get("excluded_large", []),
                     "CONTEXT_BUDGET_EXCLUDED": scope.get("excluded_budget", [])},
        "prompt_sha256": prompt_shas[0] if prompt_shas else "",
        "reused_identical_prompt": reused, "calls": calls,
        "validation": validation, "repair_used": repair_used,
        "edited_files": sorted(set(edited_files)),
        "diff_sha256": _sha(diffs) if diffs else "",
        "flags": [], "spec_sha256": spec_sha256(), "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "episode_sha256": "",
    }
    rec["episode_sha256"] = _sha({k: v for k, v in rec.items() if k != "episode_sha256"})
    _persist_episode(rec, diffs, final_texts or {})
    return rec
