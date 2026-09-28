"""WP-2 Mission-11 B10 - shared E2E instrument unit tests (ZERO API)."""

from __future__ import annotations

from pathlib import Path

import pytest

from benchmark.wp2.e2e.spec import (
    ARMS,
    CEILING_AGENT_USD,
    CEILING_SMOKE_USD,
    CEILING_TOTAL_USD,
    MAX_CONTEXT_CHARS,
    MAX_FILE_CHARS,
    MAX_REPAIRS,
    MAX_TOKENS,
    MODEL,
    PLACEBO_SALT,
    REPS,
    SMOKE_TASKS,
    SMOKE_VERSION,
    STATE_TIMEOUT_S,
    TEMPERATURE,
    TOP_P,
    spec_sha256,
)


# B1.2 spec constants
def test_spec_constants() -> None:
    assert SMOKE_VERSION == "wp2-e2e-smoke-eng-v1"
    assert ARMS == ("GOLD_HARD", "RMCSS_HARD", "AGENT_HARD", "PLACEBO_HARD")
    assert len(SMOKE_TASKS) == 14
    assert MODEL == "qwen/qwen3-coder"
    assert TEMPERATURE == 0.0
    assert TOP_P == 1.0
    assert MAX_TOKENS == 8192
    assert MAX_REPAIRS == 1
    assert MAX_FILE_CHARS == 120_000
    assert MAX_CONTEXT_CHARS == 300_000
    assert PLACEBO_SALT == "wp2-e2e-smoke-placebo-v1"
    assert CEILING_AGENT_USD == 1.00
    assert CEILING_SMOKE_USD == 4.50
    assert CEILING_TOTAL_USD == 5.50
    assert REPS == 3
    assert STATE_TIMEOUT_S == 7200
    assert len(spec_sha256()) == 64


# B2.2 task inputs rendering
def test_task_input_rendering() -> None:
    from benchmark.wp2.e2e.task_inputs import load_task_input
    ti = load_task_input("saleor-rc-39b4138e8550")
    assert ti.task_id == "saleor-rc-39b4138e8550"
    assert ti.parent_commit and ti.target_commit
    assert ti.intent_source_sha256
    assert ti.developer_change_description_rendered.strip()  # verbatim intent


# B3 evaluator-sets import boundary
def test_evaluator_sets_raises_from_generator_module() -> None:
    fake = types.ModuleType("benchmark.wp2.e2e.prompt")
    ns = fake.__dict__
    exec("def call():\n    import benchmark.wp2.e2e.evaluator_sets as ev\n"
         "    return ev.load_evaluator_sets()\n", ns)
    sys.modules["benchmark.wp2.e2e.prompt"] = fake
    try:
        with pytest.raises(RuntimeError):
            ns["call"]()
    finally:
        sys.modules.pop("benchmark.wp2.e2e.prompt", None)


# B9 scoring
def test_scoring_synthetic() -> None:
    from benchmark.wp2.e2e.evaluate import score

    out = score("saleor-rc-2d45b76a52f2", "ctrl", {"C": {}, "U": {}})
    assert out["f2p_task"] in ("FAIL", "UNDEFINED")
    assert out["resolved"] is False


# B5 patch format
def test_patch_format_ok() -> None:
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch
    text = ("FILE: saleor/a.py\n<<<<<<< SEARCH\nx = 1\n=======\nx = 2\n>>>>>>> REPLACE\n")
    sections = parse_multi_file_patch(text)
    assert sections[0][0] == "saleor/a.py"
    out = apply_patch({"saleor/a.py": "x = 1\n"}, sections, {"saleor/a.py"})
    assert out["saleor/a.py"] == "x = 2\n"


def test_patch_format_test_path_error() -> None:
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch
    text = "FILE: saleor/tests/test_a.py\n<<<<<<< SEARCH\na\n=======\nb\n>>>>>>> REPLACE\n"
    sections = parse_multi_file_patch(text)
    with pytest.raises(ValueError) as ei:
        apply_patch({}, sections, set())
    assert "TEST_PATH" in str(ei.value)


