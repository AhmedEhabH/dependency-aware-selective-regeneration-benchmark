#!/usr/bin/env python3
"""WP-1b variance substudy scoring (15 tasks x 3 fresh replicates).

Run only after the variance prediction freeze is committed and its tag is on
origin (same AC-10 discipline as MAIN_297). Labels: opened RESERVE-300 proxies.

Usage:
  python scripts/wp1b_score_variance.py --run-dir research/wp1b/variance-15x3-2026-09-22 \
     --freeze-tag wp1b-variance-predictions-frozen-2026-09-22 \
     --main-run-dir research/wp1b/main-297-2026-09-22 \
     --out-json reports/wp1b_variance_15x3_result.json --out-md reports/WP1B_VARIANCE_15X3_RESULT.md

Exit: 0 scored | 1 integrity / AC-10 failure | 3 config error | 4 origin unreachable (retry later)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

from benchmark.wp1b import freeze as fz  # noqa: E402
from benchmark.wp1b import git_gate as gg  # noqa: E402
from benchmark.wp1b import main_scoring as ms  # noqa: E402
from benchmark.wp1b.label_guard import install_sealed_outcome_guard  # noqa: E402
from benchmark.wp1b.main_runner import read_jsonl_tolerant  # noqa: E402
from benchmark.wp1b.variance_scoring import score_variance  # noqa: E402

PROXIES = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--freeze-tag", required=True)
    ap.add_argument("--main-run-dir", type=Path, default=None)
    ap.add_argument("--out-json", required=True, type=Path)
    ap.add_argument("--out-md", required=True, type=Path)
    ap.add_argument("--skip-git-check", action="store_true", help="TESTS ONLY")
    args = ap.parse_args(argv)

    def _abs(p: Path) -> Path:
        return p if p.is_absolute() else _PROJECT_DIR / p

    run_dir = _abs(args.run_dir)
    freeze = run_dir / fz.FREEZE_FILE
    ms.verify_sha_sidecar(freeze, run_dir / (fz.FREEZE_FILE + ".sha256"))
    try:
        skip = gg.skip_allowed(args.skip_git_check)
    except gg.GitGateError as exc:
        print(f"[variance] ERROR: {exc}")
        return 3
    if not skip:
        try:
            gg.verify_tag_on_origin(_PROJECT_DIR, args.freeze_tag)
            gg.verify_file_in_tag(_PROJECT_DIR, args.freeze_tag, freeze)
        except gg.GitRemoteUnavailableError as exc:
            print(f"[variance] origin unreachable - retry later (no label loaded): {exc}")
            return 4
        except gg.GitGateError as exc:
            print(f"[variance] AC-10 FAILURE - STOP (no label loaded): {exc}")
            return 1
    install_sealed_outcome_guard(_PROJECT_DIR)
    per = json.loads(freeze.read_text(encoding="utf-8"))["per_task"]
    tel_rows, _ = read_jsonl_tolerant(run_dir / "wp1b_telemetry.jsonl")
    telemetry = {str(r.get("work_key")): r for r in tel_rows}
    main_preds = None
    if args.main_run_dir is not None:
        mdir = _abs(args.main_run_dir)
        agent = ms.load_agent_freeze(mdir / fz.FREEZE_FILE, mdir / (fz.FREEZE_FILE + ".sha256"))
        main_preds = dict(agent.predictions)
    labels = ms.load_opened_proxies(PROXIES)
    res = score_variance(per, labels, telemetry=telemetry, main_predictions=main_preds)
    res["freeze_tag"] = args.freeze_tag
    out_json, out_md = _abs(args.out_json), _abs(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    lines = [
        "# WP-1b variance substudy (15 tasks x 3 fresh replicates)\n",
        f"- pooled F1 by replicate: {res['aggregate_pooled_f1_by_replicate']} "
        f"(range {res['aggregate_pooled_f1_range']:.4f})",
        f"- mean per-task F1 range across replicates: {res['per_task_f1_mean_of_ranges']:.4f}",
        f"- selected-set exact match (pairwise): {res['selected_set_exact_match_rate_pairwise']:.3f}; "
        f"all-3-identical: {res['selected_set_all_replicates_identical_rate']:.3f}; "
        f"mean pairwise Jaccard: {res['selected_set_mean_pairwise_jaccard']:.3f}",
        f"- EMPTY runs: {res['empty_frequency']} / {res['n_runs']}; truncation EMPTY: "
        f"{res['final_answer_truncation_frequency']}; cap hits: {res['cap_hit_frequency']}",
        f"- {res['interpretation_boundary']}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[variance] pooled F1 by replicate {res['aggregate_pooled_f1_by_replicate']}; "
          f"pairwise exact match {res['selected_set_exact_match_rate_pairwise']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
