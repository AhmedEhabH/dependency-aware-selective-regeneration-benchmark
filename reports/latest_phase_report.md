# Qwen 14B BNB-NF4 Canary Preparation — Latest Phase Report

## Executive decision

The Qwen 14B BNB-NF4 canary preparation closure is **complete** on branch
`fix/kaggle-smoke-v2-model-output-closure` (Commit A `0ece665` + Commit B
`0a596b8`, pushed, local = remote, tree clean). The frozen model-blind
`qwen:1:int8` identity has been replaced with a deterministic model-aware
identity, an explicit `bnb-nf4` profile exists, prequantized-checkpoint
conflicts fail fast before model load, and the notebook is pinned to the
official unquantized 14B base checkpoint with a fail-closed canary preflight
gate. **Next authorized action = Kaggle engineering preflight only.**

## Why this closure existed

- The generic auto-resume cell downloaded `exp-20260804-133016` because both
  the 7B and an attempted 14B run were labeled `qwen:1:int8` — identity
  contamination, not a 14B result.
- An attempted 14B GPTQ checkpoint run (`exp-20260804-195126`) produced
  0 records / 0 calls / 0 tokens: the preflight failed before the model probe
  because a `GPTQConfig` checkpoint cannot be loaded by the `BitsAndBytesConfig`
  loader. Preserved as engineering evidence; GPTQ support is deferred.

## What changed

- **Identity:** `qwen:<checkpoint-basename>:<quantization>:cfg-<12hex>`, computed
  before auto-resume from `config.json` fields (model_type, hidden_size,
  num_hidden_layers, num_attention_heads) + requested mode + checkpoint
  quantization method. 7B bnb-int8 / 14B bnb-int8 / 14B bnb-nf4 always differ;
  historical `qwen:1:int8` records preserved.
- **Profiles:** canonical modes `bnb-int8` / `bnb-nf4` / `fp16` via
  `--qwen-quantization` (default `bnb-int8`, unknown values exit 2). NF4 =
  `load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=
  torch.float16, bnb_4bit_use_double_quant=True` (Tesla T4).
- **Fail-fast:** a prequantized non-bitsandbytes checkpoint raises
  `PREQUANTIZED_CHECKPOINT_INCOMPATIBLE` before tokenizer/model load; no
  automatic fallback.
- **Notebook:** pinned to the unquantized `14b-instruct/1` base checkpoint
  (never `14b-instruct-gptq-int4`), `QWEN_QUANTIZATION = "bnb-nf4"`,
  `RUN_GENERIC_ONE_RUN = False`, isolated
  `/kaggle/working/runs/qwen14b_bnb_nf4_selective_canary`, a fail-closed
  canary preflight assertion, `--strategy selective --max-runs 1
  --new-experiment`, no `--auto-resume-hf`. Notebook identity
  `SOURCE_COMMIT = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c` /
  `DEPLOYED_BUILD_ID = 0ece665`.

## Gate totals

```text
Dataset Validation      PASS   27 scenario files / 27 unique IDs / 0 duplicates / 3 smoke IDs; zero dataset changes in closure
Prompt Validation       PASS   380 passed / 10 skipped / 0 failed
Pipeline Smoke Test     PASS   189 passed / 12 skipped / 0 failed
Scripted 9-record Dry   PASS   9/9 succeeded / 0 failed / exit 0 (scientific-smoke-v2, fresh dir)
Complete Integration    PASS   1,877 passed / 32 skipped / 0 failed (full tests suite, 631.20 s)
Metric Verification     PASS   169 passed / 0 failed
Ruff                    PASS   0 new findings (21 pre-existing)
strict mypy             PASS   0 new findings (5 pre-existing, identical rule set to self-contained HEAD baseline)
compileall              PASS   8 changed Python files compile
Notebook compilation    PASS   canonical 8/8 + bundled 8/8 code cells compile
builder/manifests       PASS   147 files / 962,188 bytes; rerun content-identical; manifests verified; no cache files
```

