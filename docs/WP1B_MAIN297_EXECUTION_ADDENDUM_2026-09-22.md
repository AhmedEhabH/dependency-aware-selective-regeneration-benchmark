# WP-1b MAIN_297 — Execution Addendum (operational, pre-run)

**Date:** 2026-09-22 · **Status:** FROZEN BEFORE THE FIRST PAID MAIN_297 CALL
**Scope:** harness and analysis plumbing only. **No scientific knob changes.**
The agent is protocol v3 exactly as in Calibration-3c
(`research/wp1b/wp1b_frozen_agent_protocol_v3.json`).

## 1. Why this addendum exists

The 3-task calibration runner (`scripts/wp1b_calibration_run.py`) is not safe
for a 297-task paid run. A zero-API code audit found five gaps:

| # | Gap in the calibration runner | Consequence at n = 297 | Fix (this addendum) |
|---|---|---|---|
| G-A | `selected_paths` is never persisted (the `analyze_impact` return value is discarded) | no agent predictions to score | every record stores the predicted set + its SHA-256 |
| G-B | records are written only at the end; `shutil.rmtree(out_dir)` at start | one crash loses everything; a "resume" deletes finished work | per-item fsync commit; the output directory is never deleted; `--resume` |
| G-C | backend built with the default `max_transient_retries=1`, immediate retry | violates the frozen rule (max **3** byte-identical transport retries); ~1,800 calls make a double failure likely | wrapper owns exactly 3 retries with 10/60/180 s backoff; inner backend `max_transient_retries=0` |
| G-D | an unhandled `ModelBackendError` crashes the run | not the frozen fail-closed semantics; and a naive "EMPTY on first failure" would turn a provider outage into agent EMPTYs that count against the agent (outage bias) | operational definition of "unrecoverable" (section 3, rule 8): EMPTY + `infra_failure` only after the item failed in 3 separate sessions; account/config and bad-request errors halt instead |
| G-E | Review-Card BLOCKING rules (any EMPTY, any 3-long rejection run, cost ratio > 1) | a single agent-behaviour event would stop a 297-task run and create an outcome-dependent stop | MAIN-mode card: only instrument-level anomalies block (section 4) |

Evidence: `scripts/wp1b_calibration_run.py` (lines "records.append", "shutil.rmtree",
`OpenRouterBackend(... timeout_seconds=120.0)`); `src/benchmark/llm/openrouter_backend.py`
(`max_transient_retries: int = 1`); `research/saleor-reserve-300-rmcss/sip_300_run_records.jsonl`
(SIP used up to 4 transport attempts = 3 retries).

## 2. New harness files (no frozen file is modified)

| File | Role |
|---|---|
| `src/benchmark/wp1b/resilient_backend.py` | frozen retry rule, error classification (transport / account-config / bad request), spend ledger with `attempt_id`, per-request USD guard, HTTP-attempt accounting |
| `src/benchmark/wp1b/main_runner.py` | resume-safe runner (lock file, sessions, item restarts), halting rules, predictions persisted, zero-API dry-run stub |
| `src/benchmark/wp1b/git_gate.py` | AC-4 / AC-10 gates: a tag passes only if origin points at the SAME object as the local tag; tagged-file and tagged-tree equality (LF-normalized) |
| `src/benchmark/wp1b/label_guard.py` | audit-hook guards: prediction side (no label file) / scoring side (786 sealed outcomes) |
| `src/benchmark/wp1b/freeze.py` | label-free prediction freeze + SHA-256 |
| `src/benchmark/wp1b/main_scoring.py` | decision rules v2 applied mechanically (P/S, Q5, 7 verdicts, cost verdict) |
| `src/benchmark/wp1b/variance_scoring.py` | preregistered variance metrics |
| `src/benchmark/wp1b/exploratory.py` | X1–X5 (prereg 2026-09-21) + X6–X11 (addendum v2) |
| `src/benchmark/wp1b/report_render.py`, `svg_plot.py` | deterministic Markdown / LaTeX / SVG outputs |
| `scripts/wp1b_main_run.py` | CLI: `dry_run` (zero API) · `main297` · `variance` (paid kinds require `--require-tag`) |
| `scripts/wp1b_freeze_predictions.py` | CLI: freeze |
| `scripts/wp1b_score_main.py` | CLI: AC-10-gated scoring (tag must be on origin) |
| `scripts/wp1b_score_variance.py` | CLI: variance scoring |
| `scripts/wp1b_exploratory.py` | CLI: X1–X11 after the primary result is tagged |
| `scripts/wp1b_main_review_card.py` | CLI: MAIN-mode Review Card (label-free); exit 1 on any BLOCKING item |
| `scripts/wp1b_dry_run_check.py`, `scripts/wp1b_openrouter_key_usage.py` | dry-run acceptance (D1–D5); billed-spend reconciliation and a pre-run credits gate |
| `tests/unit/test_wp1b_main_runner.py`, `test_wp1b_main_scoring.py`, `test_wp1b_exploratory_and_cards.py`, `test_wp1b_git_gate_and_cli_gates.py` | 90 zero-API tests |

