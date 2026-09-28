# WP-2 E2E Smoke ENG v1 — ERRATUM (2026-09-28)

> **ERRATUM 2026-09-28: Smoke v1 token corrected.**
> Original token `E2E_SMOKE_FLOOR_EFFECT` is superseded (not deleted) by
> `E2E_SMOKE_INSTRUMENT_INVALID`, derived from the mechanical defect audit
> (DF1-DF5) documented here. See `research/wp2/e2e_smoke_eng_v1/erratum/`
> for the machine-verifiable evidence.

## 1. Original claim

Smoke v1 (Mission-11, E2E Smoke ENG v1) reported final token
`E2E_SMOKE_FLOOR_EFFECT` with gates SG1-SG3 PASS, SG4 FAIL (GOLD_HARD
RESOLVED 0/14 not met). The instrument was declared valid on the basis of the
zero-API controls (G-FORMAT 39/39, G-POS 3/3, G-NEG 3/3, G-LEAK 0,
G-BUDGET ok) and the first-call format-adherence result was interpreted as a
model behaviour floor effect ("repair could not fix the format").

## 2. Discovery

A read-only mechanical audit (`scripts/wp2_e2e_v1_defect_audit.py`) of the
frozen v1 evidence at `research/wp2/e2e_smoke_eng_v1/` (56 episodes,
committed at HEAD) verified five instrument defects. None of the v1 result
files or tags were edited; the audit is append-only evidence under
`research/wp2/e2e_smoke_eng_v1/erratum/`.

## 3. Defect findings (DF1-DF5)

| ID | Defect | Reproduced | Evidence |
|---|---|---|---|
| DF1 | Replay test fixture written into real paid evidence | **YES** | `episodes/saleor-rc-39b4138e8550/GOLD_HARD/episode.json` has 2 calls with `route = "replay"`, `editable_set = ["saleor/x/models.py"]` (not a Saleor path), prompt_tokens 25, cost $0. The real paid GOLD episode for task `39b4` is absent from the evidence. |
| DF2 | Blind repair (no original prompt / file contents / previous output) | **YES** | `generate.py:103-104` calls `client.generate(system, build_repair_prompt(response, errors))`. `build_repair_prompt` (`prompt.py:73-75`) formats only `REPAIR_TEMPLATE` with the error list. All 46 real repair calls have 284-369 prompt tokens vs initial up to 43,267. 0/46 real repairs succeeded. |
| DF3 | Identical-prompt reuse not effective; per-episode cache; initial overwritten by repair | **YES** | Three task pairs (823b, e03ee, e25cf) share an identical `prompt_sha256` between GOLD_HARD and AGENT_HARD but were called separately. `e03ee` produced different outputs: AGENT APPLIED+RESOLVED, GOLD INVALID. `cache.put(prompt_sha, response2)` (generate.py:106) overwrites the initial response. |
| DF4 | Truncation check bypassed (finish_reason hard-coded "stop") | **YES** | `generate.py:100/111` passes literal `"stop"` to `validate_output`; the real provider finish_reason is ignored. `dc6ac9d252df/RMCSS_HARD` returned 8,192 completion tokens with `finish_reason = "length"` and was not flagged as TRUNCATED. |
| DF5 | Raw responses not persisted in the repository | **YES** | Only `response_sha256` is committed in `episode.json` call entries; no raw response text files exist. Local disk search found **no** genuine raw responses (4 empty-string hash matches are false positives from 0-byte log files). |

## 4. Gate replay (mechanical, from the frozen rules)

Frozen rules (`smoke_freeze.json` `smoke_gates`):
- SG1 = instrument validity: B11 controls PASS, 0 leakage, 0 out-of-scope,
  evidence 100%.
- SG2 = completion >= 95% terminal, anomalies <= 5%.
- SG3 = spend agent <= 1.00, smoke <= 4.50, total <= 5.50.
- SG4 = GOLD_HARD RESOLVED >= 1/14.

Mechanical application (no interpretation, `scripts/wp2_e2e_v1_gate_replay.py`):

| Gate | Original | Corrected | Basis |
|---|---|---|---|
| SG1 | PASS | **FAIL** | DF1: replay fixture in the paid evidence root breaks "evidence 100%". DF2: repair request deviates from the preregistered instrument contract. |
| SG2 | PASS | PASS | unchanged |
| SG3 | PASS | PASS | unchanged (spend $0.628 total) |
| SG4 | FAIL | FAIL | unchanged (GOLD RESOLVED 0/14) |

## 5. Corrected token

```
ORIGINAL = E2E_SMOKE_FLOOR_EFFECT
CORRECTED = E2E_SMOKE_INSTRUMENT_INVALID
```

Rule applied mechanically: SG1 or SG2 FAIL -> INSTRUMENT_INVALID.

## 6. Still-valid descriptive observations

The following remain valid and are labelled DESCRIPTIVE:
- First-call (initial) format adherence: valid outputs on 8/55 real initial
  calls (the 56th, 39b4 GOLD, is the replay fixture, not a real run).
- Dominant initial error classes: PARSE_ERROR 42 (prose preamble such as
  "Looking at the developer change description…", or a leading markdown fence)
  + NO_BLOCKS 5.
- Generation prompt mean tokens: GOLD 13.9K, RMCSS 13.2K, AGENT 7.4K,
  PLACEBO 4.5K.
- Evaluator behaviour (G-POS / G-NEG) is unaffected by these defects.

## 7. Withdrawn interpretations

- **"The repair could not fix the format"** is withdrawn: the repair was blind
  (DF2) and carried neither the original task prompt nor the file contents nor
  the previous assistant output.
- **"AGENT 1/14 is attributable to scope"** is withdrawn: the AGENT e03ee
  episode used a prompt identical to GOLD (DF3) and succeeded while GOLD
  failed; the observed success cannot be attributed to scope and is consistent
  with provider-side nondeterminism.
- Any reading of **0 repair successes as evidence of model inability** is
  withdrawn (see DF2).

## 8. Effect on conclusions

- Smoke v1 does **not** establish a pipeline-valid instrument token. The
  corrected token is `E2E_SMOKE_INSTRUMENT_INVALID`.
- The v1 result JSONs, episode files, and v1 tags are unchanged
  (immutability verified; see `erratum/v1_immutability_before.json`).
- No comparative RM-CSS vs Agent claim was ever supported by Smoke v1; that
  remains the case and is unchanged by this erratum.

## 9. Explicit statement on RM-CSS selection-stage evidence

**No change to RM-CSS selection-stage evidence.** The defects DF1-DF5 are
instrument-pipeline defects of the E2E Smoke generator/evaluator harness. They
do not touch the RM-CSS selection-stage evidence (WP-1b), the Agent selection
runs, the scopes, the oracle semantics, or the evaluator ground truth. RM-CSS
selection-stage evidence is unaffected by this erratum.

## 10. Evidence files

- `research/wp2/e2e_smoke_eng_v1/erratum/instrument_defects_v1.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/df1_replay_contamination.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/df2_repair_context.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/df3_identical_request_outcomes.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/df4_truncation.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/df5_raw_response_availability.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/v1_gate_replay.json`
- `research/wp2/e2e_smoke_eng_v1/erratum/v1_immutability_before.json`

## 11. Mandatory wording

Smoke v2 is engineering-split pipeline validation only. No comparative claim
between RM-CSS and Agent is made or supported.