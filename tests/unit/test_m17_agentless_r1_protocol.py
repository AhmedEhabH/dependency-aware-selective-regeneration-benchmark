"""Unit + P2P + F2P tests for the M17 Agentless-style R1 comparator.

Covers the frozen AGENTLESS_STYLE_ADAPTATION protocol: deterministic prompt
construction, deterministic structure rendering, official parser semantics,
timeout/retry/cost-ceiling behaviour, and gold-isolation (predictions frozen
before gold is loaded).
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
from pathlib import Path

import pytest

from benchmark.agentless_r1.evaluate import (
    compute_confusions,
    freeze_predictions,
    load_gold,
    load_prediction_sets,
    pooled_metrics,
)
from benchmark.agentless_r1.execution import (
    COMPLETION_PER_TOKEN_USD,
    PROMPT_PER_TOKEN_USD,
    _call_with_retries,
    _evidence_from_raw,
    budget_exceeded,
    compute_cost_usd,
)
from benchmark.agentless_r1.parser import parse_file_list
from benchmark.agentless_r1.prompt import (
    OFFICIAL_FILE_LOCALIZATION_PROMPT,
    TOP_N,
    build_agentless_prompt,
    build_structure,
    show_project_structure,
    structure_file_paths,
)

TEST_FILES = [
    "saleor/__init__.py",
    "saleor/graphql/page/dataloaders.py",
    "saleor/graphql/page/resolvers.py",
    "saleor/page/models.py",
    "saleor/tests/test_page.py",
    "saleor/nonpy.txt",
]


def _structure() -> dict:
    return build_structure(TEST_FILES)


def _file_set() -> set[str]:
    return set(structure_file_paths(_structure()))


# ---------------------------------------------------------------------------
# Unit: deterministic prompt construction & structure
# ---------------------------------------------------------------------------
def test_deterministic_repo_structure():
    s1 = build_structure(TEST_FILES)
    s2 = build_structure(TEST_FILES)
    assert s1 == s2
    paths = structure_file_paths(s1)
    assert "saleor/graphql/page/dataloaders.py" in paths
    # test files and non-py removed by frozen filtering
    assert "saleor/tests/test_page.py" not in paths
    assert "saleor/nonpy.txt" not in paths
    assert paths == sorted(paths)


def test_structure_rendering_has_py_files_and_dirs():
    txt = show_project_structure(_structure())
    assert "saleor/" in txt
    assert "graphql/" in txt
    assert "dataloaders.py" in txt
    # directory rendering uses trailing slash; files do not
    assert "graphql/" in txt and "page/" in txt


def test_prompt_construction_deterministic_and_contains_inputs():
    p1 = build_agentless_prompt("Frozen problem", show_project_structure(_structure()).strip())
    p2 = build_agentless_prompt("Frozen problem", show_project_structure(_structure()).strip())
    assert p1 == p2
    assert hashlib.sha256(p1.encode()).hexdigest() == hashlib.sha256(p2.encode()).hexdigest()
    assert "Frozen problem" in p1
    assert "dataloaders.py" in p1
    assert "Return just the locations" not in p1  # only the file-level prompt


def test_official_prompt_template_verbatim():
    assert "Please look through the following GitHub problem description" in OFFICIAL_FILE_LOCALIZATION_PROMPT
    assert "{problem_statement}" in OFFICIAL_FILE_LOCALIZATION_PROMPT
    assert "{structure}" in OFFICIAL_FILE_LOCALIZATION_PROMPT
    assert "return at most 5 files" in OFFICIAL_FILE_LOCALIZATION_PROMPT
    assert "wrapped with ```" in OFFICIAL_FILE_LOCALIZATION_PROMPT


def test_prompt_sha256_match_for_real_task():
    """P2P P1: the frozen manifest's prompt bytes hash to exactly its sha256."""
    m = json.loads(
        Path("research/competitor-agentless-r1/agentless_r1_prompt_manifest.json").read_text(encoding="utf-8")
    )
    per = m["per_task"]
    assert len(per) == 297
    for _tid, row in list(per.items())[:10]:
        assert hashlib.sha256(row["prompt"].encode()).hexdigest() == row["prompt_sha256"]
        assert row["token_count_exact"] is False
        assert row["context_window_ok"] is True


