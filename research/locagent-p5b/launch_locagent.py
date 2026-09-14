"""P5-B/P5-C compatibility launch layer for the pinned upstream LocAgent.

This is a LAUNCH/CONFIG compatibility layer, NOT an algorithm change.

It exists for one reason: the pinned upstream ``auto_search_main.py``
(commit 4935b557326c154bad8e8dcf3747cc8d32d1f387) restricts ``--model`` to an
argparse ``choices`` list that does NOT contain the already-verified
``openrouter/qwen/qwen3-coder`` route. Per the frozen P0_TO_P5 §P5 policy we do
NOT edit the upstream source; instead we construct the exact argparse namespace
``main()`` would produce and invoke the upstream ``localize()`` / ``merge()``
functions directly.

The wrapper does NOT change:
- prompts / task instruction (get_task_instruction)
- graph traversal (build_graph / RepoEntitySearcher)
- BM25 logic (bm25_module_retrieve / bm25_content_retrieve)
- ranking method (mrr) / iteration budget (max_attempt_num)
- output semantics (found_files / merged ranked files)
- temperature (upstream hard-codes temp=1 in run_localize)

Environment contract (set by the WSL launcher, not by this file):
- OPENROUTER_API_KEY  (transient WSLENV/stdin bridge; never printed/persisted)
- GRAPH_INDEX_DIR     (e.g. ~/p5/indexes/graph)
- BM25_INDEX_DIR      (e.g. ~/p5/indexes/bm25)

Usage (inside WSL, from the upstream repo root):
    python launch_locagent.py --upstream_dir <repo> --dataset <hf_dir> \
        --output_folder <out> --eval_n_limit 6 --num_processes 1
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

LOCAGENT_PINNED_COMMIT = "4935b557326c154bad8e8dcf3747cc8d32d1f387"
FROZEN_MODEL_ROUTE = "openrouter/qwen/qwen3-coder"
WRAPPER_VERSION = "locagent-compat-launch-layer-1"

# torch.multiprocessing.spawn requires the target function to be reachable as
# an attribute of the main module in the child (it re-imports __main__ and
# looks up fn.__name__). auto_search_main.run_localize is that function.
# The launcher MUST set PYTHONPATH to include the upstream repo root so this
# import (and the spawn child's re-import of this module) resolves.
from auto_search_main import localize, merge, run_localize  # noqa: E402,F401


def build_args(raw: argparse.Namespace) -> argparse.Namespace:
    """Construct the namespace ``main()`` would have produced."""
    args = argparse.Namespace(
        localize=True,
        merge=raw.merge,
        use_example=False,
        ranking_method=raw.ranking_method,
        dataset=raw.dataset,
        split=raw.split,
        eval_n_limit=raw.eval_n_limit,
        used_list="selected_ids",
        output_folder=raw.output_folder,
        output_file="loc_outputs.jsonl",
        merge_file="merged_loc_outputs.jsonl",
        model=FROZEN_MODEL_ROUTE,
        use_function_calling=True,
        simple_desc=False,
        max_attempt_num=raw.max_attempt_num,
        num_samples=raw.num_samples,
        num_processes=raw.num_processes,
        log_level=raw.log_level,
        timeout=raw.timeout,
        rerun_empty_location=False,
    )
    return args


def run() -> None:
    parser = argparse.ArgumentParser(
        description="P5 compatibility launch layer for pinned upstream LocAgent"
    )
    parser.add_argument("--upstream_dir", type=str, required=True)
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--output_folder", type=str, required=True)
    parser.add_argument("--split", type=str, default="train")
    parser.add_argument("--eval_n_limit", type=int, default=0)
    parser.add_argument("--ranking_method", type=str, default="mrr",
                        choices=["mrr", "majority"])
    parser.add_argument("--max_attempt_num", type=int, default=1)
    parser.add_argument("--num_samples", type=int, default=1)
    parser.add_argument("--num_processes", type=int, default=1)
    parser.add_argument("--log_level", type=str, default="INFO")
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--merge", action="store_true")
    raw = parser.parse_args()

    upstream_dir = os.path.abspath(raw.upstream_dir)
    sys.path.insert(0, upstream_dir)
    sys.path.insert(0, os.path.join(upstream_dir, ".."))
    os.chdir(upstream_dir)

    args = build_args(raw)
    args.output_file = os.path.join(args.output_folder, args.output_file)
    os.makedirs(args.output_folder, exist_ok=True)

    with open(f"{args.output_folder}/args.json", "w") as f:
        json.dump(vars(args), f, indent=4)

    logging.basicConfig(
        level=logging.getLevelName(args.log_level),
        format="%(asctime)s %(filename)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(f"{args.output_folder}/localize.log"),
            logging.StreamHandler(),
        ],
    )

    manifest = {
        "compat_wrapper_version": WRAPPER_VERSION,
        "upstream_pinned_commit": LOCAGENT_PINNED_COMMIT,
        "model": FROZEN_MODEL_ROUTE,
        "graph_index_dir": os.environ.get("GRAPH_INDEX_DIR"),
        "bm25_index_dir": os.environ.get("BM25_INDEX_DIR"),
    }
    with open(f"{args.output_folder}/wrapper_manifest.json", "w") as f:
        json.dump(manifest, f, indent=4)

    if args.localize:
        localize(args)

    if args.merge:
        merge(args)


if __name__ == "__main__":
    run()
