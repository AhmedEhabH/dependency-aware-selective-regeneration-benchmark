# Repository Agent Baseline Specification

**Date:** 2026-07-25
**Branch:** docs/research-design-v2
**Protocol Version:** 1.0 (FROZEN)
**Source Commit:** 3a16596
**Status:** DESIGN — Not Implemented

---

## 1. Purpose

This document defines the **minimum reproducible behavior** for the main Agent baseline (`repository_agent` role per RD-V2-02) that will serve as the confirmatory comparison against the `hybrid_selective` treatment.

The baseline must represent an **iterative repository-aware workflow** — not the current single-shot LLM classifier.

---

## 2. Required Behavioral Contract

### 2.1 Input Contract

| Input | Type | Description |
|-------|------|-------------|
| Natural-language requirement change | `RequirementChange` | `before` and `after` text; acceptance criteria |
| Repository snapshot | `RepositorySnapshot` | Identity, commit SHA, root path |
| Artifact universe | `ArtifactUniverse` | Candidate artifacts with paths and types |
| **No ground-truth access** | — | Must not access expected affected artifacts |
| **No dependency graph access** | — | Must not access `DependencyGraph` or `ImpactPropagator` |

### 2.2 Process Contract (Iterative Bounded Retrieval)

The agent must execute a **bounded iterative loop**:

```
for round in 1..MAX_RETRIEVAL_ROUNDS:
    1. SELECT: Choose candidate artifacts/files to inspect
    2. RETRIEVE: Read file contents (via tool)
    3. REASON: Update internal state/context with retrieved content
    4. DECIDE: Can I make a confident scope decision?
       - If YES: break → scope selection
       - If NO: continue (if rounds remain)
    5. TERMINATE: If max rounds reached → scope selection with current context
```

### 2.3 Output Contract

| Output | Type | Description |
|--------|------|-------------|
| Scope selection | `ImpactPrediction` | `ImpactDecision` tuples with `artifact`, `action`, `rationale`, `supporting_evidence` |
| Token accounting | `TokenUsage` | Aggregated across all LLM calls |
| Tool call log | `list[ToolCall]` | Each retrieval/inspection action |

---

## 3. Minimum Reproducible Behavior

### 3.1 Iterative Retrieval Specification

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Maximum retrieval rounds** | 5 | Budget-conscious; prevents unbounded exploration |
| **Maximum files inspected per round** | 10 | Context window management; ~2000 tokens/file |
| **Maximum total files inspected** | 30 | Cumulative cap across rounds |
| **Maximum model calls per round** | 1 | One reasoning call per retrieval batch |
| **Maximum total model calls** | 6 | 1 initial + 5 retrieval rounds |
| **Maximum total tokens** | 50,000 | Prompt + completion across all calls |
| **Tool interfaces** | `read_file(path)`, `list_dir(path)`, `grep(pattern, path)` | Minimal file-system tools |
| **Termination conditions** | Confident decision OR max rounds OR max tokens OR max files | Explicit stop criteria |

**Budget Status (per RD-V2 researcher review):**

| Budget Parameter | Value | Status |
|------------------|-------|--------|
| Maximum retrieval rounds | 5 | **INITIAL ENGINEERING DEFAULTS — SUBJECT TO PILOT CALIBRATION — NOT FROZEN SCIENTIFIC CONSTANTS** |
| Maximum total files inspected | 30 | **INITIAL ENGINEERING DEFAULTS — SUBJECT TO PILOT CALIBRATION — NOT FROZEN SCIENTIFIC CONSTANTS** |
| Maximum total model calls | 6 | **INITIAL ENGINEERING DEFAULTS — SUBJECT TO PILOT CALIBRATION — NOT FROZEN SCIENTIFIC CONSTANTS** |
| Maximum total tokens | 50,000 | **INITIAL ENGINEERING DEFAULTS — SUBJECT TO PILOT CALIBRATION — NOT FROZEN SCIENTIFIC CONSTANTS** |

**The final budget will be selected before confirmatory execution using a documented calibration process that does not inspect confirmatory outcomes. Do not silently present model-generated budget values as researcher-approved constants.**

### 3.2 Scope Selection

After retrieval terminates, the agent produces a final scope decision:

