#!/usr/bin/env python3
"""ISSUE_GROUNDED_INTENT_HEADROOM - path mentions + length analysis (T3).

Section 15 (path-mention sensitivity, descriptive): for each clean issue text,
detect literal mentions of exact file paths / basenames / module identifiers
that match a proxy-changed target file. Report separately A (text contains an
exact/basename target-file mention) and B (without). Do NOT delete tasks.

Section 16 (intent length): frozen buckets <=6 / 7-15 / >15 words for commit
messages + issue text word/token lengths. Descriptive only.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import Counter
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.issue_grounded.corpus import load_corpus  # noqa: E402
from benchmark.issue_grounded.dense import arm_i_queries  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "issue-grounded-intent-headroom"


def _basename(path: str) -> str:
    return Path(path.replace("\\", "/")).name


def detect_path_mentions(issue_text: str, proxy_files: list[str]) -> dict:
    """Deterministic literal-mention detection for proxy target files.

    Returns counts over: exact path, basename, module dir (longest module
    prefix present in the text). Basenames below a 4-char threshold are
    excluded to reduce false positives on common tokens.
    """
    exact = [p for p in proxy_files if p in issue_text]
    bases = []
    for p in proxy_files:
        b = _basename(p)
        if len(b) >= 4 and b in issue_text:
            bases.append(p)
    modules = []
    for p in proxy_files:
        parts = p.split("/")
        for i in range(len(parts), 1, -1):
            prefix = "/".join(parts[:i])
            if prefix in issue_text:
                modules.append(p)
                break
    return {
        "exact_path": sorted(exact),
        "basename": sorted(bases),
        "module": sorted(modules),
        "any_mention": sorted(set(exact) | set(bases) | set(modules)),
    }


def main() -> int:
    corpus = load_corpus(OUT_DIR / "issue_corpus.json")
    clean_ids = {
        r["case_id"] for r in corpus["records"]
        if any(f == "TEMPORALLY_CLEAN" for f in r["temporal_flag"])
    }
    queries = arm_i_queries(list(clean_ids), OUT_DIR / "issue_corpus.json")
    tasks = load_dev_tasks()
    proxy_by_id = {t.case_id: sorted(t.proxy) for t in tasks}

    # ---- path mentions ----
    mention_stats: dict[str, dict] = {"with_mention": [], "without_mention": []}
    for cid, q in sorted(queries.items()):
        proxy = proxy_by_id.get(cid, [])
        det = detect_path_mentions(q, proxy)
        if det["any_mention"]:
            mention_stats["with_mention"].append({"case_id": cid, "detection": det})
        else:
            mention_stats["without_mention"].append({"case_id": cid})
    n_with = len(mention_stats["with_mention"])
    n_without = len(mention_stats["without_mention"])
    with_ids = [m["case_id"] for m in mention_stats["with_mention"]]
    wo_ids = [m["case_id"] for m in mention_stats["without_mention"]]
    print(f"[pathmentions] clean tasks with mention: {n_with}, without: {n_without} "
          f"(n={n_with + n_without})")

    # ---- intent length ----
    msg_buckets: Counter[str] = Counter()
    msg_words: list[int] = []
    issue_words: list[int] = []
    for t in tasks:
        wordlen = len(t.intent_text.split())
        msg_words.append(wordlen)
        msg_buckets["<=6" if wordlen <= 6 else ("7-15" if wordlen <= 15 else ">15")] += 1
    for q in queries.values():
        issue_words.append(len(q.split()))
    issue_buckets = Counter(
        "<=6" if wl <= 6 else ("7-15" if wl <= 15 else ">15") for wl in issue_words)
    print("[lengths] commit-message buckets:", dict(msg_buckets))
    print("[lengths] issue-text buckets:", dict(issue_buckets))
    print(f"[lengths] msg words median {statistics.median(msg_words)} mean "
          f"{statistics.mean(msg_words):.1f}; issue words median "
          f"{statistics.median(issue_words)} mean {statistics.mean(issue_words):.1f}")

    # short-intent subgroup: rank improvement (descriptive, non-gated)
    arm_i = json.loads((OUT_DIR / "arm_i_dense.json").read_text(encoding="utf-8"))["tasks"]
    import pandas as pd
    msg_rank = pd.read_parquet(
        _PROJECT_DIR / "research/contamination-bridge/qwen_embed/realization_A/full_file_scores.parquet")
    msg_map = {(r.case_id, r.file_path): int(r.dense_rank) for r in msg_rank.itertuples(index=False)}
    short_info = []
    for cid in sorted(queries):
        wordlen = len(next(t for t in tasks if t.case_id == cid).intent_text.split())
        if wordlen <= 6:
            proxy = proxy_by_id[cid]
            m = [msg_map.get((cid, p)) for p in proxy]
            i = [arm_i[cid]["A"]["proxy_dense_rank"].get(p) for p in proxy]
            m_med = statistics.median([x for x in m if x is not None]) if any(m) else None
            i_med = statistics.median([x for x in i if x is not None]) if any(i) else None
            short_info.append({"case_id": cid, "message_words": wordlen,
                               "message_median_rank": m_med, "issue_median_rank": i_med})
    print("[lengths] short-intent (<=6 words) clean tasks:", len(short_info))
    for s in short_info:
        print("   ", s)

    # path-mention subgroup pooled Recall@20 (descriptive; no task deletion)
    def rec20(ids: list[str], arm_key: str) -> float:
        hits = total = 0
        for cid in ids:
            proxy = proxy_by_id.get(cid, [])
            for p in proxy:
                rank = msg_map.get((cid, p)) if arm_key == "M" else arm_i[cid]["A"]["proxy_dense_rank"].get(p)
                if rank is None:
                    continue
                total += 1
                if rank <= 20:
                    hits += 1
        return hits / total if total else 0.0

    mention_recall = {
        "with_mention_ids": with_ids,
        "without_mention_ids": wo_ids,
        "with_mention_Recall20": {"message": round(rec20(with_ids, "M"), 6),
                                  "issue": round(rec20(with_ids, "I"), 6)},
        "without_mention_Recall20": {"message": round(rec20(wo_ids, "M"), 6),
                                     "issue": round(rec20(wo_ids, "I"), 6)},
    }
    print("[pathmentions] with-mention R20 M/I:",
          mention_recall["with_mention_Recall20"])
    print("[pathmentions] without-mention R20 M/I:",
          mention_recall["without_mention_Recall20"])

    payload = {
        "path_mentions": {"n_tasks": n_with + n_without, "with_mention": n_with,
                          "without_mention": n_without,
                          "mention_examples": [m for m in mention_stats["with_mention"][:8]],
                          "mention_subgroup": mention_recall},
        "intent_length": {
            "commit_message_buckets": dict(msg_buckets),
            "issue_text_buckets": dict(issue_buckets),
            "commit_message_words": {"median": statistics.median(msg_words),
                                     "mean": round(statistics.mean(msg_words), 2)},
            "issue_text_words": {"median": statistics.median(issue_words),
                                 "mean": round(statistics.mean(issue_words), 2)},
            "short_intent_tasks": short_info,
        },
    }
    (OUT_DIR / "headroom_descriptive.json").write_text(
        json.dumps(payload, indent=1), encoding="utf-8")
    print("[descriptive] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
