#!/usr/bin/env python3
"""WP-1b MAIN_297 / variance-substudy / zero-API dry-run launcher.

Thin CLI over ``benchmark.wp1b.main_runner``. The frozen agent (protocol v3) is
used exactly as in Calibration-3c; this launcher only wires the frozen inputs,
the resilient accounting backend and the label-access guard.

Kinds:
  main297   paid; the frozen 297 IDs in manifest order; ceiling <= $21.50
  variance  paid; the preregistered 15 tasks x 3 fresh replicates; ceiling <= $3.50
  dry_run   ZERO API; stub backend; exercises materialization / universe /
            prompt construction for every MAIN_297 task (or --limit N)

Usage (PowerShell, from the project root):
  python scripts/wp1b_main_run.py --kind dry_run  --out-dir <scratch>\\wp1b-dry-run --resume
  python scripts/wp1b_main_run.py --kind main297  --out-dir research/wp1b/main-297-2026-09-22 --resume --max-items 60 \
      --require-tag wp1b-main297-harness-prereg-2026-09-22
  (repeat the same command until progress.json status == COMPLETE; --resume on an empty dir starts fresh)
  python scripts/wp1b_main_run.py --kind variance --out-dir research/wp1b/variance-15x3-2026-09-22 --resume \
      --require-tag wp1b-main297-harness-prereg-2026-09-22

Paid kinds REQUIRE --require-tag: the tag must point at the same object locally
and on origin (AC-4), and the working tree must equal the tag for the harness,
agent, scripts and preregistration files (no untagged code can spend money).

Pricing preflight (zero-token metadata call, no key):
  fresh run   : metadata unreachable -> exit 4 (retry later); route missing or
                list-price drift -> exit 3 (STOP)
  resume      : metadata unreachable -> continue (recorded); route missing ->
                exit 4 (resumable); list-price drift -> recorded, continue (the
                frozen list prices govern all accounting; drift is reported)

Exit codes: 0 complete / chunk done | 2 budget abort | 3 config error (STOP) |
4 infra halt (resumable) | 5 instrument halt (STOP, report) | 6 crash halt (see
halt_report.json) | 7 locked (another live runner holds run.lock; do NOT start a second one)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.strategies.iterative_agent import (  # noqa: E402
    IterativeRepositoryAgentStrategy,
)
from benchmark.wp1b import git_gate as gg  # noqa: E402
from benchmark.wp1b import main_runner as mr  # noqa: E402
from benchmark.wp1b.label_guard import install_label_access_guard  # noqa: E402
from benchmark.wp1b.resilient_backend import (  # noqa: E402
    ResilientAccountingBackend,
    SpendLedger,
)

RESEARCH = _PROJECT_DIR / "research"
MAIN297_MANIFEST = RESEARCH / "wp1b" / "wp1b_main_297_manifest.json"
PROTOCOL_V3 = RESEARCH / "wp1b" / "wp1b_frozen_agent_protocol_v3.json"
BUDGET_V2 = RESEARCH / "wp1b" / "wp1b_budget_model_v2.json"
VARIANCE_PREREG = _PROJECT_DIR / "artifacts" / "wp1b_variance_substudy_preregistration_2026-09-21.json"
SALEOR_SCIENTIFIC = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
SALEOR_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"

FROZEN_CEILINGS = {"main297": 21.50, "variance": 3.50, "dry_run": 1.00}
CODE_FILES = (
    "src/benchmark/strategies/iterative_agent.py",
    "src/benchmark/strategies/repository_tools.py",
    "src/benchmark/wp1b/telemetry.py",
    "src/benchmark/wp1b/main_runner.py",
    "src/benchmark/wp1b/resilient_backend.py",
    "src/benchmark/wp1b/label_guard.py",
    "scripts/wp1b_main_run.py",
)
# Paths that must equal the harness/prereg tag before any paid call (AC-4).
TAGGED_PATHSPECS = (
    "src/benchmark",
    "scripts/wp1b_main_run.py",
    "scripts/saleor_portability_fix.py",
    "research/wp1b/wp1b_frozen_agent_protocol_v3.json",
    "research/wp1b/wp1b_main_297_manifest.json",
    "research/wp1b/wp1b_budget_model_v2.json",
    "research/wp1b/wp1b_decision_rules_v2.json",
    "research/wp1b/wp1b_exploratory_prereg_addendum_v2.json",
    "research/wp1b/wp1b_agent_budget_sensitivity_prereg.json",
    "artifacts/wp1b_variance_substudy_preregistration_2026-09-21.json",
)


def _worst_case() -> dict[str, float]:
    data = json.loads(BUDGET_V2.read_text(encoding="utf-8"))
    return {tid: float(v["worst_case_usd"]) for tid, v in data["worst_case_per_task"].items()}


def _pricing_preflight() -> tuple[bool, dict[str, object]]:
    """Zero-token OpenRouter metadata check (no key, no inference)."""
    sys.path.insert(0, str(_PROJECT_DIR / "scripts"))
    from wp1b_provider_pricing_preflight import (  # type: ignore[import-not-found]
        FROZEN_COMPLETION_PER_1M_USD,
        FROZEN_PROMPT_PER_1M_USD,
        _fetch_model_metadata,
    )

    payload, error = _fetch_model_metadata()
    record: dict[str, object] = {"artifact": "wp1b_main_pricing_preflight", "utc": mr.utc_now()}
    ok = False
    if payload is None:
        record.update({"live_metadata_available": False, "error": error, "no_drift": False})
        return ok, record
    deepinfra = payload.get("deepinfra") or {}
    pricing = deepinfra.get("pricing", {}) if isinstance(deepinfra, dict) else {}
    prompt = float(pricing.get("prompt", 0)) * 1e6
    completion = float(pricing.get("completion", 0)) * 1e6
    ok = (
        bool(deepinfra)
        and abs(prompt - FROZEN_PROMPT_PER_1M_USD) < 1e-9
        and abs(completion - FROZEN_COMPLETION_PER_1M_USD) < 1e-9
    )
    record.update({
        "live_metadata_available": True,
        "deepinfra_turbo_present": bool(deepinfra),
        "prompt_per_1m_usd": prompt,
        "completion_per_1m_usd": completion,
        "input_cache_read_per_1m_usd": float(pricing.get("input_cache_read", 0)) * 1e6,
        "endpoint_status": deepinfra.get("status") if isinstance(deepinfra, dict) else None,
        "no_drift": ok,
    })
    return ok, record


def _pricing_gate(out_dir: Path, extra: dict[str, object], *, skip: bool) -> int | None:
    """Fresh vs resume pricing policy (see module docstring). Returns an exit code or None."""
    fresh_record = out_dir / "pricing_preflight.json"
    resume = False
    if fresh_record.exists() and (out_dir / mr.STATE_FILE).exists():
        try:
            resume = bool(json.loads(fresh_record.read_text(encoding="utf-8")).get("no_drift"))
        except json.JSONDecodeError:
            resume = False
    target = "pricing_preflight_last_resume.json" if resume else "pricing_preflight.json"
    if skip:
        extra[target] = {"skipped": True, "utc": mr.utc_now(),
                         "reason": "--skip-pricing-preflight (Ahmed-approved)"}
        return None
    ok, record = _pricing_preflight()
    record["mode"] = "resume" if resume else "fresh"
    extra[target] = record
    live = bool(record.get("live_metadata_available"))
    route_present = bool(record.get("deepinfra_turbo_present"))
    if ok:
        return None
    if not resume:
        if not live:
            print(f"[main] pricing metadata unreachable before a FRESH paid run - retry later: {json.dumps(record)}")
            return mr.EXIT_INFRA_HALT
        print(f"[main] PRICING/ROUTE DRIFT before a fresh paid run - STOP: {json.dumps(record)}")
        return mr.EXIT_CONFIG_ERROR
    if not live:
        print("[main] warning: pricing metadata unreachable on resume; fresh-run preflight passed - continuing")
        return None
    if not route_present:
        print(f"[main] frozen route deepinfra/turbo missing on resume - resumable infra halt: {json.dumps(record)}")
        return mr.EXIT_INFRA_HALT
    print("[main] warning: list-price drift on resume (frozen list prices govern accounting; recorded) - continuing")
    return None


def _tag_gate(tag: str | None, kind: str) -> int | None:
    if kind == "dry_run":
        return None
    if not tag:
        print("[main] ERROR: paid kinds require --require-tag <harness/prereg tag> (AC-4)")
        return mr.EXIT_CONFIG_ERROR
    try:
        info = gg.verify_tag_on_origin(_PROJECT_DIR, tag)
        gg.verify_tree_matches_tag(_PROJECT_DIR, tag, TAGGED_PATHSPECS)
    except gg.GitRemoteUnavailableError as exc:
        print(f"[main] origin unreachable for the AC-4 tag check - retry later: {exc}")
        return mr.EXIT_INFRA_HALT
    except gg.GitGateError as exc:
        print(f"[main] AC-4 FAILURE - STOP (no paid call made): {exc}")
        return mr.EXIT_CONFIG_ERROR
    print(f"[main] AC-4 ok: {tag} -> {info['commit'][:12]} on origin; frozen paths equal the tag")
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", required=True, choices=sorted(FROZEN_CEILINGS))
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--ceiling-usd", type=float, default=None)
    ap.add_argument("--max-items", type=int, default=None,
                    help="process at most N pending items in THIS invocation (chunked execution; rerun with --resume)")
    ap.add_argument("--stop-file", type=Path, default=None,
                    help="if this file appears, halt cleanly before the next item (resumable)")
    ap.add_argument("--skip-pricing-preflight", action="store_true",
                    help="ONLY if the live metadata API is unreachable AND Ahmed approved it")
    ap.add_argument("--require-tag", default=None,
                    help="harness/prereg tag that must be on origin and equal the working tree (paid kinds)")
    args = ap.parse_args(argv)
    try:
        return _main(args)
    except (mr.ManifestError, mr.KnobDriftError, json.JSONDecodeError, KeyError, FileNotFoundError) as exc:
        print(f"[main] CONFIG ERROR - STOP (no paid call made): {type(exc).__name__}: {exc}")
        return mr.EXIT_CONFIG_ERROR


def _main(args: argparse.Namespace) -> int:

    kind: str = args.kind
    frozen_ceiling = FROZEN_CEILINGS[kind]
    ceiling = frozen_ceiling if args.ceiling_usd is None else float(args.ceiling_usd)
    if ceiling > frozen_ceiling:
        print(f"[main] ERROR: ceiling {ceiling} exceeds the frozen {kind} ceiling {frozen_ceiling}")
        return mr.EXIT_CONFIG_ERROR
    if args.max_items is not None and args.max_items <= 0:
        print("[main] ERROR: --max-items must be positive")
        return mr.EXIT_CONFIG_ERROR
    out_dir: Path = args.out_dir if args.out_dir.is_absolute() else (_PROJECT_DIR / args.out_dir)

    tag_code = _tag_gate(args.require_tag, kind)
    if tag_code is not None:
        return tag_code

    try:
        knobs = mr.verify_frozen_knobs(PROTOCOL_V3)
    except mr.KnobDriftError as exc:
        print(f"[main] KNOB DRIFT - STOP: {exc}")
        return mr.EXIT_CONFIG_ERROR

    main_items = mr.load_main297_items(MAIN297_MANIFEST)
    if kind == "variance":
        items = mr.load_variance_items(VARIANCE_PREREG, [it.task_id for it in main_items])
        manifest_sha = mr.file_sha256(VARIANCE_PREREG)
    else:
        items = main_items
        manifest_sha = mr.file_sha256(MAIN297_MANIFEST)

    if not SALEOR_CACHE.is_dir():
        print(f"[main] ERROR: Saleor repository cache missing: {SALEOR_CACHE}")
        return mr.EXIT_CONFIG_ERROR

    code_sha = {rel: mr.file_sha256(_PROJECT_DIR / rel) for rel in CODE_FILES}
    code_sha["protocol_v3"] = str(knobs.get("protocol_sha256", ""))

    extra: dict[str, object] = {"knob_check.json": knobs}
    if kind != "dry_run":
        code = _pricing_gate(out_dir, extra, skip=bool(args.skip_pricing_preflight))
        if code is not None:
            return code

    # From here on, the prediction process may not open any label-bearing file.
    install_label_access_guard(_PROJECT_DIR)

    from scripts.saleor_portability_fix import materialize_production_parent

    def _materialize(bundle: mr.TaskBundle, workspace: Path) -> None:
        materialize_production_parent(SALEOR_CACHE, bundle.parent_commit, workspace, roots=("saleor",))

    def _load(task_id: str) -> mr.TaskBundle:
        return mr.load_saleor_bundle(SALEOR_SCIENTIFIC, task_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = SpendLedger.open(out_dir / mr.LEDGER_FILE)
    if kind == "dry_run":
        inner: object = mr.DryRunStubBackend()
    else:
        from benchmark.llm.openrouter_backend import OpenRouterBackend

        inner = OpenRouterBackend(
            model=mr.FROZEN_MODEL,
            provider=mr.FROZEN_PROVIDER,
            api_key_env="OPENROUTER_API_KEY",
            timeout_seconds=120.0,
            max_transient_retries=0,  # the wrapper owns the frozen 3-retry budget
        )
    backend = ResilientAccountingBackend(inner, ledger=ledger, ceiling_usd=ceiling)  # type: ignore[arg-type]

    def _make_strategy(b: ResilientAccountingBackend) -> IterativeRepositoryAgentStrategy:
        return IterativeRepositoryAgentStrategy(backend=b, agent_control_max_completion_tokens=mr.FROZEN_AGENT_CAP)

    config = mr.RunnerConfig(
        run_label={"main297": "MAIN_297", "variance": "VARIANCE_15x3", "dry_run": "DRY_RUN"}[kind],
        kind=kind,
        out_dir=out_dir,
        ceiling_usd=ceiling,
        worst_case_usd=_worst_case(),
        items=items,
        manifest_sha256=manifest_sha,
        code_sha256=code_sha,
        resume=bool(args.resume),
        limit=args.max_items,
        stop_file=args.stop_file,
        extra_files=extra,
    )
    runner = mr.MainRunner(config, backend=backend, load_bundle=_load, materialize=_materialize,
                           make_strategy=_make_strategy)
    try:
        outcome = runner.run()
    except mr.ResumeError as exc:
        print(f"[main] RESUME ERROR - STOP: {exc}")
        return mr.EXIT_CONFIG_ERROR
    if outcome.exit_code == mr.EXIT_LOCKED:
        print(f"[main] LOCKED - another runner is live on this directory; do NOT start a second one: {outcome.detail}")
        return mr.EXIT_LOCKED
    print(f"[main] {outcome.status}: {outcome.detail} | {outcome.completed}/{outcome.total} "
          f"| ledger ${outcome.ledger_usd:.6f} / ceiling ${ceiling:.2f} | exit {outcome.exit_code}")
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