- **Input:** Accumulated context (retrieved file contents + requirement change)
- **Process:** Single final LLM call with structured prompt
- **Output:** `ImpactPrediction` with decisions for each artifact in universe
- **Actions:** `regenerate`, `preserve`, `human_review` (per `ActionKind` enum)

### 3.3 Shared Regeneration Executor Integration

The agent **only produces scope selection**. Regeneration, validation, and repair are handled by the **shared regeneration executor** (see `docs/SHARED_REGENERATION_EXECUTOR_DESIGN.md`).

**Agent responsibility ends at:** `ImpactPrediction` return from `analyze_impact()`

**Executor responsibility begins at:** `ImpactPrediction` → `RegenerationPlan` → patch application → validation → repair

---

## 4. Model and Decoding Parameters (Fixed)

| Parameter | Value | Scope |
|-----------|-------|-------|
| **Model** | Qwen2.5-Coder-7B-Instruct | All conditions |
| **Temperature** | 0.0 | Deterministic |
| **Top-p** | 1.0 | No nucleus sampling |
| **Max tokens per call** | 4096 | Per LLM call |
| **Max total tokens** | 50,000 | Cumulative across calls |
| **System prompt** | Fixed template (see §5) | All conditions |

---

## 5. Prompt Templates

### 5.1 Initial Assessment Prompt

```
You are a repository-aware code change impact analyzer.

Repository: {repo_name} @ {commit_sha}
Change: {requirement_before} -> {requirement_after}
Acceptance Criteria: {criteria_list}

Candidate Artifacts ({count} total):
{artifact_list}

You have access to file inspection tools. Your task is to identify which artifacts need regeneration.

Round 1: Select up to {max_files_per_round} files to inspect. Reply with JSON:
{
  "action": "inspect",
  "files": ["path1", "path2", ...],
  "reasoning": "Why these files?"
}
```

### 5.2 Retrieval Round Prompt (Rounds 2-N)

```
Previous context:
{accumulated_file_contents}

Select up to {max_files_per_round} additional files to inspect, or make final decision.
Reply with JSON:
{
  "action": "inspect" | "decide",
  "files": ["path1", "path2", ...],  // only if action=inspect
  "reasoning": "...",
  "scope_decision": {  // only if action=decide
    "regenerate": ["path1", "path2"],
    "preserve": ["path3", "path4"],
    "human_review": ["path5"]
  }
}
```

### 5.3 Final Decision Prompt

```
Complete retrieved context:
{all_retrieved_file_contents}

Requirement Change: {requirement_before} -> {requirement_after}
Acceptance Criteria: {criteria_list}

All candidate artifacts:
{artifact_list}

Based on your inspection, which artifacts need regeneration?
Reply with JSON:
{
  "regenerate": ["path1", "path2"],
  "preserve": ["path3", "path4"],
  "human_review": ["path5"],
  "confidence": 0.0-1.0,
  "reasoning": "Summary of evidence"
}
```

---

## 6. Tool Interface Specification

### 6.1 read_file(path: str) → FileContent

```python
@dataclass
class FileContent:
    path: str
    content: str
    size_bytes: int
    truncated: bool  # True if > MAX_FILE_SIZE
```

- **MAX_FILE_SIZE:** 50,000 characters (truncated with notice)
- **Error handling:** Returns error content; agent must handle gracefully

### 6.2 list_dir(path: str) → DirListing

```python
@dataclass
class DirListing:
    path: str
    entries: list[DirEntry]  # name, is_file, size
```

- **Max entries:** 100 (truncated)

### 6.3 grep(pattern: str, path: str) → GrepResult

```python
@dataclass
class GrepResult:
    pattern: str
    matches: list[GrepMatch]  # file, line_number, line_content
```

- **Max matches:** 50

---

## 7. Termination Conditions

The iterative loop terminates when **any** condition is met:

1. **Confident decision:** Agent returns `action: "decide"` with scope decision
2. **Max rounds reached:** 5 retrieval rounds completed
3. **Max files inspected:** 30 total files read
4. **Max tokens consumed:** 50,000 tokens across all LLM calls
5. **Max model calls:** 6 total calls (1 initial + 5 rounds)
6. **Error/timeout:** Tool failure or budget exhaustion

