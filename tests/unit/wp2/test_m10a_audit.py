"""Unit tests for Mission-10A environment test-dependency audit logic."""
from __future__ import annotations

from benchmark.wp2.m10a_audit import (
    classify_error,
    detect_phase,
    evaluate_materiality,
    first_useful_line,
    package_declared_in_text,
    preregister_materiality_rule,
    reconcile_probe_sets,
    resolve_declared_version,
)
from benchmark.wp2.m10a_audit import (
    node_requests_fixture as _node_requests_fixture,
)
from benchmark.wp2.m10a_audit import (
    test_path_category as _test_path_category,
)

# ---------------------------------------------------------------------------
# Error taxonomy / phase detection
# ---------------------------------------------------------------------------


def test_missing_fixture_extraction():
    tax, detail = classify_error(
        "file /workspace/x/t.py, line 1\n  @pytest.mark.django_db\n"
        "E       fixture 'count_queries' not found\n>       available fixtures: ..."
    )
    assert tax == "MISSING_FIXTURE:count_queries"
    assert detail == "count_queries"


def test_missing_fixture_mocker():
    tax, _ = classify_error("E       fixture 'mocker' not found")
    assert tax == "MISSING_FIXTURE:mocker"


def test_module_not_found_extraction():
    tax, detail = classify_error(
        "ModuleNotFoundError: No module named 'pytest_django_queries'"
    )
    assert tax.startswith("MODULE_NOT_FOUND:")
    assert detail == "pytest_django_queries"


def test_import_error_extraction():
    tax, detail = classify_error("ImportError: cannot import name 'X' from 'm'")
    assert tax.startswith("IMPORT_ERROR:")
    assert "cannot import name" in detail


def test_db_error_classification():
    tax, _ = classify_error(
        "psycopg2.OperationalError: could not connect to server: Connection refused"
    )
    assert tax == "DB_ERROR"


def test_phase_detection_setup():
    assert detect_phase("ERROR at setup of test_x") == "setup"
    assert detect_phase("failed on setup with ...") == "setup"


def test_phase_detection_collection():
    assert detect_phase("ERROR at collection") == "collection"
    assert detect_phase("error collecting test_x") == "collection"


def test_normalization_paths():
    from benchmark.wp2.m10a_audit import normalize

    n = normalize(
        "file /workspace/74538ea00ce9_c200_p/saleor/t.py line 1 at 0xdeadbeef"
    )
    assert "/workspace/" not in n
    assert "0x" not in n


def test_first_useful_line_skips_punct():
    line = first_useful_line(
        "file /x.py line 1\n>       available fixtures: ...\nE   fixture 'x' not found"
    )
    assert "fixture" in line


def test_empty_error_text_is_other():
    tax, _ = classify_error("")
    assert tax.startswith("OTHER")


# ---------------------------------------------------------------------------
# Dependency declaration resolution
# ---------------------------------------------------------------------------


def test_pyproject_poetry_dev_group():
    txt = """
[tool.poetry.dependencies]
python = "~3.12"
django = "^4.2"

[tool.poetry.group.dev.dependencies]
pytest-django-queries = "~1.2"
pytest-mock = "^3.6.1"
"""
    d = resolve_declared_version("pytest-django-queries", {"pyproject.toml": txt})
    assert d.declared
    assert d.mechanism == "pyproject-poetry"
    assert d.group == "dev"


def test_pyproject_legacy_dev_dependencies():
    txt = """
[tool.poetry.dependencies]
django = "^3.2"

[tool.poetry.dev-dependencies]
pytest-mock = "^3.6.1"
"""
    d = resolve_declared_version("pytest-mock", {"pyproject.toml": txt})
    assert d.declared
    assert d.group == "dev"


def test_pyproject_dependency_groups_pep735():
    txt = """
[dependency-groups]
dev = [
  "pytest>=8",
  "pytest-django-queries>=1.2,<1.3",
]
"""
    d = resolve_declared_version("pytest-django-queries", {"pyproject.toml": txt})
    assert d.declared
    assert d.mechanism == "pyproject-dependency-groups"
    assert d.group == "dev"
    assert "1.2" in d.version_spec


def test_poetry_lock_pinned_version():
    txt = '''
[[package]]
name = "pytest-django-queries"
version = "1.2.0"
description = "x"
'''
    d = resolve_declared_version("pytest-django-queries", {"poetry.lock": txt})
    assert d.declared
    assert d.locked_version == "1.2.0"


def test_uv_lock_pinned_version():
    txt = '''
name = "pytest-mock"
version = "3.14.1"
'''
    d = resolve_declared_version("pytest-mock", {"uv.lock": txt})
    assert d.declared
    assert d.locked_version == "3.14.1"


def test_requirements_dev_pin():
    txt = 'pytest-mock==3.10.0 ; python_version >= "3.9" and python_version < "3.10"\n'
    d = resolve_declared_version("pytest-mock", {"requirements_dev.txt": txt})
    assert d.declared
    assert d.mechanism == "pip-requirements"
    assert d.markers


