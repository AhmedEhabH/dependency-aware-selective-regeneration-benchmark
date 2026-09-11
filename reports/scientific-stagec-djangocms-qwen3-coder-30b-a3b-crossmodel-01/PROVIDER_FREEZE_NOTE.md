# Provider Freeze Note — Qwen3-Coder-30B-A3B-Instruct cross-model study

**Study:** `scientific-stagec-djangocms-qwen3-coder-30b-a3b-crossmodel-01`
**Model:** Qwen3-Coder-30B-A3B-Instruct (OpenRouter slug
`qwen/qwen3-coder-30b-a3b-instruct`)
**Gateway:** OpenRouter
**FROZEN PROVIDER:** SiliconFlow — endpoint tag `siliconflow/fp8`
**Freeze date (UTC):** 2026-09-11

## Provider selection sequence (live OpenRouter metadata + live probes)

1. **Novita** was the task-preferred candidate. Live OpenRouter metadata
   (`provider_capability_snapshot.json`) listed `response_format` and
   `structured_outputs` in `supported_parameters`, 160k context,
   32768 max completion tokens, pricing $0.07 / $0.27 per 1M, uptime 97.4%
   (1d). It was probed first with the ACTUAL frozen ImpactPlan-v1 and
   ImpactPlan-v2 JSON schemas (identical request shape to the historical
   studies).

2. **Novita FAILED the capability contract before any scientific execution.**
   Both probes returned `HTTP 400 Bad Request` with the provider error:
   `response format json_schema is not supported` (raw metadata preserved in
   `capability_probes.json` and the OpenRouter error body below). Despite
   advertising `response_format`/`structured_outputs`, the Novita endpoint
   rejected the exact `response_format: {type: json_schema, ...}` shape used
   by the frozen protocol. The task forbids weakening the schema or switching
   to free-form JSON, so Novita could not satisfy the probe requirement
   `response_format=json_schema accepted`.

3. **SiliconFlow** was the ONE predeclared alternative candidate. The
   identical request shape (same json_schema response_format, same frozen
   schema content, temperature 0, max_tokens 4096, provider pinned with
   `allow_fallbacks=false`) was probed against `siliconflow/fp8`:
   - provider reported: SiliconFlow
   - finish_reason: stop
   - usage captured (prompt/completion/total + cost)
   - reasoning_tokens: 0 (model-native non-thinking confirmed)
   - valid JSON, strict schema valid, contract OK
   Both ACTUAL frozen schema probes PASS (`QWEN3_CODER_30B_A3B_SILICONFLOW_CONTRACT: PASS`).

## Frozen configuration (NO PROVIDER SWITCHING after this point)

- provider.order = ["siliconflow/fp8"]
- provider.allow_fallbacks = false
- provider.require_parameters = true
- quantization: fp8
- context_length: 262144
- max_completion_tokens: 235929 (>= 4096 frozen cap)
- supported_parameters: structured_outputs, response_format, temperature,
  top_p, top_k, frequency_penalty, tools, tool_choice, max_tokens
- live pricing: $0.07 / 1M input, $0.28 / 1M output (SiliconFlow)
- reasoning: model-native non-thinking — NO reasoning control parameter is
  sent at all

## Evidence files

- `endpoint_freeze.json` — frozen endpoint identity/pricing/config
- `provider_capability_snapshot.json` — full live OpenRouter metadata snapshot
- `capability_probes.json` — the two non-study capability probes (both PASS)
- Novita 400 error body (preserved here for the record):

```json
{"message": "response format json_schema is not supported trace_id: 5063b30ed278152901b8c8cae078f91a", "type": "invalid_request_error"}
```

## Provider difference disclosure

The historical scientific model Qwen3-Coder-480B-A35B-Instruct was served via
OpenRouter / **DeepInfra** (`deepinfra/turbo`). The new coder-model study is
served via OpenRouter / **SiliconFlow** (`siliconflow/fp8`). This
**cross-provider** difference is a disclosed limitation: model and provider
are confounded in any comparison with the historical study.