## 3. Execution rules

1. **Knob check before call 1.** The runner compares the code constants with
   protocol v3 (`MAX_AGENT_CALLS=8`, observation window 2000, `MAX_READ_CHARS=12000`,
   `MAX_SEARCH_RESULTS=50`, read budget 30, list 200, file size 200 KB, cap 1024) and
   stops on any drift.
2. **Pricing/route check** (zero-token metadata API): DeepInfra/turbo present;
   $0.30 / $1.00 per 1M. Before a FRESH paid run: drift or missing route → exit 3
   (STOP); metadata unreachable → exit 4 (retry later). On RESUME: metadata
   unreachable → continue (recorded); route missing → exit 4 (resumable); list-price
   drift → recorded in `pricing_preflight_last_resume.json` and continue (the frozen
   list prices govern all accounting, so a mid-run price change cannot move a verdict).
   The fresh-run record `pricing_preflight.json` is never overwritten.
2a. **Tag gate (AC-4).** Paid kinds require `--require-tag <harness/prereg tag>`:
   the tag must point at the same object locally and on origin, and the working
   tree must equal the tag for `src/benchmark`, the launcher, the portability fix,
   protocol v3, the manifests, budget v2, decision rules v2 and both
   preregistrations (no untracked files there either). Otherwise exit 3, no call.
2b. **Credits gate.** `scripts/wp1b_openrouter_key_usage.py --require-remaining-usd`
   (25 before MAIN_297, 3.50 before variance): min(key limit remaining, account
   balance) must cover the ceiling; exit 2 → top up first.
3. **Manifest check.** MAIN_297 `task_ids_sha256 = 1678dbaa…ccbceb`; calibration IDs
   absent. Variance: selection SHA `2c4ac5b1…5f9`; 15 tasks ⊂ nested MAIN_50; 3 fresh
   replicates; the main execution is **not** replicate 1.
4. **Order.** Frozen manifest order, sequential, one work item at a time.
5. **Chunked execution.** `--max-items N` processes at most N pending items per
   invocation; the same command with `--resume` continues. `--resume` on an empty or
   missing directory starts fresh. A resume refuses any change of manifest, frozen
   code SHA-256, label, kind or protocol, and refuses a higher ceiling. A `run.lock`
   (PID + start time) prevents two runners on one directory: a second invocation
   exits 7 (`LOCKED`) without touching anything; a lock older than 6 h or held by a
   dead PID is taken over and recorded. Each invocation is a numbered session.
6. **Commit order per item:** sidecar lines → telemetry line → run record (commit
   marker), each flushed + fsync'ed. A torn line or orphan lines from an unfinished
   item are moved to `*.orphaned.jsonl` on resume, never silently dropped.
7. **Spend ledger:** one fsync'ed line per call (frozen list price) and per failed
   call, each tagged with `attempt_id` (`<item>@<session>#r<k>`). Spend of an
   abandoned attempt is kept. All USD guards use the ledger. AC-14 is attempt-aware:
   every kept record equals the ledger USD of its own `attempt_id` (±$0.000001), and
   ledger total = Σ kept record USD + Σ abandoned-attempt USD.
