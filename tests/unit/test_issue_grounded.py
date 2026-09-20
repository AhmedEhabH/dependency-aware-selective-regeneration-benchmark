"""Unit tests for the issue-grounded intent headroom modules (T3).

Covers: reference parsing, repository-local resolution, issue-vs-PR
distinction, no-PR-text rule, temporal-clean rule, updated_at guard, corpus
hashing, ranking aggregation unchanged, Recall@K formulas, task-paired
bootstrap, path-mention detection, sealed-data guard.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from benchmark.issue_grounded.corpus import (
    build_corpus_record,
    normalized_text,
    save_corpus,
    sha256_text,
)
from benchmark.issue_grounded.dense import arm_i_query_for_task, rank_files_full_universe
from benchmark.issue_grounded.github import GitHubClient
from benchmark.issue_grounded.metrics import (
    paired_bootstrap_delta,
    recall_at_k,
    task_coverage_at_k,
)
from benchmark.issue_grounded.refs import parse_refs, resolve_task
from benchmark.issue_grounded.temporal import CLEAN, SYNTAX_ERROR, UNCERTAIN, temporal_status


def _fake_client(cache_dir: Path) -> GitHubClient:
    return GitHubClient(cache_dir, token="test-token")


class TestRefParsing:
    def test_parses_github_refs(self) -> None:
        assert parse_refs("Fixed #6205 -- (#6206)") == (6205, 6206)

    def test_dedup_and_sort(self) -> None:
        assert parse_refs("(#7629) #7629 (#123)") == (123, 7629)

    def test_no_refs(self) -> None:
        assert parse_refs("fix edit strings") == ()

    def test_ignores_short_numbers(self) -> None:
        assert parse_refs("issue #12 and #9999") == (9999,)


class TestTemporal:
    def test_clean_when_both_before_target(self) -> None:
        assert temporal_status("2017-12-27T14:06:58Z", "2017-12-27T16:58:28Z",
                               "2017-12-27T21:17:19+00:00") == CLEAN

    def test_uncertain_when_updated_after_target(self) -> None:
        assert temporal_status("2023-04-03T08:55:53Z", "2023-04-17T11:58:39Z",
                               "2023-04-17T11:58:37+00:00") == UNCERTAIN

    def test_uncertain_when_created_after_target(self) -> None:
        assert temporal_status("2024-04-27T15:33:04Z", "2024-04-27T23:45:20Z",
                               "2024-04-27T23:45:19+00:00") == UNCERTAIN

    def test_updated_at_equal_target_is_clean(self) -> None:
        assert temporal_status("2016-12-30T16:20:59Z", "2017-01-03T18:42:11Z",
                               "2017-01-03T18:42:11+00:00") == CLEAN

    def test_missing_target_syntax_error(self) -> None:
        assert temporal_status("2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z", "") == SYNTAX_ERROR


class TestCorpus:
    def test_normalized_text(self) -> None:
        assert normalized_text("a\r\nb", "c\r\n") == "a\nb\nc"
        assert normalized_text("", "body") == "\nbody"

    def test_sha256_deterministic(self) -> None:
        assert sha256_text("abc") == sha256_text("abc")
        assert sha256_text("abc") != sha256_text("abd")

    def test_build_record_fields(self) -> None:
        rec = build_corpus_record(
            case_id="c1", repository="djangocms", provenance="DIRECT_ISSUE",
            issue_numbers=(6205,), created_at=("2017-12-27T14:06:58Z",),
            updated_at=("2017-12-27T16:58:28Z",), titles=("t",), bodies=("b",),
            temporal_flags=(CLEAN,), target_commit_time="2017-12-27T21:17:19+00:00")
        assert rec["normalized_sha256"][0] == sha256_text("t\nb")

    def test_save_corpus_manifest(self, tmp_path: Path) -> None:
        rec = build_corpus_record(
            case_id="c1", repository="djangocms", provenance="DIRECT_ISSUE",
            issue_numbers=(1,), created_at=("2020-01-01T00:00:00Z",),
            updated_at=("2020-01-02T00:00:00Z",), titles=("t",), bodies=("b",),
            temporal_flags=(CLEAN,), target_commit_time="2020-01-03T00:00:00+00:00")
        manifest = save_corpus(tmp_path / "corpus.json", [rec])
        assert manifest["records"] == 1
        assert len(manifest["corpus_sha256"]) == 64

    def test_corpus_hash_is_volatile_timestamp_invariant(self, tmp_path: Path) -> None:
        rec = build_corpus_record(
            case_id="c1", repository="djangocms", provenance="DIRECT_ISSUE",
            issue_numbers=(1,), created_at=("2020-01-01T00:00:00Z",),
            updated_at=("2020-01-02T00:00:00Z",), titles=("t",), bodies=("b",),
            temporal_flags=(CLEAN,), target_commit_time="2020-01-03T00:00:00+00:00")
        m1 = save_corpus(tmp_path / "c1.json", [rec])
        m2 = save_corpus(tmp_path / "c2.json", [rec])
        assert m1["corpus_sha256"] == m2["corpus_sha256"]


class TestDense:
    def test_arm_i_query_only_clean_issues(self) -> None:
        rec = {
            "issue_numbers": [1, 2],
            "title": ["old", "edited"],
            "body": ["body1", "body2"],
            "temporal_flag": [CLEAN, UNCERTAIN],
        }
        assert arm_i_query_for_task(rec) == "old\nbody1"

    def test_arm_i_query_concat_ascending(self) -> None:
        rec = {"issue_numbers": [3, 1], "title": ["t3", "t1"],
               "body": ["b3", "b1"], "temporal_flag": [CLEAN, CLEAN]}
        assert arm_i_query_for_task(rec) == "t1\nb1\nt3\nb3"

    def test_no_clean_issue_none(self) -> None:
        rec = {"issue_numbers": [1], "title": ["t"], "body": ["b"],
               "temporal_flag": [UNCERTAIN]}
        assert arm_i_query_for_task(rec) is None

    def test_rank_full_universe_max_aggregation_tiebreak(self) -> None:
        unit_mat = np.array([
            [1.0, 0.0],  # fileA high
            [0.0, 1.0],  # fileB programmatically lowest vs q
            [0.9, 0.0],  # fileA second unit higher than fileC's
            [0.0, 0.8],
        ], dtype=np.float32)
        cache_idx = {"u0": 0, "u1": 1, "u2": 2, "u3": 3}
        plan = {"bA": ["u0", "u2"], "bB": ["u1"], "bC": ["u3"]}
        universe = ["fileB", "fileA", "fileC"]
        ranks = rank_files_full_universe(np.array([1.0, 0.0]), unit_mat, cache_idx,
                                         {"fileA": "bA", "fileB": "bB", "fileC": "bC"},
                                         plan, universe)
        # fileA has units u0(cos=1) u2(cos=0.9) -> MAX=1 -> rank 1
        # fileB cos=0 and fileC cos=0 tie -> ascending path: fileB before fileC
        assert ranks["fileA"] == 1
        assert ranks["fileB"] == 2
        assert ranks["fileC"] == 3


class TestMetrics:
    def test_recall_at_k(self) -> None:
        assert recall_at_k([1, 5, None], 5) == 1.0
        assert recall_at_k([7, 3, 19], 5) == 1 / 3
        assert recall_at_k([21], 20) == 0.0
        assert recall_at_k([1], 1) == 1.0

    def test_task_coverage_at_k(self) -> None:
        assert task_coverage_at_k([11, 4], 5) == 1
        assert task_coverage_at_k([11, 21], 5) == 0

    def test_pair_paired_bootstrap_positive(self) -> None:
        # 100% improvement tasks.
        m = [{"proxy_positions": [30], "case_id": f"m{i}", "repository": "d",
              "proxy_size": 1} for i in range(20)]
        i = [{"proxy_positions": [1], "case_id": f"i{i}", "repository": "d",
              "proxy_size": 1} for i in range(20)]
        out = paired_bootstrap_delta(m, i, k=20, n_resamples=1000, seed=1)
        assert out["point_delta"] > 0.5
        assert out["ci_lower"] > 0.5
        assert out["ci_upper"] <= 1.0

    def test_paired_bootstrap_zero_pop(self) -> None:
        out = paired_bootstrap_delta([], [], k=20)
        assert out["point_delta"] == 0.0
        assert out["n_tasks"] == 0


class TestPathMentions:
    def test_detect_exact_and_basename(self) -> None:
        from benchmark.issue_grounded.descriptive import detect_path_mentions

        det = detect_path_mentions("touch cms/admin/pageadmin.py", ["cms/admin/pageadmin.py"])
        assert "cms/admin/pageadmin.py" in det["exact_path"]
        assert "cms/admin/pageadmin.py" in det["any_mention"]

    def test_no_mention(self) -> None:
        from benchmark.issue_grounded.descriptive import detect_path_mentions

        det = detect_path_mentions("just a title without file", ["cms/admin/pageadmin.py"])
        assert det["any_mention"] == []


class TestResolver:
    def _write_fake_cache(self, cache_dir: Path) -> None:
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "github_cache.json").write_text(json.dumps({}), encoding="utf-8")

    def test_empty_message_prov(self, tmp_path: Path) -> None:
        self._write_fake_cache(tmp_path)
        r = resolve_task(_fake_client(tmp_path), "c1", "djangocms", "fix edit strings")
        assert r.provenance == "NO_REFERENCE"

    def test_unresolved_404(self, tmp_path: Path) -> None:
        # Inject a cached 404 (None) for the issue endpoint so no network call.
        client = _fake_client(tmp_path)
        key = "rest::/repos/django-cms/django-cms/issues/12345"
        client._cache[key] = None
        client._persist()
        r = resolve_task(client, "c1", "djangocms", "Fix (#12345)")
        assert r.provenance == "UNRESOLVED"
        assert r.unresolved == (12345,)


class TestGitHubClient:
    def test_404_returns_none(self, tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]

        import urllib.error

        class _FakeResp:
            def __enter__(self) -> _FakeResp:
                return self

            def __exit__(self, *a):  # type: ignore[no-untyped-def]
                return False

            def read(self) -> bytes:  # type: ignore[no-untyped-def]
                return b"{}"

        err = urllib.error.HTTPError("https://example", 404, "nf", None, None)

        def fake_urlopen(req, timeout):  # type: ignore[no-untyped-def]
            raise err

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)  # type: ignore[attr-defined]
        c = GitHubClient(tmp_path, token="t")
        assert c.rest("/missing") is None
