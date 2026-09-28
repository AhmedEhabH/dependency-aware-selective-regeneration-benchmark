"""Mission-12 instrument-v2 unit tests (D/E/F/G): zero API.

Covers: replay guard (I1), repair context (I2), cache (I3), finish_reason (I4),
raw responses (I5), envelope (I6), whitespace-match (I7), ellipsis (I8),
no-secret persistence (I9).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from benchmark.wp2.e2e.generate import ReplayInPaidEvidenceError as GenReplayError
from benchmark.wp2.e2e.generate_v2 import (
    ReplayInPaidEvidenceError,
    _persist_episode_v2,
    run_episode_v2,
)
from benchmark.wp2.e2e.llm_client import CallResult, OpenRouterClient, ReplayClient
from benchmark.wp2.e2e.patch_format import (
    apply_patch_v2,
    extract_envelope,
    parse_multi_file_patch_v2,
)
from benchmark.wp2.e2e.prompt import build_repair_messages
from benchmark.wp2.e2e.response_cache import ResponseCache


# ---------------------------------------------------------------------------
# I1 replay guard (F01)
# ---------------------------------------------------------------------------
def test_replay_guard_blocks_paid_root(tmp_path: Path) -> None:
    rec = {
        "smoke_version": "wp2-e2e-smoke-eng-v2", "task_id": "t1", "arm": "GOLD_HARD",
        "status": "INVALID_AFTER_REPAIR", "editable_set": [], "excluded": {},
        "calls": [{"kind": "initial", "route": "replay", "provider": "replay",
                   "prompt_tokens": 1, "completion_tokens": 0, "cost_usd_actual": 0.0,
                   "cost_usd_nominal": 0.0, "finish_reason": "stop", "latency_s": 0.0,
                   "response_sha256": ""}],
        "validation": {}, "repair_used": False, "edited_files": [], "diff_sha256": "",
        "flags": [], "spec_sha256": "", "created_utc": "", "episode_sha256": "",
    }
    paid = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v2"
    with pytest.raises(ReplayInPaidEvidenceError):
        _persist_episode_v2(paid, rec, [], {})
    with pytest.raises(GenReplayError):
        from benchmark.wp2.e2e import generate as gen
        gen.E2E_ROOT = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v1"
        gen._persist_episode(rec, [], {})


def test_replay_guard_allows_control_root(tmp_path: Path) -> None:
    rec = {
        "smoke_version": "wp2-e2e-smoke-eng-v2", "task_id": "t1", "arm": "GOLD_HARD",
        "status": "APPLIED", "editable_set": [], "excluded": {},
        "calls": [{"kind": "initial", "route": "replay", "provider": "replay",
                   "prompt_tokens": 1, "completion_tokens": 0, "cost_usd_actual": 0.0,
                   "cost_usd_nominal": 0.0, "finish_reason": "stop", "latency_s": 0.0,
                   "response_sha256": ""}],
        "validation": {}, "repair_used": False, "edited_files": [],
        "diff_sha256": "", "flags": [], "spec_sha256": "", "created_utc": "",
        "episode_sha256": "",
    }
    controls = tmp_path / "controls"
    _persist_episode_v2(controls, rec, ["diff"], {"x": "y"})
    assert (controls / "episodes" / "t1" / "GOLD_HARD" / "episode.json").exists()


# ---------------------------------------------------------------------------
# I2 repair context (D2)
# ---------------------------------------------------------------------------
def test_repair_messages_exact_four_roles() -> None:
    msgs = build_repair_messages("SYS", "ORIG", "PREV", ["PARSE_ERROR:x"])
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
    assert msgs[0]["content"] == "SYS"
    assert msgs[1]["content"] == "ORIG"          # byte-for-byte original user
    assert msgs[2]["content"] == "PREV"          # byte-for-byte previous output
    assert "PARSE_ERROR:x" in msgs[3]["content"]  # repair instruction


def test_repair_messages_hint_only_for_ellipsis() -> None:
    msgs = build_repair_messages("S", "U", "P", ["SEARCH_ELLIPSIS:a"], hint_ellipsis=True)
    assert "never abbreviate" in msgs[3]["content"]
    msgs2 = build_repair_messages("S", "U", "P", ["PARSE_ERROR:a"])
    assert "never abbreviate" not in msgs2[3]["content"]


def test_repair_messages_hashes_distinct_from_initial() -> None:
    import json as _json
    init = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
    rep = build_repair_messages("S", "U", "P", ["E"])
    assert _json.dumps(init, sort_keys=True) != _json.dumps(rep, sort_keys=True)


# ---------------------------------------------------------------------------
# I3 cache (E)
# ---------------------------------------------------------------------------
def test_cache_same_request_one_provider_call(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
    sha = ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192, msgs)
    assert cache.get(sha) is None
    cache.put(sha, {"request_sha": sha, "text": "RESP", "finish_reason": "stop"})
    entry = cache.get(sha)
    assert entry["text"] == "RESP"
    assert cache.get(sha) is not None  # survives restart semantics (re-open)
    assert cache.misses == 1 and cache.hits == 2


def test_cache_deterministic_serialization(tmp_path: Path) -> None:
    msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
    sha1 = ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192, msgs)
    sha2 = ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192,
                                     [{"role": "system", "content": "S"},
                                      {"role": "user", "content": "U"}])
    assert sha1 == sha2  # identical request -> identical hash
    msgs2 = [{"role": "user", "content": "U2"}, {"role": "system", "content": "S"}]
    assert sha1 != ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192, msgs2)


def test_cache_repair_never_overwrites_initial(tmp_path: Path) -> None:
    cache = ResponseCache(tmp_path)
    init = [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
    rep = build_repair_messages("S", "U", "PREV", ["E"])
    sha_init = ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192, init)
    sha_rep = ResponseCache.request_sha("m", "r", "p", 0.0, 1.0, 8192, rep)
    assert sha_init != sha_rep
    cache.put(sha_init, {"request_sha": sha_init, "text": "INIT"})
    cache.put(sha_rep, {"request_sha": sha_rep, "text": "REPAIR"})
    assert cache.get(sha_init)["text"] == "INIT"
    assert cache.get(sha_rep)["text"] == "REPAIR"


# ---------------------------------------------------------------------------
# I4 finish_reason (F04)
# ---------------------------------------------------------------------------
def test_finish_reason_length_truncated() -> None:
    from benchmark.wp2.e2e.generate_v2 import _validate_v2
    errors, final, blocks, stats = _validate_v2(
        "FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n",
        ["a.py"], {"a.py": "x\n"}, "length", "py312")
    assert errors == ["TRUNCATED"]
    assert final == {}


def test_finish_reason_stop_ok() -> None:
    from benchmark.wp2.e2e.generate_v2 import _validate_v2
    errors, final, blocks, stats = _validate_v2(
        "FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n",
        ["a.py"], {"a.py": "x\n"}, "stop", "py312")
    assert errors == []
    assert final == {"a.py": "y\n"}


# ---------------------------------------------------------------------------
# I5 raw responses (F05)
# ---------------------------------------------------------------------------
def test_raw_response_persisted_and_hash_verified(tmp_path: Path) -> None:
    from benchmark.wp2.e2e.generate_v2 import _persist_raw
    p, digest = _persist_raw(tmp_path, "t1", "GOLD_HARD", 1, "initial", "HELLO")
    assert p.exists()
    assert p.read_text(encoding="utf-8") == "HELLO"
    assert digest == hashlib.sha256(b"HELLO").hexdigest()
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest


def test_utf8_roundtrip(tmp_path: Path) -> None:
    from benchmark.wp2.e2e.generate_v2 import _persist_raw
    text = "café \u4e2d\u6587 \U0001f600\n"
    p, digest = _persist_raw(tmp_path, "t1", "GOLD_HARD", 1, "initial", text)
    assert p.read_text(encoding="utf-8") == text
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest


# ---------------------------------------------------------------------------
# I6 envelope (I01)
# ---------------------------------------------------------------------------
def test_envelope_preamble_prose() -> None:
    text = ("Looking at the change description...\n\n"
            "```python\nFILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n```\n")
    clean, stats = extract_envelope(text)
    assert stats["preamble_lines"] == 3
    assert stats["fence_lines"] == 0
    assert stats["trailing_lines"] == 1  # closing fence is trailing (I01 rule c)
    assert clean.startswith("FILE: a.py")
    assert "```" not in clean


def test_envelope_mid_output_fence_counted() -> None:
    text = ("FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n"
            "```\nFILE: b.py\n<<<<<<< SEARCH\np\n=======\nq\n>>>>>>> REPLACE\n")
    clean, stats = extract_envelope(text)
    assert stats["fence_lines"] == 1  # fence between two FILE sections
    assert "```" not in clean
    assert clean.count("FILE:") == 2


def test_envelope_interstitial_prose_between_files() -> None:
    text = ("FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n"
            "and also fix b\n"
            "FILE: b.py\n<<<<<<< SEARCH\np\n=======\nq\n>>>>>>> REPLACE\n"
            "done now")
    clean, stats = extract_envelope(text)
    assert stats["interstitial_lines"] == 1
    assert stats["trailing_lines"] == 1
    assert clean.count("FILE:") == 2
    assert "and also fix b" not in clean
    assert "done now" not in clean


def test_envelope_body_bytes_never_altered() -> None:
    search = "x  \nkeep  \n"
    replace = "y  \n"
    text = f"preamble\nFILE: a.py\n<<<<<<< SEARCH\n{search}=======\n{replace}>>>>>>> REPLACE\n"
    clean, _ = extract_envelope(text)
    assert search in clean
    assert replace in clean
    assert "preamble" not in clean


# ---------------------------------------------------------------------------
# I7 whitespace matching (I02)
# ---------------------------------------------------------------------------
def test_whitespace_tolerant_unique_match() -> None:
    parent = {"a.py": "x   \nkeep   \nz\n"}
    patch = "FILE: a.py\n<<<<<<< SEARCH\nx\nkeep\n=======\nx2\nkeep2\n>>>>>>> REPLACE\n"
    sections, stats = parse_multi_file_patch_v2(patch)
    out, results = apply_patch_v2(parent, sections, {"a.py"})
    assert results[0]["mode"] == "WHITESPACE_TOLERANT"
    assert out["a.py"] == "x2\nkeep2\nz\n"


def test_whitespace_tolerant_ambiguous_rejected() -> None:
    parent = {"a.py": "x\nkeep\n\nx\nkeep\nz\n"}
    patch = "FILE: a.py\n<<<<<<< SEARCH\nx\nkeep\n=======\nx2\nkeep2\n>>>>>>> REPLACE\n"
    sections, _ = parse_multi_file_patch_v2(patch)
    with pytest.raises(ValueError) as ei:
        apply_patch_v2(parent, sections, {"a.py"})
    assert "ambiguous" in str(ei.value) or "SEARCH_ERROR" in str(ei.value)


def test_exact_ambiguous_rejected() -> None:
    parent = {"a.py": "x\nx\n"}
    patch = "FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n"
    sections, _ = parse_multi_file_patch_v2(patch)
    with pytest.raises(ValueError):
        apply_patch_v2(parent, sections, {"a.py"})


def test_whitespace_zero_match_fails() -> None:
    parent = {"a.py": "zzz\n"}
    patch = "FILE: a.py\n<<<<<<< SEARCH\nx\n=======\ny\n>>>>>>> REPLACE\n"
    sections, _ = parse_multi_file_patch_v2(patch)
    with pytest.raises(ValueError) as ei:
        apply_patch_v2(parent, sections, {"a.py"})
    assert "not found" in str(ei.value)


# ---------------------------------------------------------------------------
# I8 ellipsis (I03)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("ellipsis_line", ["...", "…", "# ..."])
def test_ellipsis_rejected(ellipsis_line: str) -> None:
    patch = (f"FILE: a.py\n<<<<<<< SEARCH\n{ellipsis_line}\n"
             "=======\ny\n>>>>>>> REPLACE\n")
    with pytest.raises(ValueError) as ei:
        parse_multi_file_patch_v2(patch)
    assert "SEARCH_ELLIPSIS" in str(ei.value)


# ---------------------------------------------------------------------------
# I9 security / no secrets
# ---------------------------------------------------------------------------
def test_no_secret_in_persisted_metadata(tmp_path: Path) -> None:
    from benchmark.wp2.e2e.generate_v2 import _persist_raw
    _persist_raw(tmp_path, "t1", "GOLD_HARD", 1, "initial", "plain response text")
    rec = {
        "smoke_version": "wp2-e2e-smoke-eng-v2", "task_id": "t1", "arm": "GOLD_HARD",
        "status": "APPLIED", "editable_set": [], "excluded": {},
        "calls": [{"kind": "initial", "route": "openrouter:qwen@deepinfra",
                   "provider": "deepinfra/turbo", "prompt_tokens": 1,
                   "completion_tokens": 0, "cost_usd_actual": 0.0,
                   "cost_usd_nominal": 0.0, "finish_reason": "stop", "latency_s": 0.0,
                   "response_sha256": "a", "raw_file": "calls/1_initial.txt",
                   "raw_sha256": "b"}],
        "validation": {}, "repair_used": False, "edited_files": [],
        "diff_sha256": "", "flags": [], "spec_sha256": "", "created_utc": "",
        "episode_sha256": "",
    }
    _persist_episode_v2(tmp_path / "controls", rec, [], {})
    ep_json = (tmp_path / "controls" / "episodes" / "t1" / "GOLD_HARD" / "episode.json")
    payload = json.dumps(rec) + ep_json.read_text(encoding="utf-8")
    assert "Bearer" not in payload
    assert "Authorization" not in payload
    assert "sk-" not in payload


# ---------------------------------------------------------------------------
# Wrapper equivalence (D1.3) + role ordering (D1.4)
# ---------------------------------------------------------------------------
def test_openrouter_generate_wraps_generate_messages(monkeypatch) -> None:
    client = OpenRouterClient(api_key_env="M12_TEST_KEY")
    monkeypatch.setenv("M12_TEST_KEY", "test-key")

    calls = []

    def fake_generate_messages(self, messages):
        calls.append(messages)
        return CallResult(text="ok", finish_reason="stop", prompt_tokens=1,
                          completion_tokens=1, cost_usd=0.0, route="r",
                          provider="p", latency_s=0.0, request_id="rid")

    monkeypatch.setattr(OpenRouterClient, "generate_messages", fake_generate_messages)
    out = client.generate("SYS", "USER")
    assert out.text == "ok"
    assert calls[0] == [{"role": "system", "content": "SYS"},
                        {"role": "user", "content": "USER"}]


def test_replay_generate_wraps_generate_messages() -> None:
    c = ReplayClient({})
    r = c.generate("SYS", "USER")
    assert r.text == ""
    assert c.calls and c.calls[0][0]  # sha of the whole messages list
    assert r.route == "replay"


# ---------------------------------------------------------------------------
# run_episode_v2: full-context repair executes with exact four-message request
# ---------------------------------------------------------------------------
def test_run_episode_v2_repair_path(monkeypatch, tmp_path: Path) -> None:
    from benchmark.wp2.e2e import generate_v2 as gv2
    from benchmark.wp2.e2e.llm_client import Ledger

    scope = {"editable": ["saleor/x/models.py"],
             "excluded_large": [], "excluded_budget": [], "raw": ["saleor/x/models.py"]}
    monkeypatch.setattr(gv2, "py_compile_in_era", lambda era, files: {p: "ok" for p in files})
    monkeypatch.setattr(gv2, "editable_filter", lambda tid, arm: scope)
    monkeypatch.setattr(gv2, "_raw_scope", lambda tid, arm: ["saleor/x/models.py"])
    monkeypatch.setattr(gv2, "_parent_texts",
                        lambda tid, paths: {"saleor/x/models.py": "class A:\n    pass\n"})

    bad = ("Looking at this change, I will fix the bug.\n\n"
           "FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    WRONG\n"
           "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")
    good = ("FILE: saleor/x/models.py\n<<<<<<< SEARCH\nclass A:\n    pass\n"
            "=======\nclass A:\n    x = 1\n>>>>>>> REPLACE\n")

    captured: list[list[dict]] = []

    class ScriptedClient:
        def generate_messages(self, messages):
            captured.append(messages)
            text = bad if len(captured) == 1 else good
            return CallResult(text=text, finish_reason="stop", prompt_tokens=100,
                              completion_tokens=len(text) // 4, cost_usd=0.0,
                              route="openrouter:qwen/qwen3-coder@deepinfra/turbo",
                              provider="deepinfra/turbo", latency_s=0.0,
                              request_id=f"gen-{len(captured)}")

    root = tmp_path / "research" / "wp2" / "e2e_smoke_eng_v2"
    cache = ResponseCache(root)
    led = Ledger(tmp_path / "l.jsonl", {"SMOKE": 2.00})
    ep = run_episode_v2("saleor-rc-39b4138e8550", "GOLD_HARD", ScriptedClient(), led, cache, root)
    assert ep["status"] == "APPLIED"
    assert ep["repair_used"] is True
    assert len(captured) == 2
    # repair request is the exact four-message structure
    roles = [m["role"] for m in captured[1]]
    assert roles == ["system", "user", "assistant", "user"]
    assert captured[1][1]["content"] == captured[0][1]["content"]  # original user byte-for-byte
    assert captured[1][2]["content"] == bad  # previous assistant output byte-for-byte
    assert "Problems:" in captured[1][3]["content"]
    # episode raw files exist
    raw_files = list((root / "episodes" / "saleor-rc-39b4138e8550" / "GOLD_HARD" / "calls").glob("*.txt"))
    assert len(raw_files) == 2
    # no replay route persisted into paid root (F01)
    assert all(c["route"] != "replay" for c in ep["calls"])
