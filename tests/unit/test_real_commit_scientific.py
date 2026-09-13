"""Unit tests for RealCommitImpactDataset-v1 scientific corpus logic (M4A-2, ZERO API).

Covers the frozen-procedure pure functions: intent similarity, PR reference
extraction, year-capped selection, largest-remainder allocation, deterministic
split freeze, and duplicate/related-change adjudication rules.
"""

from __future__ import annotations

from benchmark.real_commits import scientific

# ---------------------------------------------------------------------------
# Intent similarity + PR refs
# ---------------------------------------------------------------------------


def test_intent_jaccard_identical_is_one() -> None:
    assert scientific.intent_jaccard("fix: page title bug", "fix: page title bug") == 1.0


def test_intent_jaccard_disjoint_is_zero() -> None:
    assert scientific.intent_jaccard("fix: page title", "feat: menu ordering") == 0.0


def test_intent_jaccard_empty_is_zero() -> None:
    assert scientific.intent_jaccard("", "something") == 0.0
    assert scientific.intent_jaccard("x", "") == 0.0


def test_intent_jaccard_partial() -> None:
    sim = scientific.intent_jaccard("fix: slug uniqueness", "fix: slug check")
    assert 0.0 < sim < 1.0


def test_extract_pr_refs() -> None:
    assert scientific.extract_pr_refs("fix: something (#8140)") == frozenset({"8140"})
    assert scientific.extract_pr_refs("Fixes #6205 and #6206") == frozenset({"6205", "6206"})
    assert scientific.extract_pr_refs("no reference here") == frozenset()


# ---------------------------------------------------------------------------
# Year-capped selection
# ---------------------------------------------------------------------------


def _candidate(sha: str, year: str, proxy_count: int = 1, change_type: str = "unknown") -> dict:
    return {
        "sha": sha,
        "parent": "p" * 40,
        "subject": f"subject {sha[:6]}",
        "intent": f"intent {sha[:6]}",
        "status": {f"cms/f{i}.py": "M" for i in range(proxy_count)},
        "time": f"{year}-06-01T00:00:00+00:00",
        "ts": 0,
        "year": year,
        "proxy_paths": tuple(sorted(f"cms/f{i}.py" for i in range(proxy_count))),
        "proxy_count": proxy_count,
        "change_type": change_type,
        "intent_mentions_changed_path": False,
        "prs": scientific.extract_pr_refs(f"subject {sha[:6]}"),
        "eligibility": {},
    }


def test_select_year_capped_respects_cap_and_target() -> None:
    candidates = []
    for year in ("2020", "2021", "2022"):
        for i in range(8):
            candidates.append(_candidate(f"{i:040x}", year))
    selected = scientific.select_year_capped(candidates, cap=2, target=5)
    assert len(selected) == 5
    years = sorted({c["year"] for c in selected})
    # Newest years first; each capped at 2.
    assert selected[0]["year"] == "2022"
    assert selected[1]["year"] == "2022"
    assert selected[2]["year"] == "2021"
    assert len(years) >= 2


def test_select_year_capped_never_exceeds_target() -> None:
    candidates = [_candidate(f"{i:040x}", "2020") for i in range(20)]
    selected = scientific.select_year_capped(candidates, cap=5, target=40)
    # Only 5 per year allowed even when more candidates exist in that year.
    assert len(selected) == 5


# ---------------------------------------------------------------------------
# Largest-remainder allocation
# ---------------------------------------------------------------------------


def test_largest_remainder_allocation_40() -> None:
    alloc = scientific._largest_remainder_allocation(40, scientific.SPLIT_RATIO)
    assert alloc == {"TRAIN": 24, "VALIDATION": 6, "HELD_OUT_TEST": 10}
    assert sum(alloc.values()) == 40


def test_largest_remainder_allocation_sums_to_total() -> None:
    for total in (30, 36, 40):
        alloc = scientific._largest_remainder_allocation(total, scientific.SPLIT_RATIO)
        assert sum(alloc.values()) == total


# ---------------------------------------------------------------------------
# Deterministic split freeze
# ---------------------------------------------------------------------------


