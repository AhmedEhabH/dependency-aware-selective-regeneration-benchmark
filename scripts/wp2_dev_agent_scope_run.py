#!/usr/bin/env python3
"""WP-2 Mission-11 C2.4 - DEV Agent scope selection (AU6, ceiling <= $1.00).

Thin wrapper over benchmark.wp1b.main_runner (frozen protocol v3) that swaps
only the manifest (16 DEV_TRAIN_ENG union tasks), the bundles (built from the
same scientific dir), and the ceiling ($1.00). Everything else is identical to
wp1b_main_run.py: knobs, model/route, key usage, pricing preflight, resume,
stop file, require-tag gate. The label-access guard blocks evaluator_only.

Usage:
  python scripts/wp2_dev_agent_scope_run.py --require-tag wp2-dev-eng-agent-scope-freeze-<DATE> \
      --out-dir research/wp2/e2e_smoke_eng_v1/agent_dev_eng --resume --max-items N
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
DEV_MANIFEST = RESEARCH / "wp2" / "e2e_smoke_eng_v1" / "scopes" / "dev_eng_agent_manifest.json"
PROTOCOL_V3 = RESEARCH / "wp1b" / "wp1b_frozen_agent_protocol_v3.json"
BUDGET_V2 = RESEARCH / "wp1b" / "wp1b_budget_model_v2.json"
SALEOR_SCIENTIFIC = _PROJECT_DIR / "benchmark_data" / "real_commit_impact_saleor" / "scientific"
SALEOR_CACHE = _PROJECT_DIR / "dist" / "pilot-repo-cache" / "saleor"
EVALUATOR_ONLY = "research/wp2/harness_v3_2026-09-26/evaluator_only/"

CEILING_USD = 1.00
CODE_FILES = (
    "src/benchmark/strategies/iterative_agent.py",
    "src/benchmark/strategies/repository_tools.py",
    "src/benchmark/wp1b/telemetry.py",
    "src/benchmark/wp1b/main_runner.py",
    "src/benchmark/wp1b/resilient_backend.py",
    "src/benchmark/wp1b/label_guard.py",
    "scripts/wp1b_main_run.py",
)
TAGGED_PATHSPECS = (
    "src/benchmark",
    "scripts/wp1b_main_run.py",
    "scripts/saleor_portability_fix.py",
    "research/wp1b/wp1b_frozen_agent_protocol_v3.json",
    "research/wp1b/wp1b_budget_model_v2.json",
    "research/wp1b/wp1b_decision_rules_v2.json",
    "research/wp2/harness_v3_2026-09-26/evaluator_only/",
)


def _worst_case() -> dict[str, float]:
    data = json.loads((_PROJECT_DIR / "research/wp2/e2e_smoke_eng_v1/agent_dev_eng_budget.json").read_text(encoding="utf-8"))
    return {tid: float(v["worst_case_usd"]) for tid, v in data["worst_case_per_task"].items()}


def _pricing_preflight() -> tuple[bool, dict[str, object]]:
    sys.path.insert(0, str(_PROJECT_DIR / "scripts"))
    from wp1b_provider_pricing_preflight import (  # type: ignore[import-not-found]
        FROZEN_COMPLETION_PER_1M_USD,
        FROZEN_PROMPT_PER_1M_USD,
        _fetch_model_metadata,
    )
    payload, error = _fetch_model_metadata()
    record: dict[str, object] = {"artifact": "wp2_dev_agent_pricing_preflight", "utc": mr.utc_now()}
    if payload is None:
        record.update({"live_metadata_available": False, "error": error, "no_drift": False})
        return False, record
    deepinfra = payload.get("deepinfra") or {}
    pricing = deepinfra.get("pricing", {}) if isinstance(deepinfra, dict) else {}
    prompt = float(pricing.get("prompt", 0)) * 1e6
    completion = float(pricing.get("completion", 0)) * 1e6
    ok = bool(deepinfra) and abs(prompt - FROZEN_PROMPT_PER_1M_USD) < 1e-9 \
        and abs(completion - FROZEN_COMPLETION_PER_1M_USD) < 1e-9
    record.update({"live_metadata_available": True, "deepinfra_turbo_present": bool(deepinfra),
                   "prompt_per_1m_usd": prompt, "completion_per_1m_usd": completion,
                   "no_drift": ok})
    return ok, record


def _pricing_gate(out_dir: Path, extra: dict[str, object], *, skip: bool) -> int | None:
    resume = bool((out_dir / mr.STATE_FILE).exists())
    target = "pricing_preflight.json"
    if skip:
        extra[target] = {"reason": "--skip-pricing-preflight (Ahmed-approved)"}
        return None
    ok, record = _pricing_preflight()
    record["mode"] = "resume" if resume else "fresh"
    extra[target] = record
    live = bool(record.get("live_metadata_available"))
    if ok:
        return None
    if not resume:
        if not live:
            print("[dev-agent] pricing metadata unreachable before a FRESH paid run - retry later")
            return mr.EXIT_INFRA_HALT
        print("[dev-agent] PRICING/ROUTE DRIFT before a fresh paid run - STOP")
        return mr.EXIT_CONFIG_ERROR
    return None


def _tag_gate(tag: str | None) -> int | None:
    if not tag:
        print("[dev-agent] ERROR: paid run requires --require-tag (AC-4)")
        return mr.EXIT_CONFIG_ERROR
    try:
        info = gg.verify_tag_on_origin(_PROJECT_DIR, tag)
        gg.verify_tree_matches_tag(_PROJECT_DIR, tag, TAGGED_PATHSPECS)
    except gg.GitRemoteUnavailableError as exc:
        print(f"[dev-agent] origin unreachable for the AC-4 tag check - retry later: {exc}")
        return mr.EXIT_INFRA_HALT
    except gg.GitGateError as exc:
        print(f"[dev-agent] AC-4 FAILURE - STOP (no paid call made): {exc}")
        return mr.EXIT_CONFIG_ERROR
    print(f"[dev-agent] AC-4 ok: {tag} -> {info['commit'][:12]} on origin; frozen paths equal the tag")
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default="research/wp2/e2e_smoke_eng_v1/agent_dev_eng", type=Path)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-items", type=int, default=None)
    ap.add_argument("--stop-file", type=Path, default=None)
    ap.add_argument("--skip-pricing-preflight", action="store_true")
    ap.add_argument("--require-tag", default=None)
    args = ap.parse_args(argv)

    out_dir = args.out_dir if args.out_dir.is_absolute() else (_PROJECT_DIR / args.out_dir)
    code = _tag_gate(args.require_tag)
    if code is not None:
        return code
    try:
        knobs = mr.verify_frozen_knobs(PROTOCOL_V3)
    except mr.KnobDriftError as exc:
        print(f"[dev-agent] KNOB DRIFT - STOP: {exc}")
        return mr.EXIT_CONFIG_ERROR

    dev = json.loads(DEV_MANIFEST.read_text(encoding="utf-8"))
    items = [mr.WorkItem(key=t, task_id=t, replicate=0, index=i)
             for i, t in enumerate(dev["task_ids"])]
    manifest_sha = mr.file_sha256(DEV_MANIFEST)

    code_sha = {rel: mr.file_sha256(_PROJECT_DIR / rel) for rel in CODE_FILES}
    code_sha["protocol_v3"] = str(knobs.get("protocol_sha256", ""))

    extra: dict[str, object] = {"knob_check.json": knobs}
    gate = _pricing_gate(out_dir, extra, skip=bool(args.skip_pricing_preflight))
    if gate is not None:
        return gate

    # label guard + block evaluator_only
    from benchmark.wp1b import label_guard as lg
    lg._FORBIDDEN_PREFIXES = lg._FORBIDDEN_PREFIXES + (EVALUATOR_ONLY,)
    install_label_access_guard(_PROJECT_DIR)

    from scripts.saleor_portability_fix import materialize_production_parent

    def _materialize(bundle: mr.TaskBundle, workspace: Path) -> None:
        materialize_production_parent(SALEOR_CACHE, bundle.parent_commit, workspace, roots=("saleor",))

    def _load(task_id: str) -> mr.TaskBundle:
        return mr.load_saleor_bundle(SALEOR_SCIENTIFIC, task_id)

    out_dir.mkdir(parents=True, exist_ok=True)
    ledger = SpendLedger.open(out_dir / mr.LEDGER_FILE)
    from benchmark.llm.openrouter_backend import OpenRouterBackend
    inner = OpenRouterBackend(model=mr.FROZEN_MODEL, provider=mr.FROZEN_PROVIDER,
                              api_key_env="OPENROUTER_API_KEY", timeout_seconds=120.0,
                              max_transient_retries=0)
    backend = ResilientAccountingBackend(inner, ledger=ledger, ceiling_usd=CEILING_USD)

    def _make_strategy(b: ResilientAccountingBackend) -> IterativeRepositoryAgentStrategy:
        return IterativeRepositoryAgentStrategy(backend=b,
                                                agent_control_max_completion_tokens=mr.FROZEN_AGENT_CAP)

    config = mr.RunnerConfig(
        run_label="DEV_AGENT_SCOPE", kind="dev_agent_scope", out_dir=out_dir,
        ceiling_usd=CEILING_USD, worst_case_usd=_worst_case(), items=items,
        manifest_sha256=manifest_sha, code_sha256=code_sha,
        resume=bool(args.resume), limit=args.max_items, stop_file=args.stop_file,
        extra_files=extra,
    )
    runner = mr.MainRunner(config, backend=backend, load_bundle=_load,
                           materialize=_materialize, make_strategy=_make_strategy)
    try:
        outcome = runner.run()
    except mr.ResumeError as exc:
        print(f"[dev-agent] RESUME ERROR - STOP: {exc}")
        return mr.EXIT_CONFIG_ERROR
    print(f"[dev-agent] {outcome.status}: {outcome.detail} | {outcome.completed}/{outcome.total} "
          f"| ledger ${outcome.ledger_usd:.6f} / ceiling ${CEILING_USD:.2f} | exit {outcome.exit_code}")
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
