"""Semantic-proxy audit — kappa script + integrity tests (Block G, ZERO API).

Tests:
1. Kappa script: perfect agreement => kappa 1.0
2. Kappa script: all-disagree => kappa -1.0 / low
3. Kappa script: sensitivity recoding (related-as-negative vs positive)
4. Two-rater forms: parseable, 150 rows, blank (no fabricated ratings)
5. Two-rater forms: blinded ordering SHA matches persisted
6. Finalize integrity: packet structure complete
7. Finalize synthetic dry-run: produces NOT_REAL mock output
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parent.parent.parent
OUT = PROJECT / "research" / "semantic_audit"
KAPPA = PROJECT / "scripts" / "semantic_audit_kappa.py"
FINALIZE = PROJECT / "scripts" / "semantic_audit_finalize.py"


def _write_form(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _make_forms(n: int = 20, pattern: str = "agree") -> tuple[Path, Path]:
    cats = ["1_required", "2_related_optional", "3_incidental_tangled", "4_not_determinable"]
    a = []
    b = []
    for i in range(n):
        ra = {"case_id": f"c{i}", "item_index": str(i), "rater_category": cats[i % 4], "confidence": "0.9", "notes": ""}
        if pattern == "agree":
            rb = dict(ra)
        elif pattern == "shift":
            rb = dict(ra)
            rb["rater_category"] = cats[(i + 1) % 4]
        else:  # opposite
            rb = dict(ra)
            rb["rater_category"] = cats[(i + 2) % 4]
        a.append(ra)
        b.append(rb)
    pa = OUT / "MOCK_NOT_REAL_test_a.csv"
    pb = OUT / "MOCK_NOT_REAL_test_b.csv"
    _write_form(pa, a)
    _write_form(pb, b)
    return pa, pb


def _run_kappa(pa: Path, pb: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(KAPPA), str(pa), str(pb)],
        capture_output=True, text=True, cwd=PROJECT,
    )
    assert result.returncode == 0, result.stderr
    # kappa prints a multi-line JSON result then a trailing 'output: ...' line;
    # parse everything before the 'output:' marker.
    payload = result.stdout.split("output:", 1)[0].strip()
    return json.loads(payload)


def test_kappa_perfect_agreement() -> None:
    pa, pb = _make_forms(pattern="agree")
    res = _run_kappa(pa, pb)
    assert res["raw_agreement"] == pytest.approx(1.0)
    assert res["cohen_kappa"] == pytest.approx(1.0)


def test_kappa_shifted_disagreement() -> None:
    pa, pb = _make_forms(pattern="shift")
    res = _run_kappa(pa, pb)
    assert res["cohen_kappa"] < 0.5


def test_kappa_opposite_disagreement() -> None:
    pa, pb = _make_forms(pattern="opposite")
    res = _run_kappa(pa, pb)
    assert res["cohen_kappa"] < 0.2


def test_kappa_sensitivity_fields_present() -> None:
    pa, pb = _make_forms(pattern="agree")
    res = _run_kappa(pa, pb)
    assert "sensitivity_related_as_negative" in res
    assert "sensitivity_related_as_positive" in res


def test_rater_forms_blank_and_150() -> None:
    for fname in ("rater_form_A.csv", "rater_form_B.csv", "adjudicator_form.csv"):
        with open(OUT / fname, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 150, fname
        filled = [r for r in rows if (r.get("rater_category") or "").strip()
                  or (r.get("rater_a") or r.get("rater_b") or r.get("adjudicated") or "").strip()]
        assert not filled, f"{fname}: fabricated ratings present"


def test_blinded_ordering_sha_matches() -> None:
    blinded = json.loads((OUT / "blinded_ordering.json").read_text(encoding="utf-8"))
    recomputed = hashlib.sha256(json.dumps(blinded["order"], separators=(",", ":")).encode()).hexdigest()
    assert recomputed == blinded["sha256"]


def test_finalize_integrity_and_dryrun() -> None:
    result = subprocess.run(
        [sys.executable, str(FINALIZE)], capture_output=True, text=True, cwd=PROJECT,
    )
    assert result.returncode == 0, result.stderr
    assert "PACKET_INTEGRITY PASS" in result.stdout
    assert "SYNTHETIC_DRYRUN PASS" in result.stdout
    assert (OUT / "MOCK_NOT_REAL_kappa_result.json").is_file()
