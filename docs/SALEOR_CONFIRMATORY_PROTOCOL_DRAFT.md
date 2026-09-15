# SALEOR CONFIRMATORY PROTOCOL — DRAFT (DOCUMENT-ONLY)

**Status:** DRAFT / PLANNING ONLY. **No Saleor result is produced and no API
call is made in this block.** This document funds future work; Saleor remains
the preferred second-repository candidate, subject to a protocol-fit audit.

**Owner:** Ahmed (MSc) · **Funding:** MSc roadmap Pillar 7.

---

## 1. Why Saleor is a useful second repository

- Materially different from djangoCMS: **e-commerce modular monolith** (vs CMS
  plugin architecture) — tests transfer of Preserve-by-Omission savings and
  semantic fidelity under a different architecture.
- Large production corpus: long git history, many real commits, rich candidate
  universe (scale/density stress for extraction and indexing).
- Active, real-world Python/Django (Strawberry GraphQL + Django ORM), so
  historical-change mining and proxy semantics are meaningful.
- Independent (untouched) confirmatory line: no saleor evidence has informed
  any of this thesis's selection decisions to date.

## 2. Repository / language / file-type characteristics (to audit)

- Language: Python 3.x (Django + Strawberry GraphQL), JS/TS frontends excluded
  from candidate universe (like djangoCMS, which scans `cms/`/`menus/` `.py`).
- Candidate universe options: `saleor/**/*.py` production modules excluding
  `tests/`, `migrations/`, scripts, fixtures; root package is `saleor`.
- Structure is flatter/sharded by domain (checkout, payment, order, product,
  graphql...) vs djangoCMS's `cms/` + `menus/`.

## 3. Candidate-universe options

1. `saleor/**/*.py` with `tests|migrations|scripts|benchmarks` excluded
   (recommended baseline; smallest deviation from the M4A-1 rule set).
2. Plus `saleor/graphql/**/*.py` dedicated resolvers (larger universe).
3. Plus generated/versioned nodes — decide explicitly; likely excluded.

**Decision rule for the future audit:** pick ONE canonical universe definition,
freeze a hash, and keep it constant across TRAIN/VALIDATION/TEST.

## 4. Real-commit mining feasibility

- Same `real-commit-miner-v1.0.0` rules as M4A-1: non-merge single-parent
  commits; conservative change taxonomy; production-only proxy; whitespace
  detection via `git diff -w`; dependency graph from the **parent commit only**
  via AST-import extraction.
- Anchor: pick a stable release tag ≥90 days old (DA-03) and record its SHA
  before construction (candidate: a recent release branch commit).
- Proxy subset-of-parent-universe invariant must be re-verified per case at the
  Saleor scale (~several hundred production `.py` files).

## 5. Leakage barriers

- Same physical `public/` vs `hidden/` separation as M4A-1/M4A-2.
- `intent_mentions_changed_path` detector on the SHORT subject (fix the audit
  finding from the cheap-baselines block: persist the same string that was
  tested, or test the persisted full-message intent to keep them identical).
- Explicitly exclude any case whose full-message intent mentions a changed
  path if the protocol demands leakage-free intents; otherwise record as a
  documented caveat shared identically across arms.
- 6000-ancestor or year-capped window, with R1/R2/R3 related/duplicate
  adjudication re-applied.

## 6. Split strategy

- Deterministic metadata-only split freeze BEFORE any model/baseline result:
  TRAIN : VALIDATION : HELD_OUT_TEST (e.g., 60/20/20 or larger given a bigger
  corpus), via the M4A-2 largest-remainder + seed mechanism.
- New HELD_OUT_TEST must never have informed ANY prior selection decision.

## 7. Proxy vs semantic-label strategy

- Proxy = observed changed production-Python set within U_t (identical to
  djangoCMS; evaluation-only, never semantic ground truth).
- No new semantic labeler; do not claim semantic gold.

## 8. How it differs from djangoCMS (expected)

- Larger/denser candidate universe (≈ hundreds vs ≈140–152).
- Multi-domain sharding → graph is denser within domains, sparser across them.
- Graph/hybrid baselines may behave differently (cross-domain spread).
- Bigger diff/proxy heterogeneity; stricter timeouts if re-validation is ever
  needed (this block performs NO model calls).

## 9. Expected risks / blockers

- Mining cost/compute at larger scale; candidate-universe enumeration time.
- Repository evolution drift between anchor and source availability.
- Licensing (BSD-3 like djangoCMS, but re-verify pinned SHA + license manifest).
- Potential ambiguity in commit-intent quality for larger monorepo changes.
- Need to re-run the miner's eligibility/adjudication tests for Saleor.

## 10. Required freeze conditions BEFORE the first Saleor result

1. Repository suitability audit PASS (this doc becomes the protocol after review).
2. Candidate-universe semantics frozen (option selected + hash).
3. Historical-change mining rules frozen (mirror M4A-1 + fixed leak-detector
   string).
4. Proxy/adjudication protocol frozen.
5. TRAIN/VALIDATION/TEST split freeze recorded before any result.
6. Baselines (cheap-baselines-v1) and LLM protocol (P1 Full/Sparse) frozen.
7. TEST split remains untouched until final confirmation.
8. Cost ceiling frozen if any LLM arm is added (not in this block).

**No Saleor execution today. No API calls. No results.**