def _selected_cases(n: int) -> list[dict]:
    cases = []
    for i in range(n):
        cases.append(
            {
                "sha": f"{i:012x}deadbeefcafe{i:012x}"[:40],
                "time": f"20{20 + (i % 5)}-06-01T00:00:00+00:00",
                "proxy_count": (i % 12) + 1,
            }
        )
    return cases


def test_freeze_splits_deterministic_and_exact_counts() -> None:
    cases = _selected_cases(40)
    sf1 = scientific.freeze_splits(cases)
    sf2 = scientific.freeze_splits(cases)
    assert sf1 == sf2
    assert sf1["seed"] == scientific.SPLIT_SEED
    assert sf1["miner_dev_separate"] is True
    assert sf1["related_crossing_splits"] is False
    counts = {name: sf1["per_split"][name]["count"] for name in sf1["per_split"]}
    assert counts == {"TRAIN": 24, "VALIDATION": 6, "HELD_OUT_TEST": 10}
    all_members = [m for p in sf1["per_split"].values() for m in p["case_ids"]]
    assert len(all_members) == 40
    assert len(set(all_members)) == 40


def test_freeze_splits_hashes_match() -> None:
    cases = _selected_cases(36)
    sf = scientific.freeze_splits(cases)
    for _name, part in sf["per_split"].items():
        assert part["count"] == len(part["case_ids"])
        from benchmark.real_commits.models import sha256_json

        assert sha256_json(sorted(part["case_ids"])) == part["sha256"]


def test_freeze_splits_canonical_hash_stable() -> None:
    cases = _selected_cases(40)
    sf1 = scientific.freeze_splits(cases)
    sf2 = scientific.freeze_splits(cases)
    assert (
        sf1["canonical_split_freeze_sha256"] == sf2["canonical_split_freeze_sha256"]
    )
    assert len(sf1["canonical_split_freeze_sha256"]) == 64


# ---------------------------------------------------------------------------
# Duplicate / related-change adjudication
# ---------------------------------------------------------------------------


def _dedup_case(sha: str, proxy: list[str], subject: str) -> dict:
    return {
        "sha": sha,
        "parent": "p" * 40,
        "subject": subject,
        "intent": subject,
        "status": {p: "M" for p in proxy},
        "time": f"2024-01-0{int(sha[0], 16) % 9 + 1}T00:00:00+00:00",
        "ts": 0,
        "year": "2024",
        "proxy_paths": tuple(sorted(proxy)),
        "proxy_count": len(proxy),
        "change_type": "unknown",
        "intent_mentions_changed_path": False,
        "prs": scientific.extract_pr_refs(subject),
        "eligibility": {},
    }


def test_dedup_r1_exact_proxy_set_keeps_newest() -> None:
    a = _dedup_case("a" * 40, ["cms/models/pagemodel.py"], "fix: a")
    b = _dedup_case("b" * 40, ["cms/models/pagemodel.py"], "fix: b")
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert [c["sha"] for c in kept] == ["a" * 40]
    assert any(r["rule"] == "R1_exact_proxy_set" for r in adj)
    r1 = next(r for r in adj if r["rule"] == "R1_exact_proxy_set")
    assert r1["kept_sha"] == "a" * 40
    assert r1["excluded_sha"] == "b" * 40


def test_dedup_r2_shared_pr_reference_keeps_newest() -> None:
    a = _dedup_case("a" * 40, ["cms/a.py"], "fix: a (#1234)")
    b = _dedup_case("b" * 40, ["cms/b.py"], "fix: b (#1234)")
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert [c["sha"] for c in kept] == ["a" * 40]
    assert any(r["rule"] == "R2_shared_pr_reference" for r in adj)


