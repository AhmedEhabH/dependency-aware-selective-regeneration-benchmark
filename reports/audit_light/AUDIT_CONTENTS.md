# AUDIT_CONTENTS

This is the FINAL M1A/M1B LIGHTWEIGHT AUDIT archive for the dependency-aware
selective regeneration benchmark project.

Package: `audit_light_m1a_m1b_final.zip`
Generated: 2026-09-12T23:03:22.325110+00:00
Built from final public main: `f3207fa3e18e4f5cb50375139cd0c06e720cc42b`

## Scope of this package

- **M1A — Controlled 4096-cap feasibility boundary** (post-hoc
  capability/feasibility boundary; ZERO scientific study cells; capability
  probes only).
- **M1B — Controlled 16K cap-relaxed encoding ablation** (post-hoc controlled
  cap-relaxed ablation; 60/60 cells; CONTROLLED ENCODING COST EFFECT SUPPORTED
  descriptive).
- **M2 — Controlled LLM serialization-density stress** remains **NOT STARTED**
  and is NOT part of this package.

## What it contains

- Current-state docs: README.md, SYSTEM_STATE.md, TODO.md
- Model identity reference: `docs/MODEL_IDENTITIES.md`
- Paper-writing handoff: `docs/PAPER_WRITING_HANDOFF.md`
- Supervisor package: `reports/SUPERVISOR_DECISION_MEMO.md`
- Paper claim / evidence map: `reports/PAPER_CLAIM_EVIDENCE_MAP.md`
- M1A result report: `reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md`
- M1B result report: `reports/CONTROLLED_ENCODING_16K_RESULT.md`
- M1A evidence dir `research/controlled-encoding-ablation-01/` (endpoint
  freeze, prevalidation, prestudy gates, prompt control, capability probes,
  probe failure note, raw probe responses + SHA-256 sidecars)
- M1B evidence dir `research/controlled-encoding-ablation-16k-01/` (endpoint
  freeze, FROZEN_M1A_PARITY, prevalidation, prestudy gates, prompt control,
  capability probes, frozen 60-cell manifest, run_records.jsonl, per-run
  structured records `runs/*.json`, raw response bodies + SHA-256 sidecars
  `runs/raw/*`, final_metrics, interpretation, closure gates, checkpoints,
  progress)
  - NOTE: the M1B `runs/` evidence is NOT committed to git (it is gitignored);
    this archive is the authoritative durable copy of that evidence.
- Zero-API verifiers + executor/driver scripts
- Schema / scorer module `src/benchmark/selection/encoding_ablation.py`
- Fine-tuning readiness note: `research/FINE_TUNING_READINESS.md`
- Audit metadata: this directory (`reports/audit_light/`), incl. the git-state
  snapshot, this contents list, and the raw-evidence manifest.

## Included files (relative to repository root; every path listed here is
physically present in this archive)

