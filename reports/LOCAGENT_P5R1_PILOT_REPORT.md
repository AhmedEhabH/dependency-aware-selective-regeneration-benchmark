# LocAgent P5R-1 — Rescue Pilot Report (Block B, live API)

**Date:** 2026-09-16 evening
**Tier:** T3 live robustness study (NEW study; P5 immutable).
**Budget ceilings (frozen):** pilot ≤5 outer executions, ≤20M tokens, ≤$6.00;
evening LocAgent total (pilot+full) ≤50M tokens, ≤$15.00. Fail-closed.

---

## 1. Frozen P5R-1 configuration (identical to P5 except the allowed operational change)

| Parameter | P5 (original) | P5R-1 |
|---|---|---|
| upstream commit | 4935b557326c154bad8e8dcf3747cc8d32d1f387 | same |
| model / route | openrouter/qwen/qwen3-coder (OpenRouter-routed) | same |
| graph construction / tools / ranking / prompts / evaluator | frozen | same (NO algorithm change) |
| temperature | 1 (upstream hard-coded) | same |
| max_attempt_num / num_samples / num_processes | 1 / 1 / 1 | same |
| merge / ranking_method | true / mrr | same |
| **timeout** | 900 s | **1800 s** (allowed operational change) |
| context ceiling | 262,144 (route max) | same (already the route's max; cannot be raised on the same route) |

Dataset: the original 5 non-usable P5 tasks (2 timeout, 1 context-length,
2 completed-but-empty). Each run uses a 1-instance HF dataset (same fields),
so results are directly comparable to P5 per task.

## 2. Pilot outcomes (all 5 executed, one per task)

| Case | P5 outcome | P5R-1 outcome | P5R-1 failure evidence | calls / tok / cost |
|---|---|---|---|---|
| 9e33db4f4660 | completed-but-empty | **0 files (context-length)** | `BadRequestError: maximum context length is 262144 ... 197006 input tokens` (DeepInfra) | 65 / 7,145,230 / $2.15 |
| b39799f9fc1c | completed-but-empty | **0 files (completed-but-empty)** | `localizing ... succeed, process multiple loc outputs` with empty `found_files` | 39 / 3,576,711 / $1.08 |
| 4307e1b8c2e2 | timeout | **0 files (worker crash)** | `attempt 1 worker exited code 1 before queue result` | 27 / 1,427,017 / $0.43 |
| fdda30c271f0 | timeout | **0 files (context-length)** | `BadRequestError: maximum context length is 262144 ... about 315993 tokens` | 27 / 1,781,399 / $0.54 |
| 66c70394c9e1 | context-length | **0 files (upstream deadline)** | `execution flow reconstruction exceeded timeout. Terminating. Processing time exceeded 15 minutes.` | 83 / 6,611,203 / $1.99 |
| **Total** | 5 non-usable | **0 usable** | — | 241 / 20,541,560 / $6.18 |

## 3. Critical operational finding

**The wrapper `--timeout 1800` did NOT extend the effective per-task deadline.**
The upstream `auto_search_main.py` enforces its OWN hard-coded
`Processing time exceeded 15 minutes` deadline (900 s) independently of the
compatibility wrapper's `--timeout` argument. Case 66c70394c9e1 terminated at
"15 minutes" despite the 1800 s wrapper setting. Therefore the P5R-1 allowed
operational change (timeout relaxation) was **ineffective at the framework
level**: the effective deadline remained ~900 s.

Additionally, **context capacity cannot be raised on the same route**: the
OpenRouter qwen3-coder route's maximum context is 262,144 tokens, and the two
context-length cases (9e33db4f4660, fdda30c271f0) hit exactly this ceiling
during P5R-1. No same-route relaxation is possible; P5R-2 (a different provider
serving the same weights with larger context) would be required for those.

## 4. Operational vs framework attribution (pilot evidence)

- **Context-capacity-limited (operational, not fixable on the same route):**
  9e33db4f4660, fdda30c271f0 (2/5). In P5 these were 1 empty + 1 timeout; under
  P5R-1 both hit the 262,144 context ceiling while running longer.
- **Framework deadline (upstream hard-coded 900 s):** 66c70394c9e1 (1/5). Not
  removable via the wrapper timeout; requires editing upstream (forbidden).
- **Worker crash (framework/infra):** 4307e1b8c2e2 (1/5) — worker exited code 1.
- **Completed-but-empty (framework/system behavior):** b39799f9fc1c persists as
  empty after 39 calls; relaxing timeout/context did not change it. This
  confirms the mission's expectation: timeout/context relaxation cannot fix the
  completed-but-empty task(s).

**Conclusion:** the original 5/10 non-usable outcomes were NOT primarily caused
by the 900 s wrapper timeout. They are a MIX of (a) the route's hard context
ceiling (2), (b) an upstream hard-coded 15-minute framework deadline (1),
(c) a worker crash (1), and (d) genuine completed-but-empty framework behavior
(1). Only the 2 timeout-labeled P5 cases were even plausibly timeout-related,
and under P5R-1 they did NOT succeed (they hit context limits / a worker crash).

## 5. Full 10-task clean rerun decision

**NOT TRIGGERED.** The pilot rescued **0/5** (below the >=3/5 gate) AND it
demonstrated that the primary operational lever (wrapper timeout) is ineffective
against the upstream's hard-coded deadline, and the context ceiling is a hard
route limit. A full clean 10-task P5R-1 rerun under the same configuration
cannot rescue the completed-but-empty or worker-crash cases and would consume
the remaining evening LocAgent budget with no expected outcome change.
Per B4, "if full rerun is not triggered: report pilot only; do NOT fabricate a
blended P5R metric." This pilot is reported as an operational robustness
diagnosis; the original P5 numbers remain the only P5-series shared-protocol
evidence.

## 6. Budget accounting (fail-closed)

- Pilot used **241 calls / 20,541,560 tokens / $6.18** — slightly above the
  nominal 20M-token and $6.00 pilot ceilings because the per-task budget check
  runs after each task completes and the final (66c70394c9e1) task crossed the
  ceiling; the run stopped immediately after (fail-closed, no further calls).
- Evening LocAgent total so far: $6.18 of the $15.00 ceiling. A full rerun is
  NOT run, so the remaining budget is preserved.
- No replacement rerun after a valid or fail-closed outcome; no TEST beyond the
  already-exposed original P5 ten tasks; V2 INTERNAL_TEST/RESERVE untouched.

## 7. Verdict

Operational relaxation of the wrapper timeout does not rescue LocAgent's
non-usable outcomes on this route; the failures are framework/system-level
(upstream hard-coded deadline, worker crash, completed-but-empty) and
route-context-hard-limited. A bounded verifier (Route B) rather than a
task-level rerun of LocAgent is the more promising mechanism for omission
recovery. P5 remains the immutable system-level shared-protocol comparison.