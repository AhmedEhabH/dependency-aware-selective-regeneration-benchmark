# Human-Readable Research Status (2026-09-19)

**Audience:** Ahmed, the supervisor, or a fresh AI that needs the current
scientific position WITHOUT opening dozens of raw reports.
**Source of truth for exact values:** the machine-readable JSONs referenced in
`reports/CURRENT_NUMBERS_CHEATSHEET_2026-09-19.md`. Nothing here overrides a
frozen number.
**Current phase:** `Repository change localization / impact selection`
(primary dims: Impact Correctness + Efficiency).

---

## TL;DR (30 seconds)

- **The thesis line:** given a real GitHub issue and the repository at its
  parent commit, can we select the files that a human actually changed (the
  observed change-set proxy), BEFORE any code regeneration?
- **The bottleneck (measured, frozen):** first-pass recall is high-availability
  but the **ranking** of omitted files is the dominant loss. Cheap
  structural/lexical rankers and bounded generic-Qwen semantic layers all
  failed their frozen gates.
- **The current winner (DEV, frozen):** a specialized pretrained
  issue-localization embedding signal (`SweRankEmbed-Small`, 137M) improved
  **every** metric at **every** budget on **both** DEV repositories, with all
  paired-bootstrap 95% CIs excluding zero at the primary B=5.
  **Caveat (honest):** it is an **external pretrained diagnostic baseline** —
  training-provenance overlap could NOT be ruled out (verdict C).
- **The open question:** is the gain a general dense-retrieval mechanism, or
  specialization/memorization? A Qwen3-Embedding control was authorized,
  probed (stopped on strict determinism), and then **replicated**: two
  complete independent realizations of the hosted Qwen embeddings BOTH pass
  the frozen gate on both DEV repos → **`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`**
  (97.21% A-vs-B selected-set agreement; all file-level CIs exclude zero).
  The ranking signal now has independent dense support. Caveat: Qwen does NOT
  beat Sparse final-set F1 and does NOT replace SweRankEmbed-Small — it
  confirms dense retrieval as a mechanism, not final-set superiority.
- **Stage 5 (confirmatory): PAUSED and SEALED.** Sealed sets untouched.

---

## The research ladder (where each rung stands)

| Stage | What it tested | Verdict (frozen) |
|---|---|---|
| 1 Sparse first pass + Route-B recovery | cheap candidate-level recovery | **DONE/CONFIRMED** (Route-B beats analytic Random; confirmatory CONFIRMS) |
| 2 FN anatomy | why files are missed | **DONE** — availability high, RANKING is the bottleneck |
| 3 cheap structural ranking bridge | transparent count formulas | **CHEAP_RANKING_CLOSED_FOR_NOW** (negative) |
| 4 bounded semantic rerank/verify | generic-Qwen decision layer | **BOUNDED_SEMANTIC_NEGATIVE_FROZEN** (negative) |
| 4b precision-safe acceptance | RANK→VERIFY→VARIABLE-ACCEPT | **PRECISION_SAFE_ACCEPTANCE_FAIL** (negative; descriptive statistics closed) |
| — generic cheap-semantic family | — | **BOUNDED_CHEAP_SEMANTIC_CLOSED_FOR_NOW** |
| NEW specialized embedding signal | SweRankEmbed-Small (DEV) | **SWERANK_EMBED_PASS** (external pretrained diagnostic; provenance C) |
| contamination-robustness bridge | independent dense control | **INDEPENDENT_DENSE_RETRIEVAL_REPLICATED** (Qwen3-Embedding-8B, two realizations A+B both PASS djangoCMS + Saleor @B=5; full-file scores persisted) |
| Stage 5 confirmatory | untouched sealed populations | **PAUSED and SEALED** |

## Current scientific question

"Is the improvement caused by dense semantic retrieval as a general mechanism,
or could it be unusually dependent on SweRank/SweLoc specialization, training
distribution, or possible target-repository overlap?" — The Qwen3 control
**replicates the direction**: two independent full realizations both pass the
frozen gate on both repos
(`INDEPENDENT_DENSE_RETRIEVAL_REPLICATED`), so the dense-retrieval-mechanism
reading is strengthened. Caveats remain: Qwen does not beat Sparse final-set
F1, does not replace SweRankEmbed-Small, and provenance verdict C (possible
training overlap) is unchanged — so Stage 5 stays sealed.

## What is sealed (do NOT open)

- djangoCMS RESERVE (59)
- Saleor INTERNAL_TEST (80)
- Saleor RESERVE (1086)
- spent djangoCMS INTERNAL_TEST (80) — permanently used; never reused.

## Where to look next

1. `START_HERE_CURRENT_2026-09-19.md` — this map.
2. `reports/CURRENT_NUMBERS_CHEATSHEET_2026-09-19.md` — the numbers.
3. `reports/CURRENT_ORACLE_GAP_EXPLAINED_2026-09-19.md` — why the gap exists.
4. `reports/QWEN3_TWO_REALIZATION_REPLICATION_REPORT_2026-09-19.md` — the
   Qwen3 two-realization replication outcome.
5. `reports/CONTAMINATION_ROBUSTNESS_BRIDGE_CLOSURE_2026-09-19.md` — the Qwen
   bridge arc (probe defect → availability → determinism → replication).