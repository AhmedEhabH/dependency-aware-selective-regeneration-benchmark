# Research Decision Ledger

**Purpose:** major decisions with question / options / chosen / why / rejected /
revisit condition. Appendix to `DECISIONS.md` (append-only decisions).
Entries use the format requested by the evening addendum (2026-09-16).

---

## D-001 — Selection-stage benchmark closure
- **Question:** Should the selection-stage benchmark be closed at `v0.11.0-benchmark-complete`?
- **Options:** close+tag / extend with more scenarios / start Pilot.
- **Chosen:** close and tag `v0.11.0-benchmark-complete`.
- **Why:** benchmark research complete and audited; moving to post-ICCI scientific line.
- **Rejected:** extending the legacy benchmark (no new scientific value); starting Pilot (deferred).
- **Evidence:** reports/, tags.
- **Revisit:** never for the frozen legacy benchmark.

## D-002 — P1 serialized-record metric correction
- **Question:** Was Sparse-v2's mean serialized-record figure 4.9 or 5.9?
- **Options:** keep published 4.9 / recompute as 5.9.
- **Chosen:** 4.9 is the mean serialized decision count for the corrected metric;
  the 5.9 corrected figure in one report was a recomputation of a different
  aggregate and is NOT used in the proposal.
- **Why:** the evening mission mandates Sparse mean serialized records = 4.9,
  Full = 144.0, reduction ~96.6%.
- **Evidence:** `reports/REAL_COMMIT_M4A3_P1_SERIALIZATION_METRIC_CORRECTION.md`.
- **Revisit:** no.

## D-003 — Task-level RiskScorer route
- **Question:** Should a task-level cheap RiskScorer be built?
- **Options:** build / not build.
- **Chosen:** NOT build on current evidence.
- **Why:** class-balance gate failed (v1: 4 negatives < 10; V2 merged: signal
  does not replicate within cohort; pooled signal is a universe-size artifact).
- **Rejected:** forcing a weak scorer.
- **Evidence:** `reports/OMISSION_RISK_SPARSE_V2_INFERENCE_REPORT.md`,
  `reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md`.
- **Revisit:** only if a larger balanced development set establishes a stable
  predeclared signal above the random band with direction stability.

## D-004 — Route A vs Route B contingency
- **Question:** If task-level routing fails, what mechanism answers RQ3?
- **Options:** Route A (task-level selective routing) / Route B (candidate-level
  bounded omission verification).
- **Chosen:** Route B as the default next mechanism; Route A only if a larger
  development set justifies it.
- **Why:** task-level risk is not separable on current evidence; candidate-level
  verification uses observable omitted-candidate evidence under a hard budget.
- **Rejected:** inventing a weak RiskScorer for task-level routing.
- **Evidence:** V2 protocol + proposal V1.2.
- **Revisit:** Route A if the progression gate passes on DEV_VALIDATION.

## D-005 — V2 split design
- **Question:** How to split the 289 untouched eligible djangoCMS cases?
- **Options:** DEV/INTERNAL_TEST/RESERVE metadata-only split / census (all 329).
- **Chosen:** metadata-only deterministic split (seed 20260916): DEV_TRAIN 120,
  DEV_VALIDATION 30, INTERNAL_TEST 80, RESERVE 59.
- **Why:** preserves an untouched internal test; census destroys internal
  untouched confirmation and is descriptive-only.
- **Rejected:** V2-CENSUS for the confirmatory line; reusing the exposed v1 40.
- **Evidence:** `research/transparency/v2_split_proposal.json` (hashes).
- **Revisit:** no; INTERNAL_TEST/RESERVE remain untouched.

## D-006 — V2 development inference ceiling
- **Question:** How many V2 development cells/tokens/cost to authorize?
- **Options:** 450 cells / 2.5M tokens / $1.00 (mission) vs smaller.
- **Chosen:** 450 cells / 2.5M tokens / $1.00 ceiling, fail-closed.
- **Why:** sample-size analysis recommended N=120-150 new dev tasks.
- **Rejected:** exceeding ceilings; running INTERNAL_TEST/RESERVE.
- **Evidence:** `reports/REAL_COMMIT_V2_SAMPLE_SIZE_ANALYSIS.md`.
- **Revisit:** n/a.

## D-007 — V2 inference token-ceiling post-call overshoot
- **Question:** What to do when the 431st call pushed tokens to 2,501,964
  (1,964 / 0.08% over the nominal 2.5M ceiling)?
- **Options:** continue / stop.
- **Chosen:** fail-closed stop before another call.
- **Why:** the ceiling is a hard budget; a post-call check cannot pre-empt the
  final call's own tokens.