## Commit hashes and remote equality

```text
commit A = 0ece665ef25e1b0ca3aa14f5f25977cadbd06d0c  fix(model): add model-aware Qwen BNB quantization profiles
commit B = 0a596b83bd971aacad52806461c237a72784eaef  chore(deploy): pin Qwen 14B NF4 selective-canary bundle
local HEAD = remote HEAD = 0a596b8 (pushed; working tree clean)
```

Record: `selective_updates/records/QWEN14B-BNB-NF4-CANARY-READINESS.md`.
Sentinel: `QWEN14B_NF4_CANARY_READINESS_AUDIT_REQUIRED`.

---

# Selective Calibration Canary Result — Latest Phase Report

## Executive decision

The dedicated selective calibration canary was executed on Kaggle under the
pinned bundle and its result has been ingested documentation- and ledger-only
on branch `fix/kaggle-smoke-v2-model-output-closure` (pushed, local = remote,
tree clean). **Result: the harness safety controls worked; Qwen code quality
did not improve; no successful implementation exists.**

- **Canary `exp-20260804-133523`** (`todo-smoke-001 / selective`, source/build
  `50ec2c1`): **failed / `model_output`**, 4 model calls / 5,804 tokens /
  257.596 seconds, 3 selected / 2 preserved / **0 written**. Initial generation
  = 3 calls / 3,372 tokens; repair = 1 call / 2,432 tokens. HF state =
  `recovery_uploaded`; checkpoint = 1 completed / 2 pending.
- **Qwen output defects:** `todo/models.py` used `max_length=5` for a `MEDIUM`
  value of length 6; `todo/serializers.py` and `todo/views.py` each duplicated
  `Priority(models.TextChoices)`. The first repair of `models.py` was
  byte-identical to the initial response → `repair_no_progress` stopped the
  round; the atomic application wrote zero files (workspace stayed at baseline).
- **Harness vs model:** versus the previous selective run on the same scenario,
  the canary used 41.6% fewer tokens, 33.3% fewer calls, and was 22.4% faster,
  but the initial generation tokens (3,372) and the three output SHA-256 hashes
  were **identical**. The improvement came entirely from the harness controls
  (per-call deadline, no-progress detection, atomic writes, fail-closed
  continuation gate); the model produced the same bad code.
- **Incidental monolithic run `exp-20260804-133016`** (todo-smoke-001 /
  monolithic, 6 calls / 7,927 tokens / 300.165 s / `scientific_budget_exhausted`
  / 0 written): the generic one-run cell ran before the canary and is retained as
  diagnostic calibration evidence only — NOT the authorized canary and NOT an
  accepted comparison.
- **Continuous cell:** executed after the canary and correctly stopped
  fail-closed with `CALIBRATION_REVIEW_REQUIRED`; no additional scientific model
  calls, no remaining runs launched.
- **Current scientific truth:** accepted current dedicated canary records = 1,
  successful = 0; the full current 9-record experiment is **not run**; no
  merge/tag/Pilot/Kaggle authorized; **no stable release claimed**.

Record: `selective_updates/records/SELECTIVE-CANARY-RESULTS-2026-08-04.md`.
Next action: independent result audit (`SELECTIVE_CANARY_RESULT_AUDIT_REQUIRED`),
then a deliberate decision between repeating the dedicated selective canary and
proceeding to the full 9-record run.

SELECTIVE_CANARY_RESULTS_DOCUMENTED

---

# Final Selective Canary Readiness Closure — Latest Phase Report

## Executive decision

The final selective canary readiness closure is **complete** on branch
`fix/kaggle-smoke-v2-model-output-closure` (HEAD `356722b`, pushed, local =
remote, tree clean). The independent GPT-5.6 Thinking audit at `f727b3e`
**REJECTED canary readiness** even though the full suite was green, based on
three independently reproduced blockers. All three are now closed, pinned, and
gated:

