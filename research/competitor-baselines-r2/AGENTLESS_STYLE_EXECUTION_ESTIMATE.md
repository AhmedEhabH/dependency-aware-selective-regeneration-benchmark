# Agentless-Style Execution Estimate (MAIN_297) — R2

**Mission:** `M17_COMP_BASELINES_R2_FINAL_CHEAP_SAME_PROTOCOL` — Phase 3.
**Status:** ESTIMATE ONLY. **No LLM call, no paid execution, no 297-task Agentless inference.**
**Population:** frozen MAIN_297 (297 tasks).

---

## 1. Official sources inspected

| Item | Value |
|---|---|
| Official repository URL | `https://github.com/OpenAutoCoder/Agentless` |
| Exact commit SHA inspected | `5ce5888b9f149beaace393957a55ea8ee46c9f71` (HEAD at inspection; clone depth 1) |
| File-level localization stage | `agentless/fl/localize.py` — `get_repo_structure` → `filter_none_python` + `filter_out_test_files` → `LLMFL.localize(top_n, mock)` |
| Exact localization prompt source | `agentless/fl/FL.py`, class `LLMFL`, attribute `obtain_relevant_files_prompt` (file-level localization prompt; the file also contains the folder-irrelevance prompt) |
| Prompt source lines (verbatim) | FL.py — `obtain_relevant_files_prompt` template: "Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem. ### GitHub Problem Description ### {problem_statement} ### Repository Structure ### {structure} ### Please only provide the full path and return at most 5 files. The returned files should be separated by new lines ordered by most to least important and wrapped with ```" |
| Structure representation | `agentless/util/preprocess_data.py::show_project_structure()` over the structure dict built by `get_repo_structure/get_repo_structure.py::create_structure()`; rendered as directories (`dir/`) + `.py` file names only (non-Python files removed by `filter_none_python`, test keys removed by `filter_out_test_files`); no file contents in the file-level prompt |
| Context constant | `MAX_CONTEXT_LENGTH = 128000` (`agentless/fl/FL.py`) |
| Output / top-N rule | `agentless/fl/localize.py`: `pred_files = found_files[: args.top_n]` with `--top_n` default **3**; the prompt instructs the model to return **at most 5** files, newline-separated in code fences, ordered most→least important |
| Official model/config | Model is a **CLI parameter** (`--model`), not pinned in the inspected commit. Repo README (inspected) reports published runs with a GPT family model (v1.0, Jul 2024) and later **Claude 3.5 Sonnet** integration (40.7% / 50.8% on SWE-bench Lite / Verified, Dec 2024). Table/figure-level details `UNKNOWN`; no model identity is asserted beyond what the inspected README shows. |

## 2. The three protocol questions

1. **File-level localization stage:** yes — `agentless/fl/localize.py` + `LLMFL.obtain_relevant_files_prompt`.
2. **Repository-structure representation:** a tree of directories + `.py` file names only (python-only, tests filtered). No file contents at this stage (contents are used only in later related/edit-location stages through `get_skeleton` compression).
3. **Output / top-N rule:** model returns ≤ 5 files; the code slices to `top_n` (default 3); the selected file SET is the localization output (order matters only residual).

## 3. Input/output protocol vs SIP

| Aspect | Official Agentless file-level localization | SIP (frozen MAIN_297 sparse inference) |
|---|---|---|
| Input | GitHub problem description (issue/commit intent) + repository tree (dirs + `.py` names) | Developer change description (`intent_text`) + numbered candidate list (full frozen candidate universe) + first 200 dependency-graph edges + serialization policy |
| Repository representation | Compact tree of file names (tests/non-python filtered) | Full candidate-universe enumeration with frozen numeric ids + parent-only dependency graph |
| Number/staging of calls | 1 file-level call (then optional related/edit-location calls and repair in the full pipeline) | 1 call (same single-call scaffolding) |
| Prompt structure | Fixed natural-language template → backtick-wrapped file list | Structured JSON-schema instruction with deterministic id↔path mapping |
| Output | Newline list of up to 5 file paths (code-fenced) | JSON actions per candidate; REGENERATE set = predicted scope |
| Top-N / set semantics | `found_files[:top_n]`, default 3, hard cap 5 | Variable-size calibrated set (deterministic classifier head), no fixed cap |
| Model dependence | Any chat LLM (model is a CLI argument) | qwen/qwen3-coder @ deepinfra/turbo (frozen run identity) |
| Adaptation required | Localization-only run on MAIN_297 needs prompt scaffolding for our case bundles + output parsing + same evaluator; **not** the unchanged official SWE-bench pipeline | none (frozen) |

