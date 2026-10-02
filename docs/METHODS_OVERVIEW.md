# METHODS OVERVIEW

**Role:** Concise overview of the methods behind the primary results. This is
not the frozen protocol text; it is the reader-facing explanation of how the
selection method, the comparison protocol and the downstream pipeline work.

---

## 1. The selection method: SIP → RM-CSS

### Sparse Impact Plan (SIP)

SIP is a single model call that lists only the files a change request would
touch; every unlisted file is treated as "preserve". Compared with an explicit
full-repository plan it dramatically reduces completion output and avoids
output-truncation, at the cost of possibly omitting files (omission risk).

### RM-CSS (Repository-Memory Calibrated Set Selection)

RM-CSS is the frozen localization method. On top of the SIP first pass it adds:

1. **Qwen dense ranking** of candidate files for the change request;
2. **parent-only Repository Memory** (the repository at its parent commit —
   target/hidden state never enters inference);
3. a **frozen calibrated logistic classifier** that labels each candidate
   ADD / KEEP / DROP.

RM-CSS adds no generative model call on top of SIP; it is a calibration /
re-ranking step. Thresholds and the classifier are frozen.

## 2. The comparison protocol: WP-1b MAIN_297 (selection-only)

MAIN_297 is a paid, same-model, same-protocol, selection-only comparison of
three arms on the Saleor MAIN sample (n=297):

| Arm | What it selects |
|---|---|
| SIP | sparse impact plan file set |
| RM-CSS | calibrated file set (above) |
| Agent | a budget-bounded iterative repository agent (protocol v3) |

- **Endpoint:** pooled file-level F1 against the observed parent→target
  changed production-file set (an *observed change-set proxy*, not semantic
  gold).
- **Statistic:** D = F1(RM-CSS) − F1(Agent), paired bootstrap.
- **Decision rule:** preregistered non-inferiority at Δ = 0.05 pooled micro-F1
  (fail-closed EMPTY); Δ = 0.03 is a sensitivity margin.
- **Cost accounting:** View A marginal ratios (calls, generative tokens, USD at
  list price) are the provider-robust efficiency claims; billed usage is
  reported separately.

**Boundary:** this is a **selection-stage** result (file localization), not
end-to-end code-generation correctness.

## 3. Downstream pipeline: WP2

- **Oracle/harness:** a Linux V3 environment harness (lock-exact installs,
  changed-test F2P classification) and an oracle-confirmation selection.
- **Smoke / Pilot:** a shared E2E instrument (generator + validator + repair)
  exercised on small pools to validate the pipeline.
- **Pilot-A / M14R:** generator-capability probes that measured whether a
  generator can resolve gold-patch tasks (both failed to clear the floor).
- **M15-R OPWS:** a generator-independent endpoint. OPWS asks whether the
  developer's own patch, restricted to the files a selector allowed, still
  passes the hidden tests (Pilot-B, n=10; descriptive).
- **M16-v1:** an attempted OPWS-MAIN instrument qualification that stopped
  before any experiment at the adapter-verification stage; closed as a method
  failure, no MAIN outcome.

## 4. Evaluation semantics (frozen)

- **GOLD_HARD:** modified/deleted non-test files of the developer patch
  (added and renamed files excluded), D35-filtered.
- **File-level P/R/F1** of a selected editable scope against GOLD_HARD /
  G_raw are the selection metrics.
- **OPWS_ROBUST / OPWS_STRICT:** execution-sufficiency endpoints defined in the
  M15-R design; `resolved` semantics are frozen.

## 5. Where the authoritative protocol text lives

- Formal selection model: [`docs/STAGEC_FORMAL_MODEL.md`](STAGEC_FORMAL_MODEL.md),
  [`docs/RISK_AWARE_SPARSE_IMPACT_SELECTION_MODEL.md`](RISK_AWARE_SPARSE_IMPACT_SELECTION_MODEL.md).
- WP-1b protocol / rules: `research/wp1b/wp1b_frozen_agent_protocol_v3.json`,
  `research/wp1b/wp1b_decision_rules_v2.json`.
- Evaluation/execution protocol: [`docs/EXECUTION_AND_VALIDATION_PROTOCOL_V2.md`](EXECUTION_AND_VALIDATION_PROTOCOL_V2.md),
  [`docs/GROUND_TRUTH_PROTOCOL.md`](GROUND_TRUTH_PROTOCOL.md),
  [`docs/LEAKAGE_PREVENTION_PROTOCOL.md`](LEAKAGE_PREVENTION_PROTOCOL.md).
- Experiment registry with artifact paths: [`docs/EXPERIMENT_LEDGER.md`](EXPERIMENT_LEDGER.md).