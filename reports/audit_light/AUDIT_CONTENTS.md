# AUDIT_CONTENTS

This is the LIGHTWEIGHT AUDIT archive for the dependency-aware selective
regeneration benchmark project.

## What it contains
- Model identity reference: `docs/MODEL_IDENTITIES.md`
- Current-state docs: README.md, SYSTEM_STATE.md, TODO.md
- Supervisor package: `reports/SUPERVISOR_DECISION_MEMO.md` (unified comparison table + options)
- Study protocols / integration notes: QWEN3_32B_* and QWEN3_CODER_30B_A3B_* reports
- Graph readiness: `reports/GRAPH_ONE_DAY_EXPERIMENT_PROTOCOL.md`,
  `reports/SELECTIVE_REGENERATION_GRAPH_RECONNECTION.md`
- Decisions: `reports/REAL_COMMIT_BENCHMARK_PLAN.md`, `reports/MERKLE_HASH_DECISION.md`,
  `reports/SALEOR_DECISION.md`
- Structured per-cell evidence: run_records.jsonl + per-run JSON + final_metrics.json
  + manifest_60.json + closure/prestudy gates + cross_model_agreement.json for the
  Qwen3-32B and Qwen3-Coder-30B-A3B-Instruct studies (and the historical primary/v2 run records)
- Accounting correction notes (both studies)
- Provider capability/freeze metadata (endpoint_freeze.json,
  provider_capability_snapshot.json, capability_probes.json, PROVIDER_FREEZE_NOTE.md)
- Frozen input parity files (FROZEN_INPUT_PARITY.json)
- Zero-API verifiers + focused tests + driver scripts + pyproject/requirements

## What it deliberately excludes
- Large raw per-cell provider response bodies (`runs/raw/*.txt`) — listed in
  `MANIFEST_OF_EXCLUDED_RAW_EVIDENCE.json` with SHA-256 and the immutable tag
  containing each file.
- `.git` object database, virtual environments, node_modules, caches, notebooks,
  Kaggle scratch, dry-run workspaces, old exports.

## How to run each zero-API verifier
- `python scripts/verify_paper_claims.py` (historical primary evidence)
- `python scripts/verify_qwen3_32b_crossmodel_claims.py` (corrected Qwen3-32B)
- `python scripts/verify_qwen3_coder_30b_a3b_crossmodel_claims.py` (new 30B study)
All exit 0 = PASS and require only this archive's files (run_records + sidecars).
The raw-response SHA checks require the excluded raw files; to re-run them fully,
fetch the raw files from the immutable tags listed in MANIFEST_OF_EXCLUDED_RAW_EVIDENCE.

## Which claims can be recomputed from the light archive alone
Operational counts, validity/failure/truncation counts, TP/FP/FN/P/R/F1/FNR,
full recall, per-scenario metrics, S006 analysis, cross-product Jaccard
agreement, token/cost lower-bound accounting (from run_records + final_metrics).

## Which checks require fetching raw evidence from the immutable tag
Raw SHA-256 of the excluded per-cell response bodies (the structured RunRecord
carries `raw_response_sha256`; the raw body is retrievable from the tagged
commit for independent byte verification).

## Exact immutable GitHub tags for raw-evidence fetch
- `qwen3-coder-30b-a3b-crossmodel-study-01-audited` (30B study raw responses)
- `qwen3-32b-crossmodel-study-01-audited` (Qwen3-32B study raw responses)