```text
README.md
SYSTEM_STATE.md
TODO.md
docs/MODEL_IDENTITIES.md
docs/PAPER_WRITING_HANDOFF.md
pyproject.toml
reports/CONTROLLED_ENCODING_16K_RESULT.md
reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md
reports/PAPER_CLAIM_EVIDENCE_MAP.md
reports/SUPERVISOR_DECISION_MEMO.md
reports/audit_light/AUDIT_CONTENTS.md
reports/audit_light/AUDIT_GIT_STATE.md
reports/audit_light/MANIFEST_OF_EXCLUDED_RAW_EVIDENCE.json
reports/audit_light/MANIFEST_OF_EXCLUDED_RAW_EVIDENCE.md
requirements-dev.txt
research/FINE_TUNING_READINESS.md
research/controlled-encoding-ablation-01/PROBE_A_FAILURE_NOTE.md
research/controlled-encoding-ablation-01/capability_probes.json
research/controlled-encoding-ablation-01/endpoint_freeze.json
research/controlled-encoding-ablation-01/prestudy_gates.json
research/controlled-encoding-ablation-01/prevalidation.json
research/controlled-encoding-ablation-01/probes/raw/probe_a_full_v2.sha256
research/controlled-encoding-ablation-01/probes/raw/probe_a_full_v2.txt
research/controlled-encoding-ablation-01/probes/raw/probe_b_sparse_v2.sha256
research/controlled-encoding-ablation-01/probes/raw/probe_b_sparse_v2.txt
research/controlled-encoding-ablation-01/prompt_control.json
research/controlled-encoding-ablation-16k-01/FROZEN_M1A_PARITY.json
research/controlled-encoding-ablation-16k-01/capability_probes.json
research/controlled-encoding-ablation-16k-01/checkpoint_10.json
research/controlled-encoding-ablation-16k-01/checkpoint_15.json
research/controlled-encoding-ablation-16k-01/checkpoint_20.json
research/controlled-encoding-ablation-16k-01/checkpoint_25.json
research/controlled-encoding-ablation-16k-01/checkpoint_30.json
research/controlled-encoding-ablation-16k-01/checkpoint_35.json
research/controlled-encoding-ablation-16k-01/checkpoint_40.json
research/controlled-encoding-ablation-16k-01/checkpoint_45.json
research/controlled-encoding-ablation-16k-01/checkpoint_5.json
research/controlled-encoding-ablation-16k-01/checkpoint_50.json
research/controlled-encoding-ablation-16k-01/checkpoint_55.json
research/controlled-encoding-ablation-16k-01/checkpoint_60.json
research/controlled-encoding-ablation-16k-01/closure_gates.json
research/controlled-encoding-ablation-16k-01/endpoint_freeze.json
research/controlled-encoding-ablation-16k-01/final_metrics.json
research/controlled-encoding-ablation-16k-01/interpretation.json
research/controlled-encoding-ablation-16k-01/manifest_60.json
research/controlled-encoding-ablation-16k-01/prestudy_gates.json
research/controlled-encoding-ablation-16k-01/prevalidation.json
research/controlled-encoding-ablation-16k-01/probes/raw/probe_a_full_v2.sha256
research/controlled-encoding-ablation-16k-01/probes/raw/probe_a_full_v2.txt
research/controlled-encoding-ablation-16k-01/probes/raw/probe_b_sparse_v2.sha256
research/controlled-encoding-ablation-16k-01/probes/raw/probe_b_sparse_v2.txt
research/controlled-encoding-ablation-16k-01/progress.json
research/controlled-encoding-ablation-16k-01/prompt_control.json
research/controlled-encoding-ablation-16k-01/run_records.jsonl
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-002-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-004-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-005-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-006-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-007-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-full_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-full_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-full_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-full_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-full_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-sparse_v2-r1.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-sparse_v2-r2.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-sparse_v2-r3.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-sparse_v2-r4.json
research/controlled-encoding-ablation-16k-01/runs/cea-djangocms-external-validity-008-sparse_v2-r5.json
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-002-sparse_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-004-sparse_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-005-sparse_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-006-sparse_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-007-sparse_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-full_v2-r5.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r1.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r1.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r2.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r2.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r3.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r3.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r4.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r4.txt
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r5.sha256
research/controlled-encoding-ablation-16k-01/runs/raw/cea-djangocms-external-validity-008-sparse_v2-r5.txt
scripts/controlled_encoding_ablation_16k_execute.py
scripts/controlled_encoding_ablation_execute.py
scripts/verify_controlled_encoding_16k_claims.py
scripts/verify_controlled_encoding_4096_claims.py
src/benchmark/selection/encoding_ablation.py
```

## What it deliberately excludes

- `.git` object database, virtual environments, caches, notebooks, Kaggle
  scratch, dry-run workspaces, other studies' evidence (Stage-C cross-model
  studies remain in git at their own immutable tags).
- No M1A/M1B raw evidence is excluded: ALL M1A/M1B raw response bodies and
  sidecars are embedded (see MANIFEST_OF_EXCLUDED_RAW_EVIDENCE).

## How to run each zero-API verifier

From a checkout containing this archive's `src/` module:

- `python scripts/verify_controlled_encoding_4096_claims.py` (M1A, 27 checks)
- `python scripts/verify_controlled_encoding_16k_claims.py` (M1B, 42 checks)

All exit 0 = PASS and require only this archive's files (evidence + scripts +
`src/benchmark/selection/encoding_ablation.py`). No model/API calls.

## Which claims can be recomputed from the light archive alone

M1A: prompt-controlled diff, schema identity, representation equivalence,
capability-probe usage/finish-reason/truncation classification, raw SHA-256
verification, ZERO study cells, endpoint freeze, six gates + audit.

M1B: frozen M1A parity, 60-cell topology, prompt control, representation
equivalence, operational counts, request accounting, tokens/cost recompute,
serialized-record counts, TP/FP/FN/P/R/F1/FNR recompute, raw SHA-256
verification, closure gates + audit + immutability.

## Exact immutable GitHub tags for raw-evidence fetch

All M1A/M1B raw evidence is already embedded in this archive; the tags below
hold the study snapshots for independent verification.

- `controlled-encoding-4096-feasibility-boundary-01`
- `paper-replication-artifact-controlled-encoding-4096-boundary-01`
- `controlled-encoding-ablation-16k-wiring-verified-01`
- `controlled-encoding-ablation-16k-study-01-audited`
- `paper-replication-artifact-controlled-encoding-ablation-16k-01`
