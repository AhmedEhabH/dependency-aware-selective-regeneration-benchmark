# Impact Declaration — WP-1b MAIN_297 + variance 15×3 + scoring

**Date:** 2026-09-22
**Branches:** `wp1b/main297-harness-2026-09-22` (zero-API) → `main`;
`wp1b/main-297-2026-09-22` (paid run, records, results)
**Tier:** T2 (new scientific run of a frozen evaluation) + T1 (harness only)
**Status:** Declared BEFORE the first paid call. Authorization: the §0 decision
block of the mission contract (copied verbatim into `DECISIONS.md`).

## 1. Purpose

Run the frozen repository-agent arm (protocol v3) on the frozen MAIN_297
manifest, run the preregistered variance substudy (15 tasks × 3 fresh
replicates), freeze and tag all predictions, then score SIP vs RM-CSS vs Agent
with the frozen decision rules v2, and compute the preregistered exploratory
analyses X1–X11. This is the first accuracy comparison of RM-CSS against a
repository agent under one protocol.

## 2. Scientific knobs — unchanged

Model/provider/route, temperature 0, `MAX_AGENT_CALLS` 8, completion cap 1024,
prompts, tools and arguments, observation window 2000, `MAX_READ_CHARS` 12000,
search order and 50-result cap, read budget 30, editable paths, JSON schemas,
rejection rule, SIP/RM-CSS predictions, NI margin 0.05 (+0.03/0.10 sensitivity),
decision rules v2, manifests, ceilings ($21.50 main, $3.50 variance). The
one-amendment rule stays closed.

## 3. What changes (harness, analysis, documentation)

- New harness and analysis code (no frozen file edited): see
  `docs/WP1B_MAIN297_EXECUTION_ADDENDUM_2026-09-22.md` section 2.
- New preregistrations frozen BEFORE any MAIN_297 output:
  `research/wp1b/wp1b_exploratory_prereg_addendum_v2.json` (X6–X11) and
  `research/wp1b/wp1b_agent_budget_sensitivity_prereg.json` (design only; its
  execution needs a separate decision D6).
- `scripts/render_live_status.py`: the "Authorized / not authorized" table is now
  read from `docs/LIVE_STATUS.json` (key `authorization`); it was hard-coded and
  had gone stale (it still said "Calibration-3b AUTHORIZED").
- Documentation: README (stale §3/§5/§6 rows, lessons 1a–1d, FAQ §12), AGENTS.md
  (historical release trail archived; standing rules for TODO progress, long
  commands, harness vs scaffold), `docs/MISSION_TEMPLATE.md` (§4 rules, §4b,
  AC-12..AC-14), `docs/WP1B_CALIBRATION_3C_RECORD_CORRECTION_2026-09-22.md`.

## 4. Data discipline

- Prediction side: the label-access audit hook blocks every label-bearing file,
  including `research/transparency/saleor_candidate_metadata.json` (it holds the
  786 sealed RESERVE outcomes) and `research/saleor-reserve-300-rmcss/*`.
- Labels are loaded only by `scripts/wp1b_score_main.py` /
  `scripts/wp1b_score_variance.py`, only after the freeze tag is verified on
  origin, and only from the opened RESERVE-300 proxies. The scoring-side guard
  keeps the 786 sealed outcomes unreachable.

## 5. Risks and controls

| Risk | Control |
|---|---|
| crash loses paid work | per-item fsync commit; `--resume`; ledger keeps partial spend |
| provider outage (and outage bias: outages turning into agent EMPTYs) | 3 transport retries (10/60/180 s); item restart ×2; session halt (exit 4) without recording the item; EMPTY + infra flag only after the same item failed in 3 sessions; resume |
| two runners on one directory | `run.lock` (exit 7) |
| untagged code spending money | `--require-tag`: tag on origin (same object) and working tree equal to the tag for all frozen paths |
| credits exhausted mid-run | pre-run credits gate (≥ $25 / ≥ $3.50); 401/402/403 halt (exit 3), never an EMPTY |
| accounting drift | attempt-aware ledger reconciliation (AC-14, Review Card M6) |
| outcome-dependent stop | halting is instrument-level only (H1–H7); agent behaviour never halts |
| label leakage | audit-hook guards; AC-10 tag gate; scorer drift check vs authoritative RESERVE-300 values |
| budget overrun | pre-item worst-case guard + per-request guard; ceilings unchanged |
| wrong RM-CSS probabilities in X3/X6 | deployment artifact config SHA check + exact 0.20-threshold reproduction of every frozen set |

## 6. Expected spend

Budget-v2 worst case for MAIN_297 is $12.43 (×1.5 = $18.64 ≤ $21.50). Using the
Calibration-3c cost ratios (0.331–0.645 of worst case) the expected MAIN_297
spend is about $4.1–$8.0; variance 15×3 about $0.7–$1.3.
