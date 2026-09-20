#!/usr/bin/env python3
"""ISSUE_GROUNDED_INTENT_HEADROOM - deep-dense-miss rescue + history arm (T3).

Section 13 (deep-dense-miss rescue): use the frozen V1/V2 deep-dense-miss
definition (proxy positive that remains a V1 false negative AND is outside the
V1 frozen candidate universe = Sparse UNION dense-top20). For deep misses that
belong to the PRIMARY paired population, report message dense rank, issue
dense rank, counts entering top1/3/5/10/20, and IssueDeepFNRescue@20.

Section 14 (historical episode retrieval arm): reuse the frozen parent-only
historical episode corpus + BM25 (top-10). MIL query = commit message; IIL
query = issue title/body. Report episode retrieval relevance to proxy target
files, DeepFNRecovery via retrieved episodes, useful historical files, and
candidate precision. NO model fitting.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

import pandas as pd  # noqa: E402

from benchmark.issue_grounded.corpus import load_corpus  # noqa: E402
from benchmark.issue_grounded.dense import arm_i_queries  # noqa: E402
from benchmark.memory_rescue.episodic import episode_signals  # noqa: E402
from benchmark.memory_rescue.history import RepoHistory, TaskHistory  # noqa: E402
from benchmark.recall.data import load_dev_tasks  # noqa: E402

OUT_DIR = _PROJECT_DIR / "research" / "issue-grounded-intent-headroom"
V1_FINALS = _PROJECT_DIR / "research" / "calibrated-set-selection-v1" / "final_oof_predictions_A.json"
V1_UNIVERSE = _PROJECT_DIR / "research" / "calibrated-set-selection-v1" / "candidate_universe_A.parquet"
QWEN_DIR = _PROJECT_DIR / "research" / "contamination-bridge" / "qwen_embed"


def load_v1_deep_misses() -> dict[str, list[tuple[str, str]]]:
    """{repo: [(case_id, path)]} frozen deep dense misses."""
    finals = json.loads(V1_FINALS.read_text(encoding="utf-8"))
    univ = pd.read_parquet(V1_UNIVERSE)
    cand_by_task = univ.groupby("case_id")["file_path"].apply(set).to_dict()
    ranks = pd.read_parquet(QWEN_DIR / "realization_A" / "full_file_scores.parquet")
    rank_map = {(r.case_id, r.file_path): int(r.dense_rank) for r in ranks.itertuples(index=False)}
    tasks = load_dev_tasks()
    out: dict[str, list[tuple[str, str]]] = {"djangocms": [], "saleor": []}
    for t in tasks:
        sel = set(finals.get(t.case_id, []))
        cand = cand_by_task.get(t.case_id, set())
        for p in t.proxy:
            if p in sel or p in cand:
                continue
            if (t.case_id, p) in rank_map:
                out[t.repository].append((t.case_id, p))
    return out


def main() -> int:
    corpus = load_corpus(OUT_DIR / "issue_corpus.json")
    clean_ids = {
        r["case_id"] for r in corpus["records"]
        if any(f == "TEMPORALLY_CLEAN" for f in r["temporal_flag"])
    }
    arm_i = json.loads((OUT_DIR / "arm_i_dense.json").read_text(encoding="utf-8"))["tasks"]
    tasks = load_dev_tasks()
    {t.case_id: t for t in tasks}
    message_ranks = pd.read_parquet(QWEN_DIR / "realization_A" / "full_file_scores.parquet")
    msg_rank_map = {(r.case_id, r.file_path): int(r.dense_rank)
                    for r in message_ranks.itertuples(index=False)}

    deep = load_v1_deep_misses()
    print("[deepmiss] deep dense miss counts (frozen definition):",
          {r: len(v) for r, v in deep.items()})

    # ---- Section 13: deep-dense-miss rescue within PRIMARY clean population ----
    rescue = {}
    for repo in ("djangocms", "saleor"):
        eligible = [(cid, p) for cid, p in deep[repo] if cid in clean_ids]
        rows = []
        n_top = {1: 0, 3: 0, 5: 0, 10: 0, 20: 0}
        for cid, p in eligible:
            m_rank = msg_rank_map.get((cid, p))
            i_rank = None
            if cid in arm_i:
                i_rank = arm_i[cid]["A"]["proxy_dense_rank"].get(p) or arm_i[cid]["A"].get("dense_rank", {}).get(p)
            rows.append({"case_id": cid, "path": p,
                         "message_dense_rank": m_rank, "issue_dense_rank": i_rank})
            if i_rank is not None:
                for k in n_top:
                    if i_rank <= k:
                        n_top[k] += 1
        denom = len(eligible)
        out = {
            "n_deep_misses_eligible": denom,
            "deep_misses_in_primary_population": rows,
            "entering_top": n_top,
            "counts_by_message_rank_bin": _rank_bins([r["message_dense_rank"] for r in rows]),
        }
        out["IssueDeepFNRescue@20"] = (n_top[20] / denom) if denom else 0.0
        rescue[repo] = out
        print(f"[deepmiss] {repo}: eligible={denom}, rescue@20={out['IssueDeepFNRescue@20']:.4f}, "
              f"top={n_top}")

    # ---- Section 14: historical episode retrieval arm ----
    history_out = {}
    queries = arm_i_queries(list(clean_ids), OUT_DIR / "issue_corpus.json")
    for repo in ("djangocms", "saleor"):
        repo_tasks = [t for t in tasks if t.repository == repo and t.case_id in clean_ids]
        if not repo_tasks:
            history_out[repo] = {"n_tasks": 0}
            continue
        rh = RepoHistory(repo)
        ep_m_agg = {"useful_hist_files_n": 0, "episode_files_n": 0,
                    "proxy_hits_episode": 0, "deep_in_episode": 0,
                    "tasks_with_episodes": 0, "n_tasks": len(repo_tasks)}
        ep_i_agg = dict(ep_m_agg)
        deep_set = set(deep[repo])
        for t in repo_tasks:
            universe = set(t.universe_records)
            th = TaskHistory(rh, t.parent_commit, universe)
            episode_records = [
                {"sha": rec.sha, "subject": rec.subject, "body": rec.body,
                 "paths": rec.paths} for rec in th.commits.values()
            ]
            if not episode_records:
                continue
            for _tag, query, agg in (("M", t.intent_text, ep_m_agg),
                                    ("I", queries.get(t.case_id), ep_i_agg)):
                if not query:
                    continue
                ep = episode_signals(episode_records, query)
                if ep:
                    agg["tasks_with_episodes"] += 1
                # episodic candidate set: top-10 non-sparse files by similarity
                sparse = set(t.write_set)
                scored = [(ep[f]["episode_similarity"], f) for f in universe
                          if f not in sparse and ep.get(f, {}).get("episode_similarity", 0.0) > 0.0]
                scored.sort(key=lambda x: (-x[0], x[1]))
                cand = [f for _, f in scored[:10]]
                agg["episode_files_n"] += len(cand)
                for f in cand:
                    if f in t.proxy:
                        agg["proxy_hits_episode"] += 1
                    if (t.case_id, f) in deep_set:
                        agg["deep_in_episode"] += 1
                ep_adds = [f for f in cand if f in t.proxy and f not in sparse]
                if ep_adds:
                    agg["useful_hist_files_n"] += 1
        history_out[repo] = {"arm_m": ep_m_agg, "arm_i": ep_i_agg,
                             "deepmisses_total": len(deep[repo]),
                             "deepmisses_in_clean_pop": sum(1 for c, _ in deep[repo] if c in clean_ids)}
        for arm in ("arm_m", "arm_i"):
            a = history_out[repo][arm]
            a["candidate_precision"] = round(
                (a["proxy_hits_episode"] / a["episode_files_n"]) if a["episode_files_n"] else 0.0, 6)
        print(f"[history] {repo}: M eps-cand {history_out[repo]['arm_m']['episode_files_n']} "
              f"prec {history_out[repo]['arm_m']['candidate_precision']} | "
              f"I eps-cand {history_out[repo]['arm_i']['episode_files_n']} "
              f"prec {history_out[repo]['arm_i']['candidate_precision']}")

    payload = {"deep_dense_miss_rescue": rescue, "history_arm": history_out}
    (OUT_DIR / "headroom_extended.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print("[extended] DONE")
    return 0


def _rank_bins(ranks: list[int | None]) -> dict[str, int]:
    b = {"<=5": 0, "6-20": 0, ">20": 0, "None": 0}
    for r in ranks:
        if r is None:
            b["None"] += 1
        elif r <= 5:
            b["<=5"] += 1
        elif r <= 20:
            b["6-20"] += 1
        else:
            b[">20"] += 1
    return b


if __name__ == "__main__":
    raise SystemExit(main())