**Verdict:** SIP is *structurally similar* to Agentless file localization (one call, description in, file-set out, no agent loop) but the repository representation (full enumerated candidate set + graph vs compact tree) and the output semantics (calibrated set vs top-3-of-5) differ materially. They are **not near-identical**; a same-model run of the official-style prompt on MAIN_297 is a **`AGENTLESS_STYLE_ADAPTATION`**, never "Agentless".

## 4. Planned-run classification

- `EXACT_AGENTLESS`: No — the official code targets SWE-bench datasets (its own `get_repo_structure` clones SWE-bench repos and consumes `problem_statement`); running it on MAIN_297 bundles requires input scaffolding and our evaluator, i.e. an adaptation.
- **`AGENTLESS_STYLE_ADAPTATION`**: Yes — same family of protocol (description-only single-shot file localization with a repository structure), adapted to MAIN_297 inputs and scored with our file-level evaluator.

## 5. Prompt-size measurement (offline, deterministic)

Reproducer: `scripts/m17_comp_baselines_r2_agentless_estimate.py`; data: `research/competitor-baselines-r2/agentless_prompt_sizes_r2.json`.
Method: official prompt template + official structure representation rendered per MAIN_297 task at its frozen parent snapshot (files enumerated from the frozen upstream cache), tokenized **offline** with the frozen deterministic tokenizer (`benchmark/cheap_baselines/tokenize.py`; snake/camel-split, lowercased, frozen stopwords) and with chars-per-token heuristics. The exact qwen3-coder (or any LLM) tokenizer is **not available offline** on this machine (no model download permitted) → exact LLM-token counts **UNKNOWN/UNVERIFIED**; the measured deterministic counts are a *lower bound* on BPE-style token counts, and the SIP actual/offline ratio (≈1.88, from frozen provider-reported usage) is shown as a scaling reference only.

| Statistic | Agentless-style FL prompt | SIP prompt (same tasks, offline render) |
|---|---:|---:|
| deterministic tokens min | 3,099 | 4,514 |
| deterministic tokens median | 7,697 | 8,854 |
| deterministic tokens p90 | 10,050 | 9,878 |
| deterministic tokens max | 10,793 | 10,259 |
| chars median | 74,276 | 63,026 |
| chars/4 median estimate | ≈18,569 | ≈15,756 |
| ≥128k violations | **none** | **none** |

Frozen SIP provider-reported prompt tokens (ground truth, 300 tasks): mean 16,672 / median 19,487 per task (total 5,001,746; no truncation). Scaling the Agentless-style deterministic median by the SIP offline→actual ratio (≈1.88) gives ≈14.5k estimated LLM tokens (p90 ≈ 18.9k) — all far below 128k. **No context-window violations.**

Compression note: official Agentless does **not** compress the file-level structure (names only; contents enter only at later stages via `get_skeleton`). Our rendering matches that.

## 6. Execution estimate (localization-only on MAIN_297, NO paid run)

Identity used for price: the frozen RM-CSS/SIP MAIN_297 model route **qwen/qwen3-coder @ deepinfra/turbo**, list prices **$0.30 / 1M input, $1.00 / 1M output** (frozen MAIN_297 accounting; verified in frozen run artifacts).

| Quantity | Value |
|---|---|
| Calls | **297** (1 file-level localization call per task) |
| Input tokens (median, offline lower bound) | ≈7,697 (deterministic); ≈14.5k scaled estimate |
| Output tokens (file list ≤5) | ≈50–150 (estimate; mark ESTIMATE) |
| Expected API USD (localization stage) | ≈$0.72 (offline lower bound) … ≈$1.3–$1.7 (scaled estimate) for 297 tasks |
| Approx wall time | ≈297 × ~10 s ≈ **~50 min** sequential (SIP mean latency ≈9.8 s/call from frozen runs); parallelizable |
| Repair stage (not in this estimate) | official pipeline adds related/edit-location + repair calls; would increase calls and cost (roughly 2–4×; NOT estimated to dollar precision — UNKNOWN/UNVERIFIED) |

- Provider price identity: **verified** from the frozen run accounting ($0.30/$1.00 per 1M, deepinfra/turbo).
- Exact qwen3-coder token counts for Agentless-style prompts: **UNKNOWN/UNVERIFIED** (no offline LLM tokenizer; no model download allowed).
- No fill-in of unverifiable values.

## 7. Scientific usefulness verdict

- Practical: yes — 297 zero-tuning single calls ≈ $0.7–$1.7, ~1 h wall, reuses the frozen SIP scaffolding and the frozen evaluator, and adds a same-metric non-agentic LLM baseline on our exact population.
- Scientifically useful: yes — it directly tests the "no agent loop" thesis (Agentless philosophy) at file-level P/R/F1/FNR against RM-CSS/SIP/Agent under **one evaluator**, which the literature does not provide (published numbers are PUBLISHED_CONTEXT_ONLY until re-run here).
- Not executed by this mission (no paid calls authorized).