1. **Per-call cooperative deadline (Blocker 1).** The workflow deadline was
   checked only before the whole regeneration attempt; `SharedRegenerationExecutor`
   looped through every selected artifact without consulting the deadline.
   Direct reproduction: 1s timeout, 3 selected artifacts, budget advanced after
   call 1 → **3 model calls and false success**. Now every in-flight call
   returning beyond the deadline consumes/records its tokens, makes no next
   call, writes none of the staged attempt, and returns the failed scientific
   terminal `scientific_budget_exhausted` with truthful elapsed time and budget.
   The same guard applies to every internal Iterative Agent call, not only once
   before `analyze_impact()`. Direct adversarial proofs:
   `TestRunner.test_generation_deadline_stops_after_first_model_call` (1 call,
   failed terminal, count 0, 15 tokens),
   `TestRepairDeadline.test_repair_deadline_stops_after_first_repair_call`
   (2 calls, failed terminal, count 0, `repair_model_calls == 1`, repair tokens
   retained), `TestIterativeAgentDeadline.test_agent_selection_deadline_stops_after_first_call`
   (1 call, `model_call_budget_exhausted`, 50 tokens preserved).
2. **Atomic metric truth (Blocker 2).** Atomic validation prevented writes when
   any artifact was rejected, but `regenerated_artifact_count` still counted a
   staged artifact: direct reproduction = **0 writes but count 1**. Now every
   staged `generated` status becomes `aborted` or `rejected`,
   `regenerated_artifact_count = 0`, preserved response hashes/evidence remain
   available, and an all-valid attempt still commits every artifact exactly
   once. Metric/evidence truth, not a scientific formula change.
   `test_r4_token_and_metrics.py` assertions updated to the truthful staged
   statuses (`["aborted", "aborted", "rejected"]` / `["aborted", "rejected"]`);
   `MagicMock` exec_ret gains `model_call_budget_exhausted=False` in
   `test_r3d_wiring.py`.
3. **Dedicated selective canary cell (Blocker 3).** The generic one-run cell
   selects `todo-smoke-001 / monolithic` (execution-plan order is scenario
   first, then strategies), not `selective`. A dedicated, separately named
   Selective Calibration Canary cell (`selective-calibration-canary-cell`) was
   added: `--strategy selective --max-runs 1 --new-experiment --backend
   kaggle-qwen --profile scientific-smoke-v2 --max-attempts 3
   --max-completion-tokens-per-call 1024 --max-total-workflow-tokens 0 --timeout
   300 --hf-sync`, isolated output `runs/selective_calibration_canary`, **NO**
   `--auto-resume-hf`, `AUTHORIZE_CONTINUOUS_AFTER_CALIBRATION_REVIEW = False`.
   `_verify_selective_canary()` asserts exactly one current-source RunRecord
   `todo-smoke-001 / selective`, model identity `qwen:1:int8`, model calls > 0,
   terminal scientific success/failure outcome, HF `recovery_uploaded`,
   checkpoint `total_planned = 3 / completed = 1 / pending = 2`.

Commits: `50ec2c1` (Commit A: `fix(smoke): enforce per-call deadline and atomic
metric truth`), `28ecc5a` (Commit B: `chore(deploy): pin selective-canary-ready
Smoke V2 bundle`, `SOURCE_COMMIT = 50ec2c1ca43c230aed4538be32ca7dab2ccc22e5`,
`DEPLOYED_BUILD_ID = 50ec2c1`, bundle rebuilt 147 files / 948,250 bytes),
`356722b` (test alignment: `test(smoke): align affected unit tests with atomic
metric truth`).

Final gate: full suite = **1,856 passed / 32 skipped / 0 failed** (571.57s);
grouped per-category = 629 passed / 1 skipped (530.96s); scripted dry run
`--profile scientific-smoke-v2` into a fresh dir = **9/9 exit 0** (the default
`runs` dir held a stale checkpoint causing `ReportRebuildError: Unexpected Run
IDs`, not a code defect); mypy `--strict src` Success (77 files); ruff 0 new
findings (175 pre-existing repo-wide; 19 pre-existing E501 in
`test_r4_token_and_metrics.py`); compileall clean; notebook code cells compile
(8/8 bundle, incl. the canary cell); bundle content-identical (tree hash
`3b8d5b0ebf5e3ab8`); manifests verified (code 90 / data 56 / notebook 1); `git
diff --check` clean; working tree clean.

