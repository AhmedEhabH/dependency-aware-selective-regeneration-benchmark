# P5-B — LocAgent Shared-Protocol Pilot on VALIDATION: Attempt + Exact Blocker

**Date:** 2026-09-14
**Status:** REAL PILOT ATTEMPTED ON VALIDATION ONLY — **BLOCKED before any
LocAgent localization output** by the unmodified upstream agent loop's use of
`multiprocessing.get_context('fork')` (POSIX-only) on this Windows host.
**P5-C (HELD_OUT_TEST) NOT AUTHORIZED.**

## 1. What was attempted (genuine end-to-end)

1. **Real upstream installation** — cloned upstream
   `https://github.com/gersteinlab/LocAgent` and verified HEAD == frozen pin
   `4935b557326c154bad8e8dcf3747cc8d32d1f387` (the P5-A pin). Built an
   isolated Python 3.12 venv (`dist/locagent-venv`, uv-managed) and installed
   the LocAgent runtime dependencies (litellm, openai, datasets, faiss-cpu,
   bm25s, tree-sitter(+languages), llama-index-core 0.11.22 + embedders +
   bm25 retriever, PyStemmer, libcst, ipython, torch, networkx, matplotlib,
   ...). All LocAgent modules import cleanly (`dependency_graph`,
   `util`, `plugins.LocationToolsRequirement`).
2. **Real indexing on a VALIDATION parent** — checked out
   `djangocms-rc-0daae01f2f65` parent `d7ee89da24` from the frozen
   `dist/real-commit-cache/djangocms` cache and ran LocAgent `build_graph`
   (global_import=True): **3805 nodes / 18861 edges** — indexing works.
3. **Same model/provider transport compatibility** — verified litellm can
   route the EXACT P1 model/provider from this venv:
   `openrouter/qwen/qwen3-coder` + `deepinfra/turbo` (fallback OFF,
   `require_parameters`), `finish_reason=stop`, correct content. The
   model/provider itself is fully compatible with LocAgent's litellm layer.
4. **Real `--localize` run on VALIDATION** — built a local HF-format dataset
   package (`research/locagent-p5b/ds_pkg/validation_hf`) from the P5-A
   adapter for the 6 VALIDATION cases (djangocms-rc-0daae01f2f65,
   0fec81224889, 1031d20fca28, 47b63015feb1, a9e2a8d3b7a6, e3a23a7fc757;
   `patch` EMPTY, leakage-free) and launched the frozen upstream entrypoint
   `auto_search_main.py --localize` with `eval_n_limit 1`.

## 2. Exact blocker (preserved verbatim)

The unmodified upstream agent loop (`auto_search_main.py` →
`run_localize`) executes:

```python
ctx = mp.get_context('fork')  # auto_search_main.py:363
```

On this Windows host this raises:

```
ValueError: cannot find context for 'fork'
```

Consequence: the agent subprocess cannot start, the child worker dies with
`EOFError` at the manager queue, and the localization attempt terminates with
no `loc_outputs.jsonl` / no `found_files` for any case.

Secondary upstream restriction: `--model` is an argparse `choices` list frozen
to `gpt-4o / azure/gpt-4o / openai/... / deepseek/... / litellm_proxy/... /
openai/qwen-7B|32B (and ft variants)`; an `openrouter/...` route is not in the
upstream list, so a same-model `--model openrouter/qwen/qwen3-coder` launch is
rejected by upstream argparse even though litellm supports the route.

The blocker is **environmental/platform** (POSIX `fork` unavailable on
Windows), NOT a scientific failure and NOT a model/provider failure. Per the
frozen P0_TO_P5 §P5 policy: the attempt and exact blocker are preserved here;
a SYSTEM-LEVEL comparison would be required if a different LocAgent-supported
model were used; no algorithmic-difference attribution is made.

## 3. P5 six gates + independent audit (ZERO API)

`python scripts/verify_locagent_p5a_readiness.py` — **OVERALL PASS**:

- [PASS] locagent_output_parser_valid
- [PASS] common_evaluator_metrics
- [PASS] adapter_patch_empty_all_cases
- [PASS] no_held_out_in_dryrun (36 allowed cases: MINER_DEV+TRAIN+VALIDATION)
- [PASS] upstream_pin_frozen (4935b557326c154bad8e8dcf3747cc8d32d1f387)

Shared output mapping + evaluation are frozen (P5-A):
`src/benchmark/locagent/adapter.py`,
`src/benchmark/locagent/evaluator.py` (common P/R/F1/FNR + FNR, never mixing
native Acc@K with F1).

## 4. Evidence

- Upstream clone + venv: `dist/locagent-repo` (HEAD == pinned commit),
  `dist/locagent-venv` (isolated; not committed)
- VALIDATION dataset package: `research/locagent-p5b/ds_pkg/validation_hf/`
- Graph index proof: run on parent `d7ee89da24` → 3805 nodes / 18861 edges
- litellm transport proof: `openrouter/qwen/qwen3-coder` @ DeepInfra OK
- P5-A gates/audit: `reports/LOCAGENT_P5A_READINESS.md`,
  `reports/locagent_p5a_dryrun_manifest.json`

## 5. Conclusion / claims discipline

- **P5-B real LocAgent pilot on VALIDATION: BLOCKED** (exact blocker above).
  No LocAgent `found_files` exist for any case; NO numeric comparison is made.
- **P5-C (HELD_OUT_TEST) NOT authorized** — no LocAgent output exists.
- No claim that LocAgent algorithmically differs from our method; the result is
  SYSTEM-LEVEL / environmental, not algorithmic.
- If a POSIX host or a documented adapter patch layer becomes available, the
  frozen shared protocol (P5-A) is ready to execute P5-B immediately.