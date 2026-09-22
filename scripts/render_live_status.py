#!/usr/bin/env python3
"""Render the LIVE_STATUS block from docs/LIVE_STATUS.json (ZERO API).

The block is inserted between the markers
  <!-- LIVE_STATUS:BEGIN -->  and  <!-- LIVE_STATUS:END -->
in the current-facing files. docs/LIVE_STATUS.json is the single source of
truth; the rendered block is byte-for-byte testable by
tests/unit/test_live_status_blocks.py.

Usage:
  python scripts/render_live_status.py            # print the block to stdout
  python scripts/render_live_status.py --write    # update the 4 target files

Exit codes:
  0  ok
  1  LIVE_STATUS.json missing or malformed
  2  a target file does not contain both markers
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
LIVE_STATUS = _PROJECT_DIR / "docs" / "LIVE_STATUS.json"

BEGIN = "<!-- LIVE_STATUS:BEGIN -->"
END = "<!-- LIVE_STATUS:END -->"

TARGETS = (
    _PROJECT_DIR / "README.md",
    _PROJECT_DIR / "START_HERE_CURRENT_2026-09-21b.md",
    _PROJECT_DIR / "PROGRESS.md",
    _PROJECT_DIR / "00_CURRENT_RESEARCH_STATE.md",
)

# Authorized / not authorized: read from LIVE_STATUS.json key "authorization"
# (list of {item, status, note}). The tuple below is only the legacy fallback
# for an older LIVE_STATUS.json without that key (it was hard-coded until
# 2026-09-22 and went stale; the JSON is now the single source).
_AUTHORIZED_LINES = (
    ("Calibration-3b (Phase C)", "AUTHORIZED", "D4 = YES, ceiling $0.25, paired revalidation of the D2 tool fix"),
    ("MAIN_297 + variance 15×3", "NOT AUTHORIZED", "requires D7 = YES after Ahmed reviews Calibration-3b"),
    ("786 Saleor RESERVE outcomes", "SEALED", "never opened/read/scored/sampled"),
    ("Calibration-3 / Calibration-3b F1 claims", "NOT PERMITTED", "instrument checks only; no labels loaded or scored"),
)


def _table(header: tuple[str, str, str], rows: list[tuple[str, str, str]]) -> str:
    lines = [f"| {h[0]} | {h[1]} | {h[2]} |" for h in (header,)]
    lines.append(f"| {':---|' * 3}")
    for row in rows:
        lines.append(f"| {row[0]} | {row[1]} | {row[2]} |")
    return "\n".join(lines)


def render(data: dict) -> str:
    """Render the LIVE_STATUS Markdown block (content BETWEEN the markers)."""
    out: list[str] = []
    out.append("## LIVE STATUS — single current-state source of truth")
    out.append("")
    out.append(f"**Position:** {data['position']}")
    out.append("")
    out.append("**Research pipeline:**")
    out.append("")
    out.append(_table(
        ("Step", "Status", "Note"),
        [(p["step"], p["status"], p["note"]) for p in data["pipeline"]],
    ))
    out.append("")
    out.append("**LLM-call accounting:**")
    out.append("")
    out.append(_table(
        ("Workflow", "Calls", "Note"),
        [(c["workflow"], c["calls"], c["note"]) for c in data["llm_calls"]],
    ))
    out.append("")
    out.append("**Authorized / not authorized:**")
    out.append("")
    auth = data.get("authorization")
    auth_rows = (
        [(a["item"], a["status"], a["note"]) for a in auth] if auth else list(_AUTHORIZED_LINES)
    )
    out.append(_table(
        ("Item", "Status", "Note"),
        auth_rows,
    ))
    out.append("")
    out.append(f"**Next action:** {data['next_action']}")
    out.append("")
    out.append("**End-to-end status:** WP-2 has **not started**; E2E-G6 F2P/P2P "
               "oracle has **not started**; **no** E2E Smoke, Pilot or Research Run "
               "exists yet.")
    out.append("")
    out.append(f"*Source: `docs/LIVE_STATUS.json` (schema `{data['schema']}`), "
               f"rendered by `scripts/render_live_status.py`. As of "
               f"{data['as_of_local']}.*")
    return "\n".join(out)


def _block(text: str) -> str | None:
    if BEGIN not in text or END not in text:
        return None
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    return text[start:end]


def write_blocks(data: dict) -> list[Path]:
    """Replace the block between the markers in every target file."""
    rendered = render(data)
    updated: list[Path] = []
    for target in TARGETS:
        if not target.is_file():
            print(f"[live] SKIP (missing): {target.relative_to(_PROJECT_DIR)}")
            continue
        text = target.read_text(encoding="utf-8")
        if BEGIN not in text or END not in text:
            print(f"[live] ERROR: markers missing in {target.relative_to(_PROJECT_DIR)}")
            continue
        start = text.index(BEGIN) + len(BEGIN)
        end = text.index(END)
        new_text = text[:start] + "\n\n" + rendered + "\n" + text[end:]
        target.write_text(new_text, encoding="utf-8")
        updated.append(target)
        print(f"[live] updated {target.relative_to(_PROJECT_DIR)}")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="update the 4 target files")
    args = parser.parse_args()

    if not LIVE_STATUS.is_file():
        print(f"[live] ERROR: {LIVE_STATUS} missing")
        return 1
    try:
        data = json.loads(LIVE_STATUS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[live] ERROR: malformed LIVE_STATUS.json: {exc}")
        return 1

    if args.write:
        write_blocks(data)
        return 0

    print(render(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