Calibration truth: `exp-20260803-002741` remains **preserved, 0/9 success, not
accepted scientific evidence** (9 terminal records / 0 succeeded / 8 failed / 1
timed_out / 81 model calls / 118,211 tokens). No Kaggle rerun has occurred. No
tag; no merge; Pilot not authorized; **no stable release claimed**. Next action:
after the independent re-audit, run the **dedicated selective calibration canary
cell only** (not the generic one-run cell, not the continuous cell, not a full
relaunch, not a fine-tune, not a tag/merge).

FINAL_SELECTIVE_CANARY_READINESS_AUDIT_REQUIRED

---

# Post-Smoke Calibration Closure — Latest Phase Report

## Executive decision

The post-smoke calibration closure is **complete and green** on branch
`fix/kaggle-smoke-v2-model-output-closure` (HEAD `231b0a5`, pushed, local =
remote, tree clean). The real calibration run `exp-20260803-002741` (9 terminal
records: 0 succeeded / 8 failed / 1 timed_out; 81 model calls; 118,211 total
tokens) exposed four proven control defects that were closed in three commits:
`27c1693` (runtime + tests: per-attempt atomic regeneration, repair no-progress
detection, fail-closed calibration continuation gate, cooperative deadline
semantics), `56772fe` (deployment pin: `SOURCE_COMMIT =
27c1693e22b1a68be0b299fb146d9ff1e500908b` / `DEPLOYED_BUILD_ID = 27c1693`,
bundle rebuilt, 147 files / 934,495 bytes), and `231b0a5` (test-fixture
reconciliation).

The first full gate after `56772fe` exposed **nine stale constant-output
integration fixtures** that accidentally activated the new no-progress
early-stop and lowered observed counts below the max-attempt expectations.
These failures were **not validly proven to be pre-existing**: the starting HEAD
`ec9ba0b` did not contain the `repair_no_progress` early-stop, and a detached
worktree using the main editable installation can import the current branch
instead of the detached worktree source — a cross-worktree comparison is valid
only with an isolated environment or an explicit worktree-local `PYTHONPATH`.
The reconciliation (`231b0a5`) changed tests only: `_FixedTokenBackend` gained
an opt-in `vary_output=True` (three duration tests), `_SentinelBackend` returns
a unique valid Python string per indexed response while preserving the exact
`TokenUsage`, and the five bounded-repair fixtures return distinct valid Python
per call. Every expectation was preserved unchanged (max_attempts, call counts
3/6, `repair_attempts`, `repair_model_calls` 2/4, durations 1.5/2.1, tokens
41/59/90, JSONL/reporting identity); the dedicated identical-output no-progress
tests remain unchanged; a new side-by-side boundary test proves constant output
→ 2 calls + `repair_no_progress` vs distinct outputs → 3 calls / 2 repair
attempts. These failures are documented as caused by the stale fixtures, never
as "pre-existing" production defects, and no runtime, prompt, metric, scenario,
evaluator, or dataset was changed.

Final gate: full suite = **1,849 passed / 32 skipped / 0 failed**; mypy
`--strict src/benchmark` Success (77 source files); ruff 93 findings =
identical 93-finding baseline set (0 new, verified by line-set export); compileall
clean; bundle build content-identical (147 files / 934,495 bytes; builder rerun
leaves the tree unchanged); all notebook code cells compile (canonical 7/7 +
generated 7/7); manifests verified (code 90 / data 56 / notebook 1); `git diff
--check` clean; working tree clean.