def test_not_declared():
    d = resolve_declared_version("some-unknown-pkg", {"pyproject.toml": "django = 1"})
    assert not d.declared


def test_package_declared_in_text():
    assert package_declared_in_text("pytest-mock", 'pytest-mock = "^3.6.1"')
    assert not package_declared_in_text("pytest-mock", "django = 1")


# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------


def test_test_path_category():
    assert _test_path_category(
        "saleor/graphql/discount/tests/benchmark/test_x.py::test_y"
    ) == "tests/benchmark"
    assert _test_path_category(
        "saleor/graphql/order/tests/queries/test_y.py::test_z"
    ) == "tests/queries"


def test_node_requests_fixture():
    src = (
        "@pytest.mark.django_db\n"
        "@pytest.mark.count_queries(autouse=False)\n"
        "def test_promotion_update(staff_api_client, count_queries):\n"
        "    pass\n"
    )
    assert _node_requests_fixture(src, "test_promotion_update", "count_queries")
    assert not _node_requests_fixture(src, "test_promotion_update", "mocker")


# ---------------------------------------------------------------------------
# Materiality rule
# ---------------------------------------------------------------------------


def test_materiality_rule_preregistered_before_probe():
    rule = preregister_materiality_rule("2026-09-26T00:00:00Z")
    assert rule.preregistered_before_probe is True
    assert "ENV_V3_RECOMMENDED" in rule.conditions["decision"]
    assert "ENV_AUDIT_INCONCLUSIVE" in rule.conditions["decision"]


def test_materiality_v3_recommended():
    tok = evaluate_materiality(
        declared_but_not_installed_causes=1,
        declared_installed_plugin_not_loaded_causes=0,
        m1_newly_oracle_valid_tasks=1,
        m2_recovered_behavioral_f2p_nodes=0,
        m3_systematic_category_exclusion=False,
        s1_new_infrastructure_failure_categories=0,
        s2_non_regression_holds=True,
    )
    assert tok == "ENV_V3_RECOMMENDED"


def test_materiality_v2_adequate():
    tok = evaluate_materiality(
        declared_but_not_installed_causes=0,
        declared_installed_plugin_not_loaded_causes=0,
        m1_newly_oracle_valid_tasks=0,
        m2_recovered_behavioral_f2p_nodes=0,
        m3_systematic_category_exclusion=False,
        s1_new_infrastructure_failure_categories=0,
        s2_non_regression_holds=True,
    )
    assert tok == "ENV_V2_ADEQUATE"


def test_materiality_inconclusive_on_non_regression_failure():
    tok = evaluate_materiality(
        declared_but_not_installed_causes=1,
        declared_installed_plugin_not_loaded_causes=0,
        m1_newly_oracle_valid_tasks=0,
        m2_recovered_behavioral_f2p_nodes=0,
        m3_systematic_category_exclusion=True,
        s1_new_infrastructure_failure_categories=0,
        s2_non_regression_holds=False,
    )
    assert tok == "ENV_AUDIT_INCONCLUSIVE"


def test_materiality_inconclusive_on_new_infra_failure():
    tok = evaluate_materiality(
        declared_but_not_installed_causes=1,
        declared_installed_plugin_not_loaded_causes=0,
        m1_newly_oracle_valid_tasks=1,
        m2_recovered_behavioral_f2p_nodes=0,
        m3_systematic_category_exclusion=False,
        s1_new_infrastructure_failure_categories=1,
        s2_non_regression_holds=True,
    )
    assert tok == "ENV_AUDIT_INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Probe reconciliation
# ---------------------------------------------------------------------------


def test_probe_reconcile_clean():
    v2 = {"a": "P2P_ONLY", "b": "BEHAVIORAL_F2P"}
    probe = {"a": "P2P_ONLY", "b": "BEHAVIORAL_F2P"}
    r = reconcile_probe_sets(["a"], ["a", "b"], v2, probe)
    assert r["ok"] is True


def test_probe_reconcile_class_transition():
    v2 = {"a": "P2P_ONLY", "b": "BEHAVIORAL_F2P"}
    probe = {"a": "P2P_ONLY", "b": "P2P_ONLY"}
    r = reconcile_probe_sets(["a"], ["a", "b"], v2, probe)
    assert r["ok"] is False
    assert "b" in r["class_transitions"]
    assert r["class_transitions"]["b"] == {"v2": "BEHAVIORAL_F2P", "probe": "P2P_ONLY"}


def test_probe_reconcile_missing_and_orphan():
    v2 = {"a": "P2P_ONLY"}
    probe = {"c": "P2P_ONLY"}
    r = reconcile_probe_sets(["a"], ["a"], v2, probe)
    assert r["ok"] is False
    assert r["set_b_missing"] == ["a"]
    assert r["orphan_records"] == ["c"]
