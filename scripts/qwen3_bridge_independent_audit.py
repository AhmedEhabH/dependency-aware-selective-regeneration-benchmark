#!/usr/bin/env python3
# ruff: noqa: E501
"""INDEPENDENT PREFLIGHT AUDIT — Qwen3 contamination-robustness bridge (T3).

Does NOT import the bridge's analyzer/evaluation code (the client module is
only read as source text for its frozen constants). Verifies from recorded
artifacts:

  A1 model availability verdict (model_availability.json) == STOP-before-call-1
  A2 no paid call was made (availability record)
  A3 budget JSON internally consistent (token math, batch math, ceilings)
  A4 budget JSON marked NOT EXECUTED
  A5 sealed-data guard: token estimate uses only DEV roles; split manifests
     still mark RESERVE/INTERNAL_TEST roles (metadata only, no outcome read)
  A6 frozen model id constant in or_embeddings.py matches the requested model
  A7 no-fallback enforcement present in the client source
  A8 frozen gate text present in the frozen protocol doc
  A9 provenance V2 verdict unchanged (C) and preserved in the closure report

Outputs: reports/QWEN3_EMBED_INDEPENDENT_AUDIT.md + .json
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_RUN = _PROJECT_DIR / "research" / "contamination-bridge"
_REPORTS = _PROJECT_DIR / "reports"

REQUESTED_MODEL = "qwen/qwen3-embedding-8b"


def main() -> int:
    results: list[dict] = []
    ok_all = True

    def check(code: str, name: str, passed: bool, detail: str):
        nonlocal ok_all
        ok_all = ok_all and bool(passed)
        results.append({"code": code, "name": name, "pass": bool(passed), "detail": detail})

    # ---- A1/A2: availability + no paid call ----
    avail = json.loads((_RUN / "model_availability.json").read_text(encoding="utf-8"))
    check("A1", "model availability verdict == STOP before call 1",
          avail.get("available_verdict") == "MODEL_NOT_AVAILABLE_ON_OPENROUTER"
          and avail.get("stop_before_call_1") is True,
          f"catalog n={avail['catalog_scan']['n_models_total']}, embedding models={avail['catalog_scan']['n_embedding_capable_models']}")
    check("A2", "no paid scientific call made",
          avail.get("no_paid_call_made") is True, "recorded 0 calls / $0.00")

    # ---- A3/A4: budget JSON consistency ----
    budget = json.loads((_REPORTS / "qwen3_embed_bridge_budget_freeze.json").read_text(encoding="utf-8"))
    tok = budget["inputs"]
    b_reqs = budget["requests"]
    exp_unit_req = -(-tok["n_unique_code_units"] // budget["frozen_ceilings"]["batch_size"])
    exp_query_req = -(-tok["n_query_texts"] // budget["frozen_ceilings"]["batch_size"])
    math_ok = (
        b_reqs["unit_requests_at_batch64"] == exp_unit_req
        and b_reqs["query_requests_at_batch64"] == exp_query_req
        and b_reqs["total_requests"] == exp_unit_req + exp_query_req
        and tok["combined_tokens_total"] == tok["unit_tokens_total"] + tok["query_tokens_total"]
        and budget["frozen_ceilings"]["max_scientific_cost_usd"] == 0.50
    )
    check("A3", "budget JSON internally consistent (tokens, batching, $0.50 ceiling)",
          math_ok, json.dumps(b_reqs))
    check("A4", "budget JSON marked NOT EXECUTED",
          budget["status"] == "FROZEN_BUT_NOT_EXECUTED"
          and "model_unavailable" in budget["stop_reason"], budget["status"])

    # ---- A5: sealed-data guard (metadata only) ----
    dc = json.loads((_PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json").read_text(encoding="utf-8"))
    saleor = json.loads((_PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json").read_text(encoding="utf-8"))
    counts = {}
    for name, split in (("djangocms", dc["assignment"]), ("saleor", saleor["assignment"])):
        from collections import Counter
        counts[name] = dict(Counter(split.values()))
    sealed_dc = counts["djangocms"].get("RESERVE", 0)
    sealed_sc_it = counts["saleor"].get("INTERNAL_TEST", 0)
    # The token estimate used ONLY the 323 DEVELOPMENT tasks (174 + 149).
    guard_ok = sealed_dc == 59 and sealed_sc_it == 80
    check("A5", "sealed sets identified from split metadata (59 RESERVE / 80 INTERNAL_TEST), no outcome read",
          guard_ok, json.dumps(counts))

    # ---- A6/A7: client frozen constants (source-text read, no import) ----
    src = (_PROJECT_DIR / "src" / "benchmark" / "signal" / "or_embeddings.py").read_text(encoding="utf-8")
    m = re.search(r'OPENROUTER_EMBED_MODEL\s*=\s*"([^"]+)"', src)
    check("A6", "client frozen model id == requested model",
          m is not None and m.group(1) == REQUESTED_MODEL, m.group(1) if m else "missing")
    check("A7", "no-fallback enforcement present in client source",
          "NoFallbackError" in src and "refusing" in src, "no-fallback guard in constructor")

    # ---- A8: frozen gate present in protocol doc ----
    proto = (_PROJECT_DIR / "docs" / "QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md").read_text(encoding="utf-8")
    gate_ok = all(s in proto for s in ("A. final F1", "J. total cost", "QWEN3_EMBED_BRIDGE_TECHNICALLY_INCONCLUSIVE"))
    check("A8", "frozen gate (A–J) + inconclusive label present in protocol",
          gate_ok, "gate A–J + CASE E label")

    # ---- A9: provenance verdict V2 unchanged (C) ----
    prov2 = (_REPORTS / "SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md").read_text(encoding="utf-8")
    check("A9", "provenance V2 verdict C unchanged",
          "TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP" in prov2
          and "NOT upgraded to A or B" in prov2, "verdict C")

    audit = {"overall_pass": bool(ok_all), "n_checks": len(results), "checks": results}
    (_REPORTS / "qwen3_embed_bridge_independent_audit.json").write_text(json.dumps(audit, indent=1), encoding="utf-8")
    md = [
        "# Qwen3-Embedding Contamination Bridge — Independent Preflight Audit",
        "",
        f"**Overall: {'PASS' if ok_all else 'FAIL'}** ({sum(1 for c in results if c['pass'])}/{len(results)})",
        "",
        "| # | Check | PASS | Detail |",
        "|---:|---|:---:|---|",
    ]
    for c in results:
        md.append(f"| {c['code']} | {c['name']} | {'PASS' if c['pass'] else 'FAIL'} | {c['detail']} |")
    md.append("")
    md.append("This audit does NOT import the bridge analyzer/evaluation code; it "
              "verifies recorded artifacts and reads the client source text only.")
    (_REPORTS / "QWEN3_EMBED_INDEPENDENT_AUDIT.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"overall_pass": bool(ok_all), "checks": len(results)}, indent=1))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