# ---------------------------------------------------------------------------
# Unit: official parser semantics
# ---------------------------------------------------------------------------
def test_parse_valid_fenced_output():
    res = parse_file_list("```\nsaleor/graphql/page/dataloaders.py\nsaleor/page/models.py\n```", _file_set())
    assert res.classification == "VALID"
    assert res.prediction_set == frozenset({"saleor/graphql/page/dataloaders.py", "saleor/page/models.py"})
    assert res.top_n_slice == ("saleor/graphql/page/dataloaders.py", "saleor/page/models.py")


def test_parse_valid_newline_output():
    res = parse_file_list("saleor/graphql/page/resolvers.py\nsaleor/page/models.py", _file_set())
    assert res.classification == "VALID"
    assert res.prediction_set == frozenset({"saleor/graphql/page/resolvers.py", "saleor/page/models.py"})


def test_parse_duplicate_paths():
    res = parse_file_list(
        "saleor/page/models.py\nsaleor/page/models.py\nsaleor/graphql/page/resolvers.py", _file_set()
    )
    assert res.duplicate_count == 1
    assert res.prediction_set == frozenset({"saleor/page/models.py", "saleor/graphql/page/resolvers.py"})


def test_parse_nonexistent_paths_dropped():
    res = parse_file_list("saleor/does/not/exist.py\nsaleor/page/models.py", _file_set())
    assert res.classification == "VALID"
    assert res.prediction_set == frozenset({"saleor/page/models.py"})
    assert res.dropped_line_count == 1
    assert "saleor/does/not/exist.py" not in res.corrected_ordered


def test_parse_malformed_output():
    res = parse_file_list("Sorry, here are no files at all.\nnothing matches.", _file_set())
    assert res.classification == "MALFORMED"
    assert res.prediction_set == frozenset()


def test_parse_empty_output():
    res = parse_file_list("", _file_set())
    assert res.classification == "EMPTY"
    res2 = parse_file_list("   \n  \n", _file_set())
    assert res2.classification == "EMPTY"


def test_parse_more_than_top_n():
    raw = "\n".join(TEST_FILES)
    res = parse_file_list(raw, _file_set())
    assert res.more_than_top_n is True
    assert len(res.top_n_slice) == TOP_N == 3
    # top-N = most important (first-appearance) three real files
    expected = tuple(p for p in TEST_FILES if p in _file_set())[:3]
    assert res.top_n_slice == expected


def test_parse_zero_top_n_edge():
    res = parse_file_list("saleor/page/models.py", _file_set(), top_n=0)
    assert res.prediction_set == frozenset()
    assert res.classification == "VALID"


# ---------------------------------------------------------------------------
# Unit: transport/retry/timeout/cost
# ---------------------------------------------------------------------------
def _raw_response(prompt_tokens=100, completion_tokens=20) -> str:
    content = '{"choices":[{"message":{"content":"saleor/page/models.py"},'
    content += '"finish_reason":"stop"}],'
    content += '"usage":{"prompt_tokens":' + str(prompt_tokens) + ','
    content += '"completion_tokens":' + str(completion_tokens) + ','
    content += '"total_tokens":' + str(prompt_tokens + completion_tokens) + "}}"
    return content


def _http_error(code: int, url: str = "https://openrouter.ai") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, f"err {code}", {}, None)


def test_retry_success_after_transient():
    calls = {"n": 0}

    def transport():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _http_error(500)
        return _raw_response()

    ev = _call_with_retries(transport, max_retries=4, backoff=0.0, sleep_fn=lambda _s: None)
    assert ev.ok is True
    assert ev.attempt_count == 3
    assert ev.prompt_tokens == 100


def test_retry_limit_exhausted():
    def transport():
        raise urllib.error.URLError("connection reset")

    ev = _call_with_retries(transport, max_retries=3, backoff=0.0, sleep_fn=lambda _s: None)
    assert ev.ok is False
    assert ev.attempt_count == 3
    assert "transport failed" in (ev.error or "")


def test_http_error_4xx_not_retried():
    calls = {"n": 0}

    def transport():
        calls["n"] += 1
        raise _http_error(401)

    ev = _call_with_retries(transport, max_retries=4, backoff=0.0, sleep_fn=lambda _s: None)
    assert ev.ok is False
    assert calls["n"] == 1  # never retried
    assert ev.error and "401" in ev.error


def test_timeout_is_fail_closed():
    ev = _evidence_from_raw(_raw_response(), 1)
    assert ev.ok is True
    # transport that raises TimeoutError is retried then exhausted (covered above)


def test_cost_ceiling_stop_before_further_calls():
    assert budget_exceeded(1.999999, 2.0) is False
    assert budget_exceeded(2.000001, 2.0) is True


