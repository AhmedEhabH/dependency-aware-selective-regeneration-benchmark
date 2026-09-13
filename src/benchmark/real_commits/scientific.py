"""RealCommitImpactDataset-v1 scientific corpus builder (M4A-2).

Deterministic, ZERO scientific LLM/API calls. Mines the modern PR-era djangoCMS
history (newest 6000 ancestors of the frozen anchor), applies the frozen M4A-1
eligibility rules with ``allow_intent_path_leakage=False`` (any scientific case
whose intent mentions a changed path is INELIGIBLE), excludes the 6 MINER_DEV
targets, removes related/duplicate changes (R1 exact proxy set, R2 shared
PR-reference, R3 suspected-related with adjudication), then selects up to 40
cases via year-capped selection and freezes TRAIN/VALIDATION/HELD_OUT_TEST
splits BEFORE any model result exists.

The historical diff remains an OBSERVED CHANGE-SET PROXY - never semantic
P/R/V/H ground truth. See reports/REAL_COMMIT_M4A2_PROTOCOL.md for the frozen
procedure.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from benchmark.real_commits import miner
from benchmark.real_commits.models import (
    MINER_VERSION,
    REPOSITORY_URL_DJANGOCMS,
    SCHEMA_VERSION,
    canonical_json,
    compute_canonical_dataset_manifest_hash,
    sha256_json,
)

# Frozen procedure constants (see REAL_COMMIT_M4A2_PROTOCOL.md).
SCIENTIFIC_WINDOW: int = 6000
YEAR_CAP: int = 5
TARGET_CASES: int = 40
SPLIT_SEED: int = 20260913
SPLIT_RATIO: tuple[tuple[str, float], ...] = (
    ("TRAIN", 0.60),
    ("VALIDATION", 0.15),
    ("HELD_OUT_TEST", 0.25),
)
R3_INTENT_JACCARD_THRESHOLD: float = 0.5

PR_REF_RE = re.compile(r"#(\d+)")


# ---------------------------------------------------------------------------
# Batch git scan (deterministic, single git log pass)
# ---------------------------------------------------------------------------


def batch_scan_ancestors(cache_dir: Path, anchor: str, window: int) -> list[dict[str, Any]]:
    """Return newest-first ancestor metadata + name-status in ONE git call.

    Mirrors the frozen per-commit ``diff_name_status`` semantics (single-parent
    diffs) but avoids a subprocess per commit. Deterministic topo order.
    """
    result = subprocess.run(
        [
            "git", "-C", str(cache_dir), "log", "--topo-order", "--name-status",
            "--format=%H%x1f%P%x1f%ct%x1f%s", anchor,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git log failed: {result.stderr.strip()}")

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in result.stdout.splitlines():
        ln = raw.strip()
        if not ln:
            continue
        if "\x1f" in ln:
            sha, parents, ct, subject = ln.split("\x1f", 3)
            current = {
                "sha": sha,
                "parents": tuple(parents.split()) if parents else (),
                "ct": ct,
                "subject": subject,
                "status": {},
            }
            records.append(current)
        else:
            if current is None:
                continue
            parts = ln.split("\t")
            if len(parts) == 2:
                current["status"][parts[1]] = parts[0]
            elif len(parts) == 3:
                current["status"][parts[2]] = parts[0]
    return records[:window]


def _intent_tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def intent_jaccard(a: str, b: str) -> float:
    ta, tb = _intent_tokens(a), _intent_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def extract_pr_refs(subject: str) -> frozenset[str]:
    return frozenset(PR_REF_RE.findall(subject))


# ---------------------------------------------------------------------------
# Candidate enumeration (frozen eligibility, scientific strictness)
# ---------------------------------------------------------------------------


def enumerate_scientific_candidates(
    cache_dir: Path,
    anchor: str,
    *,
    window: int = SCIENTIFIC_WINDOW,
    miner_dev_targets: frozenset[str] = frozenset(),
    proxy_max: int = 12,
    total_diff_ceiling: int = 40,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Enumerate eligible scientific candidates + exclusion counts.

    Applies the frozen v1 eligibility with ``allow_intent_path_leakage=False``
    (scientific: any leak is INELIGIBLE), the whitespace check, and the
    MINER_DEV target exclusion. Returns (candidates, exclusion_counts).
    """
    records = batch_scan_ancestors(cache_dir, anchor, window)
    counts: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []

    for r in records:
        if r["sha"] == anchor:
            continue
        if len(r["parents"]) != 1:
            counts["merge_commit"] += 1
            continue
        intent = miner.normalize_intent(r["subject"])
        if not miner.meaningful_intent(intent):
            counts["no_meaningful_intent"] += 1
            continue
        if not r["status"]:
            counts["no_production_source_change"] += 1
            continue

        elig = miner.evaluate_eligibility(
            parents=r["parents"],
            intent=intent,
            name_status=r["status"],
            proxy_max=proxy_max,
            total_diff_ceiling=total_diff_ceiling,
            allow_intent_path_leakage=False,
        )
        if not elig["eligible"]:
            reason = elig["reason_codes"][0] if elig["reason_codes"] else "no_production_source_change"
            counts[reason] += 1
            continue

        if miner.production_diff_is_whitespace_only(
            cache_dir, r["parents"][0], r["sha"], elig["proxy_paths"]
        ):
            counts["whitespace_only"] += 1
            continue

        if r["sha"] in miner_dev_targets:
            counts["miner_dev_target"] += 1
            continue

        dt = datetime.fromtimestamp(int(r["ct"]), tz=UTC).isoformat()
        candidates.append(
            {
                "sha": r["sha"],
                "parent": r["parents"][0],
                "subject": r["subject"],
                "intent": intent,
                "status": r["status"],
                "time": dt,
                "ts": int(r["ct"]),
                "year": dt[:4],
                "proxy_paths": tuple(sorted(elig["proxy_paths"])),
                "proxy_count": elig["proxy_count"],
                "change_type": elig["change_type"],
                "intent_mentions_changed_path": bool(elig["intent_mentions_changed_path"]),
                "prs": extract_pr_refs(r["subject"]),
                "eligibility": elig,
            }
        )
    return candidates, dict(sorted(counts.items()))


