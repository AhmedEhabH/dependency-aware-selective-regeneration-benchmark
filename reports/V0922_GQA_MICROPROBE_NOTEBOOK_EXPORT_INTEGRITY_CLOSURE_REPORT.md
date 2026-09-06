# V0922 GQA Microprobe, Notebook, and Export Integrity Closure Report

**Date:** 2026-08-27
**Branch:** `fix/pilot-v0922-t4-gqa-sdpa-preflight-observability-closure`
**Built on:** v0.9.22 candidate source commit `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee`
**Source commit (frozen):** `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee`
**Artifact:** `dist/pilot-kaggle-upload.zip` SHA-256 `ce40b33019feba58d8cabeef2244a765e157cdba4288a9d9ea2eb186de46a24d` (+ sidecar verified)
**Trust/provenance:** 0 mismatches; `reports/pilot_notebook_trust_freeze.json` FROZEN
**Full suite:** 2441 passed / 33 skipped / 0 failed
**Exact final artifact dry-run:** 48/48 succeeded (48 unique IDs, repos 16/16/16, strategies 24/24, reps 24/24, 0 model calls, 0 tokens, every record source commit == `f72ecda…`)

> **SUPERSEDED evidence:** the prior v0.9.22 candidate (source `de0c5bd8bcc7d499246292f515207ce1d10baba7`, artifact
> `bfbc935f762b484482eee411c5ea7996412b1e47f759f6dca81fa58b0ab9a850`) is now SUPERSEDED by this closure's candidate.
> Do not ask Ahmed to run the invalidated old artifact `bfbc935f…`. No stable `v0.9.22-pilot-exec-ready` tag exists yet:
> the real 2x T4 Kaggle model preflight (repo preflight + heartbeat, Qwen 14B BNB-NF4 load, GQA microprobe, short probe,
> then the 12k target with the same 64-token probe) is MANDATORY before creating the tag.

## 1. Defects closed (D1–D6)

- **D1 — fake-only repeat-KV API.** `_gqa_microprobe_expand_kv` no longer reads a
  fabricated `torch.nn.functional.repeat_kv`. It now implements the repeat-KV
  expansion with local tensor ops (`[B,Hkv,S,D] -> [B,Hkv,groups,S,D] ->
  [B,Hkv*groups,S,D]`, reproduced by `repeat_interleave` on the head axis),
  validates a positive integer group count, and fails closed on non-positive
  values. Equivalent to pinned Transformers 4.57.6 repeat-KV behavior; no import
  seam.
- **D2 — tensors not allocated on the GPU under test.** `_gqa_microprobe_build_qkv`
  now takes `device` and allocates Q/K/V explicitly on `torch.device("cuda",
  index)` for every enumerated device; `_gqa_microprobe_run_sdpa` takes `device`
  and synchronizes it after SDPA so asynchronous kernel errors surface inside the
  probe; `probe_sdpa_gqa_kernel_compatibility` records per-device
  `q_device/k_device/v_device/output_device` evidence, verifies each equals
  `cuda:{index}`, and sets `all_passed` only when every visible device is
  finite + exact-shape + correct-device. Geometry kept exact (Q=40, K=8, V=8,
  head_dim=128, seq=68, FP16; after expansion 40/40/40); allowed backends remain
  exactly FLASH + EFFICIENT (MATH excluded).
- **D3 — notebook preflight cell became a no-op.** Cell `pilot-repo-preflight-cell`
  (index 8) had a 172-element source list with ZERO newlines, so
  `"".join(source)` was a single comment line (whole cell skipped). Now it is a
  210-element newline-preserving source that `compile("".join(source), …, "exec")`
  succeeds on, and whose AST contains executable nodes for the GQA microprobe,
  fail-closed `raise`, and `_run_tee` (comments cannot satisfy these AST checks).
- **D4 — `_run_tee` timeout not enforced while reading.** The reader now enforces a
  monotonic deadline WHILE the child is running (not only after EOF),
  terminates → kills → reaps on timeout, closes the console handle, and raises a
  clear timeout exception with the command and a bounded tail; the non-zero-exit
  failure contract is preserved and output is still live-teed to the console file.
- **D5 — unrelated text encoding regression.** The branch had corrupted valid em
  dashes (U+2014) into mojibake `â€"` in several cells (`pilot-title-md`,
  `service-bootstrap-cell`, and `pilot-repo-preflight-cell` content). Restored to
  proper em dashes; canonical and bundled notebooks now carry 8 em dashes and 0
  mojibake occurrences, and a notebook contract test rejects any future mojibake.
