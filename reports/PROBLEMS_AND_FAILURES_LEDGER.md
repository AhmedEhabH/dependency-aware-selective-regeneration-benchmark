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