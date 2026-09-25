# OpenCode Execution & Validation Protocol v2

**Version:** 2.0 · **Status:** ACTIVE (supersedes execution-guide phase framing for scientific-work governance)
**Root files:** `docs/OPENCODE_EXECUTION_GUIDE.md` (v1.0.0), `docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md` (phase lifecycle). This v2 protocol aligns project governance on top of them.

---

## 1. CURRENT PHASE (authoritative)

```
CURRENT PHASE: Repository change localization / impact selection
```

The active scientific phase evaluates **which files an impact-selection method
would mark for change** (the predicted write/selected set) against the observed
change-set proxy, within the frozen candidate universe at the parent revision.
Selection happens BEFORE downstream regeneration.

## 2. Governance hierarchy (permanent)

1. `00_CURRENT_RESEARCH_STATE.md` — **scientific source of truth**: frozen
   evidence, datasets/splits, exposed test sets, tags/SHAs, supported claims,
   current research direction.
2. `PROGRESS.md` — **execution source of truth**: what is being executed now,
   last completed task, immediate next step, blockers.
3. `DECISIONS.md` — **append-only** record of implementation/research decisions.

No competing current-state handoff is created. Historical handoffs
(`SYSTEM_STATE.md`, `TODO.md`, `docs/PROJECT_HANDOFF.md`) remain as historical
records.

## 3. Evaluation dimensions for the current phase

PRIMARY:
1. **Impact Correctness** — Precision, Recall, F1, FNR (micro and
   task-level/macro where meaningful).
2. **Efficiency** — wall-clock runtime; index/build time separated from query
   time; computational cost; retrieval/query cost; memory if trivial to
   measure; LLM calls/tokens/cost ONLY when an LLM is actually used
   (zero for non-LLM baselines).

CONDITIONAL:
3. **Architecture / protocol compliance** (only when the method defines an
   architecture/protocol contract).

DEFERRED until downstream code regeneration:
4. **Functional Correctness**.
5. **Preservation / regression correctness**.

Rule: Do NOT force non-applicable dimensions into localization-only
experiments.

## 4. Task classification

- **T0** — documentation / reporting / governance.
- **T1** — infrastructure/engineering change with no new scientific evaluation.
- **T2** — new scientific run reusing an existing evaluation strategy.
- **T3** — new evaluation strategy / baseline family (requires all six
  pre-benchmark gates + independent audit, leakage tests, and deterministic
  reproducibility).

Protocol A of the post-ICCI block (cheap-nonllm-baselines-v1) is classified
**T3**.

## 5. Validation gates (T3)

1. Dataset Validation
2. Prompt/Input Validation (for non-LLM: visible-intent/query construction)
3. Pipeline Smoke Test
4. Dry Run
5. Integration Test
6. Metric Verification (synthetic examples with manually known TP/FP/FN/P/R/F1/FNR)

Plus: independent audit; leakage regression tests; historical-parent-state
indexing tests; deterministic-seed tests.

## 6. Data discipline

- TRAIN and VALIDATION are **development evidence** only (not confirmatory,
  not final, not statistically generalizable).
- Use VALIDATION to select/confirm the frozen candidate method; freeze
  implementation, K/config, metric code, and candidate-universe rules BEFORE
  any new confirmatory dataset is evaluated.
- The HELD_OUT_TEST ten are PERMANENTLY EXPOSED (P1 + P5 ran them). Never use
  them for tuning/threshold/K/feature selection or error-driven revision.

## 7. Cost discipline

This phase is ZERO-API for non-LLM baselines. Any future LLM use requires its
own frozen budget before cell 1. No new scientific model/API call without
explicit authorization.

## 8. Relationship to prior protocol docs

- Execution mechanics/branching from `docs/OPENCODE_EXECUTION_GUIDE.md`.
- Phase lifecycle/one-pass discipline from `docs/ONE_PASS_PHASE_EXECUTION_PROTOCOL.md`.
- Scientific protocol from `docs/FINAL_RESEARCH_PROTOCOL.md` (frozen v1.0) and
  its companion docs. This v2 doc adds the current-phase naming and the
  governance hierarchy only; it does not amend the frozen scientific protocol.

## 9. Progress response format (normal vs closure)

### 9.1 Normal progress responses

