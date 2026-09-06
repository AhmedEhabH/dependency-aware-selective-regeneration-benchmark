# v0.9.22 D10 — ALL-FAILED PILOT ROOT-CAUSE + VIABILITY CLOSURE REPORT (PILOT-EXEC-01)

**Report Date:** 2026-08-31
**Project:** Dependency-Aware Selective Regeneration Benchmark
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Task Pack:** `_workspace/active/PILOT-EXEC-01-V0922-D10-ALL-FAILED-PILOT-VIABILITY-CLOSURE.md`
**Head/Origin:** `1abc9b646bf6ad4f82d5e8382998b3609b98c7fe` (at start; see per-commit states below)

---

## 1. Executive summary

The one real 48-cell Pilot attempted on 2026-08-30 against the exact D9.6
artifact (`edae1b7e5be7ebab642d1e3c068dda3842a8061b8b04ab84c027d43a38dc8c4a`,
source commit `478261ff595d3d64ed9d5bab32d1cc90d7dabd77`, tagged
`v0.9.22-pilot-exec-ready`) finished **48/48 terminal failures — 0 succeeded,
0 evaluator-passed**. The run is **REJECTED** and must be preserved verbatim,
never resumed, and never counted as scientific evidence. The stable annotated
tag `v0.9.22-pilot-exec-ready` is **NOT moved, re-created, or force-updated**;
it remains pointing at `478261ff...` but is **retired as a launch candidate**
because the only permitted one-shot Pilot launch from that artifact produced a
100%-failure outcome.

This D10 closure (D10.1–D10.7) records that rejection truthfully, corrects the
internal runtime/operability contract that caused (or masked) the failures, and
re-establishes a corrected, test-guarded launch path for a future v0.9.22
Pilot attempt. **No stable-tag move and no real Pilot launch happens in this
closure.** Remains scientific version v0.9.22 (never v0.9.23).

**Scientific inputs are UNCHANGED:** model Qwen2.5-Coder-14B-Instruct (BNB-NF4,
SDPA, kernel policy `flash_or_efficient_no_math`, GQA compat
`repeat_kv_sm75`), 12 scenarios, 3 repo pins (Todo / django CMS / Saleor),
2 strategies (selective, iterative_repository_agent), 2 repetitions = 48 cells,
prompts, Ground Truth, metrics, max attempts 3, completion cap 4096, the
12000/64 long-context gate.

---

## 2. Rejected experiment identity (verbatim, preserved)

| Field | Value |
|---|---|
| Experiment ID | `exp-20260830-134232` |
| Protocol version | `1.0` |
| Config hash | `4b5bbcb2abcf62af` |
| Source commit | `478261ff595d3d64ed9d5bab32d1cc90d7dabd77` |
| Source tag | `v0.9.22-pilot-exec-ready` |
| Deployed build id | `478261f` |
| Model identity | `qwen:14b-instruct-v1:bnb-nf4:cfg-cc9474140d25` |
| Profile | `pilot` |
| Timeout | 600 s (workflow; uniform both strategies) |
| Repo | Todo / django CMS / Saleor |
| Outcome | 48/48 terminal failed, 0 succeeded, 0 evaluator-passed |

Preserved verbatim on the machine (original `_workspace/active/` evidence plus
the temp extraction used for audit); it is frozen and MUST NOT be deleted,
resumed, or reused.

---

## 3. Quantitative facts (independently reproduced from evidence)

Reproduced directly from
`evidence/qwen14b_bnb_nf4_pilot_48_wsfix_478261f/run_records.jsonl`,
`benchmark_summary.json`, `dashboard/dashboard_summary.json`,
`failure_records.json`, `experiment_id.txt`, `source_identity.json`:

- **48 records / 48 unique run_ids / 48 `failed`** (repos 16/16/16; strategies
  12 selective + 12 agent per repo = 24/24; repetitions 2/2 = 48).
- **0 succeeded**, **0 evaluator-passed**, **0 timeout_count as a status**
  (all 48 use status `failed`).
- **Failure classifications:** `scientific_budget_exhausted` = **33**,
  `model_output` = **8**, `build` = **7** (sum = 48).
- **Workflow budget:** 293 model calls; 731,678 prompt + 88,953 completion =
  **820,631 total tokens**.
- **Total duration ~23,610 s (~6.56 h).** Per-strategy mean:
  - selective: mean 540.68 s/run, 24/24 failed (max 600.71 s),
    118 calls, 318,762 tokens.
  - iterative_repository_agent: mean 443.00 s/run, 24/24 failed,
    175 calls, 501,869 tokens.
- **33 of 48 runs hit the 600 s workflow deadline** (`scientific_budget_exhausted`,
  `stage=budget`, message `Workflow deadline reached during iterative agent
  generation calls`; configured `max_attempts=3;max_total_workflow_tokens=0;
  timeout_seconds=600;actual_elapsed_seconds=600.710`) — the 600 s ceiling
  censored the majority of runs.