Calibration truth: `exp-20260803-002741` is **calibration evidence, not an
accepted scientific comparison** — latest real calibration = **0/9** (selective
9 artifacts vs monolithic 15 / agent 8; agent was the only arm to reach the
scenario evaluator, on `todo-smoke-002`). No Kaggle rerun has occurred. No tag;
Pilot not authorized. Next action after this independent audit: **one selective
calibration canary only** (not a full relaunch, not a fine-tune, not a
tag/merge). Fine-tuning is deferred to a separate future project on held-out
benchmark scenarios.

POST_SMOKE_CALIBRATION_CLOSURE_AUDIT_REQUIRED

---

# Pre-Benchmark Final Source Repin — Latest Phase Report

## Executive decision

The pre-benchmark reproducibility-and-truth closure is **complete and green** on
branch `fix/kaggle-smoke-v2-model-output-closure` (HEAD `f8d00d7`, pushed, local
= remote, tree clean). The pre-benchmark test environment is fully declared in
`pyproject.toml [dev]` + `requirements-dev.txt` (commits `769d84e` + `e5d9430`;
runtime `[project.dependencies]` and `requirements-smoke-kaggle.lock` untouched),
the clean environment was deleted and recreated from declarations only (Python
3.11.9, `_workspace\cache\prebenchmark-py311`), and the complete clean gate was
repeated.

The previous `76a6b16` gate had **1 failure, not a green full suite**:
**1,833 passed / 32 skipped / 1 failed**. The sole failure was
`test_notebook_source_commit_matches_deployed_runtime_tree`, structural because
the mandated `pyproject.toml` declaration change broke byte-identity with the
pinned `aac9914` SOURCE_COMMIT (frozen artifacts were not modified to force
green and the truthful total was recorded). **Root cause:** dependency
declarations changing `pyproject.toml` after the `aac9914`/`311e084` deployment
pin. **No runtime, prompt, metric, scenario, evaluator, or data change was
needed.**

The exact independently reviewed **deployment-only correction** `f8d00d7`
(imported via bundle fast-forward, exactly one commit) re-pins the deployment to
the current source snapshot `e5d9430`: bundled `kaggle_upload/code/pyproject.toml`
is now byte-identical to canonical, and both notebooks re-pin
`SOURCE_COMMIT = e5d943065c6f4158c30a1cbbba39436ab2a7a898` /
`DEPLOYED_BUILD_ID = e5d9430` (deployment source snapshot = `e5d9430`;
deployment correction = `f8d00d7`). The complete clean suite is now **green:
1,834 passed / 32 skipped / 0 failed** (the identity test passes). Dataset
Validation 285 passed / 5 skipped (data unchanged); Prompt Validation 158
passed; Pipeline Smoke 220 passed / 12 skipped; Dry Run 9/9 succeeded (exit 0);
Integration PASS; Metric Verification 169 passed; mypy strict Success (77
files); ruff 93 = 93 baseline (0 new); compileall clean; all notebook code cells
compile; bundle build content-identical (147 files / 928,329 bytes); manifests
verified; no cache files in `kaggle_upload`; git diff --check clean; tree clean.
Historical `exp-20260801-210443` produced one failed model-output terminal
record under source `6f88823` — preserved, excluded from the current `e5d9430`
aggregation; current accepted real records = **0/9**; no scientific evidence
exists; no tag; no Pilot; no Kaggle launch. Next: the only action after this
independent audit is the **Kaggle engineering preflight** cell (not the
scientific One-Run cell), after updating the Kaggle code dataset + notebook to
the corrected `e5d9430` deployment.

This report is the current, latest-first post-R6 report. The R6 acceptance,
freeze, and publication detail belongs to
`docs/R6_FINAL_INDEPENDENT_REAUDIT_AND_FREEZE_REPORT.md` and
`selective_updates/records/R6-BUNDLE-PARITY-AND-PRE-KAGGLE-HANDOFF.md` and is
not repeated here. The prior R7C root-closure report is preserved as history
in `selective_updates/records/KAGGLE-SMOKE-V2-REAL-RUN-ROOT-CLOSURE.md`.

## Models used