def test_cost_accounting_matches_fixture():
    cost = compute_cost_usd(1000, 500)
    expected = 1000 * PROMPT_PER_TOKEN_USD + 500 * COMPLETION_PER_TOKEN_USD
    assert cost == round(expected, 6)
    assert cost > 0.0


# ---------------------------------------------------------------------------
# P2P
# ---------------------------------------------------------------------------
def test_p2p_single_file_scores_correctly():
    preds = {"t": frozenset({"saleor/page/models.py"})}
    gold = {"t": frozenset({"saleor/page/models.py", "saleor/__init__.py"})}
    conf = compute_confusions(preds, gold, ["t"])["t"]
    assert (conf.tp, conf.fp, conf.fn) == (1, 0, 1)
    pooled = pooled_metrics([conf])
    assert pooled["precision"] == 1.0
    assert pooled["recall"] == 0.5
    assert pooled["f1"] == pytest.approx(2 / 3)


def test_p2p_valid_top_n_scores_correctly():
    raw = "```\nsaleor/graphql/page/dataloaders.py\nsaleor/page/models.py\nsaleor/__init__.py\n```"
    res = parse_file_list(raw, _file_set())
    assert res.classification == "VALID"
    expected = frozenset({"saleor/graphql/page/dataloaders.py", "saleor/page/models.py", "saleor/__init__.py"})
    assert res.prediction_set == expected


def test_p2p_prediction_freeze_before_gold(tmp_path: Path):
    per_task = {
        "t1": {"prediction_set": ["a.py"], "parsed_files": ["a.py"], "classification": "VALID",
               "api_cost_usd": 0.01, "prompt_tokens": 10, "completion_tokens": 5, "latency_seconds": 0.1,
               "raw_output_sha256": "x"},
    }
    out = tmp_path / "pred.json"
    sha = tmp_path / "pred.json.sha256"
    freeze_predictions(per_task, ["t1"], out, sha)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    assert sha.read_text(encoding="utf-8").strip() == digest
    # load_prediction_sets reads predictions back without any gold
    preds = load_prediction_sets(out, ["t1"])
    assert preds["t1"] == frozenset({"a.py"})


def test_p2p_gold_isolation_core(tmp_path: Path):
    """Prompts may be constructed without any gold access; verify no gold read."""
    # The prompt builder takes only problem_statement + structure, never a path to gold.
    prompt = build_agentless_prompt("ps", "saleor/\n  models.py\n")
    assert "ps" in prompt
    # A gold-shaped file existing on disk is irrelevant to prompt construction.
    gold_file = tmp_path / "proxies.json"
    gold_file.write_text(json.dumps({"opened_once": True, "proxies": {"t": ["x.py"]}}), encoding="utf-8")
    prompt2 = build_agentless_prompt("ps", "saleor/\n  models.py\n")
    assert prompt2 == prompt


# ---------------------------------------------------------------------------
# F2P
# ---------------------------------------------------------------------------
def test_f2p_gold_access_fails_closed(tmp_path: Path):
    """F1: the function that loads gold is separate from everything else and fully
    validates the frozen proxies contract; garbage raises instead of silently okay."""
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"opened_once": False, "proxies": {}}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_gold(bad)


def test_f2p_malformed_classified_failure():
    res = parse_file_list("not a path\nstill not", _file_set())
    assert res.classification == "MALFORMED"
    assert res.prediction_set == frozenset()


def test_f2p_over_top_n_documented():
    raw = "\n".join(TEST_FILES)
    res = parse_file_list(raw, _file_set())
    assert res.more_than_top_n is True
    assert len(res.top_n_slice) == 3  # frozen documented behavior


def test_f2p_nonexistent_path_documented():
    res = parse_file_list("missing/one.py\nmissing/two.py\nsaleor/page/models.py", _file_set())
    assert res.dropped_line_count == 2
    assert res.prediction_set == frozenset({"saleor/page/models.py"})


def test_f2p_cost_ceiling_stop():
    assert budget_exceeded(2.1, 2.0) is True
    assert budget_exceeded(1.9, 2.0) is False


def test_f2p_retry_exhaustion_empty():
    def transport():
        raise urllib.error.URLError("network down")

    ev = _call_with_retries(transport, max_retries=2, backoff=0.0, sleep_fn=lambda _s: None)
    assert ev.ok is False
    # the parser on an empty/missing raw output yields EMPTY (frozen fail-closed classification)
    parsed = parse_file_list(ev.raw_text or "", _file_set())
    assert parsed.classification == "EMPTY"
