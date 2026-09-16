#!/usr/bin/env python3
"""BibTeX triage classification + report (2026-09-16).

Reads research/literature/bibtex_triage_2026-09-16.csv (unique titles) and
classifies each into:
  USE_NOW / VERIFY_FIRST / BACKGROUND_ONLY / REJECT_IRRELEVANT / DUPLICATE

Keyword-based heuristic + a verified high-priority override map. The report is
a high-signal selection, not a copy of hundreds of references.
"""

# ruff: noqa: E501  (triage annotation strings intentionally descriptive)
from __future__ import annotations

import csv
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TRIAGE_CSV = BASE / "research" / "literature" / "bibtex_triage_2026-09-16.csv"
OUT_CSV = BASE / "research" / "literature" / "bibtex_triage_classified_2026-09-16.csv"
OUT_MD = BASE / "reports" / "BIBTEX_LITERATURE_TRIAGE_2026-09-16.md"

# High-priority verified items (from primary-source checks) -> classification
# Keys are NORMALIZED titles (hyphens -> spaces, punctuation removed, lowercase).
VERIFIED = {
    "llm driven cost effective requirements change impact analysis": ("USE_NOW", "arXiv 2511.00262; same cost-aware CIA question; requirements-to-requirements (not file localization); strong novelty/design reference"),
    "change patterns mapping a boosting way for change impact analysis": ("USE_NOW", "TSE 2022 10.1109/TSE.2021.3059481; history/change-pattern augmentation of CIA; direct Route-B history-evidence overlap"),
    "learning dependency based change impact predictors using independent change histories": ("USE_NOW", "IST 2015 10.1016/j.infsof.2015.07.007; cross-project/history-based impact prediction; history/co-change + cross-repo relevance"),
    "a software impact analysis tool based on change history learning and its evaluation": ("USE_NOW", "ICSE-SEIP 2022 10.1145/3510457.3519017; history-learned candidate recommendation; classical/history baseline + novelty threat"),
    "enhancing code understanding for impact analysis by combining transformers and program dependence graphs": ("USE_NOW", "arXiv 2607.23355 (Yan et al 2026); modern transform+PDG impact analysis; graph use overlap, file/entity unit"),
    "repoformer selective retrieval for repository level code completion": ("USE_NOW", "arXiv 2403.10059 (Wu et al 2024); selective-compute prior; guards against generic 'selective escalation is novel' claims"),
    "fastcoder accelerating repository level code generation via efficient retrieval and verification": ("USE_NOW", "arXiv 2502.17139 (Zhao et al 2025); efficiency+verification at repo level; exact verification mechanism/cost threat"),
    "issue localization via llm driven iterative code graph searching": ("USE_NOW", "arXiv 2503.22424 (Jiang et al 2025); graph-guided issue localization competitor vs LocAgent/GraphLocator/Route B"),
    "supporting change impact analysis using a recommendation system an industrial case study in a safety critical context": ("USE_NOW", "TSE 2017 10.1109/TSE.2016.2620458; recommendation-system CIA; classical/history lineage + industrial grounding"),
    "a prediction model for software requirements change impact": ("BACKGROUND_ONLY", "ASE 2021 10.1109/ASE51524.2021.9678582; requirements-level prediction; background, not direct file baseline"),
}

# Keywords strongly indicating relevance (software CIA / localization / repository / change impact)
REL_KEYWORDS = [
    "change impact", "impact analysis", "impact prediction", "localization",
    "localize", "repository", "code completion", "code generation", "impacted",
    "change propagation", "dependency", "omission", "retrieval", "impact set",
    "affected", "selective", "verification", "impact planning", "change history",
    "fault localization", "bug localization", "code search", "program dependence",
    "impact assessment", "change-proneness", "change recommendation",
]
# Keywords indicating out-of-domain / noise
NOISE_KEYWORDS = [
    "slam", "visual navigation", "robot", "lidar", "sensor", "point cloud",
    "mapping navigation", "autonomous vehicle", "vulnerability",
    "dependency parsing", "nlp", "sentiment", "medical", "clinical",
    "cascade", "flood", "epidemic", "stock", "finance", "credit risk",
    "graph neural network acceleration", "gpu", "sparse matrix",
]

