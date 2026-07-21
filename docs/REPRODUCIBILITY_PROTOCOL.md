# Reproducibility Protocol — v1.0 (FROZEN)

**Part of:** Research Protocol v1.0
**Approval Date:** 2026-07-22

---

## 1. Replication Package Contents

- Repository snapshots or reproducible commit references
- Requirement changes (structured specifications)
- Ground-truth annotations
- Prompts (version-controlled)
- Dependency extraction scripts
- Graph data
- Model settings (temperature, top_p, max_tokens, seed)
- Raw logs
- Analysis notebooks
- Environment instructions
- Docker/Kaggle environment specification
- Run scripts with fixed seeds
- Pre/post processing scripts
- Output manifests
- README with step-by-step reproduction instructions
- Licence file and component-level licence manifest

## 2. Hosting (per DA-10)

- **GitHub** — source, docs, public configs, scenarios, cleared notebook
- **Zenodo** — immutable archived release and DOI
- **Kaggle Datasets** — executable code/data bundles

If Zenodo is unavailable, use OSF or an institutional repository and document it.

## 3. Licences (per DA-11)

- **MIT** — original benchmark code and scripts
- **CC BY 4.0** — original documentation, scenarios, guides, and research metadata
- **Original upstream licences** — third-party repository content and derived material

Create a component-level licence manifest. Never relicense third-party source or model artifacts.

## 4. Model Outputs (per DA-12)

Redistribute raw outputs only where licences and platform terms permit. Scan for secrets, personal data, credentials, and local path disclosure. Publish sanitized outputs, hashes, metrics, and provenance when raw output cannot be public.

Classify outputs as:
- Public raw
- Public sanitized
- Metadata only
- Unavailable

## 5. Version Control

All code, prompts, and configuration files under version control (Git). Each experiment run tagged with unique run ID. Run provenance recorded in structured metadata (JSON/YAML).

## 6. Platform Documentation

- Kaggle environment: GPU type, CUDA version, Python version, package versions
- Local environment: same (as in Phase 0 report)
- All dependencies version-pinned

## 7. Determinism (per AC-07)

Temperature zero and fixed seeds do not guarantee identical GPU LLM outputs. Deterministic components must reproduce exactly; model execution is best-effort reproducible. Record hardware, CUDA, kernels, quantization, packages, parameters, and all supported seeds. Retain repeated runs.

## 8. Output Archiving

Raw model outputs preserved (not just aggregate metrics). Proprietary-model outputs archived where licensing permits. Output filenames include run ID and timestamp.

## 9. Protocol Amendments (per AC-11)

After the first main result is observed, no repository, scenario, primary metric, baseline, threshold, exclusion rule, NI margin, or statistical test may change silently. Every amendment must record:

| Field | Description |
|-------|-------------|
| Amendment ID | Unique identifier |
| Date | When the amendment was made |
| Trigger | What prompted the change |
| Already-observed results | State of data before change |
| Old rule | Previous specification |
| New rule | Revised specification |
| Rationale | Justification |
| Approval | Who approved and how |
| Affected analyses | Which results/analyses are affected |
