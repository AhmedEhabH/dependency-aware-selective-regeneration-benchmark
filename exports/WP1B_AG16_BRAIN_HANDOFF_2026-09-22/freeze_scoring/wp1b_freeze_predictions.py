#!/usr/bin/env python3
"""WP-1b - freeze agent predictions (label-free) -> wp1b_agent_predictions.json + .sha256.

Run AFTER the MAIN_297 (or variance) run finished and BEFORE any label load.
Then commit the run directory, create + push the prediction-freeze tag, and
verify the remote tag (AC-10). Only then run scripts/wp1b_score_main.py.

Usage:
  python scripts/wp1b_freeze_predictions.py --kind main297  --run-dir research/wp1b/main-297-2026-09-22
  python scripts/wp1b_freeze_predictions.py --kind variance --run-dir research/wp1b/variance-15x3-2026-09-22
  (budget abort only)  ... --kind main297 --allow-main50-fallback

Exit: 0 frozen | 1 cannot freeze (incomplete / inconsistent run) | 3 config error
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.wp1b import freeze as fz  # noqa: E402
from benchmark.wp1b import main_runner as mr  # noqa: E402

MAIN297_MANIFEST = _PROJECT_DIR / "research" / "wp1b" / "wp1b_main_297_manifest.json"
VARIANCE_PREREG = _PROJECT_DIR / "artifacts" / "wp1b_variance_substudy_preregistration_2026-09-21.json"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", required=True, choices=("main297", "variance"))
    ap.add_argument("--run-dir", required=True, type=Path)
    ap.add_argument("--allow-main50-fallback", action="store_true")
    args = ap.parse_args(argv)
    run_dir: Path = args.run_dir if args.run_dir.is_absolute() else _PROJECT_DIR / args.run_dir
    if not run_dir.is_dir():
        print(f"[freeze] ERROR: {run_dir} is not a directory")
        return 3
    main_items = mr.load_main297_items(MAIN297_MANIFEST)
    items = main_items if args.kind == "main297" else mr.load_variance_items(
        VARIANCE_PREREG, [i.task_id for i in main_items])
    try:
        payload = fz.build_freeze(run_dir, items, kind=args.kind,
                                  allow_main50_fallback=bool(args.allow_main50_fallback))
    except fz.FreezeError as exc:
        print(f"[freeze] CANNOT FREEZE: {exc}")
        return 1
    path, digest = fz.write_freeze(run_dir, payload)
    print(f"[freeze] {payload['analysis_scope']}: n={payload['n']} empty={payload['empty_count']}")
    print(f"[freeze] wrote {path.relative_to(_PROJECT_DIR)}  sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
