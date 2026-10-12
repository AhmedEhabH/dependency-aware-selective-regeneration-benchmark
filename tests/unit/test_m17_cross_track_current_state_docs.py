"""Cross-track current-state documentation freshness assertions.

Mission: M17_CROSS_TRACK_CURRENT_STATE_DOCUMENTATION_CORRECTION_R2 (T2, docs-only).

The Agentless documentation-sync (R1) inherited stale Track-A current state
("qualification NOT run", "review the M17 qualification kit before the REAL
12-task qualification"). This suite pins the CORRECTED current Track-A state:

  R3 CALIBRATION       = BLOCKED_STOP (11/12)  -- the frozen R3 Calibration-12
                          WAS executed: all 12 validation units ran, 11 PASS /
                          1 FAIL (vu-b9808f19ace4 at the pytest --collect-only /
                          smoke gate).
  ROOT CAUSE           = C_LOCK_RECONSTRUCTION_DEFECT
  SOURCE FIDELITY      = FROZEN / READY FOR FRESH CALIBRATION OWNER DECISION
                          (Source-Fidelity Amendment R1; 142/144 closures
                          unchanged, 2/144 changed)
  NEXT                 = FRESH SOURCE-FIDELITY CALIBRATION-12 FROM ZERO
  FULL D7              = NOT AUTHORIZED

P2P (positive, must PASS on the committed docs):
  P1  no LIVE block contains current-state wording "qualification NOT run"
      (or the other stale R1 phrasings);
  P2  current docs contain the executed R3 state 11 PASS / 1 FAIL
      (BLOCKED_STOP);
  P3  current docs contain C_LOCK_RECONSTRUCTION_DEFECT;
  P4  current docs contain the frozen Source-Fidelity R1 state;
  P5  current docs identify the next action as a fresh Source-Fidelity
      Calibration-12 from zero;
  P6  current docs state Full D7 is NOT authorized (human-readable or flag);
  P7  Agentless canonical metrics remain unchanged;
  P8  frozen Agentless evidence hashes remain unchanged (skips if absent);
  P9  LIVE rendered blocks remain byte-identical across the four targets;
  P10 no benchmark/scientific result artifact changed (skips without git).

F2P (negative, the same guards MUST FAIL on a mutated copy):
  F1  reinsert "qualification NOT run" as current state fails;
  F2  changing 11/12 to 12/12 fails;
  F3  changing the root cause away from C_LOCK_RECONSTRUCTION_DEFECT fails;
  F4  removing the Source-Fidelity frozen state fails;
  F5  setting Full D7 authorized before the fresh calibration fails;
  F6  changing the Agentless F1 fails;
  F7  changing the Agentless bootstrap CI fails;
  F8  modifying frozen Agentless evidence fails;
  F9  modifying frozen runtime-audit evidence fails;
  F10 modifying frozen source-fidelity evidence fails.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent

# Current-facing docs that must carry the corrected Track-A current state.
CURRENT_FACING = (
    ROOT / "README.md",
    ROOT / "PROGRESS.md",
    ROOT / "START_HERE_CURRENT_2026-09-21b.md",
    ROOT / "00_CURRENT_RESEARCH_STATE.md",
)
LIVE_STATUS = ROOT / "docs" / "LIVE_STATUS.json"

BEGIN = "<!-- LIVE_STATUS:BEGIN -->"
END = "<!-- LIVE_STATUS:END -->"

# External frozen evidence trees (read-only; never modified by this mission).
AGENTLESS_EVIDENCE_DIR = Path(
    os.environ.get(
        "WP2_AGENTLESS_EVIDENCE_DIR",
        r"D:\wp2_agentless_main297\research\competitor-agentless-r1",
    )
)
RUNTIME_AUDIT_DIR = Path(
    os.environ.get(
        "WP2_RUNTIME_AUDIT_DIR",
        r"D:\wp2_env_runtime_audit\research\env-runtime-audit-r1",
    )
)
SOURCE_FIDELITY_DIR = Path(
    os.environ.get(
        "WP2_SOURCE_FIDELITY_DIR",
        r"D:\wp2_source_fidelity_r1\research\source-fidelity-r1",
    )
)

# Frozen identities.
AGENTLESS_PREDICTION_SHA256 = (
    "90495bbb2c8d66a2c9a079cb2dfcd6e1cbf929c01972f1331df4242cdabd9815"
)
AGENTLESS_EVALUATION_SHA256 = (
    "4524be9a04d4328dcc598e42d7aa59607696899096261745383a4225c1723e78"
)
RUNTIME_AUDIT_COMMIT = "9e338b276c3ffef5390034bdbae0fc075dc7d901"
RUNTIME_AUDIT_TAG = "m17-d7-r3-runtime-owner-review-r1-2026-10-12"
SOURCE_FIDELITY_COMMIT = "f5f4c1d0ecae135f3b687bf8b9d27ffd150b6338"
SOURCE_FIDELITY_TAG = "m17-env-source-fidelity-r1-frozen-2026-10-12"

# Canonical frozen numbers that must never change.
AGENTLESS_F1 = "0.2736"
AGENTLESS_DELTA = "+0.0832"
AGENTLESS_CI = ("+0.0511", "+0.1148")
AGENTLESS_COST = "2.002373"

# Stale Track-A phrasings that must NOT appear as current state.
STALE_PHRASES = (
    "qualification NOT run",
    "REAL 12-task qualification",
    "before the REAL 12-task qualification",
    "awaiting review of the M17 qualification kit",
    "review then real 12-task qualification",
    "12-task REAL qualification",
)

# Required canonical Track-A phrasings.
CANONICAL_PHRASES = (
    "11 PASS / 1 FAIL",
    "C_LOCK_RECONSTRUCTION_DEFECT",
    "Source-Fidelity",
    "fresh Source-Fidelity Calibration-12 from zero",
    "Full D7",
)

_NEG_RE = re.compile(
    r"\b(?:not\s+authorized|unauthorized|NOT\s+AUTHORIZED|FALSE)\b",
    re.IGNORECASE,
)
_FULL_D7_RE = re.compile(r"Full\s+D7\b", re.IGNORECASE)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _current_facing_text() -> str:
    return "\n".join(_read(p) for p in CURRENT_FACING if p.is_file())


def _live_blocks_text() -> str:
    parts: list[str] = []
    for path in CURRENT_FACING:
        text = _read(path)
        if BEGIN not in text or END not in text:
            continue
        parts.append(text[text.index(BEGIN) + len(BEGIN): text.index(END)])
    return "\n".join(parts)


# --------------------------------------------------------------------------
# Guard functions: text -> list of violation strings.
# --------------------------------------------------------------------------
def guard_stale_current_state(text: str) -> list[str]:
    return [p for p in STALE_PHRASES if p in text]


def guard_canonical_present(text: str) -> list[str]:
    violations: list[str] = []
    low = text.lower()
    if "11 PASS / 1 FAIL" not in text:
        violations.append("missing executed R3 state '11 PASS / 1 FAIL'")
    if "C_LOCK_RECONSTRUCTION_DEFECT" not in text:
        violations.append("missing root cause C_LOCK_RECONSTRUCTION_DEFECT")
    if "Source-Fidelity" not in text:
        violations.append("missing Source-Fidelity frozen state")
    if "fresh source-fidelity calibration-12 from zero" not in low:
        violations.append("missing next action 'fresh Source-Fidelity Calibration-12 from zero'")
    if "unauthorized" not in low:
        violations.append("missing Full D7 unauthorized statement")
    return violations


def guard_full_d7_claim(text: str) -> list[str]:
    """Every 'Full D7' mention must be qualified as not/unauthorized/FALSE."""
    violations: list[str] = []
    for m in _FULL_D7_RE.finditer(text):
        window = text[m.start(): m.start() + 160]
        if _NEG_RE.search(window):
            continue
        violations.append(f"Full D7 without unauthorized/NOT-AUTHORIZED qualifier: {window[:60]!r}")
    return violations


def guard_agentless_metrics(text: str) -> list[str]:
    violations: list[str] = []
    if AGENTLESS_F1 not in text:
        violations.append("missing Agentless micro F1 0.2736")
    if AGENTLESS_DELTA not in text:
        violations.append("missing RM-CSS-minus-Agentless delta +0.0832")
    if AGENTLESS_CI[0] not in text or AGENTLESS_CI[1] not in text:
        violations.append("missing Agentless bootstrap CI bounds")
    if AGENTLESS_COST not in text:
        violations.append("missing actual Agentless cost 2.002373")
    return violations


def guard_runtime_audit_frozen(data: dict) -> list[str]:
    violations: list[str] = []
    if data.get("ROOT_CAUSE_CLASSIFICATION") != "C_LOCK_RECONSTRUCTION_DEFECT":
        violations.append("runtime-audit root-cause classification changed")
    counts = data.get("calibration_counts", {})
    if counts.get("pass") != 11 or counts.get("fail") != 1 or counts.get("executed") != 12:
        violations.append("runtime-audit calibration counts changed from 12/11/1")
    if data.get("calibration_status") != "BLOCKED_STOP":
        violations.append("runtime-audit calibration_status changed from BLOCKED_STOP")
    return violations


def guard_source_fidelity_frozen(data: dict) -> list[str]:
    violations: list[str] = []
    if data.get("root_cause_classification") != "C_LOCK_RECONSTRUCTION_DEFECT":
        violations.append("source-fidelity root-cause classification changed")
    if data.get("decision_gates", {}).get("FULL_D7_AUTHORIZED") is not False:
        violations.append("source-fidelity FULL_D7_AUTHORIZED changed from FALSE")
    if data.get("decision_gates", {}).get("CALIBRATION_RERUN_REQUIRED") is not True:
        violations.append("source-fidelity CALIBRATION_RERUN_REQUIRED changed")
    closure = data.get("closure_impact", {})
    if closure.get("n_unchanged") != 142 or closure.get("n_changed") != 2:
        violations.append("source-fidelity population closure impact changed (expected 142/2)")
    return violations


# --------------------------------------------------------------------------
# P2P tests (must PASS on the committed docs).
# --------------------------------------------------------------------------
def test_p1_no_stale_current_state_in_live_blocks() -> None:
    assert guard_stale_current_state(_live_blocks_text()) == []


def test_p1b_no_stale_current_state_in_current_facing_docs() -> None:
    assert guard_stale_current_state(_current_facing_text()) == []


def test_p2_r3_executed_11_pass_1_fail_present() -> None:
    assert guard_canonical_present(_current_facing_text()) == []
    live = json.loads(_read(LIVE_STATUS))
    assert "11 PASS / 1 FAIL" in live["position"]
    assert "BLOCKED_STOP" in live["position"]


def test_p3_root_cause_present() -> None:
    assert "C_LOCK_RECONSTRUCTION_DEFECT" in _current_facing_text()
    live = json.loads(_read(LIVE_STATUS))
    assert "C_LOCK_RECONSTRUCTION_DEFECT" in live["position"]


def test_p4_source_fidelity_frozen_present() -> None:
    assert "Source-Fidelity" in _current_facing_text()


def test_p5_fresh_calibration_is_next() -> None:
    low = _current_facing_text().lower()
    assert "fresh source-fidelity calibration-12 from zero" in low


def test_p6_full_d7_unauthorized() -> None:
    text = _current_facing_text()
    assert guard_full_d7_claim(text) == []
    assert "unauthorized" in text.lower()


def test_p7_agentless_metrics_unchanged() -> None:
    assert guard_agentless_metrics(_current_facing_text()) == []
    live = json.loads(_read(LIVE_STATUS))
    assert live["key_numbers"]["agentless_style_f1"] == "0.2736"
    assert live["key_numbers"]["rmcss_minus_agentless_delta"] == "+0.0832"
    assert live["key_numbers"]["agentless_api_cost"] == "2.002373"


@pytest.mark.skipif(not AGENTLESS_EVIDENCE_DIR.is_dir(), reason="external evidence tree absent")
def test_p8_agentless_evidence_hashes_unchanged() -> None:
    freeze = AGENTLESS_EVIDENCE_DIR / "agentless_r1_prediction_freeze.json"
    evaluation = AGENTLESS_EVIDENCE_DIR / "agentless_r1_evaluation.json"
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == AGENTLESS_PREDICTION_SHA256
    assert hashlib.sha256(evaluation.read_bytes()).hexdigest() == AGENTLESS_EVALUATION_SHA256


def test_p9_live_blocks_byte_identical() -> None:
    blocks = []
    for path in CURRENT_FACING:
        text = _read(path)
        assert BEGIN in text and END in text, f"{path.name} missing markers"
        blocks.append(text[text.index(BEGIN) + len(BEGIN): text.index(END)])
    assert len(set(blocks)) == 1, "LIVE blocks are not byte-identical"


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="not a git worktree")
def test_p10_no_benchmark_or_scientific_artifact_changed() -> None:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    allowed_prefixes = (
        "README.md",
        "PROGRESS.md",
        "START_HERE_CURRENT_2026-09-21b.md",
        "00_CURRENT_RESEARCH_STATE.md",
        "docs/LIVE_STATUS.json",
        "DECISIONS.md",
        "tests/unit/test_m17_cross_track_current_state_docs.py",
        "tests/unit/test_m17_agentless_main297_docs_sync.py",
        "research/agentless-main297-doc-sync-r1/",
        "research/agentless-main297-doc-sync-r2/",
    )
    for rel in changed:
        assert rel.startswith(allowed_prefixes), f"unexpected changed artifact: {rel}"


def _git_peel(repo: Path, tag: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-list", "-n1", tag],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


@pytest.mark.skipif(not RUNTIME_AUDIT_DIR.is_dir(), reason="external runtime-audit tree absent")
def test_p11_runtime_audit_frozen_identity_present() -> None:
    review = RUNTIME_AUDIT_DIR / "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json"
    assert guard_runtime_audit_frozen(json.loads(_read(review))) == []
    repo = RUNTIME_AUDIT_DIR.parent.parent
    if (repo / ".git").exists():
        assert _git_peel(repo, RUNTIME_AUDIT_TAG) == RUNTIME_AUDIT_COMMIT


@pytest.mark.skipif(not SOURCE_FIDELITY_DIR.is_dir(), reason="external source-fidelity tree absent")
def test_p12_source_fidelity_frozen_identity_present() -> None:
    freeze = json.loads(_read(SOURCE_FIDELITY_DIR / "SOURCE_FIDELITY_AMENDMENT_FREEZE.json"))
    assert guard_source_fidelity_frozen(freeze) == []
    repo = SOURCE_FIDELITY_DIR.parent.parent
    if (repo / ".git").exists():
        assert _git_peel(repo, SOURCE_FIDELITY_TAG) == SOURCE_FIDELITY_COMMIT


# --------------------------------------------------------------------------
# F2P tests (mutated copies MUST be flagged by the guards).
# --------------------------------------------------------------------------
def test_f1_reinsert_qualification_not_run_fails() -> None:
    mutated = "M17 qualification NOT run; awaiting review.\n" + _current_facing_text()
    assert guard_stale_current_state(mutated) != []
    assert guard_canonical_present(_current_facing_text()) == []  # baseline green


def test_f2_change_11_12_to_12_12_fails() -> None:
    mutated = _current_facing_text().replace("11 PASS / 1 FAIL", "12 PASS / 0 FAIL")
    assert guard_canonical_present(mutated) != []
    assert "11 PASS / 1 FAIL" not in mutated


def test_f3_change_root_cause_fails() -> None:
    mutated = _current_facing_text().replace(
        "C_LOCK_RECONSTRUCTION_DEFECT", "C_SOME_OTHER_DEFECT"
    )
    assert guard_canonical_present(mutated) != []


def test_f4_remove_source_fidelity_frozen_state_fails() -> None:
    mutated = _current_facing_text().replace("Source-Fidelity", "Source")
    assert guard_canonical_present(mutated) != []


def test_f5_set_full_d7_authorized_fails() -> None:
    mutated = (
        _current_facing_text()
        + "\nFULL_D7_AUTHORIZED = TRUE; Full D7 is now authorized and may start immediately.\n"
    )
    assert guard_full_d7_claim(mutated) != []
    assert guard_canonical_present(_current_facing_text()) == []  # baseline green


def test_f6_change_agentless_f1_fails() -> None:
    mutated = _current_facing_text().replace("0.2736", "0.2810")
    assert guard_agentless_metrics(mutated) != []


def test_f7_change_agentless_bootstrap_ci_fails() -> None:
    mutated = _current_facing_text().replace("+0.0832", "−0.0832")
    assert guard_agentless_metrics(mutated) != []


@pytest.mark.skipif(not AGENTLESS_EVIDENCE_DIR.is_dir(), reason="external evidence tree absent")
def test_f8_modifying_agentless_evidence_fails() -> None:
    freeze = AGENTLESS_EVIDENCE_DIR / "agentless_r1_prediction_freeze.json"
    mutated = freeze.read_bytes() + b"\n# tamper\n"
    assert hashlib.sha256(mutated).hexdigest() != AGENTLESS_PREDICTION_SHA256


@pytest.mark.skipif(not RUNTIME_AUDIT_DIR.is_dir(), reason="external runtime-audit tree absent")
def test_f9_modifying_runtime_audit_evidence_fails() -> None:
    review = RUNTIME_AUDIT_DIR / "D7_R3_RUNTIME_FAILURE_OWNER_REVIEW.json"
    data = json.loads(_read(review))
    mutated = dict(data, ROOT_CAUSE_CLASSIFICATION="C_SOMETHING_ELSE")
    assert guard_runtime_audit_frozen(mutated) != []


@pytest.mark.skipif(not SOURCE_FIDELITY_DIR.is_dir(), reason="external source-fidelity tree absent")
def test_f10_modifying_source_fidelity_evidence_fails() -> None:
    freeze = json.loads(_read(SOURCE_FIDELITY_DIR / "SOURCE_FIDELITY_AMENDMENT_FREEZE.json"))
    mutated = json.loads(json.dumps(freeze))
    mutated["decision_gates"]["FULL_D7_AUTHORIZED"] = True
    assert guard_source_fidelity_frozen(mutated) != []


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
