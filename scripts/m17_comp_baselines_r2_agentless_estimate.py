#!/usr/bin/env python3
# ruff: noqa: E501
"""M17_COMP_BASELINES_R2 — Phase 3: Agentless-style execution estimate.

NO LLM calls. NO paid execution. Offline only.

Measures representative official-Agentless-style repository-structure prompts
for the MAIN_297 parent snapshots with OFFLINE tokenizers (the frozen
deterministic tokenizer from benchmark.cheap_baselines.tokenize + chars-per-token
heuristics; no LLM tokenizer is available offline, identity marked UNVERIFIED),
then produces the estimate and the SIP-vs-Agentless protocol table inputs.

Official Agentless sources inspected (read-only):
  https://github.com/OpenAutoCoder/Agentless  @ 5ce5888b9f149beaace393957a55ea8ee46c9f71
  - agentless/fl/FL.py                LLMFL.obtain_relevant_files_prompt (file-level localization prompt)
  - agentless/fl/localize.py          file-level localization stage (^ top_n default 3, at most 5 files)
  - agentless/util/preprocess_data.py show_project_structure / filter_none_python / filter_out_test_files
  - get_repo_structure/get_repo_structure.py create_structure / parse_python_file
"""
from __future__ import annotations

import importlib.util
import json
import statistics
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

_tok_spec = importlib.util.spec_from_file_location(
    "frozen_tokenize", PROJECT / "src" / "benchmark" / "cheap_baselines" / "tokenize.py"
)
_tok_module = importlib.util.module_from_spec(_tok_spec)
assert _tok_spec and _tok_spec.loader
_tok_spec.loader.exec_module(_tok_module)
tokenize = _tok_module.tokenize

