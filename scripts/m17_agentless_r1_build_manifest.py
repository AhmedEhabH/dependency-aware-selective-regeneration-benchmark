#!/usr/bin/env python3
# ruff: noqa: E501
"""M17 Agentless-style R1 - Phase A3: deterministic offline prompt manifest.

Builds, OFFLINE (zero API), the exact 297 Agentless-style file-level
localization prompts from the frozen MAIN_297 public inputs and the frozen
upstream Saleor cache, and records per-task identity fields:

  task_id
  problem_statement_sha256
  repo_structure_sha256
  prompt_sha256
  prompt_chars
  token_count_exact  (false: exact qwen3-coder tokenizer is NOT available offline)
  token_count_deterministic  (frozen benchmark.cheap_baselines.tokenize count)

The previous approximate estimate (agentless_prompt_sizes_r2.json) is NOT the
authority for execution; this manifest re-measures the exact frozen rendering.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.agentless_r1.prompt import (  # noqa: E402
    build_agentless_prompt,
    build_structure,
    ls_tree_py_files,
    sha256_text,
    show_project_structure,
    structure_file_paths,
)

SCIENTIFIC = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
MANIFEST = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SALEOR_CACHE = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
OUT = PROJECT / "research" / "competitor-agentless-r1" / "agentless_r1_prompt_manifest.json"

_tok_spec = importlib.util.spec_from_file_location(
    "frozen_tokenize", PROJECT / "src" / "benchmark" / "cheap_baselines" / "tokenize.py"
)
_tok_module = importlib.util.module_from_spec(_tok_spec)
assert _tok_spec and _tok_spec.loader
_tok_spec.loader.exec_module(_tok_module)
tokenize = _tok_module.tokenize


def _file_count(node: dict) -> int:
    n = 0
    for v in node.values():
        if isinstance(v, dict) and "classes" in v:
            n += 1
        elif isinstance(v, dict):
            n += _file_count(v)
    return n


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    task_ids = list(manifest["task_ids"])
    assert len(task_ids) == 297

    rows: dict[str, dict] = {}
    prompt_chars: list[int] = []
    deterministic_tokens: list[int] = []
    for i, tid in enumerate(task_ids):
        case_dir = SCIENTIFIC / tid
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        case_manifest = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        parent = str(case_manifest["record"]["parent_commit"])
        problem_statement = str(intent["intent_text"])

        files = ls_tree_py_files(SALEOR_CACHE, parent)
        structure = build_structure(files)
        structure_text = show_project_structure(structure).strip()
        structure_paths = structure_file_paths(structure)
        prompt = build_agentless_prompt(problem_statement, structure_text)

        problem_statement_sha = sha256_text(problem_statement)
        structure_sha = sha256_text(structure_text)
        prompt_sha = sha256_text(prompt)
        det_tokens = len(tokenize(prompt))
        prompt_chars.append(len(prompt))
        deterministic_tokens.append(det_tokens)

        rows[tid] = {
            "task_id": tid,
            "parent_commit": parent,
            "problem_statement_sha256": problem_statement_sha,
            "repo_structure_sha256": structure_sha,
            "prompt_sha256": prompt_sha,
            "prompt_chars": len(prompt),
            "prompt": prompt,
            "token_count_exact": False,
            "token_count_exact_note": ("exact qwen3-coder tokenizer not available offline; "
                                       "no model download permitted; deterministic count is a lower bound"),
            "token_count_deterministic": det_tokens,
            "structure_py_files": _file_count(structure),
            "structure_files": structure_paths,
            "context_window_ok": len(prompt) <= 128000,
        }
        if (i + 1) % 50 == 0 or (i + 1) == len(task_ids):
            print(f"  [{i+1}/{len(task_ids)}]", flush=True)

    summary = {
        "n_tasks": len(task_ids),
        "task_ids_sha256": manifest["task_ids_sha256"],
        "manifest_sha256": manifest["manifest_sha256"],
        "prompt_chars": {"min": min(prompt_chars), "median": int(sorted(prompt_chars)[len(prompt_chars) // 2]), "max": max(prompt_chars)},
        "token_count_deterministic": {"min": min(deterministic_tokens), "median": int(sorted(deterministic_tokens)[len(deterministic_tokens) // 2]), "max": max(deterministic_tokens)},
        "context_window_violations": sum(1 for r in rows.values() if not r["context_window_ok"]),
        "token_count_exact": False,
        "token_count_version": "benchmark.cheap_baselines.tokenize (frozen deterministic)",
    }
    out = {
        "protocol_freeze": "research/competitor-agentless-r1/AGENTLESS_STYLE_ADAPTATION_PROTOCOL_FREEZE.json",
        "official_agentless_repo": "https://github.com/OpenAutoCoder/Agentless",
        "official_commit_sha_inspected": "5ce5888b9f149beaace393957a55ea8ee46c9f71",
        "note": "Lookahead: this manifest is created BEFORE any MAIN_297 Agentless API execution; it fixes the exact frozen prompts sent to the model.",
        "summary": summary,
        "per_task": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print(f"\nmanifest written: {OUT}")
    print("context_window_violations:", summary["context_window_violations"])
    print("deterministic median:", summary["token_count_deterministic"]["median"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
