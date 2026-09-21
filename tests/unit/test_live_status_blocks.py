"""LIVE_STATUS block synchronization tests.

docs/LIVE_STATUS.json is the single current-state source of truth. The
rendered LIVE block must appear byte-for-byte between the markers
<!-- LIVE_STATUS:BEGIN --> and <!-- LIVE_STATUS:END --> in FOUR current-facing
files:
  README.md
  START_HERE_CURRENT_2026-09-21b.md
  PROGRESS.md
  00_CURRENT_RESEARCH_STATE.md

Ahmed's authoritative clarification (2026-09-21): 00_CURRENT_RESEARCH_STATE.md
must NOT remain a manually maintained parallel current-state block — it is a
fourth rendered target.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

LIVE_STATUS = PROJECT_DIR / "docs" / "LIVE_STATUS.json"
RENDERER = PROJECT_DIR / "scripts" / "render_live_status.py"
BEGIN = "<!-- LIVE_STATUS:BEGIN -->"
END = "<!-- LIVE_STATUS:END -->"

TARGETS = (
    "README.md",
    "START_HERE_CURRENT_2026-09-21b.md",
    "PROGRESS.md",
    "00_CURRENT_RESEARCH_STATE.md",
)


def _render() -> str:
    result = subprocess.run(
        [sys.executable, str(RENDERER)],
        cwd=PROJECT_DIR, capture_output=True, timeout=60,
        env={"PYTHONIOENCODING": "utf-8", "PATH": __import__("os").environ.get("PATH", "")},
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.decode("utf-8").replace("\r\n", "\n").rstrip("\n")


def _block_between(text: str) -> str | None:
    if BEGIN not in text or END not in text:
        return None
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    return text[start:end].strip("\n")


def test_live_status_json_schema_keys_preserved() -> None:
    """AC-T7: docs/LIVE_STATUS.json keeps every key of the attached schema."""
    data = json.loads(LIVE_STATUS.read_text(encoding="utf-8"))
    for key in ("schema", "as_of_local", "evidence_snapshot", "phase", "position",
                "position_short", "now_short", "next_action", "next_short",
                "priority_chain", "weakest_risk", "wp1b_short", "pipeline",
                "preflight", "calibration_3", "llm_calls", "key_numbers", "schema_note"):
        assert key in data, f"LIVE_STATUS.json missing key {key}"
    assert data["schema"] == "live_status_v1"


def test_all_four_targets_contain_byte_identical_blocks() -> None:
    rendered = _render()
    for rel in TARGETS:
        path = PROJECT_DIR / rel
        assert path.is_file(), f"missing current-facing file: {rel}"
        text = path.read_text(encoding="utf-8")
        block = _block_between(text)
        assert block is not None, f"{rel} missing LIVE_STATUS markers"
        assert block == rendered, (
            f"{rel} LIVE block out of sync with docs/LIVE_STATUS.json\n"
            f"run: python scripts/render_live_status.py --write"
        )


def test_render_is_deterministic() -> None:
    assert _render() == _render()