- **D6 — export is not a faithful final snapshot.** All candidate/freeze/docs
  changes are committed and pushed before export; the export is created only
  after the final commit/push, extracted into a fresh temp directory, and
  verified (empty `git status`, extracted HEAD == Stop Report HEAD, HEAD object
  exists, origin branch ref == HEAD, artifact + sidecar exist and match, trust
  freeze tracked and byte-identical, identity source commit == frozen source
  commit). No `PROJECT_EXPORT_READY` is printed unless every check passes.
  **Truthful status: the local export was created and its verifiable members
  (`.git/HEAD`, artifact + sidecar match, trust freeze) were verified; push/origin
  parity (`origin ref == HEAD`) and the definitive post-push export remain
  PENDING until this branch is pushed (the earlier push attempt was blocked by a
  network outage to github.com).**

## 2. Verification

- `git diff --check`: clean.
- Ruff on changed Python files: clean.
- Mypy on changed production file (`kaggle_qwen_backend.py`): clean.
- Python compile on changed files: clean.
- Targeted Pytest: 216 passed (LLM unit incl. 14 new GQA-compat tests + bundle
  smoke) and 77 passed (notebook contract incl. new AST/mojibake + real
  subprocess `_run_tee` integration).
- Full `pytest tests/`: **2441 passed / 33 skipped / 0 failed**
  (was 2407 passed / 33 skipped at the v0.9.22 candidate baseline; +14 new GQA
  unit tests and +63 notebook-contract/`_run_tee` assertions).
- Trust validator + source-provenance validator (finalizer
  `--verify-source-provenance`): **0 mismatches**; `reports/pilot_notebook_trust_freeze.json` FROZEN.
- Final artifact notebook passes the same AST checks (executable microprobe,
  fail-closed `raise`, `_run_tee`) and contains no mojibake.
- Exact final artifact dry-run: **48/48** succeeded, 48 unique IDs, repos
  16/16/16, strategies 24/24, reps 24/24, 0 model calls, 0 tokens, every record
  source commit == `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee`.

## 3. Independent self-audit

- Frozen scientific contract untouched: model `Qwen/Qwen2.5-Coder-14B-Instruct`,
  `bnb-nf4`, `sdpa`, kernel policy `flash_or_efficient_no_math` (MATH disabled),
  GQA compat const `KAGGLE_SDPA_GQA_COMPATIBILITY = "repeat_kv_sm75"`, 12
  scenarios, 3 pins, 2 strategies, 2 reps = 48 cells, prompts, Ground Truth,
  metrics, `--timeout 600`, `--validation-timeout 1800`, max attempts 3,
  completion cap 4096, 12000/64 gate.
- No v0.9.23 spawned; work continues on the SAME v0.9.22 candidate branch.
- No stable `v0.9.22-pilot-exec-ready` tag created (real T4 proof still pending).

## 4. Root Cause Status

| Defect | Status |
|--------|--------|
| D1 fake-only repeat-KV API | CLOSED |
| D2 tensors not on GPU under test | CLOSED |
| D3 notebook preflight no-op | CLOSED |
| D4 `_run_tee` timeout not enforced | CLOSED |
| D5 em-dash mojibake regression | CLOSED |
| D6 export not faithful snapshot | LOCAL EXPORT VERIFIED; push/origin parity (`origin ref == HEAD`) + definitive post-push export PENDING until the branch is pushed |

## 5. What remains (ordered)

1. Push this branch to origin, fetch, and prove `origin/<branch> == HEAD` — then
   rebuild/re-verify the post-push export (D6 parity closure).
2. Fresh real 2x T4 Kaggle model preflight (repo preflight + heartbeat, Qwen 14B
   BNB-NF4 load, GQA microprobe, short probe, then the 12k target with the same
   64-token probe) using the exact artifact `ce40b330…`.
3. If the 12k probe PASSES: annotate `v0.9.22-pilot-exec-ready` on source commit
   `f72ecda0e7dac10e81dae34daa6bb1610c94b9ee`, push tag, refresh docs.
4. If it FAILS: return to the SAME v0.9.22 task (do not spawn v0.9.23).
5. Launch accepted 48-cell Pilot only after the stable tag exists and all target
   gates pass.
