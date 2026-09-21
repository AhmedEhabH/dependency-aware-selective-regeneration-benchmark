"""WP-1b G6 - provider/pricing preflight artifact tests.

Protects the Efficiency dimension (route/pricing must match the frozen
protocol before any paid call) and Architecture Compliance (artifact schema).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

ARTIFACT = PROJECT_DIR / "artifacts" / "wp1b_provider_pricing_preflight_2026-09-21.json"


def test_pricing_preflight_artifact_is_valid() -> None:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert data["artifact"] == "wp1b_provider_pricing_preflight"
    assert data["generated_utc"]
    if data.get("live_metadata_available"):
        checks = data["checks"]
        for key in ("model_matches_frozen", "route_matches_frozen",
                    "prompt_price_matches_frozen", "completion_price_matches_frozen"):
            assert key in checks
        assert data["deepinfra_route"]["tag"] == "deepinfra/turbo"
        assert data["model"]["id"] == "qwen/qwen3-coder"


def test_pricing_preflight_script_runs_without_paid_inference() -> None:
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "scripts" / "wp1b_provider_pricing_preflight.py")],
        cwd=PROJECT_DIR, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert "no paid inference was invoked" in data.get("note", "")


def test_frozen_pricing_matches_historical_verification() -> None:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    budget = json.loads(
        (PROJECT_DIR / "research" / "wp1a" / "wp1a_budget_model.json").read_text(encoding="utf-8")
    )
    assert budget["pricing"]["prompt_per_1m_usd"] == 0.3
    assert budget["pricing"]["completion_per_1m_usd"] == 1.0
    assert budget["model"] == "qwen/qwen3-coder"
    assert "deepinfra/turbo" in budget["provider"]
    if data.get("live_metadata_available"):
        assert data["checks"]["no_drift"] is True
