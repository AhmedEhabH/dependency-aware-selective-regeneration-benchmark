# DOCUMENTATION HYGIENE REPORT — M17 (R1)

**Mission:** M17_DOCUMENTATION_ACADEMIC_PROVENANCE_HYGIENE_R1
**Date:** 2026-10-12
**Branch:** `parallel/documentation-provenance-hygiene-2026-10-12`
**Base:** `9380e42f78d07c0047fc36d8b9f37886015f2fb8`
**Scope:** ZERO API calls; ZERO benchmark execution; documentation-only.

---

## 1. Files scanned

Tracked textual documentation scanned: **~1,425 candidate files** classified
(`.md` / `.tex` / `.rst` / `.txt` + `docs/LIVE_STATUS.json`). This covers the
current public/research-facing files, the benchmark-reproducibility config
docs, all `docs/`, `reports/`, `msc_proposal/`, `paper/`, `slides/`,
`research/` evidence trees, `selective_updates/`, `exports/`, and the current
LIVE STATUS source.

## 2. Candidate mentions found

**3,000 candidate mention rows** in `DOCUMENTATION_PROVENANCE_CENSUS.csv`.

Count by classification:

| Class | Rows | Meaning |
|:---|:---|:---|
| D — IMMUTABLE_PROVENANCE | 1,954 | frozen reports / receipts / raw evidence / rater artifacts |
| C — INTERNAL_WORKFLOW | 936 | append-only logs, mission records, execution protocols |
| A — PUBLIC_ACADEMIC | 75 | proposal/paper/slides + current-facing research status |
| B — BENCHMARK_REPRODUCIBILITY | 35 | model/provider/budget/runbook + LIVE STATUS source |

## 3. Files edited (D5)

7 files were semantically cleaned (all mutable PUBLIC_ACADEMIC or
BENCHMARK_REPRODUCIBILITY):

1. `docs/LIVE_STATUS.json` — source-of-truth neutralization (11 phrasings).
2. `README.md`, `START_HERE_CURRENT_2026-09-21b.md`, `PROGRESS.md`,
   `00_CURRENT_RESEARCH_STATE.md` — LIVE block re-rendered byte-for-byte from
   the JSON (verified by `tests/unit/test_live_status_blocks.py`, 3/3 PASS);
   PROGRESS.md and START_HERE also had narrative edits outside the block.
3. `docs/CLAIM_REGISTRY.md` — one orchestration phrase.
4. `docs/RESEARCH_STATUS_2026-10-02.md` — one orchestration phrase.

### Mentions removed / rephrased (by class)

| Class | REWRITE rows | Files |
|:---|:---|:---|
| PUBLIC_ACADEMIC | 25 | README, START_HERE, PROGRESS, 00_CURRENT (block), CLAIM_REGISTRY, RESEARCH_STATUS |
| BENCHMARK_REPRODUCIBILITY | 11 | `docs/LIVE_STATUS.json` |

Transformations applied (each recorded in `DOCUMENTATION_MUTATION_PLAN.csv`):

- `Await ChatGPT brain review of the M17 qualification kit …` →
  `Await review of the M17 qualification kit …`
- `ChatGPT = scientific brain` → `research design and scientific decisions are
  researcher-defined`
- `brain decision: …` → `review decision: …`
- `brain-built/tested bundle` → `built/tested bundle`
- `runner needs brain bundle` → `runner needs a built bundle`
- `brain-approved M16-v2` → `review-approved M16-v2`
- `brain review of the qualification evidence` → `review of the qualification
  evidence`
- `next: brain review then real 12-task qualification` → `next: review then
  real 12-task qualification`
- `the brain's G1 call` → `the G1 review decision`
- `the brain can make a clean scientific decision` → `a clean scientific
  decision can be made at the review gate`
- `brain-reviewed design amendment` → `review-approved design amendment`
- `human/ChatGPT review gate` → `review gate`
- `Validation reported by OpenCode:` → `Validation reported:`
- `STOP at G1_SCIENCE_DECISION for ChatGPT review` → `… for review`
- `needed for ChatGPT/Claude review` → `needed for independent review`

No scientific claim, metric, threshold, RQ meaning, experimental arm, budget,
or numeric result was changed (`SCIENTIFIC_INVARIANCE_RECEIPT.json` → all
FALSE).

## 4. Benchmark model references preserved

The executed benchmark/embedding model identities were **preserved** and
registered in `BENCHMARK_MODEL_REGISTRY.md/.json`:

- **Qwen3-Coder-480B-A35B-Instruct** (`qwen/qwen3-coder`, OpenRouter →
  DeepInfra `deepinfra/turbo`) — EXECUTED_BENCHMARK.
- **Qwen3-32B** (`qwen/qwen3-32b`, DeepInfra `fp8`) — EXECUTED_BENCHMARK.
- **Qwen3-Coder-30B-A3B-Instruct** — EXECUTED_BENCHMARK.
- **Qwen3-Embedding-8B** (`qwen/qwen3-embedding-8b` / `qwen/n-8b`) —
  EXECUTED_EMBEDDING.
