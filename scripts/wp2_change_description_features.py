#!/usr/bin/env python3
"""WP-2 developer-change-description deterministic feature audit (D3) - ZERO API.

For MAIN (297) and DEV (150) tasks, produce descriptive, deterministic features
from the label-free commit change description (case manifest ``intent_text``):
- first-line/title text;
- full message length;
- number of lines;
- code-like token / backtick / function-name density (deterministic rules);
- whether a body exists.

No LLM relabeling. Selector predictions are NOT modified. Also records the
future sensitivity plan (FULL_DESCRIPTION primary vs TITLE_ONLY later).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

MAIN_MANIFEST = PROJECT / "research" / "wp1b" / "wp1b_main_297_manifest.json"
SCIENTIFIC = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
SPLIT = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json"
OUT = PROJECT / "research" / "wp2" / "developer_change_description_features_2026-09-23.json"

_FN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\(")
_BACKTICK_RE = re.compile(r"`[^`]*`")
_CODE_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\.")


def features(intent_text: str) -> dict:
    text = intent_text or ""
    lines = [ln for ln in text.splitlines()]
    first_line = lines[0].strip() if lines else ""
    body = lines[1:] if len(lines) > 1 else []
    body_text = "\n".join(body)
    return {
        "title": first_line,
        "full_message_length": len(text),
        "n_lines": len(lines),
        "has_body": bool(body_text.strip()),
        "body_length": len(body_text),
        "n_backtick_tokens": len(_BACKTICK_RE.findall(text)),
        "n_function_call_tokens": len(_FN_RE.findall(text)),
        "n_dotted_code_tokens": len(_CODE_TOKEN_RE.findall(text)),
        "feature_sha256": hashlib.sha256(
            json.dumps(
                {
                    "title": first_line,
                    "len": len(text),
                    "n_lines": len(lines),
                    "has_body": bool(body_text.strip()),
                    "n_backtick_tokens": len(_BACKTICK_RE.findall(text)),
                    "n_function_call_tokens": len(_FN_RE.findall(text)),
                    "n_dotted_code_tokens": len(_CODE_TOKEN_RE.findall(text)),
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
    }


def load_intent(tid: str) -> str:
    mp = SCIENTIFIC / tid / "case_manifest.json"
    if not mp.exists():
        return ""
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    rec = manifest.get("record", {})
    if rec.get("intent_text"):
        return rec["intent_text"]
    intent_file = SCIENTIFIC / tid / "public" / "intent.json"
    if intent_file.exists():
        return json.loads(intent_file.read_text(encoding="utf-8")).get("intent_text", "")
    return ""


def main() -> int:
    main_ids = json.loads(MAIN_MANIFEST.read_text(encoding="utf-8"))["task_ids"]
    assign = json.loads(SPLIT.read_text(encoding="utf-8"))["assignment"]
    dev_ids = sorted(t for t, a in assign.items() if a in ("DEV_TRAIN", "DEV_VALIDATION"))
    assert len(main_ids) == 297 and len(dev_ids) == 150

    main_feats = {tid: features(load_intent(tid)) for tid in main_ids}
    dev_feats = {tid: features(load_intent(tid)) for tid in dev_ids}

    artifact = {
        "artifact": "developer_change_description_features",
        "date": "2026-09-23",
        "status": "DETERMINISTIC_FEATURES_ONLY_NO_LLM",
        "sensitivity_plan": {
            "primary_spec": "FULL developer change description",
            "title_only_sensitivity": "TITLE_ONLY later sensitivity analysis (amendment K: recorded, NOT executed)",
            "target_derived_signatures_forbidden": True,
        },
        "main_297": main_feats,
        "dev_150": dev_feats,
        "summary": {
            "main_297": {
                "n": len(main_feats),
                "has_body": sum(1 for f in main_feats.values() if f["has_body"]),
                "mean_len": round(sum(f["full_message_length"] for f in main_feats.values()) / len(main_feats), 1),
                "n_with_backticks": sum(1 for f in main_feats.values() if f["n_backtick_tokens"] > 0),
            },
            "dev_150": {
                "n": len(dev_feats),
                "has_body": sum(1 for f in dev_feats.values() if f["has_body"]),
                "mean_len": round(sum(f["full_message_length"] for f in dev_feats.values()) / len(dev_feats), 1),
                "n_with_backticks": sum(1 for f in dev_feats.values() if f["n_backtick_tokens"] > 0),
            },
        },
    }
    OUT.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print("summary:", json.dumps(artifact["summary"], indent=1))
    print("wrote", OUT.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
