# M3 Graph Protocol — C0 / C1 / C2

**Study ID:** `scientific-djangocms-graph-c0-c1-c2-01`
**Classification:** POST-HOC EXPLORATORY DEVELOPMENT-SET GRAPH ABLATION
**Status:** FROZEN — no scientific call may be issued until every artifact
below is persisted and the wiring tag exists.
**Date of freeze:** 2026-09-13
**Branch:** `research/graph-c0-c1-c2-01`

This protocol freezes, BEFORE scientific call 1: the automatic graph + its
independent verification, the seed algorithm and per-scenario seed/zone
hashes, the three conditions and their prompts, the failure taxonomy, the
metrics, the 3-hop eligibility rule, the statistics contract, and the
pre-benchmark validation gates.

---

## 1. Scientific model and provider (frozen)

| Input | Value |
|---|---|
| Model | Qwen3-Coder-480B-A35B-Instruct (`qwen/qwen3-coder`) |
| Gateway / provider | OpenRouter / **DeepInfra** pinned (`deepinfra/turbo`, fp4) — same frozen provider route used by audited M1A/M1B; fallback **OFF** |
| Temperature | 0.0 |
| Completion cap | 16384 (non-binding; same as M1B) |
| response_format | `json_schema` (M1 common ablation schema) |
| Reasoning mode | direct/non-thinking (no reasoning parameter sent) |
| Selection only | True |

If the live endpoint freeze for `deepinfra/turbo` cannot be re-established,
STOP (no fallback provider is permitted).

## 2. Automatic graph (frozen, verified ZERO-API)

- Artifact: `benchmark_data/external_validity/djangocms_5_0_0_dependency_graph.json`
- **144 candidate nodes; 144/144 AST parsed; 562 edges.**
- Source: `python_ast_source_extractor` (real AST import statements inside the
  candidate universe only; no fallback path).
- **Deterministic hash parity:** canonical graph hash
  `0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58`
  recomputes identically and matches BOTH recorded builds in
  `canonical_build_hashes.json` (build_1 == build_2 == artifact).
- **No manually authored scenario edges / no gold-derived edges:** the graph
  artifact contains no scenario / gold / expected / action / manual fields or
  edge tokens; every edge endpoint is a candidate-universe path; gold is a
  separate evaluation-only file and never enters graph construction. The
  extractor only reads AST imports of the pinned source commit
  `0f633fc9fa213357f4202482aab2b0edad680f95`. (Re-extraction from source
  requires the pinned checkout, which is gitignored; the frozen dual-build
  hash identity is the reproducibility witness.)
- Eligibility gate (`graph_eligibility.json`): `eligible: true`.

Independent verification command (ZERO API):
`python -c "from benchmark.selection import graph_ablation as g; print(g.graph_verification()['passed'])"`
If any check fails, **STOP** — no M3 call is issued.

## 3. Conditions

Common base = **audited M1B Sparse-v2 contract** (schema, candidate IDs,
scenario text, repository evidence, model/provider, temperature, cap, scorer,
action vocabulary). The ONLY treatment difference is the
`[[GRAPH_EVIDENCE]]` block appended after the frozen serialization-policy
block.

| Condition | Graph role | Treatment content |
|---|---|---|
| **C0** | OFF | No graph block. The rendered prompt is **byte-identical to the audited M1B Sparse-v2 prompt** (verified against M1B `run_records.jsonl` `prompt_sha256` for all 6 scenarios). **C0 evidence = REUSE of the audited M1B Sparse-v2 30 cells.** No new C0 calls. |
| **C1** | Graph Hints (soft evidence) | Complete automatic graph supplied as SOFT EVIDENCE: all 562 edges as `- {src_id} -> {dst_id}`. No pruning, no forced selection, no universe change. |
| **C2** | Graph-Gated Disclosure | Risk zone = candidates within `hop` undirected graph hops of the deterministic seed set. **Inside the zone an explicit decision is MANDATORY** (every in-zone id must be emitted with REGENERATE / VALIDATE / HUMAN_REVIEW). **Omission stays allowed outside the zone** (deterministic PRESERVE). In-zone omission fails the cell (mandatory-disclosure-failure). |