```text
Requested model:  DeepSeek V4 Flash Free through OpenCode Zen
Actual model:     opencode/deepseek-v4-flash-free
Mode:             Build
Provider:         OpenCode Zen
```

## Branch and commits

```text
Branch             = fix/kaggle-smoke-v2-model-output-closure (from the deterministic-interpreter tail)
R6 accepted HEAD   = 949e9c2; R6 freeze commit 4b2dd27 (published milestone branch)
Runtime commit     = aac9914  fix(exec): bind Python scenario commands to active runtime
Deployment pin     = 311e084  chore(deploy): pin deterministic-interpreter Smoke V2 bundle
Declaration 1      = 769d84e  chore(test): declare complete pre-benchmark dependencies
Declaration 2      = e5d9430  chore(test): declare remaining pre-benchmark dependencies
Deployment correction = f8d00d7  chore(deploy): repin reproducible pre-benchmark source snapshot (HEAD)
Deployment source = e5d9430 (SOURCE_COMMIT=e5d943065c6f4158c30a1cbbba39436ab2a7a898, DEPLOYED_BUILD_ID=e5d9430)
Failed attempts    = exp-20260801-024041, exp-20260801-024624 (preserved; not deleted)
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted; not scientific evidence)
Historical experiment = exp-20260801-210443 (ONE failed model-output terminal record under 6f88823;
                          preserved; excluded from current e5d9430 aggregation)
Record             = selective_updates/records/KAGGLE-SMOKE-V2-MODEL-OUTPUT-CLOSURE.md
```

## The failed attempts (truth)

```text
exp-20260801-024041  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-024624  planned 9 / succeeded 0 / failed 9 / model calls 0 / tokens 0
exp-20260801-123125  failed at runtime root (FP16 OOM; deps drifted from lock)
```

The first two attempts failed at the first arm/scenario triplet during
workspace **isolation** before any LLM call; the later attempt reached the
model (81 calls, 47,694 tokens) but every record failed selection/validation;
the root-closure attempt failed before any model call at runtime root. None of
these outputs are scientific evidence. They remain visible on the results
dataset and must not be deleted.

## Fix evidence

```text
Pre-benchmark categories (declarations-only recreated environment)  all passed
  Dataset Validation           285 passed / 5 skipped (data unchanged)
  Prompt Validation            158 passed
  Pipeline Smoke               220 passed / 12 skipped
  Dry Run                      scientific-smoke-v2 9/9 succeeded, exit 0
  Integration                  PASS
  Metric Verification          169 passed
Full suite (previous 76a6b16 gate)  1,833 passed / 32 skipped / 1 failed (NOT green)
  sole failure = test_notebook_source_commit_matches_deployed_runtime_tree
                 (structural: mandated pyproject.toml declaration change breaks
                  byte-identity with pinned aac9914 SOURCE_COMMIT; root cause =
                  dependency declarations changing pyproject.toml after the
                  aac9914/311e084 deployment pin; no runtime/prompt/metric/scenario/
                  evaluator/data change needed; frozen artifacts not modified to force
                  green — reported truthfully)
Full suite (after deployment-only correction f8d00d7)  1,834 passed / 32 skipped / 0 failed (GREEN)
  identity test now passes (working-tree pyproject.toml byte-matches pinned
  e5d9430 SOURCE_COMMIT)
Mypy strict src/benchmark      Success: no issues found in 77 source files
Ruff                          93 findings = 76a6b16 baseline (re-exported and re-run;
                              93 = 93) — 0 new findings
Compileall                    clean (exit 0)
Notebook cells                all compile (canonical 7/7 + generated 7/7)
git diff --check              clean
Benchmark data                unchanged
```

## Bundle inventory

```text
code = 90 files; data = 56 files; notebooks = 1; total = 147 files / 928,329 bytes
Builder = scripts/build_upload_bundle.py only; build verified and content-identical
         (manifests code 90 / data 56 / notebook 1; no cache files in kaggle_upload)
```

## Exact gates