On forced termination (2-6), agent **must** produce a scope decision from accumulated context.

---

## 8. Failure Policy

| Failure Mode | Behavior |
|--------------|----------|
| LLM JSON parse error | Retry once with corrected prompt; then return empty scope (all preserve) |
| Tool error (file not found) | Log warning; continue with remaining files |
| Token budget exceeded | Force termination → final decision from current context |
| Max attempts (repair) | Handled by shared executor, not agent |

---

## 9. Logging Requirements

Every agent run must produce a structured log:

```json
{
  "run_id": "...",
  "strategy": "repository_agent",
  "retrieval_rounds": 3,
  "files_inspected": ["path1", "path2", ...],
  "tool_calls": [
    {"tool": "read_file", "args": {"path": "..."}, "result": "success|error", "duration_ms": 12}
  ],
  "llm_calls": [
    {"round": 1, "prompt_tokens": 1200, "completion_tokens": 200, "duration_ms": 800}
  ],
  "total_tokens": 4200,
  "total_duration_seconds": 4.2,
  "termination_reason": "confident_decision|max_rounds|max_files|max_tokens|error",
  "final_scope_size": 5,
  "final_decisions": {"regenerate": 3, "preserve": 20, "human_review": 2}
}
```

---

## 10. Deterministic Experiment Controls

| Control | Implementation |
|---------|----------------|
| **Seed** | Fixed per (scenario, repetition) via `ExecutionContext.random_seed` |
| **Model determinism** | Temperature=0.0; same model weights (Qwen2.5-Coder-7B-Instruct) |
| **Tool determinism** | File system reads are deterministic at fixed commit |
| **Prompt determinism** | Fixed templates; no dynamic few-shot examples |
| **Ordering** | File inspection order logged; affects context but not final decision space |

---

## 11. Acceptance Criteria for Implementation

The baseline is **accepted** when all criteria are met:

- [ ] Implements iterative retrieval loop (max 5 rounds)
- [ ] Uses tool interface: `read_file`, `list_dir`, `grep`
- [ ] Respects all budget limits (rounds, files, tokens, calls)
- [ ] Produces `ImpactPrediction` with proper `ActionKind` enum values
- [ ] Logs complete tool call and token accounting
- [ ] Integrates with `BenchmarkRunner` via `ImpactStrategy` protocol
- [ ] Passes contract tests: `test_repository_agent_baseline.py`
- [ ] Dry-run and real-run both execute without error
- [ ] Token accounting matches `LLMBackend` reported usage
- [ ] Termination reason always recorded

---

## 12. Explicit Non-Requirements

The following are **not required** for the baseline:

- [ ] Multi-agent collaboration
- [ ] Planning/subtask decomposition
- [ ] Cross-repository knowledge
- [ ] Historical pattern learning
- [ ] Semantic embedding search (vector DB)
- [ ] Test generation or execution
- [ ] Patch/application logic (handled by shared executor)

---

## 13. Relationship to Current Implementation

| Aspect | Current (`agent`) | Specified (`repository_agent`) |
|--------|-------------------|-------------------------------|
| Retrieval | None (full context) | Iterative (5 rounds, 30 files) |
| File inspection | None | `read_file`, `list_dir`, `grep` |
| Context refinement | None | Accumulated across rounds |
| Model calls | 1 | 1-6 |
| Tools | None | 3 file-system tools |
| Generation | None (classification only) | None (classification only) |
| Role name | `agent` | `repository_agent` (RD-V2-02) |
| Protocol claim | "Repository-retrieval baseline" | **Now accurate** |

---

## 14. Implementation Notes

- **New strategy class:** `RepositoryAgentStrategy` (replace or wrap current)
- **Tool provider:** Inject via constructor or `ExecutionContext`
- **Budget enforcement:** Use existing `BudgetManager` (attempts/tokens/timeout)
- **State management:** `ExecutionContext` or internal round-state
- **Testing:** Mock tool provider for unit tests; integration test with real repo

---

**Status:** DESIGN COMPLETE — Ready for implementation (SU-0011 or later)
**Blockers:** None — design is self-contained
**Dependencies:** Shared regeneration executor (parallel design)