- **DeepSeek V4 Flash / V4 Pro** — PLANNED_NOT_EXECUTED (future candidates) or
  ORCHESTRATION_ONLY (OpenCode execution model). NOT presented as benchmark
  arms.

## 5. Related-work references preserved

Legitimate scientific entities were kept intact wherever they appear:
Agentless, RIPPLE, LocAgent, GraphLocator, BM25, dense retrieval, RM-CSS, SIP,
bounded Repository Agent, CIA-style propagation, and the ChatGPT/Claude rater
entities of the AI semantic-plausibility audit (frozen rater outputs).

## 6. Immutable evidence left untouched

1,954 immutable-provenance rows (frozen reports, receipts, manifests, rater
artifacts, run state, evidence trees) were **read-only**. `git diff --name-only`
confirms only the 7 mutable files above were modified. `runs_dryrun/`,
`research/wp2/`, `reports/`, `research/semantic_audit/`, `exports/` were not
touched.

## 7. REVIEW_ONLY items (0 high-risk, 0 blocking)

All REWRITE rows from the plan were resolved. Remaining mentions are
classified KEEP (disclosure / benchmark identity / internal workflow /
immutable provenance). The gate identifier `G0_BRAIN_REVIEW` is retained as an
INTERNAL_WORKFLOW token (it is a frozen protocol gate name referenced across
append-only records; renaming it would itself require mutating immutable
evidence). No unresolved high-risk review items remain.

## 8. Scientific invariance verdict

`SCIENTIFIC_INVARIANCE_RECEIPT.json`:

```
SCIENTIFIC_RESULTS_CHANGED = FALSE
BENCHMARK_PROTOCOL_CHANGED = FALSE
RQ_MEANING_CHANGED = FALSE
FROZEN_EVIDENCE_CHANGED = FALSE
```

## 9. Explicit answers

1. **Are ChatGPT references present in current PUBLIC_ACADEMIC docs?** No
   irrelevant orchestration references remain. ChatGPT remains only as a
   frozen rater entity in the AI semantic-audit evidence (immutable) and in
   append-only historical records.
2. **Are Claude references present in current PUBLIC_ACADEMIC docs?** No
   irrelevant orchestration references remain. Claude remains only as a frozen
   rater entity / independent-review disclosure.
3. **Are OpenCode/Pi/orchestration-model references present in benchmark
   methodology?** No. OpenCode appears only in internal workflow docs and as a
   named execution agent in immutable provenance. DeepSeek appears only as
   PLANNED_NOT_EXECUTED / ORCHESTRATION_ONLY in the registry, not in executed
   benchmark results.
4. **Are benchmark models explicitly identified?** Yes — `qwen/qwen3-coder`,
   `qwen/qwen3-32b`, `qwen/qwen3-coder-30b-a3b-instruct`,
   `qwen/qwen3-embedding-8b`, with provider/route/temperature/budget, all
   traceable to frozen artifacts.
5. **Are planned-but-unexecuted models clearly distinguished?** Yes —
   PLANNED_NOT_EXECUTED vs EXECUTED_BENCHMARK/EXECUTED_EMBEDDING in
   `BENCHMARK_MODEL_REGISTRY`.
6. **Did any frozen evidence change?** No.

## 10. P2P / F2P result

`P2P_F2P_PASS` (17/17 checks) — `scripts/m17_p2p_f2p_tests.py`.

## 11. Success criteria

```
PUBLIC_ACADEMIC_CHATGPT_IRRELEVANT_REFERENCES = 0
PUBLIC_ACADEMIC_CLAUDE_IRRELEVANT_REFERENCES = 0
PUBLIC_ACADEMIC_ORCHESTRATION_AS_SCIENTIFIC_AUTHORITY = 0
BENCHMARK_MODEL_IDENTITY_PRESERVED = TRUE
RELATED_WORK_IDENTITY_PRESERVED = TRUE
IMMUTABLE_PROVENANCE_CHANGED = FALSE
SCIENTIFIC_RESULTS_CHANGED = FALSE
BENCHMARK_PROTOCOL_CHANGED = FALSE
RQ_MEANING_CHANGED = FALSE
P2P_PASS = TRUE
F2P_PASS = TRUE
```

Artifacts (all under `research/documentation-hygiene-r1/`):
`DOCUMENTATION_PROVENANCE_CENSUS.csv/.md`, `DOCUMENT_CLASSIFICATION.csv`,
`DOCUMENTATION_MUTATION_PLAN.csv`, `BENCHMARK_MODEL_REGISTRY.md/.json`,
`SCIENTIFIC_INVARIANCE_RECEIPT.json`, `DOCUMENTATION_HYGIENE_REPORT.md`.