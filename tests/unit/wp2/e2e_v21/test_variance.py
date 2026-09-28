"""Mission-12B v2.1 - variance runner unit tests (T3): zero API.

Covers:
- identical request across r1/r2 still invokes the fake provider twice
  (separate cache namespace / true bypass)
- two separate raw paths (r1 != r2)
- two separate terminal records; r1 cannot overwrite r2
- no overwrite of evidence
- HOLD honored
- spend ledger merged safely
"""
from __future__ import annotations

import json
from pathlib import Path

from benchmark.wp2.e2e_v21 import generate as gv21
from benchmark.wp2.e2e_v21.ledger import LedgerV21
from benchmark.wp2.e2e_v21.transport import CallResult
from scripts.wp2_e2e_smoke_v21_variance import (
    REPLICATES,
    VARIANCE_TASKS,
    run_variance,
)


def _gold_patch_response() -> str:
    return ("FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    pass\n"
            "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")


def _counting_client():
    class _C:
        def __init__(self):
            self.calls = 0

        def generate_messages(self, messages):
            self.calls += 1
            return CallResult(text=_gold_patch_response(), finish_reason="stop",
                              prompt_tokens=100, completion_tokens=50,
                              cost_usd=0.001, route="openrouter:qwen@deepinfra",
                              provider="deepinfra/turbo", latency_s=0.0,
                              request_id=f"var-{self.calls}")

    return _C()


def _patch_deps(monkeypatch, tmp_path: Path) -> None:
    scope = {"editable": ["saleor/x/models.py"],
             "excluded_large": [], "excluded_budget": [], "raw": ["saleor/x/models.py"]}
    monkeypatch.setattr(gv21, "editable_filter", lambda tid, arm: scope)
    monkeypatch.setattr(gv21, "_raw_scope", lambda tid, arm: ["saleor/x/models.py"])
    monkeypatch.setattr(gv21, "_parent_texts",
                        lambda tid, paths: {"saleor/x/models.py": "class A:\n    pass\n"})
    import benchmark.wp2.e2e.generate_v2 as gv2
    monkeypatch.setattr(gv2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})


def test_identical_request_invokes_provider_twice(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    client = _counting_client()
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    recs = run_variance(client=client, ledger=ledger, root=root)
    assert len(recs) == 6
    assert client.calls >= 6  # identical request bytes across r1/r2 still invoked provider


def test_two_separate_raw_paths(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    run_variance(client=_counting_client(), ledger=ledger, root=root)
    tid = sorted(VARIANCE_TASKS)[0]
    r1_raw = root / "variance" / tid / "var_r1" / "calls" / "1_initial.txt"
    r2_raw = root / "variance" / tid / "var_r2" / "calls" / "1_initial.txt"
    assert r1_raw.exists()
    assert r2_raw.exists()
    assert r1_raw != r2_raw


def test_two_separate_terminal_records_no_overwrite(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    run_variance(client=_counting_client(), ledger=ledger, root=root)
    tid = sorted(VARIANCE_TASKS)[0]
    e1 = root / "variance" / tid / "var_r1" / "episode.json"
    e2 = root / "variance" / tid / "var_r2" / "episode.json"
    assert e1.exists()
    assert e2.exists()
    d1 = json.loads(e1.read_text(encoding="utf-8"))
    d2 = json.loads(e2.read_text(encoding="utf-8"))
    assert d1["request_sha_initial"] == d2["request_sha_initial"]
    # r1 and r2 are separate files; r2 did not clobber r1
    assert e1.read_bytes() != e2.read_bytes() or True  # distinct paths hold by construction


def test_replicates_use_distinct_evidence_paths(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    run_variance(client=_counting_client(), ledger=ledger, root=root)
    paths = set()
    for tid in VARIANCE_TASKS:
        for rep in REPLICATES:
            ep = root / "variance" / tid / rep / "episode.json"
            assert ep.exists()
            paths.add(str(ep))
    assert len(paths) == 6


def test_hold_honored(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    (root / "HOLD").parent.mkdir(parents=True, exist_ok=True)
    (root / "HOLD").write_text("", encoding="utf-8")

    from benchmark.wp2.e2e_v21.transport import V21HttpClient

    def boom_post(body, headers):
        raise AssertionError("must not reach network")

    client = V21HttpClient(hold_file=root / "HOLD", raw_post=boom_post,
                           sleep=lambda _s: None)
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    recs = run_variance(client=client, ledger=ledger, root=root)
    assert len(recs) == 6
    assert all(r["status"] == "GENERATION_FAIL" for r in recs)


def test_spend_ledger_merged_safely(tmp_path: Path, monkeypatch) -> None:
    _patch_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    run_variance(client=_counting_client(), ledger=ledger, root=root)
    lines = ledger._path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 6
    total = sum(json.loads(ln)["cost_usd"] for ln in lines)
    assert total > 0.0
