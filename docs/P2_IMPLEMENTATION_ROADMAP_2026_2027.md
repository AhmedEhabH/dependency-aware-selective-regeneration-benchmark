# P2 Implementation Roadmap — November 2026 → March 2027

**Date:** 2026-09-17
**Tier:** T0 documentation (DEVELOPMENT-only program design; ZERO API here)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731
**Status:** ROADMAP FROZEN (start: Nov 2026). Fixed Route-B is CONFIRMED and is
NOT retuned. P2 runs on DEVELOPMENT only.

**Explicit status (2026-09-17):**
- **P2 is NOT complete.** It has not been executed, has no learned policy, and
  is not a proven contribution.
- **Fixed Route B is CONFIRMED** (djangoCMS INTERNAL_TEST, 2026-09-17) and is
  the frozen fallback thesis.
- **P2 is a development research program**, not a completed contribution:
  a five-month (Nov 2026 – Mar 2027) exploration of Shichao-Zhang-inspired
  algorithms plus competitors/analogues from selective prediction / abstention,
  cascaded inference, optimal stopping, budgeted retrieval, value-of-information,
  and interpretable adaptive stopping — evaluated on djangoCMS DEV + Saleor DEV
  only under the common evaluation contract.
- **NestJS/NextJS/cross-language extension is future external-validity work**
  (April 2027), conditional on the suitability gate AND TypeScript-extractor
  readiness; it is outside the P2 five-month window.

---

## 0. Context

- djangoCMS INTERNAL_TEST confirmatory result: **CONFIRMS** (2026-09-17). The
  fixed-B thesis is now scientifically confirmed and is the fallback.
- P2 (adaptive `B_t`) is CONDITIONAL → the five-month program below is the
  path to either a justified P2 candidate or an honest negative closure.
- **Data boundary:** djangoCMS DEV + Saleor DEV only for development/selection.
  The opened djangoCMS INTERNAL_TEST is permanently spent. Saleor
  INTERNAL_TEST stays sealed as the only possible future P2 confirmation set.

## 1. Monthly plan (realistic; may finish earlier — no fabricated months)

### November 2026 — confirmation closure + formulation freeze
- [ ] Close the fixed Route-B confirmatory result (DONE 2026-09-17; CONFIRMS).
- [ ] Reproduce/verify the Shichao-Zhang algorithmic formulations from primary
      papers (Learning-k, one-step, cost-sensitive, reachable-distance,
      demand-driven kNN) — verify formulas and adaptation variables.
- [ ] Freeze the common P2 DEVELOPMENT evaluation harness (Block E contract).
- [ ] Establish fixed anchors: fixed B={1,3,5,10}, Analytic Random, BM25-only,
      frozen composite, Oracle, InspectAll; plus the three pre-registered
      policies (P2-P1/P2-P2/P2-P3) as anchors.
- **Exit:** harness reproduces the DEV anchors; formulation note written.

### December 2026 — simple adaptive policies (DEV only)
- [ ] Implement P2-P1 score-gap stopping.
- [ ] Implement P2-P2 marginal-score threshold.
- [ ] Implement P2-P3 cost-ratio stopping.
- [ ] Implement a Learning-k-inspired per-task budget selection analogue.
- [ ] Common matched-budget evaluation on djangoCMS DEV + Saleor DEV.
- **No neural / large learned model** unless evidence justifies it.
- **Exit:** per-policy recovery-vs-budget curves vs anchors.

### January 2027 — stronger interpretable policies (DEV only)
- [ ] Cost-sensitive expected-loss stopping (Zhang cost-sensitive analogue).
- [ ] One-step / joint candidate-ranking + budget-selection analogue.
- [ ] Demand-driven budget selection under explicit recovery/cost preferences.
- [ ] Deterministic selective/cascade/optimal-stopping variants if the simple
      policies underperform.
- **Exit:** candidate shortlist (interpretable, deterministic).

### February 2027 — strongest alternative algorithms
- [ ] Search + reproduce 2–4 strongest alternative algorithms from the
      systematic landscape (selective/defer/cascade/optimal-stopping/
      budget-allocation families) as applicable.
- [ ] Run common matched-budget evaluation on djangoCMS DEV + Saleor DEV.
- **Exit:** matched-budget comparison table; algorithmic-analysis notes.

### March 2027 — freeze / select / pre-register
- [ ] Freeze negative methods (record why).
- [ ] Select at most 1–2 scientifically justified P2 candidates using
      DEVELOPMENT only.
- [ ] Pre-register their final evaluation (frozen protocol).
- [ ] If justified: use still-sealed Saleor INTERNAL_TEST for P2
      confirmation; otherwise close P2 as NEGATIVE/INSUFFICIENT and keep the
      fixed-B thesis (already CONFIRMED).
- **Exit:** P2 closure decision (ACTIVE candidate / NEGATIVE closure) + final
  evaluation pre-registration or negative-closure report.

### April 2027 — optional external-validity extension (outside the P2 window)
- [ ] NestJS/NextJS cross-language extension ONLY IF the suitability gate passes
      AND the TypeScript extractor is ready (future external-validity work; no
      forced cross-language claim).
- [ ] Otherwise keep the P2 negative/ACTIVE closure as final for the program.
- **Exit:** external-validity decision recorded (run or explicitly deferred).

## 2. Hard constraints

- No P2 method selection on the opened djangoCMS INTERNAL_TEST (spent).
- No learned (neural) policy unless a deterministic/interpretable justification
  fails first and a preregistered protocol is approved.
- No fabricated months: if the program converges earlier, it finishes earlier.
- No method change to fixed Route B (CONFIRMED, frozen).

## 3. Success / failure

- **Success:** a pre-registered P2 policy achieves comparable-or-better
  omission recovery than the best fixed-B operating point with lower expected
  verification cost on DEVELOPMENT, and (if justified) confirms on Saleor
  INTERNAL_TEST.
- **Failure:** no P2 candidate dominates → P2 closes NEGATIVE; the fixed-B
  thesis (CONFIRMED) is reported intact. A negative P2 is a scientific result,
  not a failure of the thesis.
## 4. Status update — P2 PHASE-1 EXECUTED (2026-09-18, DEVELOPMENT, ZERO API)

The Nov 2026 window was brought forward and executed as a DEVELOPMENT-only
Phase-1 on 2026-09-18:

- **Harness:** common adaptive-budget DEVELOPMENT harness built
  (src/benchmark/p2/, scripts/p2_phase1_run.py, scripts/p2_phase1_gates.py)
  with the frozen anchors (fixed B={1,3,5,10}, BM25, Analytic Random, Oracle,
  InspectAll) and the measured verifier cost model.
- **P2-P1..P2-P4 implemented + evaluated** on djangoCMS DEV (174) + Saleor DEV
  (149): constants derived on djangoCMS DEV_TRAIN only (tau_gap 0.10,
  tau_marg 1.0, tau_energy 0.90, cost-ratio grid {0.5,1.0,2.0}).
- **Result: all four NEGATIVE** (P2-P3 REJECTED_BY_DESIGN as a size/repo
  artifact); strong-method gate FALSE; stronger methods NOT run.
- **P2 Phase-1 = NEGATIVE (frozen).** Phase-2 candidates: NONE yet. The fixed-B
  thesis (CONFIRMED) stands intact.
- **Remaining for the program:** Phase-2 candidates may be drawn from the
  expanded landscape (P2-025..P2-039) after further development evidence;
  Saleor INTERNAL_TEST stays sealed for a possible future P2 confirmation ONLY
  after a policy is frozen (not the case).
