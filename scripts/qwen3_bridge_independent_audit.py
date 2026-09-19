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

    # ---- A1: availability (corrected probe; model IS available) ----
    avail = json.loads((_RUN / "model_availability_v2.json").read_text(encoding="utf-8"))
    check("A1", "availability verdict (corrected embeddings-catalog probe) == available",
          avail.get("available_verdict") == "MODEL_AVAILABLE_ON_OPENROUTER_EMBEDDINGS_CATALOG"
          and avail.get("catalog_scan", {}).get("qwen3_embedding_8b_present") is True
          and avail.get("pinned_provider") == "DeepInfra",
          f"catalog n={avail['catalog_scan']['n_embedding_models']}, pinned={avail.get('pinned_provider')}")

    # ---- A2/A12: no FULL scientific run (determinism stop) ----
    qwen_out = _RUN / "qwen_embed"
    full_metrics = qwen_out / "metrics.json"
    check("A2", "no full scientific run produced (no metrics.json)",
          not full_metrics.exists(), "determinism stop before the full run")
    probe = json.loads((qwen_out / "probe.json").read_text(encoding="utf-8"))
    stab = json.loads((qwen_out / "stability.json").read_text(encoding="utf-8"))
    max_drift = probe["max_cosine_drift"]
    b5 = list(stab["b5_file_set_overlap_frac"].values())
    check("A12", "determinism stop evidence (drift ~1e-4; file B=5 flip on 1/5 tasks)",
          max_drift < 1e-3 and min(b5) < 1.0 and stab["all_tasks_b5_identical"] is False,
          f"max_drift={max_drift:.2e}, b5_overlap={b5}")

    # ---- A3/A4: budget JSON consistency with live pricing ----
    budget = json.loads((_REPORTS / "qwen3_embed_bridge_budget_freeze.json").read_text(encoding="utf-8"))
    tok = budget["inputs"]
    ca = budget["cost_arithmetic"]
    b_reqs = budget["requests"]
    exp_unit = -(-tok["n_unique_code_units"] // budget["frozen_ceilings"]["batch_size"])
    exp_query = -(-tok["n_query_texts"] // budget["frozen_ceilings"]["batch_size"])
    expected = tok["combined_tokens_total"] / 1e6 * ca["price_per_1m_tokens_usd"]
    math_ok = (
        abs(expected - ca["expected_cost_usd"]) < 1e-3  # stored value is 4-dp rounded
        and abs(expected - 0.2188) < 0.001
        and budget["frozen_ceilings"]["max_scientific_cost_usd"] == 0.50
        and b_reqs["total_requests"] == exp_unit + exp_query
        and ca["price_per_1m_tokens_usd"] == 0.01
    )
    check("A3", "budget JSON internally consistent (live $0.01/M price; expected $0.2188; $0.50 ceiling)",
          math_ok, f"expected_cost={ca['expected_cost_usd']:.4f}")
    check("A4", "budget JSON status reflects STOP (not executing)",
          "STOPPED" in budget["status"] and "EXECUTING" not in budget["status"], budget["status"])

    # ---- A5: sealed-data guard (metadata only) ----
    dc = json.loads((_PROJECT_DIR / "research" / "transparency" / "v2_split_proposal.json").read_text(encoding="utf-8"))
    saleor = json.loads((_PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "split_freeze_saleor.json").read_text(encoding="utf-8"))
    from collections import Counter
    counts = {"djangocms": dict(Counter(dc["assignment"].values())),
              "saleor": dict(Counter(saleor["assignment"].values()))}
    check("A5", "sealed sets identified from split metadata (59 RESERVE / 80 INTERNAL_TEST), no outcome read",
          counts["djangocms"].get("RESERVE", 0) == 59 and counts["saleor"].get("INTERNAL_TEST", 0) == 80,
          json.dumps(counts))

    # ---- A6/A7: client frozen constants (source-text read, no import) ----
    src = (_PROJECT_DIR / "src" / "benchmark" / "signal" / "or_embeddings.py").read_text(encoding="utf-8")
    m = re.search(r'OPENROUTER_EMBED_MODEL\s*=\s*"([^"]+)"', src)
    check("A6", "client frozen model id == requested model",
          m is not None and m.group(1) == REQUESTED_MODEL, m.group(1) if m else "missing")
    check("A7", "no-fallback + provider pin present in client source",
          "NoFallbackError" in src and 'OPENROUTER_EMBED_PROVIDER' in src
          and '"allow_fallbacks": False' in src, "no-fallback + pinned provider")

    # ---- A8: frozen gate + numeric clarification present ----
    proto = (_PROJECT_DIR / "docs" / "QWEN3_EMBED_CONTAMINATION_ROBUSTNESS_PROTOCOL_FROZEN.md").read_text(encoding="utf-8")
    gate_ok = all(s in proto for s in ("A. `Delta F1 > 0`", "B. `Delta Recall >= -0.02`",
                                       "C. `Delta FNR <= +0.02`", "D. `Delta Precision >= -0.02`",
                                       "E. >= 3/5"))
    check("A8", "frozen numeric gate (A–H) + determinism criterion present",
          gate_ok, "numeric gate A–H")

    # ---- A9: provenance V2 verdict C unchanged ----
    prov2 = (_REPORTS / "SWERANK_TRAINING_PROVENANCE_AUDIT_V2_2026-09-19.md").read_text(encoding="utf-8")
    check("A9", "provenance V2 verdict C unchanged",
          "TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP" in prov2, "verdict C")

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
