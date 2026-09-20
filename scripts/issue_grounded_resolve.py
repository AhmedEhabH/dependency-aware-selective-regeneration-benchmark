#!/usr/bin/env python3
"""ISSUE_GROUNDED_INTENT_HEADROOM - resolve DEV commit-message references (T3).

For every DEVELOPMENT task (djangocms 174 + Saleor 149), parse `#NNNN`
references from the frozen commit-message intent and resolve them through the
GitHub API (issue vs PR; PR -> linked closing issue as dataset-construction
linkage ONLY). Applies the strict temporal rule and freezes the issue corpus
BEFORE any ranking evaluation.

Cost: GitHub REST/GraphQL reads only (free). Cached on disk; resume-safe.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.issue_grounded.corpus import build_corpus_record, save_corpus  # noqa: E402
from benchmark.issue_grounded.github import GitHubClient  # noqa: E402
from benchmark.issue_grounded.refs import TaskResolution, _ref_json, resolve_task  # noqa: E402
from benchmark.issue_grounded.temporal import CLEAN, temporal_status  # noqa: E402
from benchmark.recall.data import (  # noqa: E402
    SALEOR_DATASET,
    V1_DATASET,
    V2_DATASET,
    load_dev_tasks,
)

OUT_DIR = _PROJECT_DIR / "research" / "issue-grounded-intent-headroom"
CACHE_DIR = OUT_DIR
DATASETS = (V1_DATASET, V2_DATASET, SALEOR_DATASET)


def _case_manifest(cid: str, repo: str) -> dict:
    candidate_dirs = [V1_DATASET, V2_DATASET] if repo == "djangocms" else [SALEOR_DATASET]
    for ds in candidate_dirs:
        p = ds / "scientific" / cid / "case_manifest.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"no case_manifest for {cid}")


def _target_time(cid: str, repo: str) -> str:
    m = _case_manifest(cid, repo)
    return str(m["record"].get("target_commit_time") or "")


def _res_to_dict(r: TaskResolution) -> dict:
    return {
        "case_id": r.case_id,
        "repository": r.repository,
        "ref_numbers": list(r.ref_numbers),
        "provenance": r.provenance,
        "direct_issues": [_ref_json(x) for x in r.direct_issues],
        "linked_issues": [_ref_json(x) for x in r.linked_issues],
        "pr_without_linked": [_ref_json(x) for x in r.pr_without_linked],
        "unresolved": list(r.unresolved),
    }


def _save_resolutions(path: Path, dicts: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dicts, indent=1), encoding="utf-8")


def _load_resolutions(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    tasks = load_dev_tasks()
    print(f"[issue-grounded] DEV tasks: {len(tasks)}")
    client = GitHubClient(CACHE_DIR)

    out_path = OUT_DIR / "resolutions.json"
    done = _load_resolutions(out_path)
    done_by_id = {r["case_id"]: r for r in done}
    pending = [t for t in tasks if t.case_id not in done_by_id]
    print(f"[issue-grounded] already resolved: {len(done_by_id)}; pending: {len(pending)}")

    resolutions = [done_by_id[t.case_id] for t in tasks if t.case_id in done_by_id]
    for i, t in enumerate(pending):
        for attempt in range(6):
            try:
                res = resolve_task(client, t.case_id, t.repository, t.intent_text)
                resolutions.append(_res_to_dict(res))
                break
            except RuntimeError as exc:
                _save_resolutions(out_path, resolutions)
                if attempt == 5:
                    raise
                print(f"  network retry {attempt+1}/5 for {t.case_id}: {exc}")
        if (i + 1) % 25 == 0:
            print(f"  resolved {i+1}/{len(pending)} (total {len(resolutions)})")
    _save_resolutions(out_path, resolutions)
    print("[issue-grounded] resolutions saved:", len(resolutions))

    # ---- temporal validity + corpus freeze (from saved resolutions) ----
    all_res = _load_resolutions(out_path)
    records = []
    clean_repo: Counter[str] = Counter()
    prov_repo: Counter[str] = Counter()
    prov_counts: Counter[str] = Counter()
    for d in all_res:
        _res_to_dict(TaskResolution(
            case_id=d["case_id"], repository=d["repository"],
            ref_numbers=tuple(d["ref_numbers"]), provenance=d["provenance"],
            direct_issues=(), linked_issues=(), pr_without_linked=(),
            unresolved=tuple(d["unresolved"]), raw_refs=[]))
        # rebuild candidates from saved issue dicts
        candidates = [_issue_from_dict(x) for x in (*d["direct_issues"], *d["linked_issues"])]
        candidates = sorted({(x["number"], x["repository"], x["repo_name"]): x for x in candidates}.values(),
                            key=lambda x: x["number"])
        target = _target_time(d["case_id"], d["repository"])
        prov_counts[d["provenance"]] += 1
        prov_repo[f"{d['repository']}::{d['provenance']}"] += 1
        if not candidates:
            records.append(build_corpus_record(
                case_id=d["case_id"], repository=d["repository"], provenance=d["provenance"],
                issue_numbers=(), created_at=(), updated_at=(), titles=(), bodies=(),
                temporal_flags=(), target_commit_time=target))
            clean_repo[d["repository"] + "::no_candidate"] += 1
            continue
        numbers = tuple(x["number"] for x in candidates)
        created = tuple(x["created_at"] for x in candidates)
        updated = tuple(x["updated_at"] for x in candidates)
        titles = tuple(x["title"] for x in candidates)
        bodies = tuple(x["body"] for x in candidates)
        flags = tuple(temporal_status(c, u, target) for c, u in zip(created, updated, strict=True))
        n_clean = sum(1 for f in flags if f == CLEAN)
        clean_repo[d["repository"] + f"::clean={n_clean}"] += 1
        records.append(build_corpus_record(
            case_id=d["case_id"], repository=d["repository"], provenance=d["provenance"],
            issue_numbers=numbers, created_at=created, updated_at=updated,
            titles=titles, bodies=bodies, temporal_flags=flags,
            target_commit_time=target))

    manifest = save_corpus(OUT_DIR / "issue_corpus.json", records)
    print("[issue-grounded] corpus:", json.dumps(manifest))
    print("[issue-grounded] provenance:", dict(prov_counts))
    print("[issue-grounded] provenance by repo:", dict(prov_repo))
    print("[issue-grounded] temporal-clean by repo:")
    for k, v in sorted(clean_repo.items()):
        print(f"  {k}: {v}")

    summary = {
        "n_tasks": len(all_res),
        "provenance_counts": dict(prov_counts),
        "provenance_by_repo": dict(prov_repo),
        "temporal_breakdown": dict(clean_repo),
        "corpus_manifest": manifest,
    }
    (OUT_DIR / "resolution_summary.json").write_text(
        json.dumps(summary, indent=1), encoding="utf-8")
    print("[issue-grounded] DONE")
    return 0


def _issue_from_dict(x: dict) -> dict:
    return {
        "number": int(x["number"]), "kind": x.get("kind", "issue"),
        "title": x.get("title") or "", "body": x.get("body") or "",
        "created_at": x.get("created_at") or "", "updated_at": x.get("updated_at") or "",
        "repository": x.get("repository") or "", "repo_name": x.get("repo_name") or "",
    }


if __name__ == "__main__":
    raise SystemExit(main())