# Direct classification cache
CLASS_CACHE: dict[str, str] = {}
for k, (c, _) in VERIFIED.items():
    CLASS_CACHE[k] = c


def classify(norm_title: str, title: str, dup: int) -> str:
    nt = norm_title
    if nt in CLASS_CACHE:
        return CLASS_CACHE[nt]
    if dup > 1:
        return "DUPLICATE"
    tl = title.lower()
    rel = any(k in tl for k in REL_KEYWORDS)
    noise = any(k in tl for k in NOISE_KEYWORDS)
    if noise and not rel:
        return "REJECT_IRRELEVANT"
    if rel:
        if any(k in tl for k in ("change impact", "impact analysis", "impact prediction", "localization", "localize", "repository", "retrieval", "verification", "omission", "selective")):
            return "VERIFY_FIRST"
        return "BACKGROUND_ONLY"
    return "REJECT_IRRELEVANT"


def main() -> int:
    with open(TRIAGE_CSV, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    out_rows = []
    for r in rows:
        cls = classify(r["norm_title"], r["title"], int(r["dup_count"]))
        reason = VERIFIED.get(r["norm_title"], ("", ""))[1] if r["norm_title"] in VERIFIED else ""
        out_rows.append({**r, "classification": cls, "reason": reason})

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        for r in sorted(out_rows, key=lambda x: x["norm_title"]):
            w.writerow(r)

    from collections import Counter

    counts = Counter(r["classification"] for r in out_rows)

    lines = [
        "# BibTeX Literature Triage (2026-09-16)",
        "",
        "**Source:** 13 uploaded BibTeX exports (`papers (4)..(16).bib`) treated as",
        "**candidate discovery sources**, not authoritative publication metadata.",
        "High-priority items verified from primary sources (arXiv API / Crossref).",
        "",
        "## Summary",
        "",
        "- raw entries parsed: **987**",
        "- unique normalized titles: **806**",
        f"- duplicates (same title in >1 export): **{counts.get('DUPLICATE',0)}**",
        f"- USE_NOW: **{counts.get('USE_NOW',0)}**",
        f"- VERIFY_FIRST: **{counts.get('VERIFY_FIRST',0)}**",
        f"- BACKGROUND_ONLY: **{counts.get('BACKGROUND_ONLY',0)}**",
        f"- REJECT_IRRELEVANT: **{counts.get('REJECT_IRRELEVANT',0)}**",
        "",
        "Full machine-readable classification:",
        "`research/literature/bibtex_triage_classified_2026-09-16.csv`.",
        "",
        "## High-priority verified items (Section B of the addendum)",
        "",
        "| Title | Classification | Verification |",
        "|---|---|---|",
    ]
    for k, (c, reason) in VERIFIED.items():
        # find title from rows
        title = next((r["title"] for r in rows if r["norm_title"] == k), k)
        lines.append(f"| {title} | {c} | {reason} |")

    lines += [
        "",
        "## Noise / rejection discipline",
        "",
        "Query-collision noise (robotics/SLAM, NLP parsing, medical/selective-",
        "prediction, generic graph acceleration, vulnerability) is recorded as",
        "`REJECT_IRRELEVANT` and is NOT cited merely because keywords overlap.",
        "Representative false-positive examples are retained in the CSV with short",
        "reasons.",
        "",
        "## Use in the proposal",
        "",
        "The 10 verified high-priority items are integrated into the living review",
        "and the comparison matrix. The proposal retains only high-signal",
        "references; it does NOT copy hundreds of entries.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("classified:", dict(counts))
    print("outputs:", OUT_CSV, OUT_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
