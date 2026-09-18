#!/usr/bin/env python3
"""Prepare fully blinded AI-assisted semantic-plausibility audit packages (ZERO API).

Derives an AI-blinded view from the existing human semantic-audit packets WITHOUT
touching them:

- 25 cases -> neutral case IDs (AI-CASE-001..025) with a fixed neutral seed;
- file-level rows (from the frozen rater form A) -> neutral row IDs
  (AI-ROW-0001..0361) and neutral candidate IDs (AI-CAND-0001..0361), each row
  carrying ONLY the semantic role:
      historical_changed_file  (was changed in the observed commit)
      omitted_candidate_file   (candidate NOT changed; potential omission)
- the original arm/source (observed_changed_file / top_ranked_omitted /
  matched_random_omitted) is preserved ONLY in a sealed private mapping;
- 5 batches of 5 cases per rater (chatgpt_batch_01..05, claude_batch_01..05)
  with different fixed per-rater seeds; every batch is self-contained (controlling
  prompt + output schema + its 5 case evidence files + neutral IDs only);
- seeds + per-batch hashes persisted in preparation_manifest.json.

No model/API calls. No scientific data opened. Human packets unchanged.

Usage:
    python scripts/semantic_ai_audit_prepare.py
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SRC = PROJECT / "research" / "semantic_audit"
OUT = SRC / "ai_blinded_v1"

SEED_NEUTRAL_CASES = 20260918
SEED_NEUTRAL_ROWS = 20260918
SEED_CHATGPT = 20260919
SEED_CLAUDE = 20260920

BATCH_SIZE = 5
N_BATCHES = 5
N_CASES = 25

FORBIDDEN_TOKENS = [
    "Route B",
    "route B",
    "ROUTE_B",
    "BM25",
    "bm25",
    "Graph",
    "graph",
    "Composite",
    "composite",
    "Random",
    "random",
    "Oracle",
    "oracle",
    "CIA",
    "top-ranked",
    "top_ranked",
    "matched_random",
    "matched-random",
    "matched random",
    "rank",
    "Rank",
    "proxy",
    "Precision",
    "precision",
    "Recall",
    "recall",
    "F1",
    "FNR",
    "AURC",
    "ORR",
    "harness",
    "thesis",
    "benchmark",
]

_ROW_FIELDS = ("observed_changed_file", "top_ranked_omitted", "matched_random_omitted")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _case_neutral_id(index: int) -> str:
    return f"AI-CASE-{index:03d}"


def _row_neutral_id(index: int) -> str:
    return f"AI-ROW-{index:04d}"


def _cand_neutral_id(index: int) -> str:
    return f"AI-CAND-{index:04d}"


def load_file_rows() -> list[dict]:
    """Decompose the frozen rater form A into file-level rows.

    Each original form row may list up to three files (observed changed file,
    top-ranked omitted, matched-random omitted). Each non-empty file cell becomes
    one AI file-level row with a semantic role. Original arm/source preserved
    for the sealed mapping only.
    """
    form = SRC / "rater_form_A.csv"
    rows: list[dict] = []
    import csv

    with open(form, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = (r.get("case_id") or "").strip()
            item = (r.get("item_index") or "").strip()
            for col in _ROW_FIELDS:
                path = (r.get(col) or "").strip()
                if not path:
                    continue
                role = "historical_changed_file" if col == "observed_changed_file" else "omitted_candidate_file"
                rows.append(
                    {
                        "case_id": cid,
                        "original_row_id": f"{cid}:item{item}",
                        "original_arm": col,
                        "semantic_role": role,
                        "file_path": path,
                    }
                )
    rows.sort(key=lambda r: (r["case_id"], r["original_row_id"], r["original_arm"]))
    return rows


def build_neutral_ids(file_rows: list[dict]) -> tuple[dict, dict]:
    """Assign neutral case / row / candidate IDs deterministically.

    Returns (case_map, row_map):
      case_map: original_case_id -> neutral_case_id
      row_map : (original_row_id, file_path) -> dict(neutral_row_id, neutral_candidate_id)
    """
    case_ids = sorted({r["case_id"] for r in file_rows})
    assert len(case_ids) == N_CASES, f"expected {N_CASES} cases, got {len(case_ids)}"
    rng = random.Random(SEED_NEUTRAL_CASES)
    shuffled_cases = list(case_ids)
    rng.shuffle(shuffled_cases)
    case_map = {cid: _case_neutral_id(i + 1) for i, cid in enumerate(shuffled_cases)}

    row_map: dict[tuple[str, str, str], dict] = {}
    neutral_index = 0
    for cid in shuffled_cases:
        case_rows = [r for r in file_rows if r["case_id"] == cid]
        row_rng = random.Random(f"{SEED_NEUTRAL_ROWS}:{case_map[cid]}")
        row_rng.shuffle(case_rows)
        for r in case_rows:
            neutral_index += 1
            row_map[(r["original_row_id"], r["original_arm"], r["file_path"])] = {
                "neutral_row_id": _row_neutral_id(neutral_index),
                "neutral_candidate_id": _cand_neutral_id(neutral_index),
            }
    return case_map, row_map


def load_case_evidence(cid: str) -> dict:
    """Read the original human packet (evidence_packet.json + diff.patch)."""
    p = SRC / cid
    ep = json.loads((p / "evidence_packet.json").read_text(encoding="utf-8"))
    diff = (p / "diff.patch").read_text(encoding="utf-8")
    return {
        "public_intent": ep.get("public_intent", ""),
        "candidate_universe_count": int(ep.get("candidate_universe_count", 0)),
        "candidate_universe_paths": list(ep.get("candidate_universe_paths", [])),
        "parent_context_edge_count": int(ep.get("graph_edge_count", 0)),
        "diff_patch": diff,
    }


def build_ai_case(cid: str, file_rows: list[dict], case_map: dict, row_map: dict) -> dict:
    """Build the AI-facing evidence file for one case (no arm/rank leakage)."""
    ncid = case_map[cid]
    ev = load_case_evidence(cid)
    ai_rows = []
    for r in [x for x in file_rows if x["case_id"] == cid]:
        key = (r["original_row_id"], r["original_arm"], r["file_path"])
        ids = row_map[key]
        ai_rows.append(
            {
                "neutral_row_id": ids["neutral_row_id"],
                "neutral_candidate_id": ids["neutral_candidate_id"],
                "semantic_role": r["semantic_role"],
                "file_path": r["file_path"],
            }
        )
    ai_rows.sort(key=lambda x: x["neutral_row_id"])
    return {
        "neutral_case_id": ncid,
        "public_intent": ev["public_intent"],
        "parent_source_context": {
            "candidate_universe_count": ev["candidate_universe_count"],
            "candidate_universe_paths": ev["candidate_universe_paths"],
            "parent_context_edge_count": ev["parent_context_edge_count"],
        },
        "diff_patch": ev["diff_patch"],
        "rows": ai_rows,
    }


def leak_check(ai_case: dict) -> list[str]:
    """Scan one AI-facing case for forbidden leakage tokens."""
    violations: list[str] = []
    text = json.dumps(ai_case)
    for tok in FORBIDDEN_TOKENS:
        if tok in text:
            violations.append(tok)
    return violations


def build_batches(neutral_case_ids: list[str], seed: int) -> list[list[str]]:
    """Split the 25 neutral case ids into 5 batches of 5 with a fixed seed."""
    rng = random.Random(seed)
    order = list(neutral_case_ids)
    rng.shuffle(order)
    return [order[i * BATCH_SIZE : (i + 1) * BATCH_SIZE] for i in range(N_BATCHES)]


def _batch_hash(batch: list[str], ai_cases: dict[str, dict], prompt_text: str, schema_text: str) -> str:
    h = hashlib.sha256()
    h.update(_sha256_text(prompt_text).encode())
    h.update(_sha256_text(schema_text).encode())
    for ncid in batch:
        h.update(_sha256_text(json.dumps(ai_cases[ncid], sort_keys=True)).encode())
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cases").mkdir(parents=True, exist_ok=True)
    for rater in ("chatgpt", "claude"):
        (OUT / rater).mkdir(parents=True, exist_ok=True)

    file_rows = load_file_rows()
    case_map, row_map = build_neutral_ids(file_rows)

    # --- AI-facing case evidence ---
    ai_cases: dict[str, dict] = {}
    all_leaks: list[str] = []
    for cid in sorted(case_map):
        ai = build_ai_case(cid, file_rows, case_map, row_map)
        ai_cases[ai["neutral_case_id"]] = ai
        all_leaks.extend(leak_check(ai))
        (OUT / "cases" / f"{ai['neutral_case_id']}.json").write_text(
            json.dumps(ai, indent=2), encoding="utf-8"
        )

    # --- sealed private mapping (NEVER sent to raters) ---
    sealed = {
        "package": "ai_blinded_v1",
        "created": "2026-09-18",
        "seeds": {
            "neutral_cases": SEED_NEUTRAL_CASES,
            "neutral_rows": SEED_NEUTRAL_ROWS,
            "chatgpt": SEED_CHATGPT,
            "claude": SEED_CLAUDE,
        },
        "note": "PRIVATE. Never include this file in any rater package.",
        "cases": {},
    }
    for cid, ncid in case_map.items():
        case_rows = []
        for r in [x for x in file_rows if x["case_id"] == cid]:
            key = (r["original_row_id"], r["original_arm"], r["file_path"])
            ids = row_map[key]
            case_rows.append(
                {
                    "original_row_id": r["original_row_id"],
                    "neutral_row_id": ids["neutral_row_id"],
                    "neutral_candidate_id": ids["neutral_candidate_id"],
                    "original_arm": r["original_arm"],
                    "semantic_role": r["semantic_role"],
                    "file_path": r["file_path"],
                }
            )
        case_rows.sort(key=lambda x: x["neutral_row_id"])
        sealed["cases"][ncid] = {
            "original_case_id": cid,
            "public_intent": load_case_evidence(cid)["public_intent"],
            "rows": case_rows,
        }
    (OUT / "sealed_mapping.json").write_text(json.dumps(sealed, indent=2), encoding="utf-8")

    # --- controlling prompt + schema copies ---
    prompt_text = (OUT / "AI_ASSISTED_SEMANTIC_AUDIT_PROMPT_2026-09-18.md").read_text(encoding="utf-8")
    schema_text = (OUT / "AI_AUDIT_OUTPUT_SCHEMA.json").read_text(encoding="utf-8")

    # --- batches per rater ---
    neutral_case_ids = sorted(ai_cases)
    seeds = {"chatgpt": SEED_CHATGPT, "claude": SEED_CLAUDE}
    manifest = {
        "package": "ai_blinded_v1",
        "created": "2026-09-18",
        "n_cases": N_CASES,
        "n_rows": len(row_map),
        "n_batches_per_rater": N_BATCHES,
        "batch_size": BATCH_SIZE,
        "seeds": seeds,
        "batches": {},
    }
    for rater, seed in seeds.items():
        batches = build_batches(neutral_case_ids, seed)
        for i, batch in enumerate(batches, start=1):
            batch_dir = OUT / rater / f"{rater}_batch_{i:02d}"
            batch_dir.mkdir(parents=True, exist_ok=True)
            (batch_dir / "AI_ASSISTED_SEMANTIC_AUDIT_PROMPT_2026-09-18.md").write_text(
                prompt_text, encoding="utf-8"
            )
            (batch_dir / "AI_AUDIT_OUTPUT_SCHEMA.json").write_text(schema_text, encoding="utf-8")
            (batch_dir / "cases").mkdir(parents=True, exist_ok=True)
            for ncid in batch:
                shutil.copyfile(OUT / "cases" / f"{ncid}.json", batch_dir / "cases" / f"{ncid}.json")
            bh = _batch_hash(batch, ai_cases, prompt_text, schema_text)
            manifest["batches"][f"{rater}_batch_{i:02d}"] = {
                "seed": seed,
                "case_ids": batch,
                "sha256": bh,
            }
    (OUT / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # --- spot-check placeholder (empty form) ---
    spot = OUT / "human_spotcheck_form.csv"
    if not spot.is_file():
        with open(spot, "w", encoding="utf-8", newline="") as f:
            f.write("spot_check_kind,neutral_case_id,neutral_row_id,semantic_role,"
                    "file_path,chatgpt_label,claude_label,human_verdict,notes\n")
            f.write("# PLACEHOLDER — generator fills this once rater outputs exist.\n")

    print("cases", len(ai_cases))
    print("rows", len(row_map))
    print("leak_tokens", all_leaks if all_leaks else "NONE")
    print("batches", len(manifest["batches"]))
    print("sealed mapping:", OUT / "sealed_mapping.json")
    print("manifest:", OUT / "preparation_manifest.json")
    return 1 if all_leaks else 0


if __name__ == "__main__":
    raise SystemExit(main())
