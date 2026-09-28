"""Mission-12B v2.1 - generation driver unit tests (T2): zero API.

Covers:
- driver resume: 10 existing terminal + max-new=8 -> exactly 8 new
- partial initial-success / repair-transport-fail preserves initial
  raw + ledger + call metadata (calls never replaced by [])
- HOLD prevents the call
- no v2 path written; no v2 cache read
- one NO_SCOPE uses 0 provider calls
"""
from __future__ import annotations

import json
from pathlib import Path

from benchmark.wp2.e2e.response_cache import ResponseCache
from benchmark.wp2.e2e_v21 import generate as gv21
from benchmark.wp2.e2e_v21.ledger import LedgerV21
from benchmark.wp2.e2e_v21.transport import (
    CallResult,
    GenerationFail,
)


def _gold_patch_response() -> str:
    return ("FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    pass\n"
            "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")


def _scripted_client(*responses: str):
    """Returns a client whose generate_messages pops the next canned response."""
    import collections
    queue = collections.deque(responses)

    class _C:
        def __init__(self):
            self.calls = 0

        def generate_messages(self, messages):
            self.calls += 1
            text = queue.popleft()
            return CallResult(text=text, finish_reason="stop",
                              prompt_tokens=100, completion_tokens=len(text) // 4,
                              cost_usd=0.001, route="openrouter:qwen@deepinfra",
                              provider="deepinfra/turbo", latency_s=0.0,
                              request_id=f"gen-{self.calls}")

    return _C()


def _patch_episode_deps(monkeypatch, tmp_path: Path) -> None:
    """Route run_episode_v21's scope/text/py_compile deps to a synthetic task."""
    scope = {"editable": ["saleor/x/models.py"],
             "excluded_large": [], "excluded_budget": [], "raw": ["saleor/x/models.py"]}
    monkeypatch.setattr(gv21, "editable_filter", lambda tid, arm: scope)
    monkeypatch.setattr(gv21, "_raw_scope", lambda tid, arm: ["saleor/x/models.py"])
    monkeypatch.setattr(gv21, "_parent_texts",
                        lambda tid, paths: {"saleor/x/models.py": "class A:\n    pass\n"})
    import benchmark.wp2.e2e.generate_v2 as gv2
    monkeypatch.setattr(gv2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})


def test_resume_ten_existing_max_new_eight(tmp_path: Path, monkeypatch) -> None:
    import scripts.wp2_e2e_smoke_v21_generate as drv

    root = tmp_path / "v21root"
    prog: dict = {}
    calls: list[str] = []

    def fake_run(tid, arm, client, ledger, cache, root=None):
        calls.append(f"{tid}|{arm}")
        base = root / "episodes" / tid / arm
        base.mkdir(parents=True, exist_ok=True)
        rec = {"status": "APPLIED", "diff_sha256": "d", "repair_used": False,
               "request_sha_initial": "r", "calls": [], "task_id": tid, "arm": arm}
        (base / "episode.json").write_text(json.dumps(rec), encoding="utf-8")
        return rec

    # 10 existing terminal episodes
    existing = [(f"t{i:02d}", "GOLD_HARD") for i in range(10)]
    for tid, arm in existing:
        p = root / "episodes" / tid / arm / "episode.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"status": "APPLIED"}), encoding="utf-8")

    monkeypatch.setattr(drv, "run_episode_v21", fake_run)
    monkeypatch.setattr(drv, "_save_progress", lambda p: prog.update({"x": 1}))
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    new = drv._drive(existing + [("t10", "GOLD_HARD"), ("t11", "GOLD_HARD"),
                                 ("t12", "GOLD_HARD"), ("t13", "GOLD_HARD"),
                                 ("t14", "GOLD_HARD"), ("t15", "GOLD_HARD"),
                                 ("t16", "GOLD_HARD"), ("t17", "GOLD_HARD")],
                     ledger=ledger, client=None, cache=None, prog=prog, root=root,
                     stop_file=tmp_path / "no_stop", max_new_episodes=8)
    assert new == 8
    assert len(calls) == 8


