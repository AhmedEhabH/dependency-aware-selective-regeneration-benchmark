# SCIENTIFIC-MICROSTUDY-DECISION (FAST-RESULTS-02 FINAL RUN)

Experiment `exp-20260905-225518` completed **30/30 terminal, 0 succeeded, 0 evaluator-passed** (all `model_output`, 0 retryable). Total real API spend $ 0.2978 from 558,126 tokens / 337 calls on openrouter:qwen/qwen3-coder@DeepInfra (frozen).

**Study decision: NO-GO.**
Reason: G1 correctness not cleared in all 3 scenarios; study NO-GO
Requirement: all 3 clear G1 AND G2 AND at least 2/3 clear G3

Per-scenario gates:
- todo-smoke-001: G1=False (selective_passes=0/5, agent_passes=0/5), G2=True, G3=True
- todo-smoke-002: G1=False (selective_passes=0/5, agent_passes=0/5), G2=True, G3=True
- todo-smoke-003: G1=False (selective_passes=0/5, agent_passes=0/5), G2=True, G3=True

No rerun is authorized or attempted: the task rule forbids rerunning valid scientific failures because the result is unattractive, and no parser/operational heuristic was added.

Evidence conserved verbatim: `reports/scientific_microstudy/` (run_records.jsonl 30 records, source_identity.json `d6e27d7`/`828191860bff37c0`/`openrouter:qwen/qwen3-coder@DeepInfra`, exact_patch true, agent_control_max_completion_tokens 512) + `SCIENTIFIC_MICROSTUDY_RESULTS.csv/.md`.

Next: stable `v0.9.22` tag untouched (NOT A RELEASE); neither `v0.9.22-pilot-exec-ready` nor any candidate tag moved. This closure is a results-only scientific NO-GO report.