Normal incremental progress responses may remain **one line** (e.g., "step X of
Y complete: <one-line status>"). The one-line rule is the default for
non-boundary progress.

### 9.2 Detailed closure report exception (T2/T3 MANDATORY STOP or scientific milestone closure)

**This detailed closure report is NOT prohibited by the normal one-line progress
rule.** For a **T2/T3 MANDATORY STOP** or a **scientific milestone closure**, the
final report MUST be detailed and MUST contain ALL of the following sections:

1. **Executive verdict** — one-paragraph outcome (PASS / FAIL / PARTIAL / closed
   with correction), not a bare number.
2. **Scientific question** — the exact question the milestone answers.
3. **Dataset/split and forbidden data** — which split(s) were used (development
   vs confirmatory label on each), which data was forbidden and stayed unused.
4. **Validation-gate table** — every applicable gate with PASS/FAIL and the
   evidence location.
5. **Main result table** — the headline numbers, with denominators and the
   metric definition (TP/FP/FN/P/R/F1/FNR).
6. **Development vs confirmatory label** — explicit statement that the evidence
   is development (TRAIN/VALIDATION) or confirmatory; never blurred.
7. **Fair-comparison warning** — when comparing methods across different
   splits/protocols, an explicit warning that cross-split head-to-head ranking
   is prohibited or only directional context.
8. **Interpretation** — what the numbers mean, not merely re-printing them.
9. **What the result does NOT mean** — explicit negative-space: over-strong
   claims that the result does NOT support.
10. **Competitor/baseline implication** — what the result implies for the LLM
    planner line / alternative methods, stated within the fair-comparison
    boundary.
11. **Threats/caveats** — every threat, caveat, and shortcut (e.g., frozen-corpus
    path mentions, small n, single repository).
12. **Tests/audit** — test counts, audit verdict, gate JSON locations.
13. **Documentation changed** — per-file list of docs synchronized.
14. **Git branch/commit/main status** — branch, HEAD, main, origin/main equality.
15. **Merge status** — merged or not, merge commit.
16. **Tag** — tag name and its exact meaning (e.g., DEV evidence only), or
    explicit "no tag" statement.
17. **Export ZIP + SHA256** — the light export name, path, size, SHA-256, and the
    `PROJECT_EXPORT_READY` block.
18. **Where we are now** — exact position in the research pipeline.
19. **ONE next action** — a single recommended next step (not started).

This exception exists so that milestone closures and mandatory stops leave a
durable, auditable record without weakening the one-line rule for normal
progress.

---

## 11. OpenCode Language Policy — Mandatory

All OpenCode-generated content MUST be written in English only.

This includes:

- chat/status responses;
- STOP reports;
- code comments;
- documentation;
- Markdown reports;
- governance records;
- commit messages;
- test descriptions;
- generated prompts and handoff artifacts.

Do NOT write Arabic in repository files or OpenCode status reports.

Historical content does NOT need retrospective translation.

Arabic communication with Ahmed is handled outside OpenCode.

Violation of this rule is a documentation/process defect and must be
corrected before task closure.

---

## 12. Mandatory FULL + TRUE LIGHT Export at Every STOP / Closure

Every one of the following:

- T2 completion;
- T3 completion;
- mandatory STOP;
- blocker STOP;
- handoff;
- scientific closure;

is INCOMPLETE until BOTH exports exist and are verified.

### 12.A FULL AUDIT EXPORT

Filename:

`project-YYYY-MM-DD-HHmm.zip`

Use the established FULL export script/rule.

The final report MUST contain:

```
PROJECT_EXPORT_READY
PROJECT_EXPORT_NAME=
PROJECT_EXPORT_PATH=
PROJECT_EXPORT_SIZE_BYTES=
PROJECT_EXPORT_SHA256=
```

Where applicable verify:

`.git/HEAD`

and all currently available required project-export members.

KNOWN EXCEPTION:

`dist/pilot-kaggle-upload.zip`
and
`dist/pilot-kaggle-upload.zip.sha256`

are currently archived externally and may not exist locally.

If the FULL export script returns non-zero ONLY because these two
documented archived members are absent, but:

- the FULL ZIP was actually created;
- `.git/HEAD` is present;
- the ZIP opens successfully;
- all other expected checks pass;

record:

`KNOWN_ARCHIVED_EXPORT_MEMBER_MISSING`

and do NOT fabricate/recreate the archived pilot files.

Any other export validation failure is a blocker.

### 12.B TRUE LIGHT EXPORT

Filename:

`project-LIGHT-YYYY-MM-DD-HHmm.zip`

Target size:

<= 50 MB whenever scientifically possible.

Use the established TRUE LIGHT export implementation.

The final report MUST contain:

```
LIGHT_EXPORT_READY
LIGHT_EXPORT_NAME=
LIGHT_EXPORT_PATH=
LIGHT_EXPORT_SIZE_BYTES=
LIGHT_EXPORT_SHA256=
WITHIN_50MB=
```

The TRUE LIGHT artifact may exclude documented reproducible/heavy state,
including:

- `.git/`;
- caches;
- virtual environments;
- external repository clones;
- large reproducible embeddings;
- nested ZIPs;
- temporary artifacts;
- other explicitly documented reproducible files.

It MUST retain enough material for another AI/researcher to understand and
continue the work, including as applicable:

- source code;
- tests;
- governance;
- current-state documentation;
- compact scientific evidence;
- experiment definitions;
- reports necessary to interpret the current state.

If either FULL or TRUE LIGHT export is missing:

DO NOT report the work package COMPLETE.

Report:

`EXPORT_CLOSURE_INCOMPLETE`

Finish the exports first.

Ahmed must never need to remind OpenCode to produce the two exports.

---

## 13. Todo Synchronization — Mandatory

The visible Todo list is a **live execution-state mirror**, not a
retrospective checklist. Stale Todo state is an execution-protocol defect and
must be corrected before starting another phase.

Rules:

1. **Update before each phase** — mark the incoming item active (`[•]`)
   BEFORE beginning work.
2. **Update after every durable chunk/checkpoint** — keep `[•]` but update
   the progress counter in the item text (e.g. `Node discovery — 41/47`).
   Update at least once per completed chunk for long-running batches.
3. **Update immediately after validation** — only after the durable output
   AND its validation gate both exist, flip `[•]` -> `[✓]`.
4. **Status must derive from persisted state** — use the filesystem/artifacts
   (JSON/JSONL, progress files, manifests, completed task IDs) as
   authoritative; never infer progress only from chat prose.
5. **Status symbols** — `[ ]` not started / `[•]` actively executing or
   partially complete / `[✓]` durably complete and validated / `[!]` blocked
   or STOP condition (include the concise blocker in the item).
6. **Before beginning the next Todo item**, synchronize the entire list once.
7. Do NOT update Todo after every individual shell command; that is noise.
   Use meaningful durable checkpoints (task/chunk completion, artifact
   creation, validation completion, phase transition, STOP/blocker).