def test_dedup_r3_suspected_related_keeps_newest() -> None:
    a = _dedup_case("a" * 40, ["cms/x.py", "cms/y.py"], "fixes failing tests")
    b = _dedup_case("b" * 40, ["cms/x.py", "cms/z.py"], "fixes failing tests")
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert [c["sha"] for c in kept] == ["a" * 40]
    assert any(r["rule"] == "R3_suspected_related" for r in adj)
    r3 = next(r for r in adj if r["rule"] == "R3_suspected_related")
    assert r3["decision"] == "exclude_older_keep_newest"
    assert r3["decision_source"] == "deterministic_same_change_predicate"
    assert r3["kept_sha"] == "a" * 40
    assert r3["excluded_sha"] == "b" * 40
    assert "rationale" in r3


def test_dedup_r3_suspected_related_different_change_keeps_both() -> None:
    # Jaccard >= 0.5 + shared proxy path, but messages describe DIFFERENT
    # changes (shared tokens < 3, no subset) -> the frozen R3 rule keeps BOTH
    # (never drops a possibly independent change).
    a = _dedup_case("a" * 40, ["cms/x.py", "cms/y.py"], "fix: page menu")
    b = _dedup_case("b" * 40, ["cms/x.py", "cms/z.py"], "fix: page cache")
    assert scientific.intent_jaccard("fix: page menu", "fix: page cache") >= 0.5
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert sorted(c["sha"] for c in kept) == ["a" * 40, "b" * 40]
    r3 = next(r for r in adj if r["rule"] == "R3_suspected_related")
    assert r3["decision"] == "keep_both"
    assert r3["excluded_sha"] == ""
    assert r3["kept_sha"] == "a" * 40


def test_messages_describe_same_change_predicate() -> None:
    assert scientific._messages_describe_same_change(
        "Dropped support for Django < 1.11", "Drop support for Django 1.7."
    )
    assert scientific._messages_describe_same_change(
        "Initial compatibility", "Initial compatibility effort"
    )
    assert scientific._messages_describe_same_change(
        "More fixes", "More context fixes"
    )
    assert scientific._messages_describe_same_change(
        "fixes failing tests", "fixes failing tests"
    )
    assert not scientific._messages_describe_same_change(
        "fix: page menu", "fix: page cache"
    )
    assert not scientific._messages_describe_same_change(
        "fix: menu", "feat: batch publish"
    )
    assert not scientific._messages_describe_same_change("", "fix: something")


def test_dedup_independent_cases_kept() -> None:
    a = _dedup_case("a" * 40, ["cms/a.py"], "fix: slug uniqueness (#8100)")
    b = _dedup_case("b" * 40, ["cms/b.py"], "feat: menu ordering (#8101)")
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert len(kept) == 2
    assert adj == []


def test_dedup_shared_file_alone_is_not_related() -> None:
    # Overlapping (but non-identical) proxy sets, different PRs, no intent
    # overlap: independent changes, both kept. (Identical single-file sets are
    # R1 duplicates and correctly removed by the frozen exact-set rule.)
    a = _dedup_case(
        "a" * 40,
        ["cms/admin/pageadmin.py", "cms/models/pagemodel.py"],
        "fix: delete confirmation (#8100)",
    )
    b = _dedup_case(
        "b" * 40,
        ["cms/admin/pageadmin.py", "cms/toolbar/toolbar.py"],
        "feat: batch publish (#8101)",
    )
    kept, adj = scientific.deduplicate_candidates([a, b])
    assert len(kept) == 2
    assert adj == []


# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------


def test_protocol_constants_frozen() -> None:
    assert scientific.SCIENTIFIC_WINDOW == 6000
    assert scientific.YEAR_CAP == 5
    assert scientific.TARGET_CASES == 40
    assert scientific.SPLIT_SEED == 20260913
    assert dict(scientific.SPLIT_RATIO) == {
        "TRAIN": 0.60,
        "VALIDATION": 0.15,
        "HELD_OUT_TEST": 0.25,
    }
    assert scientific.R3_INTENT_JACCARD_THRESHOLD == 0.5


def test_shape_bucket_boundaries() -> None:
    assert scientific._shape_bucket(1) == "small"
    assert scientific._shape_bucket(2) == "small"
    assert scientific._shape_bucket(3) == "medium"
    assert scientific._shape_bucket(6) == "medium"
    assert scientific._shape_bucket(7) == "large"
    assert scientific._shape_bucket(12) == "large"
