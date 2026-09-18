# Problems and Failures Ledger

**Purpose:** every meaningful problem/failure with symptoms, root cause, fixes,
outcome, unresolved risk, scientific impact, follow-up. Appendix to the living
reports. Entries from 2026-09-16 evening (and carried historical items).

---

## PF-001 — Missing pinned djangocms git cache
- **Where:** `benchmark_data/repositories/djangocms` (parent-commit corpus).
- **Symptoms:** StageC runtime-wiring tests fail; parent-commit corpus not
  re-materializable.
- **Root cause:** pinned upstream cache absent locally.
- **Attempted fixes:** documented; not fetched (network/scope).
- **Outcome:** pre-existing environmental failure (2 tests), identical on clean
  base; unrelated to this work.
- **Unresolved risk:** low; documented in the repository evidence audit.
- **Scientific impact:** none on the delivered evidence.
- **Follow-up:** fetch full history if cross-repo/history work needs it.

## PF-002 — V2 sampling-frame reconstruction needed full history
- **Where:** `dist/real-commit-cache/djangocms` (shallow at first).
- **Symptoms:** 329-case frame not reconstructable from the frozen 40-case
  adjudication JSON alone.
- **Root cause:** per-case metadata for the non-selected pool is not persisted.
- **Attempted fixes:** used `dist/real-commit-cache/djangocms` (full history)
  with the frozen scientific builder → funnel 6000→916→334→329→40 reproduced.
- **Outcome:** frame reconstructed deterministically (289 untouched beyond v1 40).
- **Unresolved risk:** none (frame verified against frozen adjudication).
- **Scientific impact:** enables V2 design.
- **Follow-up:** none.

## PF-003 — V2 token-ceiling post-call overshoot
- **Where:** V2 Sparse development inference executor.
- **Symptoms:** cumulative 2,501,964 tokens vs nominal 2,500,000 ceiling
  (1,964 / 0.08% over) after the 431st completed call.
- **Root cause:** per-cell budget check is post-call; the final call's own
  tokens cannot be pre-empted.
