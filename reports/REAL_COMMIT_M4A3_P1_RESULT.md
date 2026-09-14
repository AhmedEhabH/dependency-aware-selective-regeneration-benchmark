# M4A-3 / P1 — Real-Commit FULL-v2 vs SPARSE-v2 Held-out Evaluation RESULT

**Study ID:** `real-commit-p1-full-v2-vs-sparse-v2-01`
**Executed:** 2026-09-14
**Status:** 60/60 frozen cells executed; all evidence persisted and SHA-verified.
**Frozen protocol:** `reports/REAL_COMMIT_M4A3_P1_PROTOCOL.md` (completion cap
corrected 4096 → 16384 to replicate the controlled M1B configuration).

---

## 1. Configuration (frozen before call #1)

| Setting | Value |
|---|---|
| Model | `qwen/qwen3-coder` (Qwen3-Coder-480B-A35B-Instruct) |
| Provider | DeepInfra pinned through OpenRouter (`deepinfra/turbo`), fallback OFF |
| Temperature | `0.0` |
| Completion cap | `16384` for BOTH arms (M1B replication; was 4096) |
| Graph | OFF (no graph hint injection) |
| Response format | native `json_schema` (strict) |
| Independent tasks | 10 (HELD_OUT_TEST) |
| Arms × reps | `full_v2`, `sparse_v2` × 3 nested repetitions |
| Total cells | `10 × 2 × 3 = 60` |
| Cost ceiling (frozen) | `$1.50` |
| Result-dependent reruns | FORBIDDEN |

## 2. Provider capability probe (TRAIN/VALIDATION) — PASS

Four real non-study probe calls (TRAIN full/sparse + VALIDATION full/sparse) all
PASS: provider `DeepInfra`, `finish_reason=stop`, usage known, schema-valid
decode for both arms, 16384 cap accepted. Evidence:
`research/real-commit-p1-01/capability_probes.json`.

## 3. Totals

- Cells recorded: **60/60**
- Valid (succeeded): **60**
- Failed: **0**
- Truncations (`finish_reason=length`): **0**
- Model calls: **60** (1 per cell)
- Prompt tokens: 295,410
- Completion tokens: 271,345
- Total tokens: **566,755**
- Latency total: 1,916.1 s
- Recorded API cost: **$0.359964** (< $1.50 ceiling)

## 4. Per-arm micro metrics (pooled over valid cells)

| Arm | Valid/Rec | Precision | Recall | F1 | FNR | Completion mean | Records mean | Cost |
|---|---|---|---|---|---|---|---|---|
| `full_v2` | 30/30 | 0.338843 | 0.369369 | 0.353448 | 0.630631 | 8,445.8 | 4.03 | $0.297623 |
| `sparse_v2` | 30/30 | 0.386667 | 0.261261 | 0.311828 | 0.738739 | 599.0 | 2.50 | $0.062341 |

Validity rate 1.0 and truncation rate 0.0 for BOTH arms at the 16384 cap.

## 5. Task-level metrics (n = 10 independent tasks; nested reps pooled per task)

| Task | Full P/R/F1/FNR | Sparse P/R/F1/FNR |
|---|---|---|
| djangocms-rc-4307e1b8c2e2 | 0.333 / 1.000 / 0.500 / 0.000 | 0.250 / 1.000 / 0.400 / 0.000 |
| djangocms-rc-50c3576080be | 0.667 / 0.222 / 0.333 / 0.778 | 0.500 / 0.083 / 0.143 / 0.917 |
| djangocms-rc-630a50361ada | 0.111 / 0.333 / 0.167 / 0.667 | 0.000 / 0.000 / 0.000 / 1.000 |
| djangocms-rc-66c70394c9e1 | 0.120 / 1.000 / 0.214 / 0.000 | 0.375 / 1.000 / 0.545 / 0.000 |
| djangocms-rc-75978fb1c3ad | 1.000 / 1.000 / 1.000 / 0.000 | 1.000 / 1.000 / 1.000 / 0.000 |
| djangocms-rc-8d50660e7bcf | 1.000 / 0.867 / 0.929 / 0.133 | 1.000 / 0.400 / 0.571 / 0.600 |
| djangocms-rc-9e33db4f4660 | 0.091 / 0.167 / 0.118 / 0.833 | 0.333 / 0.500 / 0.400 / 0.500 |
| djangocms-rc-b39799f9fc1c | 0.269 / 0.467 / 0.341 / 0.533 | 0.385 / 0.333 / 0.357 / 0.667 |
| djangocms-rc-ba16eb9a1d09 | 0.000 / 0.000 / 0.000 / 1.000 | 0.000 / 0.000 / 0.000 / 1.000 |
| djangocms-rc-fdda30c271f0 | 0.333 / 0.222 / 0.267 / 0.778 | 0.429 / 0.333 / 0.375 / 0.667 |

## 6. Paired task-level deltas (sparse − full) + bootstrap over tasks

Bootstrap = 10,000 resamples over the **10 independent tasks** (never over
repetitions), seeded 20260914.

| Metric | Mean delta | 95% CI |
|---|---|---|
| F1 | −0.008822 | [−0.129720, +0.118938] |
| Precision | +0.034241 | [−0.046795, +0.120882] |
| Recall | −0.064160 | [−0.196111, +0.064444] |
| FNR | +0.064160 | [−0.064444, +0.196111] |
| Completion tokens (mean) | −7,847.9 | [−8,136.0, −7,596.8] |
| Serialized records (mean) | −1.540 | [−2.833, −0.367] |
| Cost (USD) | −0.023531 | [−0.024396, −0.022778] |

## 7. Reading (descriptive)

- At the M1B 16384 cap, BOTH arms complete operationally on independent real
  changes: 60/60 valid, 0 truncations (vs the historical 4096-cap feasibility
  boundary where Full-v2 could not serialize 140–152 candidates).
- The controlled encoding-cost effect replicates directionally: Sparse-v2 cuts
  mean completion tokens by ~7,848 and cost by ~$0.0235 per task vs Full-v2,
  with the 95% bootstrap CI excluding zero (completion/cost).
- Selection-quality deltas (F1/recall/precision/FNR) are small and the 95% CIs
  straddle zero: no claim of semantic superiority or inferiority is made for
  either arm on these 10 independent tasks.
- The historical diff is an **OBSERVED CHANGE-SET PROXY**, never semantic ground
  truth. Independent task = historical change; the 3 nested repetitions per arm
  are nested observations, not independent examples.

## 8. Evidence

- Study dir: `research/real-commit-p1-01/`
- `manifest_60.json` (frozen 60-cell manifest, 16384 cap)
- `run_records.jsonl` (60 records, append-only)
- `runs/<run_id>.json` per-cell evidence (60 files)
- `runs/raw/<run_id>.txt` + `.sha256` raw responses (60 pairs, all SHA-verified)
- `capability_probes.json`, `endpoint_freeze.json`, `final_metrics.json`,
  `closure.json`, checkpoints
- Independent gates/audit: `reports/real_commit_m4a3_p1_gates.json`,
  `reports/REAL_COMMIT_M4A3_P1_VALIDATION.md`

## 9. Claim discipline (prohibited)

- No "n = 60 independent examples" claim; independent n = 10 tasks.
- No comparison of these results with any published LocAgent `Acc@K`.
- No P/R/V/H semantic gold fabricated from diffs.
- No universal sparse-superiority claim from a 10-task single-repository study.