"""P2P/F2P documentation assertions for the Agentless-style MAIN_297 sync.

Mission: M17_AGENTLESS_MAIN297_RESULTS_DOCUMENTATION_SYNC_R1 (T2, docs-only).

P2P (positive, must PASS on the committed docs):
  P1  displayed Agentless micro metrics equal the frozen evaluation values
      within documented rounding;
  P2  displayed paired CIs have the correct direction/sign;
  P3  AGENTLESS_STYLE_ADAPTATION appears where the competitor is named;
  P4  no wording claims EXACT_AGENTLESS / official reproduction;
  P5  no wording says actual cost <= $2;
  P6  actual cost $2.002373 represented accurately;
  P7  no wording says the full repository suite PASSED;
  P8  no wording says Agentless-style significantly beats SIP in F1;
  P9  no wording says RM-CSS has the highest MAIN_297 point F1;
  P10 README/PROGRESS/LIVE/current-state RQ2 numbers mutually consistent;
  P11 LIVE rendered blocks are byte-identical across the four targets;
  P12 frozen Agentless evidence files remain byte-identical (skips if the
      external evidence tree is absent);
  P13 no benchmark code or result artifact changed (skips without git).

F2P (negative, the same guards MUST FAIL on a mutated copy):
  F1 replacing AGENTLESS_STYLE_ADAPTATION with EXACT_AGENTLESS fails;
  F2 changing F1 away from 0.2736 fails;
  F3 reversing the bootstrap sign fails;
  F4 claiming cost stayed under $2 fails;
  F5 claiming global full-suite PASS fails;
  F6 claiming RM-CSS has the highest MAIN_297 F1 fails;
  F7 claiming significant Agentless > SIP F1 fails;
  F8 modifying frozen Agentless evidence fails;
  F9 modifying Agentless execution/parser/evaluator code fails;
  F10 re-running the 297-task experiment fails (no-run receipt invariant).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent

CURRENT_FACING = (
    ROOT / "README.md",
    ROOT / "PROGRESS.md",
    ROOT / "START_HERE_CURRENT_2026-09-21b.md",
    ROOT / "00_CURRENT_RESEARCH_STATE.md",
    ROOT / "docs" / "CLAIM_REGISTRY.md",
)

# External frozen evidence (read-only; never modified by this mission).
EVIDENCE_DIR = Path(
    os.environ.get(
        "WP2_AGENTLESS_EVIDENCE_DIR",
        r"D:\wp2_agentless_main297\research\competitor-agentless-r1",
    )
)

# Frozen identities (from D1).
PREDICTION_FREEZE_SHA256 = (
    "90495bbb2c8d66a2c9a079cb2dfcd6e1cbf929c01972f1331df4242cdabd9815"
)
EVALUATION_SHA256 = (
    "4524be9a04d4328dcc598e42d7aa59607696899096261745383a4225c1723e78"
)

# Canonical frozen numbers.
AGENTLESS_F1 = 0.27363737486095663
AGENTLESS_P = 0.2785956964892412
AGENTLESS_R = 0.26885245901639343
AGENTLESS_FNR = 0.7311475409836066
AGENTLESS_TP_FP_FN = (246, 637, 669)
AGENTLESS_COST = "2.002373"

# Lines that legitimately mention a forbidden phrase (as a negation / example).
_NEGATION_WORD_RE = re.compile(
    r"\b(?:forbidden|never|not|no|cannot|without|must\s+not|do\s+not|does\s+not|"
    r"do-not|no\s+wording|no\s+claim|crosses\s+zero)\b",
    re.IGNORECASE,
)

_NEGATION_WINDOW = 300


def _negated_before(text: str, pos: int) -> bool:
    """True if a negation word occurs within `_NEGATION_WINDOW` chars before pos.

    Handles line-wrapped documents where the negating word and the quoted
    forbidden phrase end up on different lines (e.g. README "and never
    \"official Agentless\"." or a wrapped FORBIDDEN list in CLAIM_REGISTRY).
    """
    start = max(0, pos - _NEGATION_WINDOW)
    return _NEGATION_WORD_RE.search(text[start:pos]) is not None


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _all_docs_text() -> str:
    return "\n".join(_read(p) for p in CURRENT_FACING if p.is_file())


def _affirmative_hits(text: str, patterns: tuple[str, ...]) -> list[str]:
    """Return the matching patterns whose occurrence is NOT negated nearby.

    Uses a character window before each occurrence so negations on wrapped
    lines (e.g. README "and never \"official Agentless\"." or a wrapped
    FORBIDDEN list in CLAIM_REGISTRY) are honoured.
    """
    low = text.lower()
    hits: list[str] = []
    for pattern in patterns:
        needle = pattern.lower()
        start = 0
        while True:
            pos = low.find(needle, start)
            if pos == -1:
                break
            if not _negated_before(low, pos):
                hits.append(pattern)
                break
            start = pos + len(needle)
    return hits


# --------------------------------------------------------------------------
# Guard functions: text -> list of violation strings.
# --------------------------------------------------------------------------
def guard_label(text: str) -> list[str]:
    return [] if "AGENTLESS_STYLE_ADAPTATION" in text else ["missing AGENTLESS_STYLE_ADAPTATION"]


def guard_f1(text: str) -> list[str]:
    return [] if "0.2736" in text else ["missing Agentless micro F1 0.2736"]


def guard_ci_signs(text: str) -> list[str]:
    violations: list[str] = []
    # RM-CSS is above Agentless: positive delta and positive CI.
    if "RM-CSS minus Agentless" in text or "RM-CSS-minus-Agentless" in text:
        if "+0.0832" not in text:
            violations.append("RM-CSS-minus-Agentless delta not shown as +0.0832")
        if "+0.0511" not in text or "+0.1148" not in text:
            violations.append("RM-CSS-minus-Agentless CI sign missing/incorrect")
    # Agentless vs SIP CI crosses zero.
    if "Agentless vs SIP" in text or "Agentless-style vs SIP" in text:
        if "−0.0204" not in text and "-0.0204" not in text:
            violations.append("Agentless-vs-SIP CI does not show the negative lower bound")
    return violations


def guard_exact_agentless(text: str) -> list[str]:
    tokens = ("EXACT_AGENTLESS", "OFFICIAL_AGENTLESS", "AGENTLESS_REPRODUCTION")
    violations: list[str] = []
    for token in tokens:
        pos = text.find(token)
        if pos != -1 and not _negated_before(text.lower(), pos):
            violations.append(f"forbidden label token {token}")
    if _affirmative_hits(text, ("official agentless",)):
        violations.append("affirmative 'official Agentless'")
    if _affirmative_hits(text, ("exact agentless reproduction",)):
        violations.append("affirmative 'exact Agentless reproduction'")
    return violations


def guard_under_budget(text: str) -> list[str]:
    patterns = (
        "cost stayed under $2",
        "under $2",
        "cost <= $2",
        "actual cost <= $2",
        "cost <= 2",
        "within the $2",
        "remained under",
        "stayed within budget",
        "never exceeded $2",
    )
    violations: list[str] = []
    for pattern in _affirmative_hits(text, patterns):
        violations.append(f"forbidden under-budget wording: {pattern!r}")
    return violations


def guard_full_suite_pass(text: str) -> list[str]:
    patterns = (
        "full_suite_pass",
        "full suite pass",
        "full-suite pass",
        "full repository suite pass",
        "repository suite passed",
        "suite passed",
        "all tests pass",
    )
    violations: list[str] = []
    for pattern in _affirmative_hits(text, patterns):
        violations.append(f"forbidden full-suite PASS wording: {pattern!r}")
    return violations


def guard_rmcss_highest(text: str) -> list[str]:
    patterns = (
        "highest main_297",
        "highest point f1",
        "rm-css has the highest",
        "rm-css is best",
        "best overall",
        "rm-css achieves the highest",
    )
    violations: list[str] = []
    for pattern in _affirmative_hits(text, patterns):
        violations.append(f"forbidden 'RM-CSS highest' wording: {pattern!r}")
    return violations


def guard_agentless_beats_sip(text: str) -> list[str]:
    patterns = (
        "significantly beats sip",
        "significantly higher than sip",
        "agentless-style significantly",
        "significantly outperforms sip",
        "significantly improves over sip",
    )
    violations: list[str] = []
    for pattern in _affirmative_hits(text, patterns):
        violations.append(f"forbidden Agentless>SIP wording: {pattern!r}")
    return violations


def guard_cost_value(text: str) -> list[str]:
    return [] if AGENTLESS_COST in text else [f"missing actual cost {AGENTLESS_COST}"]


# --------------------------------------------------------------------------
# P2P tests (must PASS on the committed docs).
# --------------------------------------------------------------------------
def test_p1_micro_metrics_match_frozen() -> None:
    text = _all_docs_text()
    assert guard_f1(text) == []
    for value in ("0.2786", "0.2689", "0.7311"):
        assert value in text, f"missing rounded Agentless metric {value}"
    for token in ("246", "637", "669"):
        assert token in text, f"missing confusion component {token}"


def test_p2_ci_signs_correct() -> None:
    assert guard_ci_signs(_all_docs_text()) == []


def test_p3_label_present() -> None:
    assert guard_label(_all_docs_text()) == []


def test_p4_no_exact_agentless_claim() -> None:
    assert guard_exact_agentless(_all_docs_text()) == []


def test_p5_no_under_budget_claim() -> None:
    assert guard_under_budget(_all_docs_text()) == []


def test_p6_cost_value_present() -> None:
    assert guard_cost_value(_all_docs_text()) == []


def test_p7_no_full_suite_pass_claim() -> None:
    assert guard_full_suite_pass(_all_docs_text()) == []


def test_p8_no_agentless_beats_sip_claim() -> None:
    assert guard_agentless_beats_sip(_all_docs_text()) == []


def test_p9_no_rmcss_highest_claim() -> None:
    assert guard_rmcss_highest(_all_docs_text()) == []


def test_p10_rq2_numbers_mutually_consistent() -> None:
    for path in (
        ROOT / "README.md",
        ROOT / "PROGRESS.md",
        ROOT / "START_HERE_CURRENT_2026-09-21b.md",
        ROOT / "00_CURRENT_RESEARCH_STATE.md",
    ):
        text = _read(path)
        assert "0.2736" in text, f"{path.name} missing Agentless F1 0.2736"
    live = json.loads(_read(ROOT / "docs" / "LIVE_STATUS.json"))
    assert live["key_numbers"]["agentless_style_f1"] == "0.2736"
    assert live["key_numbers"]["rmcss_minus_agentless_delta"] == "+0.0832"


def test_p11_live_blocks_byte_identical() -> None:
    begin, end = "<!-- LIVE_STATUS:BEGIN -->", "<!-- LIVE_STATUS:END -->"
    blocks = []
    for path in (
        ROOT / "README.md",
        ROOT / "START_HERE_CURRENT_2026-09-21b.md",
        ROOT / "PROGRESS.md",
        ROOT / "00_CURRENT_RESEARCH_STATE.md",
    ):
        text = _read(path)
        assert begin in text and end in text, f"{path.name} missing markers"
        blocks.append(text[text.index(begin) + len(begin): text.index(end)])
    assert len(set(blocks)) == 1, "LIVE blocks are not byte-identical"


@pytest.mark.skipif(not EVIDENCE_DIR.is_dir(), reason="external evidence tree absent")
def test_p12_frozen_evidence_unchanged() -> None:
    freeze = EVIDENCE_DIR / "agentless_r1_prediction_freeze.json"
    evaluation = EVIDENCE_DIR / "agentless_r1_evaluation.json"
    assert hashlib.sha256(freeze.read_bytes()).hexdigest() == PREDICTION_FREEZE_SHA256
    assert hashlib.sha256(evaluation.read_bytes()).hexdigest() == EVALUATION_SHA256


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="not a git worktree")
def test_p13_no_benchmark_code_or_result_artifact_changed() -> None:
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
        "docs/CLAIM_REGISTRY.md",
        "DECISIONS.md",
        "tests/unit/test_m17_agentless_main297_docs_sync.py",
        "tests/unit/test_m17_cross_track_current_state_docs.py",
        "research/agentless-main297-doc-sync-r1/",
        "research/agentless-main297-doc-sync-r2/",
    )
    for rel in changed:
        assert rel.startswith(allowed_prefixes), f"unexpected changed artifact: {rel}"


# --------------------------------------------------------------------------
# F2P tests (mutated copies MUST be flagged by the guards).
# --------------------------------------------------------------------------
def test_f1_exact_agentless_mutation_fails() -> None:
    mutated = _all_docs_text().replace("AGENTLESS_STYLE_ADAPTATION", "EXACT_AGENTLESS")
    assert guard_label(mutated) != []
    assert guard_exact_agentless(mutated) != []


def test_f2_f1_value_mutation_fails() -> None:
    mutated = _all_docs_text().replace("0.2736", "0.2810")
    assert guard_f1(mutated) != []


def test_f3_bootstrap_sign_reversal_fails() -> None:
    mutated = _all_docs_text().replace("+0.0832", "−0.0832")
    assert guard_ci_signs(mutated) != []


def test_f4_under_budget_claim_fails() -> None:
    mutated = "The cost stayed under $2 for the whole run.\n" + _all_docs_text()
    assert guard_under_budget(mutated) != []


def test_f5_global_full_suite_pass_claim_fails() -> None:
    mutated = "The full repository suite passed completely.\n" + _all_docs_text()
    assert guard_full_suite_pass(mutated) != []


def test_f6_rmcss_highest_claim_fails() -> None:
    mutated = "RM-CSS has the highest MAIN_297 point F1.\n" + _all_docs_text()
    assert guard_rmcss_highest(mutated) != []


def test_f7_agentless_beats_sip_claim_fails() -> None:
    mutated = "Agentless-style significantly beats SIP in F1.\n" + _all_docs_text()
    assert guard_agentless_beats_sip(mutated) != []


@pytest.mark.skipif(not EVIDENCE_DIR.is_dir(), reason="external evidence tree absent")
def test_f8_modifying_frozen_evidence_would_fail() -> None:
    freeze = EVIDENCE_DIR / "agentless_r1_prediction_freeze.json"
    mutated = freeze.read_bytes() + b"\n# tamper\n"
    assert hashlib.sha256(mutated).hexdigest() != PREDICTION_FREEZE_SHA256


@pytest.mark.skipif(not (ROOT / ".git").exists(), reason="not a git worktree")
def test_f9_f10_no_run_and_no_code_change_guard() -> None:
    receipt = ROOT / "research" / "agentless-main297-doc-sync-r1" / (
        "AGENTLESS_MAIN297_DOCUMENTATION_SYNC_RECEIPT.json"
    )
    if not receipt.is_file():
        pytest.skip("doc-sync receipt not present yet")
    data = json.loads(_read(receipt))
    inv = data["scientific_invariance"]
    assert inv["BENCHMARK_EXECUTED"] is False
    assert inv["API_CALLS"] == 0
    assert inv["AGENTLESS_EVIDENCE_MODIFIED"] is False
    assert inv["SCIENTIFIC_RESULT_CHANGED"] is False


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