- **Attempted fixes:** fail-closed stop before another call.
- **Outcome:** 431/450 cells executed; 19 cells not run; run halted correctly.
- **Unresolved risk:** none; the overshoot is documented exactly (not "within
  ceiling").
- **Scientific impact:** 144 V2 tasks labeled (>= N=120 recommendation).
- **Follow-up:** none.

## PF-004 — LocAgent P5 timeout failures (2)
- **Where:** cases 4307e1b8c2e2, fdda30c271f0.
- **Symptoms:** `execution flow reconstruction exceeded timeout. Terminating.`
- **Root cause:** 900 s per-task timeout under heavy context.
- **Attempted fixes:** none in P5 (immutable).
- **Outcome:** fail-closed empty (2).
- **Unresolved risk:** P5R-1 relaxes timeout to 1800 s to test if operational.
- **Scientific impact:** P5 is system-level context; P5R is a new study.
- **Follow-up:** P5R-1 rescue pilot.

## PF-005 — LocAgent P5 context-length failure (1)
- **Where:** case 66c70394c9e1.
- **Symptoms:** `OpenrouterException - Upstream error from Venice: ... maximum
  context length ... 198248 input tokens`.
- **Root cause:** agent context near the route's limit; OpenRouter-routed.
- **Attempted fixes:** bounded BadRequestError handler (infrastructure repair,
  not scientific tuning).
- **Outcome:** fail-closed empty (1).
- **Unresolved risk:** P5R-1 raises context to the same route's max if supported.
- **Scientific impact:** none on P5's classification.
- **Follow-up:** P5R-1 / P5R-2 (provider-deviation diagnostic only if needed).

## PF-006 — LocAgent P5 completed-but-empty (2)
- **Where:** cases 9e33db4f4660, b39799f9fc1c.
- **Symptoms:** `localizing ... succeed, process multiple loc outputs` with
  empty `found_files`.
- **Root cause:** framework produced a structurally valid answer with no
  parseable file set (NOT a timeout).
- **Attempted fixes:** none (P5 immutable).
- **Outcome:** completed-but-empty (2).
- **Unresolved risk:** P5R-1 allows exactly one rerun each; if still empty,
  treat as framework/system behavior, not timeout.
- **Scientific impact:** taxonomy corrected (2 timeout + 1 context + 2 empty).
- **Follow-up:** P5R-1.

## PF-007 — Graph features confounded by candidate-universe size (V2)
- **Where:** V2 omission-risk analysis.
- **Symptoms:** pooled V2 analysis showed ~33 features "above band"; graph
  features correlated ~0.99 with candidate-universe size.
- **Root cause:** V2 universes (up to 234) systematically larger than v1
  (140-152); pooling v1+v2 conflates cohort membership with omission risk.
- **Attempted fixes:** within-cohort AUROC replication.
- **Outcome:** v1 peakiness signal (bm25_zero_count 0.837) does NOT replicate in
  V2 (0.592); no multivariable RiskScorer.
- **Unresolved risk:** none; artifact documented.
- **Scientific impact:** negative result frozen; Route B pivot.
- **Follow-up:** Route B must stratify/adjust for universe size.

## PF-008 — BibTeX parser brace/quote handling
- **Where:** `scripts/parse_bibtex_triage.py`.
- **Symptoms:** 0 entries parsed on first run.
- **Root cause:** `split_entries` required `{` right after key+comma and
  `field()` only matched quoted values.
- **Attempted fixes:** balanced-brace entry splitting + `{...}`/`"..."` field
  values.
- **Outcome:** 987 raw entries / 806 unique titles parsed.
- **Unresolved risk:** nested braces in a few values may split early; acceptable
  for triage.
- **Scientific impact:** none (triage only).
- **Follow-up:** none.

## PF-009 — Reports/*.md gitignored
- **Where:** repo `.gitignore` (`reports/*.md`).
- **Symptoms:** new report `.md` files not added by `git add -A`.
- **Root cause:** `reports/*.md` is gitignored with an allowlist.
- **Attempted fixes:** `git add -f` for the new report files (matching the
  existing convention for tracked reports).
- **Outcome:** reports tracked.
- **Unresolved risk:** none.
- **Scientific impact:** none.
- **Follow-up:** none.
## PF-010 — P5R-1 wrapper timeout ineffective (upstream hard-coded deadline)
- **Where:** P5R-1 rescue pilot, case 66c70394c9e1.
- **Symptoms:** terminated at "Processing time exceeded 15 minutes" despite wrapper --timeout 1800.
- **Root cause:** upstream auto_search_main.py enforces its own 900 s deadline independent of the wrapper timeout.
- **Attempted fixes:** none (editing upstream forbidden).
- **Outcome:** timeout relaxation is operationally ineffective; full rerun not triggered.
- **Unresolved risk:** low; documented.
- **Scientific impact:** P5 failures are NOT primarily wrapper-timeout artifacts.
- **Follow-up:** none (Route B is the promising mechanism instead).

## PF-011 — P5R-1 pilot token/cost ceiling overshoot (post-call)
- **Where:** P5R-1 pilot.
- **Symptoms:** cumulative 20,541,560 tokens / .18 after the final (66c70394c9e1) task, vs 20M / .00 ceilings.
- **Root cause:** per-task budget check runs after each task; the final task crossed the ceiling.
- **Attempted fixes:** fail-closed stop before another call.
- **Outcome:** 5/5 tasks executed; 0 usable; run halted; remaining evening budget preserved (.18 of ).
- **Unresolved risk:** none.
- **Scientific impact:** pilot reported with exact ceilings overshoot; no blended P5R metric.
- **Follow-up:** none.

## PF-012 — Saleor bundle build: 52/150 DEV blocked by Windows git archive path
- **Where:** Saleor case-bundle build (2026-09-17).
- **Symptoms:** git archive fails on a cassette path with ? and [ ] characters
  (test_get_oembed_data[...].yaml).
- **Root cause:** Windows git archive rejects the filename; build_parent_universe_and_graph raises.
- **Attempted fixes:** none tonight (documented).
- **Outcome:** 98/150 DEV bundles built and valid; 52 blocked; TEST/RESERVE untouched.
- **Unresolved risk:** SALEOR INFERENCE READY not reached.
- **Scientific impact:** none (no inference run; no TEST exposure).
- **Follow-up:** POSIX re-run or minimal cassette-exclusion workaround (deferred).

## PF-013 — P5R-1 report correction: timeout WAS honored (1800s)
- **Where:** P5R-1 pilot, case 66c70394c9e1 (2026-09-17 correction).
- **Symptoms:** the report initially claimed the wrapper timeout was ineffective
  against an upstream 900 s hard-coded deadline.
- **Root cause of the error:** the "Processing time exceeded 15 minutes" log
  string is a STALE fixed message in the TimeoutError handler; the real deadline
  is process.join(timeout=args.timeout), which P5R-1 set to 1800.
- **Corrected finding:** args.json records timeout=1800; the case ran ~33 min of
  wall time before the 1800 s join deadline expired. The timeout relaxation WAS
  effective; the case failed from genuinely long-running search + context.
- **Attempted fixes:** none (correction only).
- **Outcome:** report + forensics corrected; P5 remains immutable.
- **Unresolved risk:** none.
- **Scientific impact:** P5R interpretation corrected (no hard 900 s cap); the
  0/5 pilot outcome and the no-full-rerun decision are unchanged.
- **Follow-up:** P5R-2 feasibility note updated accordingly.

## PF-014 — Saleor sparse inference BUDGET-BLOCKED (2026-09-17)
- **Problem:** measured Saleor per-cell cost (~14.5k tokens / .0047 from a
  live smoke cell) makes the full 450-cell DEV run ~6.5-7.4M tokens / .13-2.23,
  2.4-2.7x the authorized hard ceiling (2.7M / .00).
- **Root cause:** Saleor candidate universes (median 761 files) are 3-4x larger
  than djangoCMS; the Saleor protocol §5.1 explicitly warned to re-budget from
  the frame, never assume djangoCMS per-cell cost.
- **Action:** FAIL-CLOSED after 1 smoke cell (valid evidence, .0047); the
  remaining 449 cells NOT run; no silent protocol reduction. Block D (Route-B
  replication) blocked because it requires C.
- **Status:** OPEN (blocker for Saleor inference + replication).
- **Fix options (require explicit authorization):** raise ceiling to measured
  ~7.5M tok / .25; or pre-register a documented subset / 1-rep protocol; or
  shrink the candidate universe via a documented production-scope rule.
- **RESOLVED (2026-09-17):** re-authorized with a measured budget — hard
  ceilings 450 cells / 9,000,000 total tokens / .00 (covers the ~7.5M-token /
  ~.25 measured projection with ~20% headroom). Also corrected dataset
  identity (saleor-rc-*); pre-fix smoke archived as operational (not scientific).

## PF-015 — Saleor identity provenance leak (djangocms-rc-* in prompt) (2026-09-17)
- **Problem:** the Saleor case ID djangocms-rc-<sha> was rendered into the
  inference prompt (Frozen real historical change (djangocms-rc-...)) -> the
  model saw djangoCMS provenance for a Saleor task.
- **Root cause:** frozen djangoCMS miner constants baked into the Saleor bundles.
- **Action:** deterministic migration to saleor-rc-<sha> + corrected identity;
  150/150 scientific-payload equivalence PASS; pre-fix smoke call archived as
  operational (not scientific evidence).
- **Status:** RESOLVED.

## PF-016 — Saleor clean run failures (2026-09-17)
- **Problem:** 4/450 cells failed: 3x HTTP 429 transport (saleor-rc-012472eb8482,
  all reps; the case the pre-fix smoke ran on) + 1x schema duplicate-id
  (saleor-rc-d7fe298a4752 rep2).
- **Action:** recorded per frozen failure semantics (recall 0, fn=proxy);
  NO result-dependent reruns (mission rule). Task 012472eb8482 has no succeeded
  rep -> excluded from Route-B transfer (149 tasks).
- **Status:** DOCUMENTED (honest failure records; not scientific anomalies).

## PF-017 - CIA/Hybrid redundancy + overstating Classical-CIA label (2026-09-17)
- **Problem:** the Route-B V2 results reported CIA and Hybrid as if distinct,
  and the confirmatory packet described CIA as a classical
  association/importance-weighted fusion of BM25/graph/path.
- **Root cause:** the frozen code defines CIA = normalized BM25 + binary
  graph-neighbor, and Hybrid = 0.5 * (same) -> a positive scalar multiple ->
  identical ranking. The genuinely classical CIA baseline
  (classical_cia_baseline_v1.py) is a different script.
- **Action:** ranker-identity audit (mathematical proof + empirical top-B
  identity on 323 tasks); Hybrid reclassified redundant alias/control;
  terminology corrected to BM25+Graph-Neighbor Composite (historical label:
  CIA); no formula change.
- **Status:** RESOLVED (2026-09-17; zero API).

## PF-018 - Saleor parent-visible history unavailable for ablation (2026-09-17)
- **Problem:** the incremental ablation could not compute a Saleor co-change
  arm.
- **Root cause:** no Saleor history cache (dist/real-commit-cache/saleor
  absent).
- **Action:** recorded UNAVAILABLE in the ablation; djangoCMS history arm used
  where available (94 tasks).
- **Status:** DOCUMENTED (not a scientific anomaly).

## PF-0XX - P2 adaptive-budget policies NEGATIVE on DEVELOPMENT (2026-09-18)
- **Where:** src/benchmark/p2/ evaluation on djangoCMS DEV + Saleor DEV.
- **Symptoms:** no P2-P1..P2-P4 policy beats fixed-B on BOTH repos; P2-P3
  repo-asymmetric (djangoCMS B_t=1 vs Saleor B_t=9 at the same tau).
- **Root cause:** (a) sparse composite-score tail (58% zeros) makes score-gap /
  marginal rules stop early or track B10; (b) cost-ratio rule is dominated by
  omitted-size/universe-size distributions (size artifact).
- **Fixes:** none needed — pre-registered gate correctly FALSE; negative frozen
  as the scientific result per mission section 4.
- **Outcome:** P2 Phase-1 NEGATIVE closure; fixed-B thesis (CONFIRMED) intact.
- **Unresolved risk:** adaptive B_t remains not-justified for Phase 2; landscape
  expansion provides the Phase-2 candidate pool.
- **Scientific impact:** none negative for the fixed-B contribution.
- **Follow-up:** Phase-2 candidates drawn from P2-025..P2-039 only after further
  development evidence.

## PF-019 - Stale P2 docs said Phase-1 "not executed" (2026-09-18)
- **Where:** `docs/P2_IMPLEMENTATION_ROADMAP_2026_2027.md` (header "It has not
  been executed"), `docs/ADAPTIVE_BUDGET_P2_PRE_REGISTRATION_NOTE.md` ("no P2
  execution has started"), `reports/P2_ALGORITHM_LANDSCAPE_2026-09.md`
  ("not executed here").
- **Symptoms:** documentation conflicted with the executed-and-frozen P2
  Phase-1 NEGATIVE closure (2026-09-18).
- **Root cause:** those documents predated the Phase-1 execution; the closure
  updated 00_CURRENT_RESEARCH_STATE.md / PROGRESS.md / DECISIONS.md but the
  three historical P2 docs were not reconciled.
- **Action:** reconciled all three headers/status lines to state the current
  truth — Phase-1 EXECUTED on DEVELOPMENT, NEGATIVE closure, broader P2
  program remains OPEN for possible Phase-2 candidates; MSC roadmap updated
  with a 2026-09-18 block.
- **Status:** RESOLVED (docs-only; ZERO API).

## PF-020 - AI-blinded package needed neutral identity (2026-09-18)
- **Where:** `research/semantic_audit/ai_blinded_v1/` preparation.
- **Symptoms:** the original human packets/forms carry arm labels
  (top_ranked_omitted / matched_random_omitted) and method context; raw reuse
  would leak method/rank to the AI raters.
- **Root cause:** the human audit was designed for humans, not for blinded AI
  rating.
- **Action:** derived AI-facing packets with neutral case/row/candidate IDs and
  ONLY the semantic role (historical_changed_file / omitted_candidate_file);
  original arms preserved in a sealed private mapping never sent to raters;
  leak scan (FORBIDDEN_TOKENS) clean.
- **Status:** RESOLVED (prepared; AWAITING_RATER_OUTPUTS).

## PF-021 - Two frozen AI-audit outputs were not strict JSON (2026-09-18)
- **Where:** inputs/semantic/results/chatgpt_batch_02_result.json and
  chatgpt_batch_04_result.json (frozen rater outputs, as received).
- **Symptoms:** json.loads failed — unescaped inner double quotes inside
  vidence string values (e.g. select_related("parent", "placeholder"),
  getattr(request, "placeholders", {}).values(), "oqn" corrected to "own").
- **Root cause:** the external raters embedded code-ish quotes in evidence
  strings without JSON escaping.
- **Action:** created normalized syntax-only copies (deterministic tolerant
  parse re-serialization; only unescaped quotes re-escaped, markdown fences +
  trailing commas stripped); originals preserved byte-identical; full content
  preservation verified by tolerant-parse equality; analysis ingested the
  normalized copies.
- **Status:** RESOLVED (syntax-only; no label/confidence/rationale/evidence/
  case judgment changed; originals frozen and untouched).