8. **Transport retries and the operational meaning of "unrecoverable"** (fixed
   before any MAIN_297 output; triggered only by transport status, never by content):
   - only HTTP 408/429/5xx, connection and timeout errors are TRANSPORT; the same
     byte-identical request is retried at most 3 times (10 s, 60 s, 180 s);
   - a call still failing after its 3 retries abandons the item attempt; the item
     restarts from scratch after 120 s, at most 2 times per session;
   - still failing → the session halts with `PROVIDER_OUTAGE_HALT` (exit 4) and the
     item is NOT recorded; the operator waits ≥ 10 min and resumes;
   - only when the same item has failed in 3 different sessions is the transport
     failure "unrecoverable": the frozen fail-closed rule applies (EMPTY,
     `empty_reason=infrastructure`, `infra_failure=true`);
   - HTTP 401/402/403/404 or "key not found" → `ACCOUNT_OR_CONFIG_HALT` (exit 3, fix
     key/credits/route, then resume); any other 4xx → `BAD_REQUEST_HALT` (exit 5,
     STOP and report). Neither ever produces an EMPTY. An unclassified provider
     error is treated like a transport failure at the item level (restart, then
     outage halt), never as an EMPTY.
   Rationale: without this, a provider outage would convert into agent EMPTYs that
   count against the agent in analysis P (outage bias). No content or schema retry,
   and no re-run of a completed item.
9. **Label isolation.** The prediction process installs an audit hook that raises on
   any open of a label-bearing file, including
   `research/transparency/saleor_candidate_metadata.json` (it holds the proxy paths of
   **all** Saleor tasks, including the **786 sealed RESERVE outcomes**) and anything
   under `research/saleor-reserve-300-rmcss/`.

## 4. Halting rules for a MAIN run (instrument level only)

| ID | Condition | Exit | Action |
|---|---|---|---|
| H1 | ledger + budget-v2 worst case of the next item > ceiling; or a per-request guard | 2 | budget abort (rule v2; nested MAIN_50 fallback only if the first 50 finished) |
| H3 | 3 consecutive RECORDED `infrastructure` EMPTY items (i.e. items already failed in 3 sessions) | 4 | infra halt; wait ≥ 10 min; resume |
| — | `PROVIDER_OUTAGE_HALT` (rule 8) | 4 | wait ≥ 10 min (sleep in its own tool call); resume; after 4 consecutive exit-4 invocations with no new completed item, STOP and report |
| — | `MATERIALIZATION_HALT` (parent snapshot could not be built) | 4 | resume once; repeats → STOP and report |
| — | `ACCOUNT_OR_CONFIG_HALT` (401/402/403/404, key missing) | 3 | STOP; Ahmed fixes key/credits; resume unchanged |
| — | `BAD_REQUEST_HALT` (other 4xx) | 5 | STOP, report |
| — | second runner on the same directory | 7 | do nothing; the first runner is still live |
| H4 | instrument-class tool errors in ≥ 3 of the last 20 items | 5 | STOP, report (no repair-and-continue) |
| H6 | 5 consecutive EMPTY items from truncation / parser_failure | 5 | STOP, report |
| H7 | 10 consecutive items in which tools were attempted and EVERY attempted tool call failed (items with no tool call do not count; a zero-hit search is a successful call) | 5 | STOP, report |
| — | unexpected exception | 6 | read `halt_report.json` `origin`: `FROZEN_AGENT_CODE` → STOP and report; `HARNESS_CODE` → fix only the new harness file, add a test, record it, resume |
| — | `STOP` file present (`--stop-file`) | 4 | operator stop; resumable |