def test_partial_success_repair_transport_fail_preserves_initial(tmp_path: Path, monkeypatch) -> None:
    """Initial succeeds (raw+ledger+call persisted); repair transport-fails:
    the GENERATION_FAIL record must keep the initial call metadata (not [])."""
    _patch_episode_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    bad = ("FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    WRONG\n"
           "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")

    class FailRepairClient:
        def __init__(self):
            self.calls = 0

        def generate_messages(self, messages):
            self.calls += 1
            if self.calls == 1:
                return CallResult(text=bad, finish_reason="stop", prompt_tokens=100,
                                  completion_tokens=10, cost_usd=0.001,
                                  route="openrouter:qwen@deepinfra",
                                  provider="deepinfra/turbo", latency_s=0.0,
                                  request_id="gen-1")
            raise GenerationFail("after 4 attempts; terminal_reason=EXHAUSTED_RETRYABLE")

    cache = ResponseCache(root)
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    ep = gv21.run_episode_v21("saleor-rc-39b4138e8550", "GOLD_HARD",
                              FailRepairClient(), ledger, cache, root)
    assert ep["status"] == "GENERATION_FAIL"
    assert ep["repair_used"] is True
    assert len(ep["calls"]) == 1
    assert ep["calls"][0]["kind"] == "initial"
    assert ep["calls"][0]["provider_call"] is True
    assert ep["calls"][0]["raw_file"].endswith("1_initial.txt")
    # raw response file persisted
    raw = root / "episodes" / "saleor-rc-39b4138e8550" / "GOLD_HARD" / "calls" / "1_initial.txt"
    assert raw.exists()
    assert raw.read_text(encoding="utf-8") == bad
    # ledger has the initial call recorded
    assert len(ledger._path.read_text(encoding="utf-8").splitlines()) == 1


def test_hold_prevents_call(tmp_path: Path, monkeypatch) -> None:
    _patch_episode_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    (root / "HOLD").parent.mkdir(parents=True, exist_ok=True)
    (root / "HOLD").write_text("", encoding="utf-8")
    cache = ResponseCache(root)

    from benchmark.wp2.e2e_v21.transport import V21HttpClient

    def boom_post(body, headers):
        raise AssertionError("must not reach network")

    client = V21HttpClient(hold_file=root / "HOLD", raw_post=boom_post,
                           sleep=lambda _s: None)

    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    ep = gv21.run_episode_v21("saleor-rc-39b4138e8550", "GOLD_HARD",
                              client, ledger, cache, root)
    assert ep["status"] == "GENERATION_FAIL"
    assert "HOLD_ACTIVE" in ep["flags"][-1]
    # no provider calls
    assert sum(c["provider_call"] for c in ep["calls"]) == 0


def test_no_v2_path_written_and_no_v2_cache_read(tmp_path: Path, monkeypatch) -> None:
    v2_root = Path(__file__).resolve().parents[4] / "research/wp2/e2e_smoke_eng_v2"
    before_ep = list((v2_root / "episodes").rglob("episode.json"))
    before_cache = list((v2_root / "cache").rglob("*.json"))

    _patch_episode_deps(monkeypatch, tmp_path)
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"
    client = _scripted_client(_gold_patch_response())
    cache = ResponseCache(root)
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    ep = gv21.run_episode_v21("saleor-rc-39b4138e8550", "GOLD_HARD",
                              client, ledger, cache, root)
    assert ep["status"] == "APPLIED"
    assert client.calls == 1

    after_ep = list((v2_root / "episodes").rglob("episode.json"))
    after_cache = list((v2_root / "cache").rglob("*.json"))
    assert [p for p in after_ep if p not in before_ep] == []
    assert [p for p in after_cache if p not in before_cache] == []
    # v21 writes landed under the tmp root only
    assert (root / "episodes" / "saleor-rc-39b4138e8550" / "GOLD_HARD" / "episode.json").exists()
    assert list((root / "cache" / "responses").glob("*.json"))


def test_noscope_uses_zero_provider_calls(tmp_path: Path, monkeypatch) -> None:
    scope = {"editable": [], "excluded_large": [], "excluded_budget": [], "raw": []}
    monkeypatch.setattr(gv21, "editable_filter", lambda tid, arm: scope)
    monkeypatch.setattr(gv21, "_raw_scope", lambda tid, arm: [])
    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v21"

    class Client:
        def __init__(self):
            self.calls = 0

        def generate_messages(self, messages):
            self.calls += 1
            raise AssertionError("NO_SCOPE must not call the provider")

    cache = ResponseCache(root)
    ledger = LedgerV21(tmp_path / "ledger.jsonl", {"SMOKE": 2.00})
    ep = gv21.run_episode_v21("saleor-rc-39b4138e8550", "GOLD_HARD",
                              Client(), ledger, cache, root)
    assert ep["status"] == "NO_SCOPE"
    assert ep["calls"] == []
    assert len(ledger._path.read_text(encoding="utf-8").splitlines() if ledger._path.exists() else []) == 0


def test_generation_fail_record_never_replaces_calls_with_empty(tmp_path: Path, monkeypatch) -> None:
    rec = gv21._generation_fail_rec("t1", "GOLD_HARD",
                                    [{"kind": "initial", "provider_call": True}],
                                    "TransportError: boom")
    assert rec["calls"] == [{"kind": "initial", "provider_call": True}]
    assert rec["status"] == "GENERATION_FAIL"
    assert "TransportError: boom" in rec["flags"][-1]
