"""Unit tests for RealCommitImpactDataset-v1 eligibility filters (M4A-1, ZERO API)."""

from __future__ import annotations

from benchmark.real_commits.miner import (
    classify_paths,
    evaluate_eligibility,
    infer_change_type,
    intent_mentions_changed_path,
    is_generated_or_vendor_path,
    is_migration_path,
    is_production_python,
    is_tests_path,
    meaningful_intent,
    normalize_intent,
)


def test_production_path_classification() -> None:
    assert is_production_python("cms/models/pagemodel.py")
    assert is_production_python("menus/menu.py")
    assert not is_production_python("cms/tests/test_page.py")
    assert not is_production_python("cms/test_utils/helpers.py")
    assert not is_production_python("cms/migrations/0001.py")
    assert not is_production_python("cms/static/cms/css/x.css")
    assert not is_production_python("setup.py")
    assert not is_production_python("cms/models/pagemodel.pyc")


def test_tests_migrations_generated_detection() -> None:
    assert is_tests_path("cms/tests/test_page.py")
    assert is_tests_path("cms/test_utils/helpers.py")
    assert not is_tests_path("cms/models/pagemodel.py")
    assert is_migration_path("cms/migrations/0001.py")
    assert not is_migration_path("cms/models/pagemodel.py")
    assert is_generated_or_vendor_path("cms/static/cms/css/x.css")
    assert is_generated_or_vendor_path("cms/locale/en/LC_MESSAGES/django.po")
    assert is_generated_or_vendor_path("package-lock.json")
    assert not is_generated_or_vendor_path("cms/models/pagemodel.py")


def test_classify_paths() -> None:
    name_status = {
        "cms/models/pagemodel.py": "M",
        "cms/tests/test_page.py": "M",
        "cms/migrations/0001.py": "A",
        "cms/static/cms/css/x.css": "M",
        "setup.py": "M",
    }
    classified = classify_paths(name_status)
    assert classified["production"] == ["cms/models/pagemodel.py"]
    assert classified["tests"] == ["cms/tests/test_page.py"]
    assert classified["migrations"] == ["cms/migrations/0001.py"]
    assert classified["generated_vendor"] == ["cms/static/cms/css/x.css"]
    assert classified["other"] == ["setup.py"]


def test_normalize_and_meaningful_intent() -> None:
    assert normalize_intent("  fix:  add page   validation  \n") == "fix: add page validation"
    assert normalize_intent("   ") == ""
    assert meaningful_intent("fix: add page validation")
    assert not meaningful_intent("")
    assert not meaningful_intent("bump django to 4.2")
    assert not meaningful_intent("Update CHANGELOG")
    assert not meaningful_intent("[ci skip] chore")


def test_infer_change_type_conservative() -> None:
    assert infer_change_type("fix: crash on publish") == "bugfix"
    assert infer_change_type("feat: add toolbar") == "feature"
    assert infer_change_type("refactor: clean up") == "refactor"
    assert infer_change_type("docs: update readme") == "docs"
    assert infer_change_type("test: cover publish") == "test"
    assert infer_change_type("unknown message here") == "unknown"


def test_intent_mentions_changed_path_exact_and_basename() -> None:
    intent = "fix: update cms/admin/pageadmin.py to handle new field"
    assert intent_mentions_changed_path(intent, ("cms/admin/pageadmin.py",))
    intent2 = "fix: update pageadmin to be faster"
    assert intent2_mentions("cms/admin/pageadmin.py", intent2)


def intent2_mentions(path: str, text: str) -> bool:
    return intent_mentions_changed_path(text, (path,))


def test_intent_does_not_mention_other_path() -> None:
    intent = "fix: handle NoReverseMatch in template tags"
    assert not intent_mentions_changed_path(intent, ("cms/admin/pageadmin.py",))


def test_eligibility_single_parent_acceptance() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40,),
        intent="fix: add publish validation",
        name_status={"cms/models/pagemodel.py": "M"},
    )
    assert result["eligible"] is True
    assert result["reason_codes"] == []
    assert result["proxy_paths"] == ("cms/models/pagemodel.py",)


def test_eligibility_merge_rejected() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40, "b" * 40),
        intent="merge branch",
        name_status={"cms/models/pagemodel.py": "M"},
    )
    assert result["eligible"] is False
    assert "merge_commit" in result["reason_codes"]


def test_eligibility_tests_only_rejected() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40,),
        intent="test: cover publish",
        name_status={"cms/tests/test_page.py": "M"},
    )
    assert result["eligible"] is False
    assert "tests_only" in result["reason_codes"]


def test_eligibility_migrations_only_rejected() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40,),
        intent="chore: add migration",
        name_status={"cms/migrations/0002.py": "A"},
    )
    assert result["eligible"] is False
    assert "migrations_only" in result["reason_codes"]


def test_eligibility_no_meaningful_intent_rejected() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40,),
        intent="   ",
        name_status={"cms/models/pagemodel.py": "M"},
    )
    assert result["eligible"] is False
    assert "no_meaningful_intent" in result["reason_codes"]


def test_eligibility_add_delete_rename_unsupported() -> None:
    result = evaluate_eligibility(
        parents=("a" * 40,),
        intent="feat: add module",
        name_status={"cms/utils/newutil.py": "A"},
    )
    assert result["eligible"] is False
    assert "production_add_delete_rename_copy_v1_unsupported" in result["reason_codes"]


def test_eligibility_proxy_size_boundaries() -> None:
    # 1 file eligible, 12 eligible, 13 too large, 0 -> no production change.
    one = {"cms/a.py": "M"}
    assert evaluate_eligibility(parents=("a" * 40,), intent="fix: x", name_status=one)["eligible"]

    twelve = {f"cms/m{i:02d}.py": "M" for i in range(12)}
    assert evaluate_eligibility(parents=("a" * 40,), intent="fix: x", name_status=twelve)["eligible"]

    thirteen = {f"cms/m{i:02d}.py": "M" for i in range(13)}
    res13 = evaluate_eligibility(parents=("a" * 40,), intent="fix: x", name_status=thirteen)
    assert res13["eligible"] is False
    assert "proxy_too_large" in res13["reason_codes"]


def test_eligibility_diff_too_large() -> None:
    name_status = {f"cms/m{i:02d}.py": "M" for i in range(5)}
    name_status.update({f"setup{i}.py": "M" for i in range(40)})
    res = evaluate_eligibility(
        parents=("a" * 40,),
        intent="fix: x",
        name_status=name_status,
        total_diff_ceiling=40,
    )
    assert "diff_too_large" in res["reason_codes"]


def test_eligibility_intent_path_leakage_flag_and_gate() -> None:
    intent = "fix: update cms/models/pagemodel.py"
    ns = {"cms/models/pagemodel.py": "M"}
    strict = evaluate_eligibility(parents=("a" * 40,), intent=intent, name_status=ns)
    assert strict["eligible"] is False
    assert "intent_path_leakage" in strict["reason_codes"]
    assert strict["intent_mentions_changed_path"] is True

    # MINER_DEV may keep one leak case (allow_intent_path_leakage=True).
    dev = evaluate_eligibility(
        parents=("a" * 40,),
        intent=intent,
        name_status=ns,
        allow_intent_path_leakage=True,
    )
    assert dev["eligible"] is True
    assert dev["intent_mentions_changed_path"] is True
