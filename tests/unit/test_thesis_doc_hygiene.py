"""Thesis-hygiene documentation regression check.

Ensures CURRENT-FACING thesis documents do not attribute research findings to
development-assistant tools that were NOT scientific models under evaluation
(e.g. OpenCode, GPT-5.6 Sol, ChatGPT, Claude, Gemini, DeepSeek V4 Flash).

The check deliberately DOES NOT scan immutable raw / historical evidence:
- research/*/runs/, *.jsonl run records, raw responses, sidecars
- reports/scientific-*, reports/dryrun_*, *_probes/
- anything below a "HISTORICAL RECORD" heading in SYSTEM_STATE.md / TODO.md
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Incidental development-assistant tool names (not scientific models under
# evaluation). Exact model slugs that ARE scientific (Qwen3-Coder-480B-A35B,
# Qwen3-32B, Qwen3-Coder-30B-A3B) and serving infrastructure (OpenRouter,
# DeepInfra, SiliconFlow) are intentionally NOT in this list.
INCIDENTAL_TOOL_PATTERNS = (
    "opencode",
    "gpt-5.6",
    "gpt5.6",
    "chatgpt",
    "claude",
    "gemini",
    "deepseek v4 flash",
    "v4 flash 0731",
)

# Whole-file current-facing docs (thesis-facing scientific documentation).
CURRENT_FACING_FILES = (
    "README.md",
    "docs/PAPER_WRITING_HANDOFF.md",
    "docs/MODEL_IDENTITIES.md",
    "docs/MSC_RESEARCH_ROADMAP_2026_2027.md",
    "reports/PAPER_CLAIM_EVIDENCE_MAP.md",
    "reports/SUPERVISOR_DECISION_MEMO.md",
    "reports/CONTROLLED_ENCODING_4096_FEASIBILITY_RESULT.md",
    "reports/CONTROLLED_ENCODING_16K_RESULT.md",
    "reports/FINAL_BENCHMARK_RESULTS.md",
    "reports/RESEARCH_TRUTH_MATRIX.md",
    "reports/BENCHMARK_VALIDITY_AND_LIMITATIONS.md",
    "reports/BENCHMARK_REPRODUCIBILITY_INDEX.md",
    "reports/THESIS_EVIDENCE_MATRIX.md",
)

# Files where only the region ABOVE the first "## HISTORICAL RECORD" heading is
# current-facing; content below is a historical record and is NOT scanned.
HISTORICAL_BOUNDARY_FILES = ("SYSTEM_STATE.md", "TODO.md")

HISTORICAL_BOUNDARY_MARKER = "## HISTORICAL RECORD"


def _current_facing_text(rel_path: str) -> str:
    """Return the current-facing portion of a file (respecting boundaries)."""
    text = (ROOT / rel_path).read_text(encoding="utf-8")
    if rel_path in HISTORICAL_BOUNDARY_FILES:
        idx = text.find(HISTORICAL_BOUNDARY_MARKER)
        if idx != -1:
            return text[:idx]
    return text


def _find_incidental_hits(text: str) -> list[tuple[int, str, str]]:
    """Return (line_no, pattern, line) for incidental tool-name hits."""
    hits: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        lower = line.lower()
        for pattern in INCIDENTAL_TOOL_PATTERNS:
            if pattern in lower:
                hits.append((line_no, pattern, line.strip()))
                break
    return hits


class TestCurrentFacingDocsFreeOfIncidentalAIToolNames:
    """Regression: no dev-assistant branding in thesis-facing docs."""

    def test_whole_file_current_facing_docs(self) -> None:
        for rel in CURRENT_FACING_FILES:
            path = ROOT / rel
            assert path.is_file(), f"missing current-facing doc: {rel}"
            hits = _find_incidental_hits(_current_facing_text(rel))
            assert not hits, (
                f"{rel} contains incidental development-assistant name(s): "
                f"{[(h[0], h[1], h[2][:80]) for h in hits]}"
            )

    def test_boundary_files_only_scan_above_historical_record(self) -> None:
        for rel in HISTORICAL_BOUNDARY_FILES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            assert HISTORICAL_BOUNDARY_MARKER in text, (
                f"{rel} must contain a '{HISTORICAL_BOUNDARY_MARKER}' heading"
            )
            hits = _find_incidental_hits(_current_facing_text(rel))
            assert not hits, (
                f"{rel} CURRENT STATE region contains incidental development-"
                f"assistant name(s): {[(h[0], h[1], h[2][:80]) for h in hits]}"
            )

    def test_incidental_patterns_detected_when_present(self) -> None:
        # Prove the detector is not a no-op (RED capability of the check).
        assert _find_incidental_hits("STOP FOR GPT-5.6 Sol review\n")
        assert _find_incidental_hits("Owner: OpenCode\n")
        assert not _find_incidental_hits("Qwen3-Coder-480B-A35B-Instruct\n")
        assert not _find_incidental_hits("OpenRouter / DeepInfra / SiliconFlow\n")
