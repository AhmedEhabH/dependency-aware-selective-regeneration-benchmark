"""djangoCMS confirmatory execution package — frozen-contract tests (ZERO API).

These tests prove the ready-to-run confirmatory package (Block C) is internally
consistent with the frozen freeze packet V2 + API budget freeze, without
opening INTERNAL_TEST contents/outcomes and without any API call:
- the frozen ceilings (560 calls / 2,100,000 tokens / $1.00) and per-call
  reservation rule match the budget freeze;
- the ReservationLedger is fail-closed (never dispatches a call that would
  breach a ceiling);
- the dry-run pipeline runs end-to-end with synthetic data (NOT REAL) and
  respects the ledger;
- the real path is fail-closed: refuses to run without --authorize + API key.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent.parent
PY = sys.executable


def _config_module() -> dict:
    import importlib

    sys.path.insert(0, str(PROJECT))
    cfg = importlib.import_module("scripts.djangocms_confirmatory_config")
    return cfg


def test_frozen_ceilings_match_budget_freeze() -> None:
    cfg = _config_module()
    assert cfg.MAX_CALLS == 560
    assert cfg.MAX_TOKENS == 2_100_000
    assert cfg.MAX_COST_USD == 1.00
    assert cfg.BUDGETS == (0, 1, 3, 5, 10)
    assert cfg.VERIFIER_BUDGETS == (1, 3, 5, 10)
    assert cfg.N_TASKS == 80
    assert cfg.REPS == 3


def test_frozen_model_config() -> None:
    cfg = _config_module()
    assert cfg.MODEL == "qwen/qwen3-coder"
    assert cfg.PROVIDER_TAG == "deepinfra/turbo"
    assert cfg.TEMPERATURE == 0.0
    assert cfg.SPARSE_CAP == 16384
    assert cfg.VERIFIER_CAP == 512


def test_reservation_totals_under_ceilings() -> None:
    cfg = _config_module()
    sparse = cfg.N_TASKS * cfg.REPS
    verifier = cfg.N_TASKS * len(cfg.VERIFIER_BUDGETS)
    assert sparse + verifier == cfg.MAX_CALLS == 560
    res_tokens = sparse * cfg.RESERVATION_SPARSE_TOKENS + verifier * cfg.RESERVATION_VERIFIER_TOKENS
    res_cost = sparse * cfg.RESERVATION_SPARSE_COST + verifier * cfg.RESERVATION_VERIFIER_COST
    assert res_tokens <= cfg.MAX_TOKENS
    assert res_cost <= cfg.MAX_COST_USD
    # matches the budget-freeze arithmetic
    assert res_tokens == 2_018_480
    assert round(res_cost, 4) == round(0.7248 + 0.0480, 4)


def test_ledger_fail_closed() -> None:
    from scripts.djangocms_confirmatory_execution import ReservationLedger

    ledger = ReservationLedger(Path(PROJECT) / "research" / "djangocms-confirmatory-route-b" / "test")
    # drain the call ceiling
    for _ in range(560):
        assert ledger.can_dispatch(1, 0.0)
        ledger.reserve(1, 0.0)
    assert ledger.stopped is False
    assert ledger.can_dispatch(1, 0.0) is False  # calls ceiling
    assert ledger.stop_reason == "calls_ceiling"


def test_real_path_requires_authorize() -> None:
    out = subprocess.run(
        [PY, str(PROJECT / "scripts" / "djangocms_confirmatory_execution.py"), "--real"],
        cwd=PROJECT, capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 2
    assert "BLOCKED" in out.stdout


def test_dry_run_pipeline_pass(tmp_path: Path) -> None:
    out = subprocess.run(
        [PY, str(PROJECT / "scripts" / "djangocms_confirmatory_execution.py"), "--dry-run"],
        cwd=PROJECT, capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, out.stdout[-2000:]
    assert "DRY_RUN PASS" in out.stdout
    summary = json.loads(
        (PROJECT / "research" / "djangocms-confirmatory-route-b" / "dryrun" / "confirmatory_dryrun_summary.json")
        .read_text(encoding="utf-8")
    )
    assert summary["NOT_REAL"] is True
    assert summary["ledger"]["reserved_calls"] == 560
    assert summary["ceiling_respected"] is True
    raw = list((PROJECT / "research" / "djangocms-confirmatory-route-b" / "dryrun" / "runs" / "raw").glob("*.sha256"))
    assert len(raw) > 0
