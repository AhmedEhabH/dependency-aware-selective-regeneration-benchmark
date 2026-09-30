# WP2 M14R V1 — design freeze (DEV_TRAIN_ENG only)

**Status:** `DESIGN_FROZEN_BEFORE_ANY_M14R_OUTPUT`

**Machine artifact:** `research/wp2/m14r_v1/m14r_design_freeze_v1.json` (sha `4d3e73fac6f4095622f448ff85cc4e53aa7cf493ded14c698447b477943bc68f`). If this summary and the JSON disagree, the JSON wins.

## Question

Can a small, deployment-realistic change to the generator or its interface raise the GOLD_HARD floor? The change must not weaken the hard editable scope, and it must not use hidden tests or any target information.

## Population

- **Candidates:** the 14 ENG tasks that have a frozen ENG v3 behavioural F2P set.
- **Membership:** only tasks that pass zero-API readiness are included:
  - the empty-diff negative control fails F2P and keeps robust preservation;
  - the scoped-gold positive control is robust-RESOLVED.
- **Minimum size:** 10 members.
- **Protected tasks:** none. The guard checks that no Pilot-A, Pilot-B or reserve task is in the population.

## Arms and replicates

- **GOLD_HARD:** r1, r2, r3.
- **PLACEBO_HARD:** r1 only.
- Each arm and replicate is run under both contexts, C0 and C2.

## Factors and variants

**Context factor**

- **C0** is the frozen prompt.
- **C2** is C0 plus `IMPORT_OUTLINE_V1`: read-only outlines of the modules the editable files import, one hop only.
  - The outlines contain verbatim parent lines only (signatures and class-level attribute lines).
  - The caps are 6k characters per module and 40k characters in total.
  - Test files, migrations and the editable files themselves are excluded.

**Static factor**

`STATIC_UNDEFINED_V1` works as follows:

- It runs pyflakes on an APPLIED candidate.
- Only new UndefinedName, UndefinedLocal or UndefinedExport findings trigger it (new relative to the parent file).
- A trigger gives exactly one extra repair. The repair message contains only those findings.
- If the repair output is invalid, the APPLIED base is kept.

**Variants**

| Variant | Context | Static | Generation |
|---|---|---|---|
| G0 | C0 | off | independent |
| G1 | C0 | on | paired with G0 (same base generation) |
| G2 | C2 | off | independent |
| G3 | C2 | on | paired with G2 (same base generation) |

## Endpoints

- **Primary (development): RESOLVED_ROBUST.**
  - Every F2P node must pass in all 3 reps.
  - A preservation node counts as broken only if it is non-passing in 2 or more of the 3 reps.
- **Always co-reported: RESOLVED_STRICT**, the frozen Smoke v2.2 D50–D52 rule.

## Decision rule

The rule is frozen and unit-tested in `wp2_m14r_core.decide`.

**Eligibility.** A variant is eligible only if all three conditions hold:
- its robust count is at least G0 + 3;
- its invalid count is at most G0 + 3;
- the number of tasks where it is better than G0 is at least the number where it is worse.

**Winner.** The eligible variant with the highest robust count wins. Ties are broken by lower mean tokens per episode, then by simplicity (G0 < G1 < G2 < G3). If no variant is eligible, the winner is G0.

**Floor.** The floor is met when all three conditions hold:
- the winner's robust count is at least ceil(0.20 × 3n);
- the number of tasks with at least one robust resolve is at least ceil(n/3);
- every PLACEBO robust count is at most 1.

**Outcome tokens**

| Token | What happens next |
|---|---|
| `M14R_FLOOR_MET` | Human decision, then a separately frozen M15 amendment |
| `M14R_FLOOR_NOT_MET` | Human decision on reshaping WP2 |
| `M14R_PLACEBO_LEAK_REVIEW` | Human decision |
| `M14R_INSTRUMENT_FIX` | Brain review |

No token starts anything automatically.

## Budget and time

| Item | Value |
|---|---|
| Authorization cap | ≤ $3.00 |
| Expected spend | About $1.1 |
| Worst-episode reserve | $0.12 |
| Readiness | About 2.5–3 h |
| Generation | About 1.5 h |
| Evaluation | About 8–10 h |

Every stage is resumable.