- **Primary zone:** C2 1-hop.
- **Pre-registered sensitivity:** C2 2-hop.
- **C2 3-hop:** exploratory ONLY if the frozen eligibility condition (below)
  passes BEFORE any 3-hop call. No hop tuning after seeing results. No
  hard-pruning of the candidate universe in any condition.

## 4. Seed construction (frozen algorithm v1, BEFORE any call)

Seeds come ONLY from information legitimately available at inference time.

1. Visible text `T` = requirement_before + requirement_after + acceptance
   criteria + architecture constraints (the exact fields rendered into the
   prompt).
2. Domain terms = CamelCase identifiers and snake_case identifiers in `T`
   (stopword list frozen; unmatched terms are inert).
3. A candidate is a **seed** iff any of its classes / functions / path tokens /
   module segments contains a domain term.
4. Seed set = sorted candidate ids.

**No gold, no expected-action files, no post-hoc selection using any known
answer (including S006).** The algorithm is deterministic and was frozen
before any M3 call. If seed construction ever required model output it would
have to be frozen as an ordered algorithm first — it does not.

Per-scenario seed ids / risk zones are persisted with hashes in
`research/graph-c0-c1-c2-01/seed_zone_identity.json` (computed zero-API).

### Frozen seed sets and zone sizes (from `seed_zone_identity.json`)

| Scenario | Seed ids | 1-hop zone | 2-hop zone | 3-hop zone |
|---|---|---|---|---|
| 002 | {66, 69} | 28 | 112 | 130 |
| 004 | {66, 69} | 28 | 112 | 130 |
| 005 | {5, 70} | 25 | 111 | 129 |
| 006 | {66, 71, 73, 80, 96} | 37 | 116 | 130 |
| 007 | {5, 66} | 29 | 111 | 130 |
| 008 | {66, 69, 71, 73, 96} | 41 | 119 | 130 |

S006 note (pre-registered): the S006 gold file `cms/utils/plugins.py` (the
file Sparse-v2 systematically misses in M1B) is **inside the 1-hop risk zone**
(graph distance 1 from seed `cms/models/pluginmodel.py`), so C2 1-hop
MANDATES an explicit decision on it. This is the pre-registered S006 test.

### 3-hop eligibility (frozen rule, applied ZERO-API before any 3-hop call)

Eligible only if, **for all 6 scenarios**:
`|zone_3hop| > |zone_2hop|` AND `|zone_3hop| <= 115` (≤ 80% of 144).

Result of the frozen analysis: **NOT ELIGIBLE** — 3-hop zones are 129–130 of
144 (~90%, effectively repository-wide) for every scenario. **C2 3-hop is
therefore NOT run** (no tuning; the rule is applied as frozen). Expected M3
calls = 30 (C1) + 30 (C2 1-hop) + 30 (C2 2-hop) = **90 new cells**; C0 = 30
reused M1B cells.

## 5. Pre-registered failure taxonomy

Applied per failed/weak cell in the results analysis (frozen categories):

1. `missed-neighbor` — a gold file at graph distance ≤ hop was not selected.
2. `over-expansion` — selections spread well beyond the zone/plausible scope.
3. `wrong-edge-direction` — graph evidence used against its direction (e.g.,
   treating importers as importees).
4. `graph-evidence-ignored` — output consistent with ignoring the graph block.
5. `mandatory-disclosure-failure` — C2 in-zone id omitted (fail-closed).
6. `unrelated-module-attraction` — selection attracted to unrelated modules.
7. `graph-coverage-gap` — gold file outside the graph risk zone / graph
   cannot see it.