# ---------------------------------------------------------------------------
# Related / duplicate detection (R1 exact set, R2 shared PR, R3 suspected)
# ---------------------------------------------------------------------------


def deduplicate_candidates(
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Remove related/duplicate candidates; return (kept, adjudication_records).

    R1: identical frozenset(proxy_paths) -> keep the newest.
    R2: shared #NNNN PR/issue reference -> keep the newest of the PR group.
    R3: overlapping proxy paths AND intent Jaccard >= 0.5 AND non-identical
        proxy set -> SUSPECTED related; adjudicated by inspection (keep the
        newest when the messages describe the same change). Every R3 pair is
        recorded with a decision and rationale.
    """
    kept: list[dict[str, Any]] = []
    adjudication: list[dict[str, Any]] = []

    seen_proxy_sets: dict[frozenset[str], str] = {}
    seen_pr_refs: dict[str, str] = {}

    # R3 adjudication needs the full pool; collect first-pass R1/R2 survivors.
    r1r2: list[dict[str, Any]] = []
    for c in candidates:  # newest-first
        key = frozenset(c["proxy_paths"])
        if key in seen_proxy_sets:
            adjudication.append(
                {
                    "rule": "R1_exact_proxy_set",
                    "decision": "exclude_older",
                    "kept_sha": seen_proxy_sets[key],
                    "excluded_sha": c["sha"],
                    "reason": "identical proxy set already accepted",
                    "proxy_set": sorted(key),
                }
            )
            continue
        shared = c["prs"] & set(seen_pr_refs)
        if shared:
            adjudication.append(
                {
                    "rule": "R2_shared_pr_reference",
                    "decision": "exclude_older",
                    "kept_sha": seen_pr_refs[next(iter(shared))],
                    "excluded_sha": c["sha"],
                    "reason": f"shares PR/issue refs with earlier candidate: {sorted(shared)}",
                }
            )
            continue
        seen_proxy_sets[key] = c["sha"]
        for pr in c["prs"]:
            seen_pr_refs.setdefault(pr, c["sha"])
        r1r2.append(c)

    # R3: pairwise suspected-related across R1/R2 survivors.
    r3_excluded: set[str] = set()
    for i in range(len(r1r2)):
        for j in range(i + 1, len(r1r2)):
            a, b = r1r2[i], r1r2[j]
            overlap = set(a["proxy_paths"]) & set(b["proxy_paths"])
            if not overlap:
                continue
            if set(a["proxy_paths"]) == set(b["proxy_paths"]):
                continue
            sim = intent_jaccard(a["subject"], b["subject"])
            if sim < R3_INTENT_JACCARD_THRESHOLD:
                continue
            # Adjudicate: keep the newest, exclude the older (same change).
            adjudication.append(
                {
                    "rule": "R3_suspected_related",
                    "decision": "exclude_older_keep_newest",
                    "kept_sha": a["sha"],
                    "excluded_sha": b["sha"],
                    "intent_jaccard": round(sim, 3),
                    "overlapping_proxy_paths": sorted(overlap),
                    "rationale": (
                        f"shared proxy paths and intent Jaccard {sim:.2f} >= 0.5; "
                        f"messages describe the same/continuation change "
                        f"({a['subject'][:60]!r} vs {b['subject'][:60]!r})"
                    ),
                }
            )
            r3_excluded.add(b["sha"])

    kept = [c for c in r1r2 if c["sha"] not in r3_excluded]
    return kept, adjudication


# ---------------------------------------------------------------------------
# Deterministic year-capped selection
# ---------------------------------------------------------------------------


def select_year_capped(
    candidates: list[dict[str, Any]],
    *,
    cap: int = YEAR_CAP,
    target: int = TARGET_CASES,
) -> list[dict[str, Any]]:
    """Select up to ``target`` cases, at most ``cap`` per calendar year.

    Iterates years newest -> oldest; within each year takes candidates newest
    -> oldest up to the cap; stops at ``target``. Deterministic.
    """
    by_year: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        by_year[c["year"]].append(c)

    selected: list[dict[str, Any]] = []
    taken_per_year: Counter[str] = Counter()
    for year in sorted(by_year.keys(), reverse=True):
        for c in by_year[year]:
            if len(selected) >= target:
                break
            if taken_per_year[year] >= cap:
                continue
            selected.append(c)
            taken_per_year[year] += 1
        if len(selected) >= target:
            break
    return selected


def _shape_bucket(proxy_count: int) -> str:
    if proxy_count <= 2:
        return "small"
    if proxy_count <= 6:
        return "medium"
    return "large"


# ---------------------------------------------------------------------------
# Split freeze (metadata-only, deterministic, BEFORE any model result)
# ---------------------------------------------------------------------------


def _largest_remainder_allocation(total: int, ratio: tuple[tuple[str, float], ...]) -> dict[str, int]:
    """Allocate ``total`` seats to splits via largest-remainder on ``ratio``."""
    floor_counts: dict[str, int] = {}
    floor_total = 0
    for name, frac in ratio:
        floor_counts[name] = int(total * frac)
        floor_total += floor_counts[name]
    remainder = total - floor_total
    order = sorted(
        ratio, key=lambda item: (total * item[1] - int(total * item[1])), reverse=True
    )
    for name, _ in order:
        if remainder <= 0:
            break
        floor_counts[name] += 1
        remainder -= 1
    return floor_counts


def freeze_splits(
    selected: list[dict[str, Any]],
    *,
    seed: int = SPLIT_SEED,
    ratio: tuple[tuple[str, float], ...] = SPLIT_RATIO,
) -> dict[str, Any]:
    """Deterministic metadata-only split freeze.

    Buckets by proxy-size bucket (small/medium/large), seeded-shuffles within
    each bucket, concatenates buckets, and assigns splits in seeded order
    proportional to the target ratio (largest-remainder over the whole set).
    Returns a frozen split manifest with per-case assignment, per-split counts,
    per-split hashes, and the canonical manifest hash.
    """
    names = [name for name, _ in ratio]
    targets = _largest_remainder_allocation(len(selected), ratio)

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in selected:
        buckets[_shape_bucket(c["proxy_count"])].append(c)

    rng = random.Random(seed)
    ordered: list[dict[str, Any]] = []
    for bucket in ("small", "medium", "large"):
        shuffled = list(buckets[bucket])
        shuffled.sort(key=lambda c: (c["time"], c["sha"]))
        rng.shuffle(shuffled)
        ordered.extend(shuffled)

    assignment: dict[str, str] = {}
    counts: Counter[str] = Counter()
    # Largest-deficit assignment in seeded order -> exact target counts.
    remaining = dict(targets)
    for c in ordered:
        split_name = max(
            (n for n in names if remaining[n] > 0),
            key=lambda n: remaining[n],
        )
        assignment[c["sha"]] = split_name
        counts[split_name] += 1
        remaining[split_name] -= 1

    case_ids = [miner.make_case_id(c["sha"]) for c in selected]
    per_split: dict[str, dict[str, Any]] = {}
    for name in names:
        assigned = [assignment[c["sha"]] for c in selected]
        members = sorted(
            cid for cid, sn in zip(case_ids, assigned, strict=True) if sn == name
        )
        per_split[name] = {
            "count": len(members),
            "case_ids": members,
            "sha256": sha256_json(members),
        }

    split_freeze = {
        "schema_version": SCHEMA_VERSION,
        "miner_version": MINER_VERSION,
        "procedure": "metadata-only deterministic split freeze (M4A-2 protocol section 7)",
        "seed": seed,
        "ratio": dict(ratio),
        "target_counts": targets,
        "assignment": {miner.make_case_id(c["sha"]): assignment[c["sha"]] for c in selected},
        "per_split": per_split,
        "miner_dev_separate": True,
        "related_crossing_splits": False,
    }
    split_freeze["canonical_split_freeze_sha256"] = compute_canonical_split_freeze_hash(split_freeze)
    return split_freeze


def compute_canonical_split_freeze_hash(split_freeze: dict[str, Any]) -> str:
    payload = {k: v for k, v in split_freeze.items() if k != "canonical_split_freeze_sha256"}
    return sha256_json(payload)


# ---------------------------------------------------------------------------
# Scientific dataset build
# ---------------------------------------------------------------------------


def build_scientific_dataset(
    *,
    cache_dir: Path,
    anchor: str,
    dataset_dir: Path,
    created_utc: str,
    window: int = SCIENTIFIC_WINDOW,
    year_cap: int = YEAR_CAP,
    target_cases: int = TARGET_CASES,
    split_seed: int = SPLIT_SEED,
    miner_dev_targets: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """Build the M4A-2 scientific corpus + split freeze. ZERO API calls.

    Returns a summary dict with scan/exclusion/dedup/selection/split/build
    evidence. Materializes ``scientific/<case_id>/`` dirs, writes
    ``scientific_manifest.json`` and ``split_freeze.json`` under dataset_dir.
    """
    candidates, exclusion_counts = enumerate_scientific_candidates(
        cache_dir, anchor, window=window, miner_dev_targets=miner_dev_targets
    )
    kept, adjudication = deduplicate_candidates(candidates)
    selected = select_year_capped(kept, cap=year_cap, target=target_cases)
    split_freeze = freeze_splits(selected, seed=split_seed)

    scientific_dir = dataset_dir / "scientific"
    scientific_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for c in selected:
        case_id = miner.make_case_id(c["sha"])
        split_name = split_freeze["assignment"][case_id]
        split_freeze["canonical_split_freeze_sha256"]
        eligibility = dict(c["eligibility"])
        miner.build_case(
            cache_dir=cache_dir,
            case_id=case_id,
            target=c["sha"],
            parent=c["parent"],
            name_status=c["status"],
            eligibility=eligibility,
            output_dir=scientific_dir,
            created_utc=created_utc,
            partition_role="SCIENTIFIC",
            split=split_name,
        )
        case_manifest = json.loads(
            (scientific_dir / case_id / "case_manifest.json").read_text(encoding="utf-8")
        )
        records.append(case_manifest["record"])

    manifest: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "miner_version": MINER_VERSION,
        "dataset_version": "v1",
        "repository": "djangocms",
        "repository_url": REPOSITORY_URL_DJANGOCMS,
        "anchor_commit": anchor,
        "window": window,
        "split_seed": split_seed,
        "created_utc": created_utc,
        "case_ids": [miner.make_case_id(c["sha"]) for c in selected],
        "cases": records,
        "canonical_manifest_sha256": "",
    }
    manifest["canonical_manifest_sha256"] = compute_canonical_dataset_manifest_hash(manifest)
    manifest_path = dataset_dir / "scientific_manifest.json"
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")

    split_freeze_path = dataset_dir / "split_freeze.json"
    split_freeze_path.write_text(canonical_json(split_freeze), encoding="utf-8")

    return {
        "dataset_dir": dataset_dir,
        "manifest_path": manifest_path,
        "split_freeze_path": split_freeze_path,
        "scan_summary": {
            "window": window,
            "candidates_eligible": len(candidates),
            "exclusion_counts": exclusion_counts,
        },
        "dedup_summary": {
            "after_r1_r2": len(kept) + len([a for a in adjudication if a["rule"] == "R3_suspected_related"]),
            "after_r3": len(kept),
            "adjudication_count": len(adjudication),
        },
        "selection_summary": {
            "target": target_cases,
            "year_cap": year_cap,
            "selected": len(selected),
            "years": dict(sorted(Counter(c["year"] for c in selected).items())),
            "proxy_sizes": dict(sorted(Counter(c["proxy_count"] for c in selected).items())),
            "change_types": dict(sorted(Counter(c["change_type"] for c in selected).items())),
        },
        "split_summary": {
            name: per["count"] for name, per in split_freeze["per_split"].items()
        },
        "case_ids": [miner.make_case_id(c["sha"]) for c in selected],
        "cases": records,
        "adjudication": adjudication,
    }
