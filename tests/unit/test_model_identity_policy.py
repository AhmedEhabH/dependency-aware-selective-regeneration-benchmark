"""Regression tests for the current-facing model-identity policy.

Policy: current-facing reviewer documentation must never refer to the
historical scientific model merely as ``Qwen3-Coder``. It must use the full
human-readable name ``Qwen3-Coder-480B-A35B-Instruct`` and, when the raw API
identifier matters, also the OpenRouter slug ``qwen/qwen3-coder``.

These tests fail if a current-facing document regresses to the ambiguous bare
label without the complete model identity.
"""

from __future__ import annotations

import re
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent.parent

CURRENT_FACING_DOCS = (
    "README.md",
    "SYSTEM_STATE.md",
    "TODO.md",
    "docs/MODEL_IDENTITIES.md",
    "docs/PAPER_WRITING_HANDOFF.md",
    "reports/PAPER_CLAIM_EVIDENCE_MAP.md",
    "reports/QWEN3_32B_PAPER_INTEGRATION_NOTE.md",
)

# Bare "Qwen3-Coder" that is NOT part of a fuller model token such as
# Qwen3-Coder-480B-A35B-Instruct or Qwen3-Coder-30B-A3B-Instruct.
_BARE_QWEN3_CODER = re.compile(r"Qwen3-Coder(?!-480B)(?!-30B)")


def test_model_identity_doc_exists_and_is_self_contained():
    path = _PROJECT_DIR / "docs" / "MODEL_IDENTITIES.md"
    text = path.read_text(encoding="utf-8")
    assert "Qwen3-Coder-480B-A35B-Instruct" in text
    assert "qwen/qwen3-coder" in text
    assert "Qwen3-32B" in text
    assert "qwen/qwen3-32b" in text
    assert "Qwen3-Coder-30B-A3B-Instruct" in text
    assert "qwen/qwen3-coder-30b-a3b-instruct" in text


def test_full_model_name_present_in_current_facing_docs():
    for rel in CURRENT_FACING_DOCS:
        path = _PROJECT_DIR / rel
        assert path.is_file(), f"missing current-facing doc: {rel}"
        text = path.read_text(encoding="utf-8")
        assert (
            "Qwen3-Coder-480B-A35B-Instruct" in text
        ), f"{rel} must use the full model name Qwen3-Coder-480B-A35B-Instruct"


def test_no_bare_ambiguous_qwen3_coder_in_current_facing_docs():
    for rel in CURRENT_FACING_DOCS:
        path = _PROJECT_DIR / rel
        text = path.read_text(encoding="utf-8")
        hits = [m.group(0) for m in _BARE_QWEN3_CODER.finditer(text)]
        assert not hits, f"{rel} uses ambiguous bare label(s): {sorted(set(hits))}"


def test_slug_and_full_name_both_required_when_slug_used():
    """When the raw slug `qwen/qwen3-coder` appears in current-facing prose, the
    full human-readable name must appear nearby (same doc)."""
    for rel in CURRENT_FACING_DOCS:
        path = _PROJECT_DIR / rel
        text = path.read_text(encoding="utf-8")
        if "qwen/qwen3-coder" in text:
            assert (
                "Qwen3-Coder-480B-A35B-Instruct" in text
            ), f"{rel} uses slug qwen/qwen3-coder without the full model name"


def test_new_model_slug_identity_policy():
    """The new coder-model identity constants used across the study must agree
    with the documented policy."""
    text = (_PROJECT_DIR / "docs" / "MODEL_IDENTITIES.md").read_text(encoding="utf-8")
    assert "Qwen3-Coder-30B-A3B-Instruct" in text
    assert "qwen/qwen3-coder-30b-a3b-instruct" in text