SCIENTIFIC = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
MANIFEST = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SALEOR_CACHE = Path(r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355\project\dist\pilot-repo-cache\saleor")
OUT = PROJECT / "research" / "competitor-baselines-r2" / "agentless_prompt_sizes_r2.json"

# Official Agentless FL prompt (verbatim from agentless/fl/FL.py at the inspected commit)
OFFICIAL_AGENTLESS_FL_PROMPT = """Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please only provide the full path and return at most 5 files.
The returned files should be separated by new lines ordered by most to least important and wrapped with ```
For example:
```
file1.py
file2.py
```
"""

# SIP prompt = P1_COMMON_PROMPT_TEMPLATE + sparse serialization policy (verbatim from
# src/benchmark/real_commits/p1_evaluation.py), rendered exactly as the frozen SiP ran.
SIP_COMMON = """You are an impact planner for a software repository using a common structured policy representation.

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
{rw_reason_codes}

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
SPARSE SERIALIZATION POLICY (PRESERVE-BY-OMISSION):
- Emit a decision ONLY for a candidate whose action is NOT "PRESERVE".
- NEVER emit a "PRESERVE" decision.
- Candidate ids that are NOT emitted are deterministically decoded by the harness as "PRESERVE".
- After decoding, every one of the {candidate_count} candidate ids is classified exactly once.
- Never emit an id outside [1, {candidate_count}] and never repeat an id.
[[/SERIALIZATION_POLICY]]
"""

P1_REASON_CODES = [
    "intent_reference", "content_match", "dependency_edge", "path_semantics",
    "cochange", "architecture_boundary", "data_dependency",
    "export_import_chain", "test_obligation", "uncertain_scope",
]


def ls_tree_files(cache: Path, parent: str) -> list[str]:
    lst = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", "-r", "-z", parent],
        capture_output=True, check=True,
    ).stdout
    files = []
    for rec in lst.split(b"\x00"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        if meta.split(b" ")[1] == b"blob":
            files.append(path.decode("utf-8", "replace"))
    return files


def build_agentless_structure(files: list[str]) -> dict:
    """Official create_structure + filter_none_python + filter_out_test_files semantics.

    Only .py files kept; entries under keys starting with 'test' are dropped
    (official filter_out_test_files). Non-python leaves are removed.
    """
    structure: dict = {}
    for f in files:
        if not f.endswith(".py"):
            continue
        parts = f.split("/")
        if any(p.startswith("test") for p in parts):
            continue  # official filter_out_test_files (key.startswith('test'))
        node = structure
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault(parts[-1], {"classes": [], "functions": [], "text": []})
    # filter_none_python: drop non-.py leaves (already done) and empty dirs
    return structure


def show_project_structure(structure: dict, spacing: int = 0) -> str:
    pp = ""
    for key, value in structure.items():
        if "." in key and ".py" not in key:
            continue  # skip none python files (official)
        if "." in key:
            pp += " " * spacing + str(key) + "\n"
        else:
            pp += " " * spacing + str(key) + "/" + "\n"
        if "classes" not in value:
            pp += show_project_structure(value, spacing + 4)
    return pp


def count_offline_tokens(text: str) -> dict:
    deter = len(tokenize(text))
    return {
        "frozen_deterministic_tokens": deter,
        "chars4_heuristic_tokens": max(1, len(text) // 4),
        "chars3_5_heuristic_tokens": max(1, int(len(text) / 3.5)),
        "chars": len(text),
    }


def render_sip_prompt(intent: str, case_id: str, candidate_paths: list[str],
                      graph_edges: list[str]) -> str:
    candidates = "\n".join(f"- {i}. {p}" for i, p in enumerate(candidate_paths, start=1))
    return SIP_COMMON.format(
        case_id=case_id, intent=intent, candidate_count=len(candidate_paths),
        candidates=candidates,
        graph_edges="\n".join(f"- {s} -> {d}" for s, d in graph_edges[:200]) or "- (none)",
        rw_reason_codes="\n".join(f"- {c}" for c in P1_REASON_CODES),
    )


def main() -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    task_ids = list(manifest["task_ids"])

    rows: dict = {}
    for i, tid in enumerate(task_ids):
        case_dir = SCIENTIFIC / tid
        intent = json.loads((case_dir / "public" / "intent.json").read_text(encoding="utf-8"))
        manifest_case = json.loads((case_dir / "case_manifest.json").read_text(encoding="utf-8"))
        parent = str(manifest_case["record"]["parent_commit"])
        universe = json.loads((case_dir / "public" / "candidate_universe.json").read_text(encoding="utf-8"))
        candidate_paths = sorted(str(r["path"]) for r in universe["records"])
        graph = json.loads((case_dir / "public" / "dependency_graph.json").read_text(encoding="utf-8"))
        edges = [[str(s), str(d)] for s, d in graph.get("edges", [])]

        all_files = ls_tree_files(SALEOR_CACHE, parent)
        struct = build_agentless_structure(all_files)
        tree_repr = show_project_structure(struct)
        agentless_prompt = OFFICIAL_AGENTLESS_FL_PROMPT.format(
            problem_statement=str(intent["intent_text"]), structure=tree_repr
        )
        sip_prompt = render_sip_prompt(
            str(intent["intent_text"]), tid, candidate_paths, edges
        )

        rows[tid] = {
            "parent_commit": parent,
            "agentless_structure_py_files": _file_count(struct),
            "agentless_prompt": count_offline_tokens(agentless_prompt),
            "sip_prompt": count_offline_tokens(sip_prompt),
        }
        if (i + 1) % 50 == 0 or (i + 1) == len(task_ids):
            print(f"  [{i+1}/{len(task_ids)}]", flush=True)

    def summary(key: str) -> dict:
        vals = sorted(r[key]["frozen_deterministic_tokens"] for r in rows.values())
        chars = sorted(r[key]["chars"] for r in rows.values())
        return {
            "frozen_deterministic_tokens": {
                "min": vals[0], "median": statistics.median(vals),
                "p90": vals[int(0.90 * (len(vals) - 1))], "max": vals[-1],
            },
            "chars": {"min": chars[0], "median": statistics.median(chars),
                      "p90": chars[int(0.90 * (len(chars) - 1))], "max": chars[-1]},
            "chars4_median_tokens": max(1, int(statistics.median(chars) / 4)),
        }

    out = {
        "official_agentless_repo": "https://github.com/OpenAutoCoder/Agentless",
        "official_commit_sha_inspected": "5ce5888b9f149beaace393957a55ea8ee46c9f71",
        "official_localization_prompt_source": "agentless/fl/FL.py — LLMFL.obtain_relevant_files_prompt (file-level localization stage)",
        "official_file_level_stage": "agentless/fl/localize.py (LLMFL.localize; top_n default 3; prompt instructs 'return at most 5 files')",
        "official_structure_representation": "agentless/util/preprocess_data.py show_project_structure() over get_repo_structure() (dirs + .py file names only; filter_none_python + filter_out_test_files applied)",
        "official_context_constant": "MAX_CONTEXT_LENGTH = 128000 (agentless/fl/FL.py)",
        "tokenizer_identity": {
            "frozen_deterministic": "benchmark.cheap_baselines.tokenize (deterministic snake/camel split, lowercase, frozen stopwords) — OFFLINE, AVAILABLE",
            "llm_tokenizer": "exact qwen3-coder / official model tokenizer NOT available offline; no model download permitted on this mission -> UNVERIFIED",
        },
        "n_tasks": len(task_ids),
        "agentless_style_repr": summary("agentless_prompt"),
        "sip_repr": summary("sip_prompt"),
        "per_task": rows,
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print("\nAgentless-style FL prompt (deterministic tokens):",
          out["agentless_style_repr"]["frozen_deterministic_tokens"])
    print("SIP prompt (deterministic tokens):", out["sip_repr"]["frozen_deterministic_tokens"])
    print("wrote:", OUT)
    return 0


def _file_count(node: dict) -> int:
    n = 0
    for v in node.values():
        if isinstance(v, dict) and set(v.keys()) >= {"classes", "functions", "text"}:
            n += 1  # a .py file leaf
        elif isinstance(v, dict):
            n += _file_count(v)
    return n


def _flatten(node: dict):
    for k, v in node.items():
        if isinstance(v, dict) and set(v.keys()) >= {"classes", "functions", "text"}:
            yield k, v
        elif isinstance(v, dict):
            yield from _flatten(v)


if __name__ == "__main__":
    raise SystemExit(main())
