#!/usr/bin/env python3
"""Parse + deduplicate the 13 uploaded BibTeX exports (candidate discovery only).

Treats the .bib files as CANDIDATE DISCOVERY SOURCES, not authoritative
metadata. Emits a normalized CSV for manual triage:
research/literature/bibtex_triage_2026-09-16.csv
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

BIB_DIR = Path(__file__).resolve().parent.parent / "research" / "literature" / "bibtex_imports"
OUT_CSV = Path(__file__).resolve().parent.parent / "research" / "literature" / "bibtex_triage_2026-09-16.csv"

# key = { value }  or  key = " value "  (value may span lines, no nested handling)
FIELD_RE = re.compile(
    r"[ \t]*([A-Za-z][A-Za-z0-9_:\-]*)[ \t]*=[ \t]*([{\"])(.*?)([}\"])(?=[ \t]*,?[ \t]*$)",
    re.M | re.S,
)


def split_entries(text: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    pos = 0
    while pos < len(text):
        m = re.search(r"@(?P<type>\w+)\s*\{\s*(?P<key>[^,\s]+)\s*,", text[pos:])
        if not m:
            break
        open_brace = text.find("{", pos + m.start())
        if open_brace < 0:
            break
        depth = 0
        j = open_brace
        end = -1
        while j < len(text):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    end = j
                    break
            j += 1
        if end < 0:
            break
        body = text[open_brace + 1 : end]
        entries.append((m.group("type").lower(), m.group("key"), body))
        pos = end + 1
    return entries


def field(body: str, name: str) -> str:
    # match a line starting with name= ... capturing {..} or ".."
    pat = re.compile(
        r"(?m)[ \t]*" + re.escape(name) + r"[ \t]*=[ \t]*([{\"])(.*?)([}\"])[ \t]*,?[ \t]*$"
    )
    m = pat.search(body)
    if m:
        return m.group(2).strip()
    return ""


def norm_title(t: str) -> str:
    t = re.sub(r"[\{\}]", "", t)
    t = re.sub(r"\\[\w]+", "", t)
    t = re.sub(r"[^A-Za-z0-9 ]", " ", t)
    return " ".join(t.lower().split())


def main() -> int:
    rows: list[dict] = []
    for bib in sorted(BIB_DIR.glob("papers_*.bib")):
        text = bib.read_text(encoding="utf-8", errors="replace")
        for etype, ekey, body in split_entries(text):
            title = field(body, "title")
            if not title:
                continue
            rows.append(
                {
                    "source_file": bib.name,
                    "bibkey": ekey,
                    "entry_type": etype,
                    "title": title,
                    "authors": field(body, "author"),
                    "year": field(body, "year"),
                    "journal": field(body, "journal") or field(body, "booktitle"),
                    "doi": field(body, "doi"),
                    "url": field(body, "url") or field(body, "eprint"),
                    "norm_title": norm_title(title),
                }
            )

    by_title: dict[str, list[dict]] = {}
    for r in rows:
        by_title.setdefault(r["norm_title"], []).append(r)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "title", "authors", "year", "venue", "entry_type", "doi", "url",
                "source_files", "dup_count", "norm_title",
            ]
        )
        for nt, group in sorted(by_title.items(), key=lambda kv: kv[0]):
            first = group[0]
            w.writerow(
                [
                    first["title"], first["authors"], first["year"], first["journal"],
                    first["entry_type"], first["doi"], first["url"],
                    "+".join(sorted({r["source_file"] for r in group})),
                    len(group), nt,
                ]
            )

    print("raw entries:", len(rows))
    print("unique titles:", len(by_title))
    print("output:", OUT_CSV)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