```text
git diff --check    clean
Ruff                93 = 93 vs 76a6b16 baseline (0 new)
Mypy strict         Success: no issues found in 77 source files
Compileall          clean
notebook cells      all compile (7/7 canonical + 7/7 generated)
full suite          1,834 passed / 32 skipped / 0 failed (green)
identity test       test_notebook_source_commit_matches_deployed_runtime_tree PASSES
                    (deployment re-pinned to SOURCE_COMMIT=e5d9430 by f8d00d7)
bundle build        content-identical (147 files / 928,329 bytes); manifests verified
```

## Current status

```text
R4 = accepted and frozen (f5ae826)
R5 = accepted and frozen (7761c48)
R6 = ACCEPTED AND FROZEN (949e9c2; freeze commit 4b2dd27; branch published)
Kaggle attempts = 2 (exp-20260801-024041, exp-20260801-024624) — failed pre-model, preserved
Latest real attempt = exp-20260801-123125 (FP16 → OOM; deps drifted) — not scientific evidence
Runtime fixes  = committed (de3163f) and pinned (fb60972) — core accepted by independent audit
R7A hardening  = complete (d50e89e + 4c73db6) — four audit findings closed
R7B Smoke Finish = complete (bff0a82 + 17207bf)
R7C root closure = complete (7a80e53 + f01b8f0) + correction imported (ffa179a + 6d6aa36)
                    + post-gate correction imported (6f88823 + 5797fc0, HEAD 5797fc0, pushed)
Full-gate truth = prior "1,451 full suite" was a SUBSET; true first full suite
                  23 failed / 1,759 passed / 32 skipped; after correction 1,790 passed / 32 skipped / 0 failed;
                  after post-gate correction 1,796 passed / 32 skipped / 0 failed
Deterministic interpreter closure = complete (aac9914 + 311e084) — bare interpreter tokens bound to active runtime
Pre-benchmark reproducibility closure = COMPLETE AND GREEN (769d84e + e5d9430 declarations;
                  deployment-only correction f8d00d7, HEAD f8d00d7, pushed) — previous 76a6b16 gate
                  1,833 passed / 32 skipped / 1 failed (structural notebook-pin identity test, truthful,
                  not forced green); f8d00d7 re-pins deployment to e5d9430; complete clean suite now
                  1,834 passed / 32 skipped / 0 failed; Dataset 285/5 (data unchanged), Prompt 158,
                  Pipeline Smoke 220/12, Dry Run 9/9, Integration PASS, Metric Verification 169;
                  mypy strict Success (77 files); ruff 93 = 93 baseline (0 new)
Historical experiment = exp-20260801-210443 produced ONE failed model-output terminal record under 6f88823 —
                  preserved, excluded from current e5d9430 aggregation
Current real records = 0/9
Local scripted Smoke = 9/9
Bundled CLI dry-run  = 9/9
Real Qwen Smoke      = 0/9
Scientific evidence  = NONE (no real-model success yet)
Tag                  = not created
Pilot                = not authorized
```

## Near goal

Independent audit complete and its exact deployment-only correction applied
(`f8d00d7`, pushed) → the only authorized Kaggle action is the engineering
preflight cell (not the scientific One-Run cell) → update the Kaggle code
dataset + notebook to the corrected `e5d9430` deployment → run the engineering
preflight → one real cell (require 1/9 succeeded) → remaining eight real Qwen
Scientific Smoke V2 records → independent result audit.

## Far goal

Independent real-result audit → stable `v2.0.0-scientific-smoke` tag → freeze
Pilot matrix → Pilot execution → research experiment → statistical analysis →
paper evidence package.

## Next action

**Only Kaggle engineering preflight** after this independent audit (HEAD
`f8d00d7`): update the Kaggle code dataset + notebook to the corrected
`e5d9430` deployment, then run the preflight cell only. Do not relaunch Kaggle,
tag, merge, or force-push beyond that documented preflight step.

PRE_BENCHMARK_FINAL_SOURCE_REPIN_AUDIT_REQUIRED
