# Runtime remediation decision matrix

Evaluation only; no option executed. Evidence R2–R6 is complete. Costs below are planning estimates, not measured timings. Every changed canon requires separate owner authorization. Full D7 is currently NO.

## 1 — Keep PyXB 1.2.5 and use a historically justified runtime

| Dimension | Assessment |
|---|---|
| Scientific validity | Python 3.12 is already historically justified; lowering it contradicts this commit. Keeping 3.12 alone does not repair source loss. |
| Frozen-protocol impact | A downgrade changes the frozen runtime/profile and needs a new amendment. |
| Population impact | Two exposed tasks initially; a broad runtime change would affect more and lacks support. |
| Reproducibility impact | Requires new image/source identities; older Python does not recreate the 2024 commit. |
| Expected engineering cost | Low to propose, high to rebuild/qualify; estimate 1–3 engineering days, not measured. |
| Changes task eligibility | No intended eligibility change. |
| Changes historical dependency semantics | Downgrade changes execution semantics; generic PyXB 1.2.5 still differs from vendor source. |
| Recalibration of all 12 | Yes for any amended canon; all 12. |
| Full D7 start/restart from zero | Yes, new canon from zero; current calibration cannot authorize launch. |
| Risks | May hide this error while breaking dependencies explicitly requiring 3.12. |

## 2 — Keep 3.12 and introduce an explicit compatibility backport

| Dimension | Assessment |
|---|---|
| Scientific validity | Conditional; an arbitrary MutableSequence patch fixes one symptom but does not prove historical source equivalence. Prefer exact historical vendor restoration. |
| Frozen-protocol impact | New owner-approved additive amendment; previous find_spec exception does not cover this change. |
| Population impact | At least the two exposed units; artifact sharing and all source identities must be enumerated. |
| Reproducibility impact | Freeze exact source/diff/build/wheel hashes and state historical differences. |
| Expected engineering cost | Moderate; estimate 1–3 engineering days plus separately authorized qualification. |
| Changes task eligibility | No intended eligibility change. |
| Changes historical dependency semantics | Yes for an arbitrary patch; exact historical source restoration can restore intended dependency semantics, subject to validation. |
| Recalibration of all 12 | Yes, all 12 under the new canon. |
| Full D7 start/restart from zero | Yes, zero-start new canon. |
| Risks | Patch whack-a-mole, unreviewed authorizenet differences, mislabeled same-version artifacts. |

## 3 — Substitute PyXB-X under a frozen compatibility amendment

| Dimension | Assessment |
|---|---|
| Scientific validity | Not established; same import name and compatible content.py do not establish whole-package equivalence. |
| Frozen-protocol impact | Changes distribution/version and dependency metadata resolution; explicit amendment required. |
| Population impact | At least two units if narrowly scoped; replacing every PyXB pin would affect up to 84 units. |
| Reproducibility impact | Hash exact replacement and metadata changes; record changed package file sets. |
| Expected engineering cost | Moderate/high; estimate 2–5 engineering days plus qualification; not measured. |
| Changes task eligibility | No intended eligibility change. |
| Changes historical dependency semantics | Yes: PyXB-X identity differs; authorizenet demands PyXB==1.2.5. |
| Recalibration of all 12 | Yes, all 12. |
| Full D7 start/restart from zero | Yes, zero-start new canon. |
| Risks | Overlapping imports, pip-check conflicts, unrelated behavior changes and outcome-driven substitution. |

## 4 — Mark tasks environment-ineligible under a predeclared rule

| Dimension | Assessment |
|---|---|
| Scientific validity | Not defensible ad hoc. Reviewed frozen disposition says no unambiguous covering rule. A new prospective population-wide amendment must disclose prior observation. |
| Frozen-protocol impact | Eligibility/population rule change, not an engineering shortcut. |
| Population impact | At least both affected tasks; reapply rule to entire frozen 219-task/144-unit population. |
| Reproducibility impact | Preserve original population and record all exclusions and denominator changes. |
| Expected engineering cost | Low coding cost but substantial protocol review; owner review duration unknown. |
| Changes task eligibility | YES. |
| Changes historical dependency semantics | Retained task dependencies unchanged, but scientific population and conclusions change. |
| Recalibration of all 12 | Yes; any replacement calibration plan itself needs explicit prospective approval. |
| Full D7 start/restart from zero | Yes for newly defined population; do not carry old acceptance as new qualification. |
| Risks | Post-hoc cherry-picking and selection bias. |

## 5 — Reconstruct per-task/per-era Python runtime selection

| Dimension | Assessment |
|---|---|
| Scientific validity | General audit is useful, but this audit already confirms all declared minor-version assignments; does not solve source loss. |
| Frozen-protocol impact | Any actual change requires frozen profile/canon amendment; read-only review does not. |
| Population impact | All 144 units/219 commits need consistent rule application. |
| Reproducibility impact | Pin runtime declarations, role rules, images and patch versions. |
| Expected engineering cost | High; estimate 3–10 engineering days if implemented, not measured. |
| Changes task eligibility | Potentially, if additional historical runtimes unavailable; cannot silently exclude. |
| Changes historical dependency semantics | Can change runtime behavior; does not restore vendor-source identity by itself. |
| Recalibration of all 12 | Yes if canon changes, all 12. |
| Full D7 start/restart from zero | Yes for changed canon. |
| Risks | Unnecessary reconstruction, new confounds, mistaking historical patch/OS normalization for the proven cause. |

## Recommended additional option 6 — restore historical source identity

Keep Python 3.12. Ask the owner to authorize a separate additive reconstruction mission that consumes exact commit-local `vendored/pyxb` and `vendored/authorizenet`, preserves directory-source identities through the closure/canon, and freezes resulting provenance. Review the shared closure/driver impact without editing R3 in place. Both affected tasks must be covered under the same rule. Require source-tree identity checks, distinct same-version artifact provenance, fresh qualification of all 12, and Full D7 from zero only after valid calibration and explicit launch authorization.

This restores the intended historical dependency inputs rather than choosing a new implementation because it passes. It still changes the frozen canon and therefore cannot be done in this audit. PyXB-X remains a comparison artifact, not an approved replacement. Do not downgrade Python, exclude Unit 12, weaken smoke, or treat 11/12 as a pass.
