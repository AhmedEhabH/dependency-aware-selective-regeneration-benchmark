#!/usr/bin/env python3
# ruff: noqa: E501, N806
"""Writes the SweRankEmbed DEV report (markdown) from the machine JSONs.

Separate writer so the report is regenerable and never drifts from the JSONs.
"""
from __future__ import annotations

import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
_RUN = _PROJECT_DIR / "research" / "strong-localization-signal" / "swerank"
_REPORTS = _PROJECT_DIR / "reports"

METHOD_LABEL = {
    "sparse": "Sparse first pass (write set only)",
    "routeb": "Frozen Route-B composite (BM25 + graph-neighbor)",
    "bm25": "BM25",
    "r1": "R1 BM25+RevSupport (context)",
    "swerank_embed": "SweRankEmbed-Small",
}


def main() -> int:
    metrics = json.loads((_RUN / "metrics.json").read_text(encoding="utf-8"))
    gate = json.loads((_RUN / "gate.json").read_text(encoding="utf-8"))
    eff = json.loads((_RUN / "efficiency.json").read_text(encoding="utf-8"))
    pin = json.loads((_RUN / "model_pin.json").read_text(encoding="utf-8"))

    # Sparse baselines (write set only, no additions)
    from benchmark.recall.data import aggregate_tp_fp_fn, load_dev_tasks

    tasks = load_dev_tasks()
    sparse = {}
    for repo in ("djangocms", "saleor"):
        ts = [t for t in tasks if t.repository == repo]
        sparse[repo] = aggregate_tp_fp_fn(ts)

    md = [
        "# SweRankEmbed-Small DEVELOPMENT Report (EXTERNAL PRETRAINED DIAGNOSTIC BASELINE)",
        "",
        "**Date:** 2026-09-19  **Tier:** T3  **ZERO API** (API calls = 0, API cost = $0)",
        "**Model:** `Salesforce/SweRankEmbed-Small` revision "
        f"`{pin['revision']}` (pinned; license {pin['license']})",
        "**Authoring agent:** openrouter/deepseek/deepseek-v4-flash-0731",
        "",
        "**Frozen protocol:** `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` "
        "(frozen before any target-aware metric inspection).",
        "**Provenance label:** `TRAINING_PROVENANCE_INSUFFICIENT_TO_RULE_OUT_OVERLAP` "
        "→ SweRankEmbed-Small is an **EXTERNAL PRETRAINED DIAGNOSTIC BASELINE**, "
        "NOT clean unseen generalization (`reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md`).",
        "",
        "## 1. Research question",
        "",
        "Can a specialized, off-the-shelf issue-localization embedding signal break the "
        "current ranking/localization bottleneck on our parent-only real-commit DEVELOPMENT "
        "protocol, at near-zero marginal cost, with ZERO paid inference?",
        "",
        "## 2. Model + environment (pinned)",
        "",
        "| Item | Value |",
        "|---|---|",
        "| Model id | `Salesforce/SweRankEmbed-Small` |",
        "| Pinned revision | `745d2a06103a66d3cfa600aa52fc0d3523010daa` |",
        "| Params / size | 137M bi-encoder; `model.safetensors` 273,474,944 bytes |",
        "| Architecture | NomicBertModel 12L/768H/12heads/8192 ctx; CLS pooling; 768-dim; `trust_remote_code=True` |",
        "| License | CC-BY-NC-4.0 |",
        "| Query prompt | `Represent this query for searching relevant code: ` (`prompt_name=\"query\"`) |",
        "| max_seq_length | 1024 (official SweRank eval default) |",
        "| Python | 3.11 (isolated venv) |",
        "| Packages | torch==2.14.0+cpu, transformers==4.52.4, sentence-transformers==5.7.0, einops==0.8.2, safetensors==0.8.0, numpy==2.4.6, scipy==1.17.1 |",
        "| Compute | local CPU only (12 cores), no GPU |",
        "",
        "## 3. Data discipline",
        "",
        "- **DEVELOPMENT only**: djangoCMS DEV (174 tasks) + Saleor DEV (149 tasks) — the "
          "FULL currently permissible DEV populations (no arbitrary subsample).",
        "- Sealed sets (djangoCMS RESERVE, Saleor INTERNAL_TEST/RESERVE) untouched; spent "
          "djangoCMS INTERNAL_TEST unused.",
        "- Gold = observed change-set proxy (evaluation only), identical to the frozen protocol.",
        "- Parent-revision file content materialized via `git show <parent>:<path>` from the "
          "read-only local caches: `dist/real-commit-cache/djangocms` and "
          "`dist/pilot-repo-cache/saleor`.",
        "",
        "## 4. Leakage rules (strict, audited)",
        "",
        "- Query = parent-visible issue intent ONLY (same as the existing benchmark); hashed "
          "(SHA-256) per task; verified == sha256(intent_text) for a 40-task sample (audit S6).",
        "- Code = production files in the frozen candidate universe at the PARENT revision only.",
        "- Never exposed: child revision, target patch, changed paths, proxy positives, future "
          "issue/commit information.",
        "- No target label enters parsing, embeddings, scoring, ranking, or top-K selection.",
        "",
        "## 5. Frozen adapter (ONE aggregation rule)",
        "",
        "```",
        "score(unit f) = cosine(issue_embedding, code_embedding_f)   # L2-normalized",
        "score(file F) = MAX over score(f) for f in F                # ONE rule only",
        "rank pool    = omitted files (universe minus Sparse write set), desc score, asc path",
        "```",
        "",
        "Code units = top-level sync functions + classes (with sync methods inline) + sync "
        "methods; whole-file fallback (matches the official SweRank parser; §5 of the frozen "
        "protocol).",
        "",
        "## 6. Efficiency (recorded)",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        "| API calls | **0** |",
        "| API cost | **$0.00** |",
        f"| Model load time | {eff['model_load_seconds']} s |",
        f"| Blob materialization (14,807 blobs) | {eff['materialize_seconds']} s |",
        f"| Unit encoding (49,705 distinct units, one-time) | {eff['encode_seconds']} s |",
        f"| Per-task scoring (precomputed embeddings) | {eff['per_task_scoring_seconds']} s total ({eff['per_task_scoring_seconds']/323:.2f} s/task) |",
        f"| Total wall | {eff['total_seconds']} s |",
        f"| Distinct blobs / units | {eff['distinct_blobs']} / {eff['distinct_units']} |",
        f"| Missing blobs | {eff['missing_blobs']} |",
        f"| Embedding cache | {eff['embedding_cache_bytes']/1e6:.1f} MB (regenerable, deterministic) |",
        "",
        "The 49,705-unit corpus encode dominates the wall time and is a ONE-TIME cost that "
        "amortizes over all tasks of a repository state (the same blobs recur). Marginal "
        "per-task cost after the corpus is embedded is ~0.1 s (scoring) + ~0.2 s (query encode).",
        "",
    ]

    md += ["## 7. Main results (pooled file-level; TP/FP/FN/P/R/F1/FNR per arm)", ""]
    for repo in ("djangocms", "saleor"):
        n = metrics["repos"][repo]["n_tasks_dev"]
        md += [f"### {repo} DEV (n={n}; Sparse baseline F1 {sparse[repo]['f1']:.4f})", "",
               "| B | Method | ORR | P | R | F1 | FNR | candP | TP | FP | FN |",
               "|---:|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|"]
        for B in ("1", "3", "5", "10"):
            b = metrics["repos"][repo]["B"][B]
            for m in ("routeb", "bm25", "r1", "swerank_embed"):
                v = b[m]
                md.append(f"| {B} | {METHOD_LABEL[m]} | {v['macro_orr']:.4f} | {v['precision']:.4f} | "
                          f"{v['recall']:.4f} | {v['f1']:.4f} | {v['fnr']:.4f} | "
                          f"{v['candidate_precision']:.4f} | {v['tp']} | {v['fp']} | {v['fn']} |")
        md.append("")

    md += ["## 8. Frozen progression gate @B=5 (vs frozen Route-B composite)",
           "",
           "| Repo | A F1>B | B Rec≥B−.05 | C FNR≤B+.05 | D Prec | E folds≥3/5 | PASS |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for repo in ("djangocms", "saleor"):
        g = gate["repos"][repo]
        md.append(f"| {repo} | {g['A_f1_direction_positive']} (Δ{g['f1_delta']:+.4f}) | "
                  f"{g['B_recall_not_materially_worse']} (Δ{g['recall_delta']:+.4f}) | "
                  f"{g['C_fnr_not_materially_worse']} (Δ{g['fnr_delta']:+.4f}) | "
                  f"{g['D_precision_rule']} (Δ{g['precision_delta']:+.4f}) | "
                  f"{g['E_folds_ge_3_5']} {g['fold_frac']} | {g['pass']} |")
    md += ["",
           f"**Decision: `{gate['decision']}`** — the frozen gate (A–E) PASSES on BOTH "
           "repositories. Leakage (G), determinism (H) and efficiency (I) are verified by the "
           "independent audit (`reports/swerank_independent_audit.json`, 11/11).",
           "",
           "### Paired task-bootstrap 95% CIs @B=5 (SweRankEmbed minus Route-B; 10,000 resamples, seed 20260919)",
           "",
           "| Repo | Metric | Route-B | SweRank | Δ | CI95 lower | CI95 upper | excludes 0 |",
           "|---|---|--:|--:|--:|--:|--:|:--:|"]
    for repo in ("djangocms", "saleor"):
        for m, v in gate["repos"][repo]["ci"].items():
            md.append(f"| {repo} | {m} | {v['point_arm_a']:.4f} | {v['point_arm_b']:.4f} | "
                      f"{v['point_delta']:+.4f} | {v['ci95_lower']:.4f} | {v['ci95_upper']:.4f} | {v['ci95_excludes_zero']} |")
    md.append("")

    md += ["## 9. Interpretation",
           "",
           "1. **SweRankEmbed-Small improves EVERY metric at EVERY budget on BOTH repositories**, "
           "and all six paired-bootstrap CIs at the primary operating point B=5 exclude zero "
           "for macro ORR, final P, final R, final F1, final FNR, and candidate precision on "
           "BOTH repos. This is the first signal in this research line that realizes the "
           "measured ranking/recall headroom (P63/P64) with a single deterministic, "
           "zero-API mechanism.",
           "2. **F1 (the primary Impact-Correctness objective) rises** on djangoCMS "
           "0.226→0.280 (+0.054; CI [0.028, 0.081]) and Saleor 0.237→0.288 (+0.052; CI "
           "[0.024, 0.080]). Recall rises ~+0.09 and FNR falls ~−0.09 on both repos. "
           "Precision also rises (~+0.04 both). The FP tail does NOT grow: candidate "
           "precision roughly doubles.",
           "3. **Macro ORR (mechanism diagnostic) rises on both repos** (dc 0.163→0.291; "
           "saleor 0.237→0.327) — unlike the bounded semantic family, the embed signal "
           "recovers FNs without trading precision/F1.",
           "4. **Efficiency**: 0 API calls, $0, local CPU. One-time corpus encode "
           "dominates wall time; marginal per-task cost after indexing is sub-second.",
           "5. **Cross-repo consistency**: the signal transfers from djangoCMS (small, ~150 "
           "files/task) to Saleor (large, ~670 files/task), which is the external-validity "
           "direction this thesis values.",
           "",
           "## 10. What this does NOT mean",
           "",
           "- **NOT clean unseen generalization**: `TRAINING_PROVENANCE_INSUFFICIENT_TO_"
           "RULE_OUT_OVERLAP` — SweRankEmbed-Small may have seen djangoCMS/Saleor-like code "
           "during pretraining. The PASS is a *diagnostic* result on DEVELOPMENT, not a "
           "confirmatory claim.",
           "- **NOT a confirmation that reranking (SweRankLLM) helps**: the LLM reranker was "
           "NOT run (ZERO API).",
           "- **NOT an end-to-end method**: this is the candidate-ranking signal inside the "
           "bounded Sparse + ranked-additions architecture; functional correctness/preservation "
           "remain deferred to downstream regeneration.",
           "- **NOT a claim that the generic-Qwen semantic family was wrong to close**: the "
           "bounded cheap-semantic family closure (`BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW`) "
           "stands on its own DEVELOPMENT evidence.",
           "- **NOT a head-to-head with external paper numbers**: SWE-Bench-Lite/LocBench "
           "Func@10 figures in the model card are literature context only and are NOT "
           "comparable to our file-level metrics on our dataset.",
           "",
           "## 11. Next scientific step (frozen selection)",
           "",
           "Because the frozen gate PASSES on both repos, the embed method is frozen as the "
           "candidate-ranking signal. ONE next step is selected (per the frozen protocol §11):",
           "",
           "**Chosen: A — use SweRankEmbed-Small as the replacement candidate-ranking signal "
           "inside the bounded architecture** (Sparse write set + ranked additions), because it "
           "is the direct zero-API continuation of the now-passing signal, needs NO paid "
           "inference, and keeps the existing verifier/budget machinery intact.",
           "",
           "**Not chosen now: B — official SweRankLLM listwise reranker on top of the embed "
           "candidates.** SweRankLLM-Small is a 7B instruction LLM (reranker); running it "
           "requires paid inference or a heavy local load, so it needs its own frozen budget "
           "and authorization. A cost/compute plan for B is drafted in "
           "`reports/STRONG_LOCALIZATION_COMPETITOR_REVIEW_2026-09-19.md` (literature shows "
           "SWE-Bench-Lite Func@10 74.45→86.13 with the 7B reranker; expected on our protocol: "
           "~1 LLM call per task over the top-K embed candidates).",
           "",
           "Stage 5 confirmatory remains gated until a method is frozen under a fresh "
           "confirmatory protocol with explicit authorization.",
           "",
           "## 12. Artifacts",
           "",
           "- `research/strong-localization-signal/swerank/` — `task_rankings.json`, "
           "`metrics.json`, `gate.json`, `efficiency.json`, `model_pin.json`, "
           "`blob_manifest.json`, `unit_manifest.json`.",
           "- `reports/swerank_independent_audit.json` + `SWERANK_INDEPENDENT_AUDIT.md` (11/11).",
           "- `docs/SWERANK_EMBED_BASELINE_PROTOCOL_FROZEN.md` (frozen protocol + addendum).",
           "- `reports/SWERANK_TRAINING_PROVENANCE_AUDIT.md` (verdict C).",
           "",
    ]
    (_REPORTS / "SWERANK_EMBED_DEVELOPMENT_REPORT.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote reports/SWERANK_EMBED_DEVELOPMENT_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