**After any halt** the only permitted continuations are: (a) resume the SAME run
unchanged (after the stated wait, or after Ahmed's review for exit 5), or (b)
stop the study. A halt never leads to an agent change, a re-run of finished
items, or a retroactive exclusion.

**Zero-API dry run before call 1 (AC-12):** `--kind dry_run` over all 297 items
(stub backend, real materialization, universe and prompt construction), then
`scripts/wp1b_dry_run_check.py`: D1 297/297, no halt, no infra failure; D2 no
empty stub prediction; D3 call-1 prompt within 500 chars of the budget-v2 base
prompt (+ the ~70-char G12 counter line); D4 projected runtime; D5 projected
cost range (Σ budget-v2 worst case × Calibration-3c ratio range 0.331–0.645).

**Never halting (data, not instrument):** any single EMPTY (`round_cap`,
`parser_failure`, `truncation`, `infrastructure`), rejected repeats and 3-long
rejection runs, zero-read items, forced finals at call 8, observation truncation,
search-cap hits, a cost ratio > 1 on one item.

MAIN-mode Review Card (`scripts/wp1b_main_review_card.py`) BLOCKING = M1 halted or
incomplete · M2 instrument errors > 5% of items · M3 transport EMPTY > 5% of items ·
M4 knob/protocol drift · M5 `allow_ground_truth_universe` not False · M6 ledger/record
accounting mismatch (attempt-aware AC-14). The card exits 1 on any BLOCKING item.
Everything else is INFORMATIONAL. The calibration card (`scripts/run_review_card.py`) is unchanged
and still governs calibration runs.

## 5. Freeze, tag, score (AC-10)

1. MAIN_297 complete → `scripts/wp1b_freeze_predictions.py --kind main297` →
   commit the run directory → tag `wp1b-main297-predictions-frozen-2026-09-22` →
   push → verify with `git ls-remote --tags origin`.
2. Variance run (label-blind) → freeze → commit → tag
   `wp1b-variance-predictions-frozen-2026-09-22` → push → verify.
   If the variance run halts, scoring of MAIN_297 still proceeds; variance is
   reported as incomplete and resumed later.
3. `scripts/wp1b_score_main.py` refuses to load any label unless the freeze tag
   points at the **same object** locally and on origin **and** `git show
   <tag>:<freeze>` equals the working-tree freeze (LF-normalized). Origin
   unreachable → exit 4 (retry), never a bypass. `--skip-git-check` exists for unit
   tests only and is refused unless `WP1B_ALLOW_SKIP_GIT_CHECK=1`. Bootstrap draws
   are index-based, so the scorer fixes the task order: sorted task IDs (the wp1a
   convention; the MAIN_297 manifest is already sorted). It installs the scoring-side guard (786 sealed outcomes
   unreachable) and first re-scores RESERVE-300 SIP/RM-CSS; any deviation from
   F1 0.26474622770919065 / 0.35687263556116017 stops with `SCORER_DRIFT`.
4. Result committed and tagged `wp1b-main297-result-2026-09-22` before X1–X11;
   `scripts/wp1b_exploratory.py` checks that this tag is on origin and contains the
   exact `reports/wp1b_main297_result.json` it reads.

## 6. Cost accounting definitions (pre-result)

- **Agent:** tokens = prompt + completion over all calls; calls = logical model
  calls (HTTP attempts reported separately); USD = frozen list price.
- **RM-CSS View A (marginal):** tokens = SIP total tokens (per task) + query-embedding
  tokens (`query_est_tokens / query_count_unique`); **calls = 2 per task** (1 SIP coder
  call + 1 query-embedding request); USD = SIP `api_cost` + query-embedding USD
  (`query_cost_usd / query_count_unique`). Sensitivities (reported, not decisive):
  coder-calls-only (1), generative-tokens-only.
- **View B:** + embedding-corpus build ($0.025909) amortized over n; repository-memory
  build $0 API (local).
- **Provider-billed reconciliation (descriptive):** record the OpenRouter key usage
  before and after each paid run; report billed/list-price ratio (prompt caching may
  make the agent cheaper than list price; the preregistered verdict uses list price).

## 7. What does NOT change

Model/provider/route · temperature 0 · `MAX_AGENT_CALLS` 8 · cap 1024 · prompts ·
tools and arguments · observation window 2000 · `MAX_READ_CHARS` · search order and
cap · read budget 30 · editable paths · schemas · rejection rule · SIP/RM-CSS
predictions · NI margin and decision rules v2 · manifests · ceilings ($21.50 main,
$3.50 variance). The one-amendment rule (D5) stays closed.
