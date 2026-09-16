# Saleor Repository Suitability Audit — Stage 2 generalization

**Date:** 2026-09-16
**Tier:** T3 research-design / ZERO scientific LLM calls
**Repo:** Saleor Core (`https://github.com/saleor/saleor`)
**Protocol:** `docs/SALEOR_REAL_COMMIT_PROTOCOL_V1.md`
**Classification: SUITABLE-WITH-DEVIATIONS** (see §11).

---

## 1. Scope of this audit

Saleor is Stage 2 of the generalization ladder (cross-repository confirmation
in a second real system). This audit determines whether a
RealCommitImpact-style real-commit dataset and the existing Sparse impact-plan
evaluation can be built on Saleor **fairly**, i.e. without relaxing the frozen
leakage/data rules and without tuning the djangoCMS method on Saleor TEST.

## 2. Identity / license / anchor

| Item | Value |
|---|---|
| repo_url | https://github.com/saleor/saleor |
| pinned snapshot | `2c48391b652c26ce4f27a53d6532d4c873306af0` (frozen in `dist/pilot-repo-cache/saleor`) |
| profile version | 3.23.0 (`benchmark_data/repository_profiles/saleor.yaml`) |
| license | BSD-3-Clause (Saleor Core) |
| cache state | shallow clone (1 commit: the pinned snapshot); full history NOT present locally |

## 3. Historical commit depth

- **Blocked locally:** the pinned cache is shallow (`rev-parse --is-shallow-repository`
  = true, depth 1). A historical sampling frame (single-parent, meaningful-intent,
  production-only, leakage-filtered eligible changes) cannot be reconstructed
  from the current cache.
- **Expected depth (documented fact):** Saleor Core is an actively developed
  Django monolith with tens of thousands of commits; the modern PR-era history
  (post-2020) is dense enough to support a 6000-commit window analogous to
  djangoCMS. This is a claim about the repository, not about locally available
  evidence.
- **Action:** acquiring full history (a full `git fetch` into a pinned cache)
  is required before any Saleor sampling-frame reconstruction. It is a
  zero-scientific-call data operation.

## 4. Language / framework / module boundaries

- Python 3.12, Django 4.2+, Graphene (graphene-django).
- **Modular monolith:** domain apps under `saleor/<domain>/` (product, checkout,
  order, account, payment, channel, warehouse) + a separated GraphQL layer
  `saleor/graphql/` + plugin system `saleor/plugins/` + webhook layer.
- Import/dependency graph is derivable from AST imports at the parent commit,
  exactly as for djangoCMS (`build_parent_universe_and_graph`).
- Production-file universe semantics are well defined in the frozen profile:
  `saleor/graphql/**`, domain `models.py`/service modules, `saleor/core/**`,
  `saleor/permission/**`, `saleor/plugins/**`, `saleor/webhook/**`; migrations
  and tests excluded.

## 5. Candidate-universe scale

- Saleor is substantially larger than djangoCMS (hundreds of production Python
  files). Candidate universes will be in the low hundreds to ~1k files per
  parent, i.e. **1–5× larger than djangoCMS's 140–152**. This raises prompt
  size and inference cost per cell.
- Density/cap behavior (M1/M2 style) is expected to differ; this is an
  empirical question, not assumed.

## 6. Parent/target reconstruction + observed-change proxy

- Same frozen M4A-1/M4A-2 machinery applies: parent commit P (single parent),
  target T, `name-status` diff, production proxy = changed production files
  (status M only, v1 rule).
- The observed change-set proxy is an OBSERVED proxy, never semantic gold —
  identical discipline.
- **Deviation:** Saleor commits are large and multi-purpose; the `proxy_too_large`
  / `diff_too_large` exclusion ceilings (proxy ≤ 12, total diff ≤ 40) may reject
  a larger share of candidates than djangoCMS. The frozen ceilings must NOT be
  loosened; a lower acceptance rate is acceptable.

## 7. Intent quality / filename leakage

- Commit messages in Saleor are conventional-commit/PR-referenced on the modern
  history (e.g. "Remove deprecated exportGiftCards... (#19583)"), similar to
  djangoCMS's modern window.
- `allow_intent_path_leakage=False` applies unchanged: any intent that mentions
  a changed path is ineligible.
- PR-body/issue mining is NOT used (frozen choice); intent source = commit
  message only.

## 8. Duplicate / related-change rules

- R1 exact-proxy-set, R2 shared-PR-reference, R3 suspected-related (same-change
  predicate) apply unchanged. Saleor's large feature branches make R2 (shared
  PR refs) more common; the frozen rules already merge shared-PR groups.

## 9. Dependency-graph coverage / density / history

- **Graph:** AST import graph is buildable at parent (frozen builder). Saleor's
  modular-monolith structure yields a denser, more layered graph than djangoCMS
  (graphql → domain → core). Graph coverage expected to be high.
- **History / co-change:** currently unavailable locally (shallow cache); full
  history would enable history/co-change features — the same capability
  limitation as djangoCMS v1 (deferred there).

## 10. Sample-size potential + expected Sparse inference cost

- With a 6000-commit window and the frozen ceilings, an eligible pool of
  several hundred is plausible (Saleor's commit volume is high). No local
  reconstruction is possible until full history is cached.
- Per-cell Sparse cost at djangoCMS scale: ~5.5k prompt tokens / ~600 completion
  tokens → ~$0.002/cell. Saleor's larger universes raise prompt tokens
  (candidate listing is the dominant prompt cost); a 500-file universe could
  roughly double prompt tokens per cell (~$0.004/cell). Budget planning must
  account for this; 3-rep development on ~120 tasks would be ~360 cells and
  roughly $0.75–$1.50 depending on universe size — to be re-budgeted when the
  frame exists, not assumed.

## 11. Classification

**SUITABLE-WITH-DEVIATIONS.**

- Suitable because: real second system, same Python/Django ecosystem, frozen
  builder/machinery applies, well-defined production universe, PR-era intent
  quality, BSD license, active maintained history.
- Deviations (documented, not silent):
  1. **Larger candidate universes** → higher prompt cost per cell; re-budget.
  2. **Higher exclusion rate** from frozen size ceilings (Saleor commits are
     larger); accept a smaller eligible pool rather than loosening rules.
  3. **History/co-change features require full cache** (currently shallow).
  4. **Cross-repo comparability:** per-repository metrics primary; macro-average
     across repos; repo-ID confound check; never a head-to-head djangoCMS-vs-
     Saleor superiority claim on pooled numbers.

## 12. Role / boundary

- Cross-repository confirmation across two real systems.
- NOT universal generalization.
- Do NOT inspect future Saleor TEST model outcomes for tuning.
- Do NOT tune the djangoCMS method on Saleor TEST.

## 13. Blocker

- Full Saleor history not cached locally → no sampling-frame reconstruction
  yet. Next action (zero API): full `git fetch` into a pinned cache + run the
  frozen `reconstruct` style enumeration against Saleor, reusing
  `scripts/reconstruct_v2_sampling_frame.py` with a Saleor cache/anchor.