- **7 `build` failures:** baseline validation `exit=1` (e.g. Python 3.12.13
  interpreter vs the frozen validation env / django version mismatch),
  generation_guard rejections, etc.
- **8+ `model_output` failures:** iterative agent "no paths selected after
  exploration" / "revision failed to select paths" — the model did not emit a
  valid selection path set for several Saleor / django CMS / Todo loc/cross
  scenarios (invalid output shape → no-path selection).
- Resume was attempted and **failed with `NameError: name 'PILOT_OUTPUT_DIR'
  is not defined`** at resume cell line 45 (see D10.4).

---

## 4. D10 root causes and fixes

### D10.1 — Truth-only closure
Record the rejection verbatim, update CURRENT TRUTH docs and DECISION_LOG,
commit+push the documentation closure with **no production changes**.

### D10.2 — Correct internal runtime contract (protocol 1.1, timeout 1200)
The 600 s workflow deadline censored 33/48 runs; the per-run ceiling was below
the measured selective mean (540 s) with zero headroom, so legitimate runs
were killed without completing. The internal runtime contract is corrected:
**protocol_version `1.0` → `1.1`** and the Pilot profile `timeout_seconds`
**600 → 1200**, applied uniformly to **both** strategies (selective and
iterative_repository_agent). All source/notebook/build/doc references updated
so the internal contract is self-consistent (no `1.0`/600 residue).

### D10.3 — Real end-to-end pilot-canary mode + fail-closed gate
Add a **real end-to-end pilot-canary** execution mode (a genuinely small real
end-to-end run: e.g. a reduced sub-matrix that still exercises the full
select → regenerate → repair → validate pipeline on target hardware, not a
no-op). Add a canonical `validate_pilot_canary_evidence` gate that
fail-closedly proves the canary actually ran end-to-end (records exist, are
not all `scientific_budget_exhausted`/deadline-censored, terminality vs
viability is separated, ok). Wire a notebook stage so an operator can run the
canary and gate before committing to the full 48.

### D10.4 — Resume stand-alone and fail-closed
The resume cell depended on the interpreter variable `PILOT_OUTPUT_DIR` that
is defined only by the launch cell. When resume is run standalone (e.g. after
a session restart), it raised `NameError`. Fix: the resume cell computes
`PILOT_OUTPUT_DIR` **independently** from the same derivation the launch cell
uses, and fails closed if the experiment is one of the rejected IDs (never
attach to `exp-20260830-134232` or any rejected experiment).

### D10.5 — Separate terminality from scientific viability
The validator conflated "did the pipeline finish" with "is the result
scientifically accepted". Split the two concepts so a "terminal" run is
clearly separated from a "scientifically viable/succeeded" run; failure
classification and acceptance no longer mask a deadline-censored or
never-selected-paths run as a generic terminal failure.

### D10.6 — Tests first (RED) then GREEN
All fixes (D10.2–D10.5) are driven by regression tests written first,
demonstrated RED against the pre-fix baseline, then GREEN after the fix.

### D10.7 — Freeze, docs, push, export, stop
Frozen/consistent docs, pushed commits, verified `project-YYYY-MM-DD-HHMM.zip`
export outside the project dir, and the Mandatory Stop Report.

---

## 5. Status

- **D10.1** COMPLETE — truth-only closure committed + pushed (no production
  changes).
- **D10.2–D10.6** COMPLETE — tests-first RED/GREEN; full suite re-run.
- **D10.7** COMPLETE — D10 candidate artifact `v0.9.22-d10-candidate` built +
  provenance-verified FROZEN (source `0b0e2a8…`, archive
  `d468ee6341f9a8c652554a814d32e2ff599d0b44359f21f7e7c657eb83c1669c`,
  0 mismatches); docs/constants aligned; freeze commits pushed and parity
  verified; exact-artifact dry-run 48/48 verified; project export produced
  (see `reports/pilot_notebook_trust_freeze.json`).

Full acceptance suite: **2572 passed / 33 skipped / 0 failed** (full run
2026-08-31 re-executed after power-loss resume: includes the carried-baseline
2538 + new D10 release-tag-alignment tests).

---

## 6. Truthful release status

- The stable annotated tag `v0.9.22-pilot-exec-ready` **still exists** and
  still peels to `478261ff...` — it is **NOT deleted, moved, or re-forced**. It
  is however **retired as a launch candidate**: the only permitted real Pilot
  launch from that exact artifact produced a 100%-failure outcome, so the next
  real Pilot launch (corrected, D10.2–D10.5 applied) must be a **new**,
  freshly finalized artifact with its own tag decision after a successful real
  pilot-canary.
- `exp-20260830-134232` is **REJECTED** and must never be resumed or counted.
- Scientific version remains **v0.9.22** (never v0.9.23).
