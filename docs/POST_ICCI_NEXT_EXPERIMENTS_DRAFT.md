# POST-ICCI Next-Experiment Protocol DRAFTS (NOT EXECUTED)

**Date:** 2026-09-15 · **Status:** DRAFT ONLY — no API call, no model run.
**Zero scientific inference in this document.**
These protocols are proposals for supervisor review. None is authorized to run
yet; each requires its own preregistration, frozen manifest, cost ceiling, and
authorization before cell 1.

**Universal constraints:**
- The exposed `HELD_OUT_TEST` ten are **PERMANENTLY EXPOSED** — they may be
  used for reporting/audit only. No tuning, no confirmatory "check" calls.
- Any decision rule (threshold, features, escalation policy) must be selected
  on TRAIN/VALIDATION (or MINER_DEV) only.
- Fresh confirmatory evidence requires a fresh split or a second repository.
- Ground truth = observed change-set proxy (evaluation-only).

---

## Protocol A — Cheap non-LLM baseline (TRAIN/VALIDATION only)

**Question.** How good is a zero-LLM-cost retriever at reproducing the observed
change-set proxy, as an upper/lower reference for selective escalation?

**Design (draft).**
- Universe: the frozen TRAIN 24 + VALIDATION 6 case candidate universes
  (MINER_DEV 6 allowed for development).
- Methods (all deterministic, zero LLM): BM25 on the parent snapshot
  file contents vs the normalized commit intent; Graph@K (parent-only
  dependency graph, seed = intent-hit files); Hybrid@K (BM25 + graph);
  Random@K (control).
- Metric: task-level P/R/F1/FNR at fixed K ∈ {1,3,5,10} against the
  observed change-set proxy; report at task level and pooled micro.
- Selection: any threshold/graph-zone choice is made on TRAIN, locked on
  VALIDATION, NEVER on HELD_OUT_TEST.
- Cost: $0 (no API). Ceiling: none needed.
- Deliverable: baseline table + frozen hyperparameters + zero-API verifier.

**Do NOT:** tune on the exposed 10; claim a semantic ground-truth match
(the proxy is an observed diff).

---

## Protocol B — Faithful LocAgent replication (VALIDATION; NEW budget)

**Question.** Does a faithful re-execution of the pinned upstream LocAgent
(no compatibility divergence) reproduce the P5 descriptive result, on the
VALIDATION split (not the exposed held-out ten)?

**Design (draft).**
- Target: upstream `gersteinlab/LocAgent` @ `4935b557326c154bad8e8dcf3747cc8d32d1f387`.
- Inputs: VALIDATION 6 (leakage-free adapter inputs, `patch=""`), NOT the
  exposed HELD_OUT_TEST ten.
- Settings: temperature 1 (upstream), num_samples 1, max_attempt_num 1,
  timeout 900, ranking MRR — exactly as P5-C; NO per-call backend pin claim
  (OpenRouter-routed, provider provenance logged).
- Cost ceiling: fresh frozen budget (P5-C was ~$9.93 for 10 tasks → scale
  estimate for 6 tasks; ceiling proposed after supervisor review, e.g. ≤ $6).
- Credential: dedicated Benchmark key only; ledger per call; upstream
  `calc_cost` diagnostic-only.
- Common evaluator: frozen exact-emitted-file-set policy
  (`evaluator.COMMON_EVALUATOR_VERSION`), universe intersection, fail-closed
  empty retention; native Acc@K reported separately.
- Audit: reuse `scripts/audit_locagent_p5c.py` pattern on the new run.

**Do NOT:** claim this reproduces the published fine-tuned LocAgent result;
report provider-route limitation; report survivor-conditioned numbers only as
diagnostic.

---

## Protocol C — Fresh second-repository / fresh-held-out confirmatory

**Question.** Does the sparse-vs-full cost effect (and any selective-escalation
signal) replicate on a repository and split that have NEVER been used for a
decision?

**Design (draft).**
- Option C1 (fresh repository): mine a second repository (e.g. a second
  Django-ecosystem repo or Saleor per `reports/SALEOR_DECISION.md`) with the
  M4A-1 miner rules + leakage barrier; freeze TRAIN/VALIDATION/HELD_OUT_TEST
  BEFORE any model result; run the frozen P1 protocol (Full-v2 vs Sparse-v2,
  cap 16384, temp 0) with its own cost ceiling.
- Option C2 (fresh split, same repo): mine a NEW non-overlapping batch of
  djangoCMS cases that are NOT among the 40 mined cases and NOT the 6
  MINER_DEV cases; freeze a new split; same frozen P1 protocol.
- Rule: the new HELD_OUT_TEST must be disjoint from every case that informed
  ANY prior decision (P1/P5/M3/M1 development cases).
- Cost: fresh budget per protocol, frozen before cell 1 (P1 full 60-cell
  scale ~$0.36; scale to repository size).
- Deliverable: P/R/F1/FNR + cost + bootstrap over the new tasks; zero-API
  verifier; independent audit.

**Do NOT:** reuse the exposed ten; do NOT pool the new held-out with the old
held-out into one "n=20" without preregistering the pooling rule.

---

## Relationship to the MSc proposal

- Protocol A = the cheap-baseline first rung of the selective-escalation
  pipeline (sparse first pass → omission-risk detection → bounded escalation).
- Protocol B = descriptive replication of the agentic localization baseline.
- Protocol C = the fresh confirmatory test required before ANY new-method
  claim.

All three are INPUTS to the MSc proposal package
(`docs/MSC_RESEARCH_ROADMAP_2026_2027.md`); none has been run.