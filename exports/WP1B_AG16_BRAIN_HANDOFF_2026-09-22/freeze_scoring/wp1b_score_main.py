#!/usr/bin/env python3
"""WP-1b MAIN_297 scoring - AC-10 gated (freeze tag must exist locally AND on origin).

Order enforced here (fail-closed):
 1. the agent prediction freeze matches its .sha256 sidecar;
 2. the freeze tag exists locally, is on origin, and ``git show <tag>:<freeze>``
    is byte-identical to the working-tree freeze (predictions were tagged
    before any label load);
 3. the scoring-side sealed-outcome guard is installed (the 786 sealed RESERVE
    outcomes can never be opened by this process);
 4. SIP / RM-CSS frozen predictions match their sidecar;
 5. the frozen scorer reproduces the authoritative RESERVE-300 values EXACTLY;
 6. ONLY THEN the opened RESERVE-300 proxies are used to score the 297 tasks
    (or the nested MAIN_50 fallback after a budget abort).

Usage:
  python scripts/wp1b_score_main.py --run-dir research/wp1b/main-297-2026-09-22 \
      --freeze-tag wp1b-main297-predictions-frozen-2026-09-22 \
      --out-json reports/wp1b_main297_result.json --out-md reports/WP1B_MAIN297_RESULT.md \
      --out-tex paper/wp1b_tables/wp1b_main297_table.tex

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

from benchmark.wp1b import freeze as fz  # noqa: E402
from benchmark.wp1b import git_gate as gg  # noqa: E402
from benchmark.wp1b import main_scoring as ms  # noqa: E402
from benchmark.wp1b.label_guard import install_sealed_outcome_guard  # noqa: E402
from benchmark.wp1b.report_render import render_latex_table, render_markdown  # noqa: E402

SIP_RMCSS = _PROJECT_DIR / "research" / "wp1a" / "sip_rmcss_per_task_predictions.json"
PROXIES = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_proxies.json"
SIP_RECORDS = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "sip_300_run_records.jsonl"
EFFICIENCY = _PROJECT_DIR / "research" / "saleor-reserve-300-rmcss" / "saleor_reserve_300_efficiency.json"
MAIN297 = _PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json"


def verify_freeze_tag(tag: str, freeze_path: Path) -> dict[str, str]:
    """AC-10: the freeze tag is on origin (same object as local) and holds this freeze."""
    info = gg.verify_tag_on_origin(_PROJECT_DIR, tag)
    freeze_sha = gg.verify_file_in_tag(_PROJECT_DIR, tag, freeze_path)
    return {"tag": tag, "commit": info["commit"], "tag_object": info["tag_object"],
            "remote_object": info["remote_object"], "freeze_sha256": freeze_sha}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--freeze-tag", required=True)
    ap.add_argument("--out-json", required=True, type=Path)
    ap.add_argument("--out-md", required=True, type=Path)
    ap.add_argument("--out-tex", type=Path, default=None)
    ap.add_argument("--skip-git-check", action="store_true", help="TESTS ONLY - never for the real run")
    args = ap.parse_args(argv)

    run_dir: Path = args.run_dir if args.run_dir.is_absolute() else _PROJECT_DIR / args.run_dir
    freeze_path = run_dir / fz.FREEZE_FILE
    sidecar = run_dir / (fz.FREEZE_FILE + ".sha256")
    try:
        agent = ms.load_agent_freeze(freeze_path, sidecar)
    except (ms.FreezeIntegrityError, FileNotFoundError) as exc:
        print(f"[score] FREEZE INTEGRITY FAILURE - STOP: {exc}")
        return 1
    try:
        skip = gg.skip_allowed(args.skip_git_check)
    except gg.GitGateError as exc:
        print(f"[score] ERROR: {exc}")
        return 3
    if skip:
        tag_info = {"tag": args.freeze_tag, "note": "git check skipped (tests only)"}
    else:
        try:
            tag_info = verify_freeze_tag(args.freeze_tag, freeze_path)
        except gg.GitRemoteUnavailableError as exc:
            print(f"[score] origin unreachable - retry later (no label was loaded): {exc}")
            return 4
        except gg.GitGateError as exc:
            print(f"[score] AC-10 FAILURE - STOP (no label was loaded): {exc}")
            return 1

    install_sealed_outcome_guard(_PROJECT_DIR)

    manifest_ids = json.loads(MAIN297.read_text(encoding="utf-8"))["task_ids"]
    scope = str(agent.meta.get("analysis_scope"))
    if scope == "MAIN_297":
        ids = list(manifest_ids)
        label = "PRIMARY_MAIN_297"
    elif scope == "MAIN_50_UNDERPOWERED_FALLBACK":
        ids = list(manifest_ids[:50])
        label = "MAIN_50_UNDERPOWERED_FALLBACK (never the primary claim)"
    else:
        print(f"[score] ERROR: unexpected freeze scope {scope!r}")
        return 3
    if list(agent.task_ids) != ids:
        print("[score] ERROR: freeze task IDs differ from the frozen manifest order")
        return 1
    # score_main bootstraps over SORTED IDs (wp1a convention); the manifest is sorted too.

    sip, rmcss = ms.load_sip_rmcss(SIP_RMCSS, SIP_RMCSS.with_suffix(".sha256"))
    labels = ms.load_opened_proxies(PROXIES)  # opened RESERVE-300 proxies only
    try:
        sanity = ms.verify_authoritative(sip, rmcss, labels)
    except ms.ScorerDriftError as exc:
        print(f"[score] SCORER DRIFT - STOP: {exc}")
        return 1

    res = ms.score_main(agent=agent, sip=sip, rmcss=rmcss, labels=labels,
                        sip_cost=ms.load_sip_cost(SIP_RECORDS), emb=ms.load_embedding_cost(EFFICIENCY),
                        task_ids=ids, analysis_label=label)
    res["scorer_sanity_reserve300"] = sanity
    res["prediction_freeze"] = tag_info
    run_summary = agent.meta.get("run_summary", {}) or {}
    res["run_summary"] = run_summary
    out_json: Path = args.out_json if args.out_json.is_absolute() else _PROJECT_DIR / args.out_json
    out_md: Path = args.out_md if args.out_md.is_absolute() else _PROJECT_DIR / args.out_md
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(res, freeze_tag=args.freeze_tag,
                                      freeze_sha256=str(tag_info.get("freeze_sha256", "")),
                                      run_summary=run_summary), encoding="utf-8")
    if args.out_tex is not None:
        out_tex: Path = args.out_tex if args.out_tex.is_absolute() else _PROJECT_DIR / args.out_tex
        out_tex.parent.mkdir(parents=True, exist_ok=True)
        out_tex.write_text(render_latex_table(res), encoding="utf-8")
    p = res["P_primary_fail_closed"]
    print(f"[score] {label}: verdict={res['quality_verdict']['verdict']} category={res['final_category']}")
    print(f"[score] D={p['point']:+.4f} [{p['q025']:+.4f},{p['q975']:+.4f}] Q5={p['q05']:+.4f} "
          f"cheaper={res['cheaper_view_A']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