- **Rejected:** running the remaining 19 cells.
- **Evidence:** `reports/REAL_COMMIT_V2_OMISSION_RISK_DEVELOPMENT_ANALYSIS.md`.
- **Revisit:** n/a; documented exactly as an overshoot, not "within ceiling".

## D-008 — LocAgent P5 classification
- **Question:** Is P5 a faithful reproduction or system-level context?
- **Options:** faithful / system-level shared-protocol context.
- **Chosen:** system-level shared-protocol context; P5 is NOT a reproduction of
  the published fine-tuned result.
- **Why:** OpenRouter-routed (backend not pinned per call), upstream hard-coded
  temperature 1, only 10 tasks, 5/10 non-usable.
- **Rejected:** claiming LocAgent P5 as authoritative algorithm ablation.
- **Evidence:** `reports/LOCAGENT_P5C_HELDOUT_RUN.md`.
- **Revisit:** P5R-1 relaxes operational limits (timeout 1800s, context to the
  same route's max) while keeping algorithm constant; P5R metrics are NOT blended
  with P5.

## D-009 — LocAgent P5 failure taxonomy
- **Question:** Were the 5 non-usable outcomes all timeouts?
- **Options:** all timeouts / mixed taxonomy.
- **Chosen:** mixed: 2 timeout + 1 context-length + 2 completed-but-empty.
- **Why:** raw logs show distinct failure types; "50% empty localization rate"
  wording is NOT supported.
- **Evidence:** `reports/LOCAGENT_P5C_HELDOUT_RUN.md`.
- **Revisit:** n/a; corrected wording used in all documents.

## D-010 — Classical/static CIA baseline
- **Question:** Should a zero-LLM classical change-impact baseline be added?
- **Options:** yes / no.
- **Chosen:** yes (Milestone D).
- **Why:** the thesis must compare LLM/agent methods against fair classical
  baselines, not only against each other.
- **Rejected:** forcing CodeQL or an external tool whose input contract is
  incompatible.
- **Evidence:** `reports/CLASSICAL_CIA_BASELINE_V1_REPORT.md`.
- **Revisit:** extend to cross-repo if frames are rebuilt.

## D-011 — Saleor classification
- **Question:** Is Saleor suitable as Stage 2?
- **Options:** SUITABLE / SUITABLE-WITH-DEVIATIONS / UNSUITABLE.
- **Chosen:** SUITABLE-WITH-DEVIATIONS (larger universes, higher frozen-ceiling
  exclusion rate, history requires full cache).
- **Why:** same Python/Django stack; frozen machinery applies; real second system.
- **Rejected:** UNSUITABLE (not supported by evidence); no Saleor inference tonight.
- **Evidence:** `reports/SALEOR_REPOSITORY_SUITABILITY_AUDIT.md`.
- **Revisit:** after full-history cache → sampling frame → split freeze.

## D-012 — NestJS classification
- **Question:** Is NestJS suitable as Stage 3?
- **Options:** SUITABLE / SUITABLE-WITH-DEVIATIONS / UNSUITABLE.
- **Chosen:** SUITABLE-WITH-DEVIATIONS (TS import extractor required; small
  universe; predeclared >=60 eligible yield; JabRef backup).
- **Why:** cross-language/cross-framework evidence; MIT license; active history.
- **Rejected:** choosing a replacement based on model results.
- **Evidence:** `reports/NESTJS_REPOSITORY_SUITABILITY_AUDIT.md`.
- **Revisit:** after TS extractor + eligible-pool yield check.

## D-013 — Proposal title
- **Question:** What working title for the thesis?
- **Options:** Cost-Aware Repository Change Localization with Sparse Impact
  Planning and Bounded Verification / Repository Change Localization Under
  Limited Inference Budgets / graph-in-title variants.
- **Chosen:** the preferred cost-aware title; graph is only one optional
  verifier, never a required success.
- **Why:** does not assume graph or RiskScorer success.
- **Rejected:** "Graph-Guided" in the primary title unless the text scopes graph
  as optional.
- **Evidence:** proposal V1.2.

## D-014 — Proposal factual corrections (V1.2)
- **Question:** Which stale numbers had to be corrected?
- **Options:** correct / leave.
- **Chosen:** correct all: Sparse 4.9 / Full 144.0 / reduction ~96.6%;
  LocAgent 5/10 non-usable taxonomy; V2 431 calls / 2,501,964 tokens /
  1,964-token (0.08%) overshoot; remove unsupported latency/cost claims.
- **Why:** every number must map to one frozen artifact; no placeholder authors
  in a print bibliography.
- **Rejected:** keeping stale 5.9 / "50% empty" / "within ceiling".
- **Evidence:** M1B report, P5C report, V2 closure.
- **Revisit:** n/a.
## D-015 — Route B primary mechanism: classical CIA candidate ranking
- **Question:** Which zero-LLM candidate-ranking arm is the primary Route B mechanism?
- **Options:** BM25 / path-token / graph-neighbor / classical CIA (BM25+graph) / hybrid / random.
- **Chosen:** R4_Classical CIA (BM25-seed 1-hop closure + graph neighbor) as the best predeclared arm at B=5.
- **Why:** beats Random on both splits with no universe-size artifact; same direction.
- **Rejected:** path-token (worst arm); random (floor).
- **Evidence:** reports/ROUTE_B_OMISSION_RECOVERY_V1_REPORT.md.
- **Revisit:** if a larger validation set changes the comparison; verifier pilot only if the gate strongly passes.

## D-016 — Route B V2 progression gate PASS; CIA ranker family frozen
- **Question:** Does the candidate-level CIA ranker robustly beat analytic Random over the B curve on DEVELOPMENT?
- **Options:** freeze CIA as the verifier ranker / keep exploring.
- **Chosen:** freeze CIA (BM25 + graph-neighbor) as the predeclared ranker family for the conditional verifier pilot.
- **Why:** 5/5 folds positive direction; 4/4 B-curve points above analytic Random; bootstrap CIs exclude zero at B in {1,3,5,10}; no omitted/universe-size artifact (corr -0.119/-0.117).
- **Rejected:** path-token (worst); single-draw Random (replaced by analytic hypergeometric expectation); tuning per fold.
- **Evidence:** reports/ROUTE_B_V2_ROBUSTNESS_REPORT.md; research/transparency/route_b_v2_results.json.
- **Revisit:** if a fresh confirmatory set (INTERNAL_TEST, after full freeze) contradicts the direction.

## D-017 — B=5 is a reference point, not the sole primary
- **Question:** Is B=5 the sole primary scientific claim?
- **Options:** B=5 only / budget curve B in {0,1,3,5,10}.
- **Chosen:** budget curve; B=5 is a convenient reference operating point only.
- **Why:** the scientific object is recovery effectiveness as a function of added inspection budget; a single point is fragile.
- **Rejected:** claiming B=5 is scientifically privileged.
- **Evidence:** docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md.
- **Revisit:** n/a.

## D-018 — Analytic Random (hypergeometric) replaces single-draw Random
- **Question:** Which Random control for ranking-only experiments?
- **Options:** single random draw / analytic hypergeometric expectation.
- **Chosen:** analytic E[X] = B*M/N (B clipped to N).
- **Why:** avoids dependence on one lucky draw; the comparison is per-task analytic expectation with task-level bootstrap CI.
- **Rejected:** single-draw Random (variance from one seed); counting random repetitions as independent tasks.
- **Evidence:** docs/ROUTE_B_V2_DEVELOPMENT_PROTOCOL.md.
- **Revisit:** n/a (frozen).

## D-019 — Saleor bundle build partial; inference NOT run tonight
- **Question:** Is Saleor scientific inference ready?
- **Options:** run inference on the 98 built / wait for all 150.
- **Chosen:** do NOT run inference tonight; the mission's Section 11 requires
  Saleor bundles + split + gates + audit PASS for all needed DEV cases, which
  the 52 extraction-blocked cases prevent.
- **Why:** 52/150 DEV bundles could not be materialized on Windows (git archive
  path rejection); running on 98 would be an undocumented subset.
- **Rejected:** running Saleor inference on a partial DEV set; weakening the
  production-file rule to skip the cassette path.
- **Evidence:** reports/SALEOR_CASE_BUNDLE_BUILD_REPORT.md.
- **Revisit:** POSIX re-run or cassette-exclusion workaround, then re-freeze.

## D-020 — Saleor identity/provenance correction + re-authorization (2026-09-17)
- **Question:** Should the Saleor dataset be re-run with corrected identity, and
  is Saleor DEVELOPMENT scientific execution now authorized?
- **Options:** (a) migrate IDs to saleor-rc-<sha> + fix identity + re-freeze;
  (b) run with the djangocms-rc-* leak; (c) keep blocked.
- **Chosen:** (a) — deterministic migration (saleor-rc-<sha>), corrected
  repository URL/anchor/license/repo identity, old→new mapping, 150/150
  scientific-payload equivalence PASS (commits/split/universes/proxies/edges
  preserved). The single pre-fix smoke call is archived as operational smoke
  (NOT scientific evidence).
- **Why:** the djangocms-rc-* case ID was visible in the inference prompt — a
  provenance leak that would corrupt a Saleor scientific run.
- **Rejected:** (b) leaking wrong repo identity into prompts; (c) leaving Saleor
  permanently blocked after the portability fix.
- **Evidence:** reports/SALEOR_IDENTITY_MIGRATION_REPORT.md,
  research/transparency/saleor_identity_equivalence_150.json.
- **Revisit:** n/a (identity is a correction, not a protocol change).
- **AUTHORIZATION (2026-09-17):** a clean 150x3 DEVELOPMENT sparse run is
  authorized with hard ceilings 450 cells / 9,000,000 total tokens / .00; no
  INTERNAL_TEST/RESERVE; no result-dependent reruns; no Saleor-specific tuning.
  After the run closes, the frozen Route-B transfer replication is executed and
  classified (REPLICATES / PARTIAL / DOES NOT REPLICATE).

## D-021 - Ranker-identity audit + terminology correction (2026-09-17)
- **Question:** Is the frozen Route-B V2 "Classical-CIA" arm actually a
  classical dependency-propagation CIA, and is Hybrid independent of CIA?
- **Options:** (a) audit the exact code + prove equivalence; (b) trust the
  historical label.
- **Chosen:** (a) - audit confirms CIA = normalized BM25 + binary graph-neighbor
  (NOT dependency-propagation CIA); Hybrid is a positive scalar multiple of the
  CIA key -> MATHEMATICALLY RANK-EQUIVALENT (0 differing task-budget cells on
  174 djangoCMS + 149 Saleor DEV tasks). Hybrid = redundant alias/control.
  Terminology corrected to BM25+Graph-Neighbor Composite (historical label:
  CIA). No formula change before confirmatory testing.
- **Why:** documentation must match the exact committed code; Hybrid was never
  an independent baseline.
- **Rejected:** (b) retaining an overstating label in the confirmatory packet.
- **Evidence:** reports/ROUTE_B_RANKER_IDENTITY_AUDIT.md.
- **Revisit:** n/a (correction appended; historical results unchanged).

## D-022 - Incremental-evidence ablation scoped as characterization (2026-09-17)
- **Question:** Does graph evidence materially add to BM25, or is the transfer
  signal predominantly lexical?
- **Options:** (a) characterize on DEVELOPMENT; (b) choose a new ranker now.
- **Chosen:** (a) - composite−BM25 paired deltas small, CIs include zero at
  most B; signal predominantly lexical; NO new ranker chosen; frozen
  confirmatory method unchanged. Saleor history UNAVAILABLE (no cache).
- **Rejected:** (b) method change before confirmatory testing.
- **Evidence:** reports/ROUTE_B_INCREMENTAL_EVIDENCE_ABLATION.md.
- **Revisit:** n/a (characterization only).

## D-023 - Confirmatory budget frozen (2026-09-17)
- **Question:** What is the exact confirmatory API budget for 80 djangoCMS
  INTERNAL_TEST tasks?
- **Options:** (a) DEVELOPMENT-distribution-based ceilings; (b) ad-hoc budget.
- **Chosen:** (a) - 560 calls / ≤2,100,000 tokens / ≤.00; per-call
  reservation rule (sparse p99 7,877 tok / .00302; verifier 400 tok /
  .00015) so cumulative budget cannot overshoot materially. ZERO test peek.
- **Rejected:** (b).
- **Evidence:** reports/DJANGOCMS_CONFIRMATORY_API_BUDGET_FREEZE.md.
- **Revisit:** requires Ahmed's approval before any confirmatory call.

## D-0XX - P2 Phase-1 negative closure + fixed Route-B reviewer closure (2026-09-18)
- **Question:** Should P2 Phase-1 close negative, and should the fixed Route-B
  reviewer-facing issues be closed without changing the frozen result?
- **Options:** (a) close P2 Phase-1 negative + add POST-HOC characterization;
  (b) tune further / run stronger methods / edit the frozen confirmatory.
- **Chosen:** (a) — P2-P1..P2-P4 all NEGATIVE on DEVELOPMENT; strong-method gate
  FALSE; fixed Route-B confirmatory untouched; curve-level POST-HOC
  characterization, sparse-vs-full parity audit (PARITY_VERIFIED), and dataset
  operational-definition audit produced. ZERO API.
- **Why:** the pre-registered gate for stronger methods was False on both repos
  (each policy either saved cost but lost >50% recovery or matched recovery at
  no saving); a negative is a valid scientific result; reviewer issues are
  closure/documentation, not method change.
- **Rejected:** (b) — tuning/stronger methods without gate passage; editing the
  frozen confirmatory; opening sealed sets; new model calls.
- **Evidence:** reports/P2_PHASE1_* + research/p2-phase1/* + 31 tests.
- **Revisit:** Phase-2 candidates from the expanded landscape after further
  development evidence; Saleor INTERNAL_TEST stays sealed.