8. `semantic-misreasoning` — plausible reasoning but wrong requirement link.
9. `operational/schema failure` — invalid output, truncation, transport.
10. `other-with-rationale` — anything else, with an explicit rationale.

No new categories are created after observing results unless explicitly
labeled post-hoc.

## 6. Metrics

Per condition AND per scenario:

- recorded / valid / failed / truncations
- TP / FP / FN / P / R / F1 / FNR / full-recall
- prompt tokens / completion tokens / total tokens
- serialized records / latency / cost

For C1 / C2 additionally:

- seed count, risk-zone size
- hop-distance distribution for selected files and for missed gold files

For C2:

- mandatory-zone disclosure compliance (fraction of runs with
  `disclosure_valid == True`)

Explicitly analyzed (per scenario and overall):

- ΔFN, ΔFP, ΔRecall, ΔPrecision, ΔF1, Δtokens for:
  - C0 → C1
  - C0 → C2 1-hop
  - C2 1-hop → C2 2-hop
  - (C2 2-hop → C2 3-hop only if 3-hop had run — it does not)

## 7. Statistics contract (frozen, same as M1)

- 6 scenarios = independent task units (n = 6).
- 5 repetitions = repeated observations NESTED within scenario.
- **No n=30 claim; no significance test treats repetitions as independent.**
- Paired differences = C1/C2 minus C0 within the SAME scenario (condition
  means over the 5 repetitions per scenario; C0 from audited M1B Sparse-v2).
- Scenario-level paired summaries; mean / median paired effects across the 6
  scenarios; effect sizes; per-scenario distributions.
- Bootstrap (if used) resamples SCENARIOS (n = 6) and states the limitation.

## 8. Scientific design

- Six cases are a **CURATED DEVELOPMENT / MECHANISM SET**, NOT held-out
  confirmation. No confirmatory claim is made.
- 5 repetitions per condition/scenario (C1 30, C2 1-hop 30, C2 2-hop 30).
- C0 reuse is authorized because the audited M1B Sparse-v2 evidence is
  EXACTLY compatible in model, provider, schema, prompt, cap, scenario,
  candidate universe and evidence (verified byte-identical prompt hashes;
  see `c0_reuse.json`). No incompatible historical run is silently reused.
- Conditions run sequentially; checkpoint every 5 cells; raw response + SHA +
  RunRecord persisted immediately; append-only; **no result-based reruns**.

## 9. Pre-benchmark validation (EXACT six gates + independent audit)

Run EXACTLY, in order, all ZERO-API:

1. Dataset Validation
2. Prompt Validation (incl. controlled-diff C0/C1/C2)
3. Pipeline Smoke Test
4. Dry Run (manifest shape: 90 cells, 6 scenarios, 3 condition-arms, 5 reps)
5. Integration Test
6. Metric Verification

then Independent Audit. Every gate reports PASS / WARNING / FAIL. On any
FAIL: STOP.

Frozen before call 1: protocol (this file), manifest, graph hash, seed
algorithm + seed/zone hashes, 3-hop eligibility, failure taxonomy, statistics
contract, prompt-control proof, endpoint freeze.

## 10. Interpretation (post-execution, committed questions)

- Where does Graph help / hurt?
- Does it reduce FN? At what FP/token cost?
- Is soft evidence ignored?
- Does mandatory disclosure repair missed structural neighbors?
- How sensitive to hop distance?
- Does S006 improve, and WHY?
- Does another scenario get worse, and WHY?
- Per-scenario classification, then overall:
  **GRAPH HINT SIGNAL: PROMISING / MIXED / NOT PROMISING** and
  **GRAPH-GATED DISCLOSURE: PROMISING / MIXED / NOT PROMISING**.
- No universal graph claim.

## 11. Cost / runtime ceilings

- Hard cost ceiling: **$2.00 USD** cumulative+projected for the 90 new cells.
- Runtime ceiling: 6 hours per full run command; resumable.
- Checkpoint every 5 cells; cost lock checked before and during the run.