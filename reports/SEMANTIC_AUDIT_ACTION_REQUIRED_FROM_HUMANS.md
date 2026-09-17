# Semantic-Audit Action Required From Humans

**Date:** 2026-09-18
**Status:** **AWAITING_HUMAN_RATINGS** (scientific blocker — no fabrication)
**Model (authoring agent):** openrouter/deepseek/deepseek-v4-flash-0731

This report verifies the ready machine-prepared package and states exactly what
a human must do. It does NOT fabricate human labels. No coding work was spent
rebuilding already-ready forms.

---

## 1. Package verified (2026-09-18, re-run of the frozen finalize script)

`python scripts/semantic_audit_finalize.py` →
**PACKET_INTEGRITY PASS** + **SYNTHETIC_DRYRUN PASS**.

## 2. Packet count

- **25 blinded evidence packets** (`research/semantic_audit/djangocms-rc-*/`),
  DEVELOPMENT-only, each with `diff.patch` + `evidence_packet.json`
  (+ `intent.json` / `candidate_universe.json` / `dependency_graph.json` /
  `observed_change_set_proxy.json` as required).
- Blinded ordering: seed `20260917`, SHA `a48c52e2…` (recomputed = matches),
  25 ordered case ids.

## 3. Rater instructions

- `research/semantic_audit/rater_instructions_v2.md` — one-page, 4-category
  definitions (`1_required`, `2_related_optional`, `3_incidental_tangled`,
  `4_not_determinable`) + rules.
- `research/semantic_audit/reviewer_instructions.md` — 3-question protocol
  notes.

## 4. Blind / randomization status

- The forms are BLINDED (blinded ordering, no semantic labels revealed;
  rater A and B receive the same order but must not share judgments).
- Rater B must NOT peek at Rater A's filled form.

## 5. Exact save files (filled)

| Role | Blank form (read) | Filled form (save) |
|---|---|---|
| Rater A | `research/semantic_audit/rater_form_A.csv` | `rater_form_A_filled.csv` (same dir) |
| Rater B | `research/semantic_audit/rater_form_B.csv` | `rater_form_B_filled.csv` (same dir) |
| Adjudicator | `research/semantic_audit/adjudicator_form.csv` | `adjudicator_form_filled.csv` (same dir) |

## 6. Adjudication workflow

1. Rater A fills `rater_form_A_filled.csv` (150 rows).
2. Rater B fills `rater_form_B_filled.csv` independently.
3. Agreement: `python scripts/semantic_audit_kappa.py research/semantic_audit/rater_form_A_filled.csv research/semantic_audit/rater_form_B_filled.csv`
   → writes `research/semantic_audit/kappa_result.json`.
4. Adjudicator resolves disagreements in `adjudicator_form_filled.csv`
   (rater_a/rater_b/adjudicated columns).
5. Re-run kappa on the consensus set if needed.

## 7. Cohen's kappa / sensitivity workflow

- Cohen's kappa + raw agreement + sensitivity (related-as-positive/negative)
  computed by `scripts/semantic_audit_kappa.py`.
- Pre-registered acceptance bar: kappa ≥ 0.6 (or documented lower with
  adjudication); conclusion stable whether `2_related_optional` counts positive
  or negative.
- Synthetic dry-run pipeline PROVEN (`MOCK_NOT_REAL_*` artifacts, clearly
  marked NOT_REAL).

## 8. Exact human ask (minimum)

1. Run the kappa command above after both raters finish (or delegate to a
   human operator).
2. Record the verdict in `DECISIONS.md` + living review (append-only).

## 9. Scientific blocker

**AWAITING_HUMAN_RATINGS** — the semantic-proxy audit (how far the observed
change-set proxy is from semantic impact gold) cannot advance without human
judgments. All machine-preparable work is complete and verified. This is a
HUMAN-work blocker, not a code blocker; do not spend coding time on it.

## 10. Forbidden (unchanged)

- Do NOT tune the ranker using the audit.
- Do NOT open djangoCMS/Saleor INTERNAL_TEST or RESERVE.
- AI/machine notes are never semantic gold.