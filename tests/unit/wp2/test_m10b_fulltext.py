"""Unit tests for Mission-10B full-text root-cause extraction (V3 taxonomy)."""
from __future__ import annotations

from benchmark.wp2.m10b_fulltext import (
    attribute_node_target_reps,
    cause_family,
    classify_error_v3,
    final_exception_line,
    merge_rep_junit,
    normalize,
    parse_junit_fulltext,
    reconcile_counts,
)

# ---------------------------------------------------------------------------
# INFRA:EMFILE
# ---------------------------------------------------------------------------


def test_emfile_from_message():
    tax, detail = classify_error_v3(
        "request = <SubRequest 'django_db_setup' for <function test_x>>\n"
        "E   OSError: [Errno 24] Too many open files",
        message='failed on setup with "OSError: [Errno 24] Too many open files"',
    )
    assert tax == "INFRA:EMFILE"
    assert "Errno 24" in detail


def test_emfile_from_fulltext_body():
    tax, _ = classify_error_v3(
        ">       a, b = _socket.socketpair(family, type, proto)\n"
        "E       OSError: [Errno 24] Too many open files"
    )
    assert tax == "INFRA:EMFILE"


# ---------------------------------------------------------------------------
# DB taxonomy
# ---------------------------------------------------------------------------


def test_wrong_constraints():
    tax, detail = classify_error_v3(
        "E   django.db.utils.ProgrammingError: Found wrong number (3) of "
        "constraints for public.order"
    )
    assert tax == "DB:WRONG_CONSTRAINTS"
    assert "3" in detail


def test_set_session_in_txn():
    tax, _ = classify_error_v3(
        "E       django.db.utils.ProgrammingError: set_session cannot be used "
        "inside a transaction"
    )
    assert tax == "DB:SET_SESSION_IN_TXN"


def test_db_other():
    tax, _ = classify_error_v3(
        "E   psycopg2.OperationalError: could not connect to server: "
        "Connection refused\nIs the server running on host"
    )
    assert tax == "DB:OTHER"


# ---------------------------------------------------------------------------
# Missing fixture / module / import
# ---------------------------------------------------------------------------


def test_missing_fixture_count_queries():
    tax, detail = classify_error_v3(
        "file /workspace/x/t.py, line 1\n  @pytest.mark.django_db\n"
        "E       fixture 'count_queries' not found\n>       available fixtures: ..."
    )
    assert tax == "MISSING_FIXTURE:count_queries"
    assert detail == "count_queries"


def test_module_not_found():
    tax, detail = classify_error_v3("ModuleNotFoundError: No module named 'pytest_django_queries'")
    assert tax == "MODULE_NOT_FOUND:pytest_django_queries"
    assert detail == "pytest_django_queries"


def test_import_error():
    tax, detail = classify_error_v3("ImportError: cannot import name 'X' from 'm'")
    assert tax.startswith("IMPORT_ERROR:")
    assert "cannot import name" in detail


# ---------------------------------------------------------------------------
# TIME taxonomy
# ---------------------------------------------------------------------------


def test_time_immature_signature():
    tax, _ = classify_error_v3(
        "E   jwt.exceptions.ImmatureSignatureError: The token is not yet valid "
        "(iat)"
    )
    assert tax == "TIME:IMMATURE_SIGNATURE"


def test_time_expired_signature():
    tax, _ = classify_error_v3(
        "E   jwt.exceptions.ExpiredSignatureError: Signature has expired"
    )
    assert tax == "TIME:EXPIRED_SIGNATURE"


def test_time_freezegun():
    tax, _ = classify_error_v3("E   freezegun.api.FrozenDateTimeError: wrong_auto_tick")
    assert tax == "TIME:FREEZEGUN"


# ---------------------------------------------------------------------------
# Exception tail selection (7.1) and normalization
# ---------------------------------------------------------------------------


def test_exception_tail_selection_prefers_last_exception_line():
    text = (
        "Traceback (most recent call last):\n"
        "  File \"/usr/local/lib/python3.9/site-packages/django/db/backends/utils.py\", line 84\n"
        "    return self.cursor.execute(sql, params)\n"
        "  File \"/usr/local/lib/python3.9/site-packages/django/db/backends/base/base.py\", line 218\n"
        "    connection = self.ensure_connection()\n"
        "E   psycopg2.OperationalError: could not connect to server\n"
        "E   ConnectionRefusedError: [Errno 111] Connection refused\n"
        "E   OSError: [Errno 24] Too many open files\n"
    )
    exc = final_exception_line(text)
    assert "Too many open files" in exc


def test_setup_with_message_priority():
    exc = final_exception_line(
        "request = <SubRequest 'django_db_setup'>\nE   OSError: [Errno 24] Too many open files",
        message='failed on setup with "OSError: [Errno 24] Too many open files"',
    )
    assert "Errno 24" in exc


def test_normalize_preserves_errno_and_classes():
    n = normalize("OSError: [Errno 24] Too many open files at 0x7f3a; /tmp/x/db.sqlite3")
    assert "Errno 24" in n
    assert "Too many open files" in n
    assert "0x7f3a" not in n
    assert "HEX" in n


# ---------------------------------------------------------------------------
# Full-text JUnit parsing (per file, full text retained)
# ---------------------------------------------------------------------------


