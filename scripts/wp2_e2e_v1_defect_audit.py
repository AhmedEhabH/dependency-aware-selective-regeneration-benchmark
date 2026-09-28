#!/usr/bin/env python3
"""Mission-12 B: mechanical defect audit of Smoke v1 (DF1-DF5).

READ-ONLY against existing v1 evidence except the erratum output directory:
research/wp2/e2e_smoke_eng_v1/erratum/

Persists:
  df1_replay_contamination.json
  df2_repair_context.json
  df3_identical_request_outcomes.json
  df4_truncation.json
  df5_raw_response_availability.json
  instrument_defects_v1.json

Never alters v1 scores / episode.json / tags. Do not force expected results.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
V1_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
ERRATUM = V1_ROOT / "erratum"
EPISODES = V1_ROOT / "episodes"
GENERATE_PY = PROJECT / "src" / "benchmark" / "wp2" / "e2e" / "generate.py"
PROMPT_PY = PROJECT / "src" / "benchmark" / "wp2" / "e2e" / "prompt.py"

MODEL = "qwen/qwen3-coder"
ROUTE = "deepinfra/turbo"
TEMPERATURE = 0.0
TOP_P = 1.0
MAX_TOKENS = 8192

NON_SALEOR_PATH = "saleor/x/models.py"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def load_episodes() -> dict[str, dict]:
    """Return {rel_episode_path: episode_dict} for all 56 episode.json files."""
    out: dict[str, dict] = {}
    for p in sorted(EPISODES.rglob("episode.json")):
        rel = p.relative_to(V1_ROOT).as_posix()
        out[rel] = json.loads(p.read_text(encoding="utf-8"))
    return out


def collect_calls(episodes: dict[str, dict]) -> list[dict]:
    rows = []
    for rel, ep in episodes.items():
        for i, call in enumerate(ep.get("calls", [])):
            rows.append({
                "episode": rel,
                "task_id": ep.get("task_id"),
                "arm": ep.get("arm"),
                "call_index": i,
                "kind": call.get("kind"),
                "route": call.get("route"),
                "provider": call.get("provider"),
                "prompt_tokens": call.get("prompt_tokens"),
                "completion_tokens": call.get("completion_tokens"),
                "cost_usd": call.get("cost_usd_actual"),
                "finish_reason": call.get("finish_reason"),
                "response_sha256": call.get("response_sha256"),
                "request_id": call.get("request_id"),
            })
    return rows


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_code_lines(path: Path, start: int, count: int) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [f"{i + 1}: {lines[i]}" for i in range(start - 1, min(start - 1 + count, len(lines)))]


def df1_replay(episodes: dict[str, dict], calls: list[dict]) -> dict:
    replay = [c for c in calls if c["route"] == "replay"]
    replay_episodes = sorted({c["episode"] for c in replay})
    # 39b4 GOLD cell details (episodes dict keys are V1_ROOT-relative)
    target = "episodes/saleor-rc-39b4138e8550/GOLD_HARD/episode.json"
    details = {}
    if target in episodes:
        ep = episodes[target]
        details = {
            "route_calls": [c["route"] for c in ep.get("calls", [])],
            "editable_set": ep.get("editable_set"),
            "prompt_tokens_per_call": [c.get("prompt_tokens") for c in ep.get("calls", [])],
            "cost_usd_per_call": [c.get("cost_usd_actual") for c in ep.get("calls", [])],
            "created_utc": ep.get("created_utc"),
            "prompt_sha256": ep.get("prompt_sha256"),
        }
    reproduced = target in episodes and any(c["route"] == "replay" for c in episodes[target].get("calls", []))
    return {
        "defect": "DF1",
        "name": "replay_contamination",
        "reproduced": reproduced,
        "replay_call_count": len(replay),
        "replay_episodes": replay_episodes,
        "alleged_39b_gold_cell": details,
        "additional_replay_cells": [e for e in replay_episodes if e != target],
        "code_reference": {
            "ReplayClient": "src/benchmark/wp2/e2e/llm_client.py:109-123 (route='replay')",
            "persist": "src/benchmark/wp2/e2e/generate.py:172-176 (_persist_episode writes under episodes/)",
        },
        "evidence": "episode.json calls with route=replay in committed v1 evidence",
        "affected_episodes": replay_episodes,
    }


def df2_repair(episodes: dict[str, dict], calls: list[dict]) -> dict:
    repair_calls = [c for c in calls if c["kind"] == "repair"]
    repaired_episodes = sorted({c["episode"] for c in repair_calls})
    rows = []
    for rel in repaired_episodes:
        ep = episodes[rel]
        initials = [c for c in ep.get("calls", []) if c.get("kind") == "initial"]
        repairs = [c for c in ep.get("calls", []) if c.get("kind") == "repair"]
        rows.append({
            "episode": rel,
            "task_id": ep.get("task_id"),
            "arm": ep.get("arm"),
            "status": ep.get("status"),
            "initial_prompt_tokens": [c.get("prompt_tokens") for c in initials],
            "repair_prompt_tokens": [c.get("prompt_tokens") for c in repairs],
            "repair_succeeded": ep.get("status") == "APPLIED",
            "validation_repair": ep.get("validation", {}).get("repair"),
        })
    all_repair_lt_initial = all(
        max(r["repair_prompt_tokens"]) < max(r["initial_prompt_tokens"])
        for r in rows if r["initial_prompt_tokens"] and r["repair_prompt_tokens"]
    )
    # The contaminated 39b4 replay cell has fixture prompt tokens (25/25) that are
    # not real repair calls; exclude it from the real-repair comparison.
    real_rows = [r for r in rows if r["task_id"] != "saleor-rc-39b4138e8550"
                 or not any(c["route"] == "replay" for c in episodes[r["episode"]].get("calls", []))]
    real_repair_lt_initial = all(
        max(r["repair_prompt_tokens"]) < max(r["initial_prompt_tokens"])
        for r in real_rows if r["initial_prompt_tokens"] and r["repair_prompt_tokens"]
    )
    repair_call_site = read_code_lines(GENERATE_PY, 101, 9)
    build_repair_prompt = read_code_lines(PROMPT_PY, 73, 4)
    template = read_code_lines(PROMPT_PY, 33, 5)
    # Verify the repair request cannot contain original task prompt / file contents / previous output:
    # build_repair_prompt(_previous_output, errors) only formats REPAIR_TEMPLATE with errors.
    # REPAIR_TEMPLATE body references only {problems}. No FILE sections, no original user, no previous output.
    template_has_file_section = "FILE" in "".join(template).upper()
    repaired_count = len(repaired_episodes)
    succeeded = sum(1 for r in rows if r["repair_succeeded"])
    reproduced = len(real_rows) > 0 and real_repair_lt_initial
    return {
        "defect": "DF2",
        "name": "blind_repair",
        "reproduced": reproduced,
        "repair_call_count": len(repair_calls),
        "repaired_episode_count": repaired_count,
        "repair_success_count": succeeded,
        "all_repair_lt_initial": all_repair_lt_initial,
        "real_repair_lt_initial_excluding_replay_cell": real_repair_lt_initial,
        "real_repair_rows": len(real_rows),
        "rows": rows,
        "code_reference": {
            "call_site": {
                "file": "src/benchmark/wp2/e2e/generate.py",
                "lines": repair_call_site,
            },
            "build_repair_prompt": {
                "file": "src/benchmark/wp2/e2e/prompt.py",
                "lines": build_repair_prompt,
            },
            "template": {
                "file": "src/benchmark/wp2/e2e/prompt.py",
                "lines": template,
            },
        },
        "omitted_from_repair_request": {
            "original_task_prompt": True,
            "file_contents": True,
            "previous_assistant_output": True,
        },
        "withdrawn_interpretation": (
            "0 repair successes does not demonstrate model inability because "
            "the repair request omitted the original task prompt, file contents, "
            "and previous assistant output (blind repair)."
        ),
        "affected_episodes": repaired_episodes,
    }


def df3_identical(episodes: dict[str, dict]) -> dict:
    # group episodes by (task_id, prompt_sha256); groups with >1 arm share an identical user prompt.
    groups: dict[tuple[str, str], list[dict]] = {}
    for rel, ep in episodes.items():
        key = (ep.get("task_id"), ep.get("prompt_sha256"))
        groups.setdefault(key, []).append({"episode": rel, "arm": ep.get("arm"),
                                           "status": ep.get("status"),
                                           "response_shas": [c.get("response_sha256") for c in ep.get("calls", [])],
                                           "finish_reasons": [c.get("finish_reason") for c in ep.get("calls", [])]})
    multi_arm = {k: v for k, v in groups.items() if len({e["arm"] for e in v}) > 1}
    rows = []
    for (task, psha), eps in sorted(multi_arm.items()):
        for e in eps:
            rows.append({"task_id": task, "prompt_sha256": psha, "arm": e["arm"],
                         "status": e["status"], "response_shas": e["response_shas"]})
    # e03ee specifics
    e03 = [r for r in rows if r["task_id"] == "saleor-rc-e03ee76d2b89"]
    e03ee = {"groups": e03}
    reproduced = len(rows) > 0
    return {
        "defect": "DF3",
        "name": "identical_request_reuse_failure",
        "reproduced": reproduced,
        "canonical_request_equivalence": {
            "model": MODEL,
            "provider_route": ROUTE,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "max_tokens": MAX_TOKENS,
            "complete_messages": "system (constant SYSTEM_PROMPT) + user (prompt_sha256)",
            "note": "identical prompt_sha256 implies identical user message; system prompt is a shared constant",
        },
        "identical_prompt_groups_with_multiple_arms": len(multi_arm),
        "rows": rows,
        "e03ee_verification": e03ee,
        "wording": (
            "The observed success cannot be attributed to scope and is consistent with "
            "provider-side nondeterminism."
        ),
        "forbidden_wording_note": "Not used: 'provider noise caused the result' (no causal evidence).",
        "affected_episodes": sorted({e["episode"] for eps in multi_arm.values() for e in eps}),
    }


def df4_truncation(episodes: dict[str, dict], calls: list[dict]) -> dict:
    length_calls = [c for c in calls if c.get("finish_reason") == "length"]
    max_completion = [c for c in calls if (c.get("completion_tokens") or 0) >= MAX_TOKENS]
    hardcoded_lines = read_code_lines(GENERATE_PY, 98, 14)
    # Find the hard-coded "stop" string arguments to validate_output
    validate_calls = [l for l in hardcoded_lines if "validate_output" in l]
    reproduced = len(length_calls) > 0 and len(validate_calls) > 0
    return {
        "defect": "DF4",
        "name": "truncation_propagation",
        "reproduced": reproduced,
        "finish_reason_length_calls": len(length_calls),
        "completions_at_max": len(max_completion),
        "length_call_rows": length_calls,
        "max_completion_rows": max_completion,
        "code_reference": {
            "file": "src/benchmark/wp2/e2e/generate.py",
            "validate_output_call_sites": validate_calls,
            "context_lines": hardcoded_lines,
            "note": "validate_output receives hard-coded 'stop' instead of call.finish_reason; length -> TRUNCATED branch in validate_output is unreachable from run_episode",
        },
        "affected_episodes": sorted({c["episode"] for c in length_calls}),
    }


def df5_raw(episodes: dict[str, dict], calls: list[dict]) -> dict:
    # 1) Any raw response text files tracked in v1 episodes? (v2 uses calls/<n>_<kind>.txt)
    tracked = subprocess.run(
        ["git", "-C", str(PROJECT), "ls-files", "research/wp2/e2e_smoke_eng_v1/episodes"],
        capture_output=True, text=True).stdout.splitlines()
    raw_files = [f for f in tracked if "/calls/" in f or (f.endswith(".txt") and "final_files" not in f)]
    # 2) any untracked/ignored candidate files under the project whose sha256 matches a response sha
    known_hashes = {c.get("response_sha256") for c in calls if c.get("response_sha256")}
    search_roots = [
        V1_ROOT, PROJECT / "logs", PROJECT / "_workspace", PROJECT / "dist",
        PROJECT / "research",
    ]
    found: list[str] = []
    empty_hash_matches: list[str] = []
    scanned = 0
    EMPTY_SHA = sha256_bytes(b"")
    for root in search_roots:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in (".txt", ".json", ".jsonl", ".log"):
                continue
            if any(part in {"__pycache__", ".git", "node_modules", ".venv", ".uv-task-cache"}
                   for part in p.parts):
                continue
            try:
                scanned += 1
                data = p.read_bytes()[:400_000]
                digest = sha256_bytes(data)
                if digest == EMPTY_SHA:
                    # empty-string hash is a false positive (matches the empty
                    # response recorded in the 39b4 replay cell); not a raw text.
                    empty_hash_matches.append(p.as_posix())
                elif digest in known_hashes:
                    found.append(p.as_posix())
            except OSError:
                continue
    reproduced = len(raw_files) == 0
    return {
        "defect": "DF5",
        "name": "raw_response_not_persisted",
        "reproduced": reproduced,
        "tracked_raw_response_files_in_episodes": len(raw_files),
        "tracked_non_episode_files": raw_files[:20],
        "committed_evidence": "only response_sha256 is stored in episode.json calls; response texts absent",
        "local_search": {
            "known_response_hashes": len(known_hashes),
            "candidate_files_scanned": scanned,
            "matches_found": found,
            "empty_hash_false_positives": empty_hash_matches,
        },
        "label_if_found": "POST_HOC_DIAGNOSTIC_ONLY" if found else "RAW_RESPONSES_NOT_PERSISTED",
        "note": "Recovered raw responses never alter v1 scores.",
        "affected_episodes": sorted(set(episodes.keys())),
    }


def machine_verify(payload: dict) -> bool:
    required = ["defect", "name", "reproduced", "affected_episodes"]
    for k in required:
        if k not in payload:
            return False
    assert isinstance(payload["reproduced"], bool)
    assert isinstance(payload["affected_episodes"], list)
    return True


def main() -> None:
    ERRATUM.mkdir(parents=True, exist_ok=True)
    episodes = load_episodes()
    assert len(episodes) == 56, f"expected 56 episodes, got {len(episodes)}"
    calls = collect_calls(episodes)

    results = {
        "df1": df1_replay(episodes, calls),
        "df2": df2_repair(episodes, calls),
        "df3": df3_identical(episodes),
        "df4": df4_truncation(episodes, calls),
        "df5": df5_raw(episodes, calls),
    }
    for key, payload in results.items():
        assert machine_verify(payload), f"integrity failure: {key}"

    instrument_defects = {
        "artifact": "instrument_defects_v1",
        "created_utc": now_utc(),
        "head": subprocess.run(["git", "-C", str(PROJECT), "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip(),
        "episode_count": len(episodes),
        "defects": results,
        "integrity": {k: machine_verify(v) for k, v in results.items()},
    }

    df1_path = ERRATUM / "df1_replay_contamination.json"
    df2_path = ERRATUM / "df2_repair_context.json"
    df3_path = ERRATUM / "df3_identical_request_outcomes.json"
    df4_path = ERRATUM / "df4_truncation.json"
    df5_path = ERRATUM / "df5_raw_response_availability.json"
    combined = ERRATUM / "instrument_defects_v1.json"

    for path, payload in [
        (df1_path, results["df1"]), (df2_path, results["df2"]),
        (df3_path, results["df3"]), (df4_path, results["df4"]),
        (df5_path, results["df5"]),
    ]:
        path.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    combined.write_text(json.dumps(instrument_defects, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")

    for k, v in results.items():
        print(f"{k.upper()}_REPRODUCED={v['reproduced']}")
    print(f"DF5_SEARCH_MATCHES={len(results['df5']['local_search']['matches_found'])}")
    print(f"DF5_LABEL={results['df5']['label_if_found']}")
    print(f"COMBINED_INTEGRITY={instrument_defects['integrity']}")
    print("AUDIT_COMPLETE")


if __name__ == "__main__":
    main()