def test_patch_format_out_of_scope() -> None:
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch
    text = "FILE: saleor/b.py\n<<<<<<< SEARCH\na\n=======\nb\n>>>>>>> REPLACE\n"
    sections = parse_multi_file_patch(text)
    with pytest.raises(ValueError) as ei:
        apply_patch({"saleor/b.py": "a\n"}, sections, {"saleor/a.py"})
    assert "OUT_OF_SCOPE_FILE" in str(ei.value)


def test_patch_format_search_not_found() -> None:
    from benchmark.wp2.e2e.patch_format import apply_patch, parse_multi_file_patch
    text = "FILE: saleor/a.py\n<<<<<<< SEARCH\nzzz\n=======\nb\n>>>>>>> REPLACE\n"
    sections = parse_multi_file_patch(text)
    with pytest.raises(ValueError) as ei:
        apply_patch({"saleor/a.py": "a\n"}, sections, {"saleor/a.py"})
    assert "SEARCH" in str(ei.value)


# B6 prompt + leakage
def test_prompt_build_and_leakage() -> None:
    from benchmark.wp2.e2e.prompt import build_prompt, leakage_scan
    from benchmark.wp2.e2e.task_inputs import load_task_input
    ti = load_task_input("saleor-rc-39b4138e8550")
    system, user, sha = build_prompt(ti, ["saleor/a.py"], {"saleor/a.py": "x = 1\n"},
                                     {"LARGE_FILE_EXCLUDED": [], "CONTEXT_BUDGET_EXCLUDED": []})
    assert "DEVELOPER CHANGE DESCRIPTION" in user
    assert "===== FILE: saleor/a.py" in user
    assert sha
    leaks = leakage_scan(user, {"f2p_ids": ["secret-node"], "changed_test_paths": [],
                                "target_added_lines": []})
    assert leaks["blocking"] == []
    leaks2 = leakage_scan(user.replace("x = 1", "secret-node"), {"f2p_ids": ["secret-node"]})
    assert leaks2["blocking"]


# B7 ledger
def test_ledger_ceiling_and_reload(tmp_path: Path) -> None:
    from benchmark.wp2.e2e.llm_client import Ledger
    p = tmp_path / "ledger.jsonl"
    led = Ledger(p, {"SMOKE": 4.50, "AGENT": 1.00})
    assert led.can_spend(0.5) is True
    led.record({"stage": "SMOKE", "cost_usd": 4.40, "request_id": "a"})
    assert led.can_spend(0.5) is False
    led2 = Ledger(p, {"SMOKE": 4.50, "AGENT": 1.00})
    assert led2.total() == pytest.approx(4.40)


# B7 ReplayClient determinism
def test_replay_client_deterministic() -> None:
    from benchmark.wp2.e2e.llm_client import ReplayClient
    c = ReplayClient({})
    r1 = c.generate("s", "hello")
    r2 = c.generate("s", "hello")
    assert r1.text == r2.text == ""
    assert r1.cost_usd == 0.0


# B8 generate episodes
def test_generate_valid_episode(monkeypatch, tmp_path: Path) -> None:
    from benchmark.wp2.e2e import generate as gen
    from benchmark.wp2.e2e.generate import run_episode
    from benchmark.wp2.e2e.llm_client import Ledger, ReplayClient
    monkeypatch.setattr(gen, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})
    monkeypatch.setattr(gen, "editable_filter",
                        lambda tid, arm: {"editable": ["saleor/x/models.py"],
                                          "excluded_large": [], "excluded_budget": []})
    monkeypatch.setattr(gen, "_parent_texts",
                        lambda tid, paths: {"saleor/x/models.py": "class A:\n    pass\n"})
    good = ("FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    pass\n"
            "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")

    class C:
        def generate(self, system, user):
            return ReplayClient({}).generate(system, good)

    led = Ledger(tmp_path / "l.jsonl", {"SMOKE": 4.50, "AGENT": 1.00})
    ep = run_episode("saleor-rc-39b4138e8550", "GOLD_HARD", C(), led)
    assert ep["status"] in ("APPLIED", "INVALID_AFTER_REPAIR")
    assert ep["task_id"] == "saleor-rc-39b4138e8550"
    assert ep["arm"] == "GOLD_HARD"


import sys  # noqa: E402
import types  # noqa: E402
