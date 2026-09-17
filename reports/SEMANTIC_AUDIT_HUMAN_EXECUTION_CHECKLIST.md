# Semantic-Proxy Human Audit — One-Page Execution Checklist

**Date:** 2026-09-17
**Scope:** the 25 DEVELOPMENT-only evidence packets + two-rater blind audit.
**Rules:** do NOT fabricate judgments; do NOT open INTERNAL_TEST/RESERVE.

## Materials (research/semantic_audit/)
- [ ] `rater_form_A.csv` (blank, 150 rows) — give to Rater A
- [ ] `rater_form_B.csv` (blank, 150 rows) — give to Rater B
- [ ] `adjudicator_form.csv` (blank, 150 rows) — for the adjudicator
- [ ] `rater_instructions_v2.md` + `reviewer_instructions.md`
- [ ] 25 packet dirs (`djangocms-rc-*`): intent + candidate universe + graph + proxy
- [ ] `blinded_ordering.json` (order seed 20260917, SHA `a48c52e2…`)

## Run the audit
1. [ ] Rater A fills `rater_form_A.csv` (one category per row:
     1_required / 2_related_optional / 3_incidental_tangled / 4_not_determinable).
2. [ ] Rater B fills `rater_form_B.csv` (same items, independent, no peeking).
3. [ ] Compute agreement:
     `python scripts/semantic_audit_kappa.py research/semantic_audit/rater_form_A_filled.csv research/semantic_audit/rater_form_B_filled.csv`
     → writes `research/semantic_audit/kappa_result.json`
     (raw agreement, Cohen's kappa, sensitivity as related-as-positive/negative).
4. [ ] Adjudicator resolves disagreements in `adjudicator_form.csv`.
5. [ ] Re-run kappa after adjudication if a consensus set is needed.

## Acceptance bar (pre-registered)
- [ ] kappa ≥ 0.6 (or documented lower with adjudication) on the 4-category coding
- [ ] sensitivity: conclusion stable whether 2_related_optional counts positive or negative
- [ ] no packet marked missing in `scripts/semantic_audit_finalize.py` (PACKET_INTEGRITY PASS)
- [ ] synthetic dry-run re-verified: `python scripts/semantic_audit_finalize.py`
      → PACKET_INTEGRITY PASS + SYNTHETIC_DRYRUN PASS (MOCK NOT_REAL)

## After the audit (do NOT do now)
- [ ] Do NOT use the audit to tune the ranker; it is a proxy-validity check.
- [ ] Do NOT open djangoCMS/Saleor INTERNAL_TEST or RESERVE.
- [ ] Record verdict + any drop in DECISIONS + living review; update kappa JSON.