def _xml_with_error(msg: str, body: str) -> str:
    import html as _html

    return (
        '<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite errors="1">'
        f'<testcase classname="saleor.graphql.product.tests.test_product" '
        f'name="test_assign_variant_media" time="1.0"><error message="{_html.escape(msg)}">'
        f"{_html.escape(body)}</error></testcase></testsuite></testsuites>"
    )


def test_parse_junit_fulltext_keeps_full_error_body():
    body = "E   OSError: [Errno 24] Too many open files\n" + "A" * 5000
    recs = parse_junit_fulltext(_xml_with_error("failed on setup with ...", body))
    assert len(recs) == 1
    rec = recs[0]
    assert rec.node_id == "saleor/graphql/product/tests/test_product.py::test_assign_variant_media"
    assert rec.outcome == "error"
    assert len(rec.full_text) == len(body)  # NOT truncated (fixes 10A limitation)
    assert "Too many open files" in rec.full_text


def test_parse_junit_fulltext_passed_node():
    xml = (
        '<testsuites><testsuite><testcase classname="a.b" name="t" '
        'time="0.1" /></testsuite></testsuites>'
    )
    recs = parse_junit_fulltext(xml)
    assert len(recs) == 1
    assert recs[0].outcome == "passed"


def test_merge_rep_junit_prefers_error_over_passed():
    xml_passed = '<testsuites><testsuite><testcase classname="a.b" name="t" time="0.1"/></testsuite></testsuites>'
    xml_error = _xml_with_error("failed on setup with X", "E   OSError: [Errno 24] Too many open files")
    merged = merge_rep_junit(
        task_id="saleor-rc-abc", side="t", repetition=0,
        xml_files=[("f0", xml_passed), ("f1", xml_error)],
    )
    # both testcases map to distinct node_ids; the error one must win for its node
    assert merged["a/b.py::t"].outcome == "passed"
    err_node = "saleor/graphql/product/tests/test_product.py::test_assign_variant_media"
    assert merged[err_node].outcome == "error"
    assert "Too many open files" in merged[err_node].full_text


# ---------------------------------------------------------------------------
# Node-level attribution (7.3)
# ---------------------------------------------------------------------------


def _ev(task: str, side: str, rep: int, node: str, tax_text: str, msg: str = "") -> object:
    from benchmark.wp2.m10b_fulltext import RepEvidence

    return RepEvidence(task_id=task, side=side, repetition=rep, node_id=node,
                       outcome="error", message=msg, full_text=tax_text, phase="setup")


def test_stable_cause_when_all_three_reps_same_family():
    evs = [_ev("t", "t", i, "n", "E   OSError: [Errno 24] Too many open files") for i in range(3)]
    attr = attribute_node_target_reps(evs)
    assert attr["stability"] == "STABLE_CAUSE"
    assert attr["stable_family"] == "INFRA"
    assert attr["materiality"] is True


def test_mixed_cause_when_families_differ():
    evs = [
        _ev("t", "t", 0, "n", "E   OSError: [Errno 24] Too many open files"),
        _ev("t", "t", 1, "n", "E   django.db.utils.ProgrammingError: Found wrong number (3) of constraints"),
        _ev("t", "t", 2, "n", "E   OSError: [Errno 24] Too many open files"),
    ]
    attr = attribute_node_target_reps(evs)
    assert attr["stability"] == "MIXED_CAUSE"
    assert attr["majority_families"] == ["INFRA"]
    assert attr["materiality"] is False


def test_missing_evidence_when_no_reps():
    attr = attribute_node_target_reps([None, None, None])
    assert attr["stability"] == "MISSING_EVIDENCE"
    assert attr["materiality"] is False


def test_materiality_requires_stable_and_family_in_set():
    # stable MISSING_FIXTURE counts toward materiality (declared-dep family)
    evs = [_ev("t", "t", i, "n", "E       fixture 'count_queries' not found") for i in range(3)]
    attr = attribute_node_target_reps(evs)
    assert attr["stability"] == "STABLE_CAUSE"
    assert attr["stable_family"] == "MISSING_FIXTURE"
    assert attr["materiality"] is True


# ---------------------------------------------------------------------------
# Reconciliation (7.4)
# ---------------------------------------------------------------------------


def test_reconcile_counts_exact():
    attributed = {
        "a": {"stability": "STABLE_CAUSE"},
        "b": {"stability": "MIXED_CAUSE"},
        "c": {"stability": "MISSING_EVIDENCE"},
        "d": {"stability": "FAILED_ONLY"},
    }
    r = reconcile_counts(authoritative_total=4, authoritative_error=3,
                         authoritative_failed=1, attributed=attributed)
    assert r["ok"] is True
    assert r["mismatch"] == 0


def test_reconcile_counts_mismatch():
    attributed = {"a": {"stability": "STABLE_CAUSE"}}
    r = reconcile_counts(authoritative_total=5, authoritative_error=5,
                         authoritative_failed=0, attributed=attributed)
    assert r["ok"] is False
    assert r["mismatch"] == 4


def test_cause_family_mapping():
    assert cause_family("INFRA:EMFILE") == "INFRA"
    assert cause_family("DB:WRONG_CONSTRAINTS") == "DB"
    assert cause_family("MISSING_FIXTURE:count_queries") == "MISSING_FIXTURE"
    assert cause_family("TIME:IMMATURE_SIGNATURE") == "TIME"
    assert cause_family("OTHER") == "OTHER"
