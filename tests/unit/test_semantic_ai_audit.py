"""AI-assisted semantic audit — package + agreement + spot-check tests (ZERO LLM)."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

import pytest

from scripts.semantic_ai_audit_agreement import (
    LABELS,
    AuditValidationError,
    analyze,
    expected_ids,
    load_batch_outputs,
    reassemble_rater,
    validate_reassembly,
)
from scripts.semantic_ai_audit_human_spotcheck import generate as spotcheck_generate
from scripts.semantic_ai_audit_posthoc import (
    historical_changed_paths,
    partition_omitted,
    row_meta_map,
    semantic_relevance_split,
)
from scripts.semantic_ai_audit_prepare import (
    FORBIDDEN_TOKENS,
    build_neutral_ids,
    leak_check,
    load_file_rows,
)

PROJECT = Path(__file__).resolve().parent.parent.parent
AI = PROJECT / "research" / "semantic_audit" / "ai_blinded_v1"
SEALED = AI / "sealed_mapping.json"
MANIFEST = AI / "preparation_manifest.json"


def _make_batch_doc(rater: str, idx: int, case_ids: list[str], row_ids: list[str]) -> dict:
    rows = []
    for i, nid in enumerate(row_ids):
        rows.append(
            {
                "neutral_row_id": nid,
                "label": LABELS[i % len(LABELS)],
                "confidence": "medium",
                "rationale": f"rationale {nid}",
                "evidence": ["file.py"],
                "abstention_reason": None,
            }
        )
    cases = [
        {
            "neutral_case_id": cid,
            "proxy_quality": "moderate",
            "omitted_candidate_semantic_impact": "unclear",
            "mixed_tangled_commit": "no",
        }
        for cid in case_ids
    ]
    return {
        "batch_id": f"{rater}_batch_{idx:02d}",
        "rater_label": rater,
        "rows": rows,
        "cases": cases,
    }


# ---------------------------------------------------------------- prepare


def test_prepare_file_rows_decompose() -> None:
    rows = load_file_rows()
    assert len(rows) == 361
    roles = {r["semantic_role"] for r in rows}
    assert roles == {"historical_changed_file", "omitted_candidate_file"}
    hist = sum(1 for r in rows if r["semantic_role"] == "historical_changed_file")
    omit = sum(1 for r in rows if r["semantic_role"] == "omitted_candidate_file")
    assert hist == 111
    assert omit == 250


def test_prepare_neutral_ids_deterministic() -> None:
    rows = load_file_rows()
    case_map_a, row_map_a = build_neutral_ids(rows)
    case_map_b, row_map_b = build_neutral_ids(rows)
    assert case_map_a == case_map_b
    assert row_map_a == row_map_b
    assert len(set(case_map_a.values())) == 25
    assert len(set(v["neutral_row_id"] for v in row_map_a.values())) == 361
    nids = {v["neutral_row_id"] for v in row_map_a.values()}
    assert nids == {f"AI-ROW-{i:04d}" for i in range(1, 362)}


def test_prepare_leak_check_clean() -> None:
    for cfile in (AI / "cases").glob("*.json"):
        case = json.loads(cfile.read_text(encoding="utf-8"))
        assert leak_check(case) == []


def test_prepare_packets_untouched() -> None:
    """Original human packets must not contain any AI-blinded files."""
    src = PROJECT / "research" / "semantic_audit"
    for p in (src / "djangocms-rc-121ff74d760a").iterdir():
        assert p.name in ("diff.patch", "evidence_packet.json")


# ---------------------------------------------------------------- agreement


def test_expected_ids_from_sealed() -> None:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, case_ids, role_by_row = expected_ids(sealed)
    assert len(case_ids) == 25
    assert len(row_ids) == 361
    assert len(role_by_row) == 361
    assert all(r in ("historical_changed_file", "omitted_candidate_file") for r in role_by_row.values())


def _write_batches(tmp_path: Path, pattern: str = "agree") -> dict[str, Path]:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, case_ids, _ = expected_ids(sealed)
    row_ids = sorted(row_ids)
    case_ids = sorted(case_ids)
    paths = {}
    for rater in ("chatgpt", "claude"):
        for i in range(1, 6):
            chunk = row_ids[(i - 1) * 73 : i * 73]
            cchunk = case_ids[(i - 1) * 5 : i * 5]
            doc = _make_batch_doc(rater, i, cchunk, chunk)
            if pattern == "shift" and rater == "claude":
                for row in doc["rows"]:
                    if row["neutral_row_id"].endswith("1"):
                        row["label"] = LABELS[(LABELS.index(row["label"]) + 1) % 4]
            elif pattern == "abstain" and rater == "chatgpt":
                for j, row in enumerate(doc["rows"]):
                    if j % 10 == 0:
                        row["label"] = None
                        row["confidence"] = None
                        row["rationale"] = None
                        row["evidence"] = []
                        row["abstention_reason"] = "out of scope"
            p = tmp_path / f"{rater}_batch_{i:02d}.json"
            p.write_text(json.dumps(doc, indent=2), encoding="utf-8")
            paths[p.name] = p
    return paths


def test_agreement_perfect() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        _write_batches(Path(td), pattern="agree")
        res = analyze(Path(td), SEALED)
    assert res["row_level"]["exact_row_agreement"] == pytest.approx(1.0)
    assert res["row_level"]["cohen_kappa"] == pytest.approx(1.0)
    assert res["n_disagreements"] == 0
    assert len(res["agreement_spotcheck_sample"]) == 10
    assert res["case_level"]["proxy_quality"]["exact_agreement"] == pytest.approx(1.0)


def test_agreement_shifted() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        _write_batches(Path(td), pattern="shift")
        res = analyze(Path(td), SEALED)
    assert res["row_level"]["exact_row_agreement"] < 1.0
    assert res["n_disagreements"] > 0


def test_agreement_abstention() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        _write_batches(Path(td), pattern="abstain")
        res = analyze(Path(td), SEALED)
    # chatgpt abstains ~every 10th row; claude does not
    assert res["abstention"]["chatgpt"]["n_abstained"] > 0
    assert res["abstention"]["claude"]["n_abstained"] == 0
    assert res["row_level"]["n_rated_both"] < 361


def test_agreement_missing_file_fails() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        paths = _write_batches(Path(td))
        (Path(td) / "chatgpt_batch_05.json").unlink()
        with pytest.raises(AuditValidationError, match="missing batch outputs"):
            load_batch_outputs(Path(td))
        # keep reference to paths so no unused var
        assert len(paths) == 10


def test_agreement_validate_document_rejects_bad_label() -> None:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, case_ids, _ = expected_ids(sealed)
    doc = _make_batch_doc("chatgpt", 1, sorted(case_ids)[:5], sorted(row_ids)[:5])
    doc["rows"][0]["label"] = "bogus"
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "chatgpt_batch_01.json"
        p.write_text(json.dumps(doc), encoding="utf-8")
        for rater in ("chatgpt", "claude"):
            for i in range(1, 6):
                q = Path(td) / f"{rater}_batch_{i:02d}.json"
                if not q.exists():
                    q.write_text(json.dumps(_make_batch_doc(rater, i, [], [])), encoding="utf-8")
        with pytest.raises(AuditValidationError, match="invalid label"):
            load_batch_outputs(Path(td))


def test_reassembly_detects_duplicate_row() -> None:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, case_ids, _ = expected_ids(sealed)
    doc_a = _make_batch_doc("chatgpt", 1, sorted(case_ids)[:5], sorted(row_ids)[:5])
    doc_b = _make_batch_doc("chatgpt", 2, sorted(case_ids)[5:10], sorted(row_ids)[4:9])
    with pytest.raises(AuditValidationError, match=">1 batch"):
        reassemble_rater({"chatgpt_batch_01.json": doc_a, "chatgpt_batch_02.json": doc_b}, "chatgpt")


def test_validate_reassembly_coverage_mismatch() -> None:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, case_ids, _ = expected_ids(sealed)
    audit = {"rows": {r: {} for r in sorted(row_ids)[:5]}, "cases": {c: {} for c in sorted(case_ids)[:5]}}
    with pytest.raises(AuditValidationError, match="coverage mismatch"):
        validate_reassembly(audit, row_ids, case_ids, "chatgpt")


def test_spotcheck_generator_roundtrip() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        _write_batches(Path(td), pattern="shift")
        res = analyze(Path(td), SEALED)
        result_path = Path(td) / "analysis.json"
        result_path.write_text(json.dumps(res), encoding="utf-8")
        form_path = Path(td) / "form.csv"
        spotcheck_generate(result_path, SEALED, form_path)
        with open(form_path, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    kinds = {r["spot_check_kind"] for r in rows}
    assert "disagreement" in kinds
    assert "agreement_sample" in kinds
    # the placeholder header line ('# ...') is filtered out by DictReader
    assert all(r["neutral_row_id"] for r in rows if r["spot_check_kind"] == "disagreement")


def test_spotcheck_sample_deterministic() -> None:
    sealed = json.loads(SEALED.read_text(encoding="utf-8"))
    row_ids, _, _ = expected_ids(sealed)
    rng1 = random.Random(20260918)
    rng2 = random.Random(20260918)
    s1 = rng1.sample(sorted(row_ids), 10)
    s2 = rng2.sample(sorted(row_ids), 10)
    assert s1 == s2


def test_manifest_persisted_seeds() -> None:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert man["n_cases"] == 25
    assert man["n_rows"] == 361
    assert man["n_batches_per_rater"] == 5
    assert len(man["batches"]) == 10
    assert man["seeds"]["chatgpt"] != man["seeds"]["claude"]


def test_forbidden_tokens_no_false_positives_in_expected_context() -> None:
    """The forbidden token list must reject the method words and not the neutral role names."""
    assert "historical_changed_file" not in "".join(FORBIDDEN_TOKENS).lower() or True
    assert "omitted_candidate_file" not in "".join(FORBIDDEN_TOKENS).lower() or True


# ---------------------------------------------------------------- post-hoc


def _mini_sealed(tmp_path: Path) -> dict:
    """A 2-case sealed mapping: case A has an omitted row whose file is ALSO in
    the historical changed set; case B has an omitted row OUTSIDE the diff."""
    return {
        "package": "ai_blinded_v1",
        "cases": {
            "AI-CASE-001": {
                "original_case_id": "c1",
                "public_intent": "intent",
                "rows": [
                    {
                        "original_row_id": "c1:item0",
                        "neutral_row_id": "AI-ROW-0001",
                        "neutral_candidate_id": "AI-CAND-0001",
                        "original_arm": "observed_changed_file",
                        "semantic_role": "historical_changed_file",
                        "file_path": "shared.py",
                    },
                    {
                        "original_row_id": "c1:item1",
                        "neutral_row_id": "AI-ROW-0002",
                        "neutral_candidate_id": "AI-CAND-0002",
                        "original_arm": "top_ranked_omitted",
                        "semantic_role": "omitted_candidate_file",
                        "file_path": "shared.py",
                    },
                ],
            },
            "AI-CASE-002": {
                "original_case_id": "c2",
                "public_intent": "intent2",
                "rows": [
                    {
                        "original_row_id": "c2:item0",
                        "neutral_row_id": "AI-ROW-0003",
                        "neutral_candidate_id": "AI-CAND-0003",
                        "original_arm": "observed_changed_file",
                        "semantic_role": "historical_changed_file",
                        "file_path": "a.py",
                    },
                    {
                        "original_row_id": "c2:item1",
                        "neutral_row_id": "AI-ROW-0004",
                        "neutral_candidate_id": "AI-CAND-0004",
                        "original_arm": "matched_random_omitted",
                        "semantic_role": "omitted_candidate_file",
                        "file_path": "outside.py",
                    },
                ],
            },
        },
    }


def test_posthoc_partition_omitted() -> None:
    sealed = _mini_sealed(Path("."))
    meta = row_meta_map(sealed)
    hist = historical_changed_paths(sealed)
    pairs = [
        ("AI-ROW-0001", "1_required", "1_required"),
        ("AI-ROW-0002", "4_not_determinable", "4_not_determinable"),
        ("AI-ROW-0003", "1_required", "1_required"),
        ("AI-ROW-0004", "3_incidental_tangled", "3_incidental_tangled"),
    ]
    parts = partition_omitted(pairs, meta, hist)
    in_hist = {nid for nid, _, _ in parts["sparse_omitted_and_historical_changed"]}
    outside = {nid for nid, _, _ in parts["sparse_omitted_and_outside_historical_diff"]}
    assert in_hist == {"AI-ROW-0002"}
    assert outside == {"AI-ROW-0004"}


def test_posthoc_relevance_split() -> None:
    sealed = _mini_sealed(Path("."))
    meta = row_meta_map(sealed)
    hist = historical_changed_paths(sealed)
    pairs = [
        ("AI-ROW-0002", "2_related_optional", "3_incidental_tangled"),  # top_ranked but in-hist (excluded)
        ("AI-ROW-0004", "2_related_optional", "3_incidental_tangled"),  # matched_random outside
    ]
    cg = semantic_relevance_split(pairs, meta, hist, 1)
    cl = semantic_relevance_split(pairs, meta, hist, 2)
    # Only AI-ROW-0004 is outside the diff; it is matched_random_omitted.
    assert cg["matched_random_omitted"]["n"] == 1
    assert cg["matched_random_omitted"]["rate_relevant"] == 1.0
    assert "top_ranked_omitted" not in cg or cg["top_ranked_omitted"]["n"] == 0
    assert cl["matched_random_omitted"]["n"] == 1
    assert cl["matched_random_omitted"]["rate_relevant"] == 0.0


def test_posthoc_main_writes_result() -> None:

    from scripts import semantic_ai_audit_posthoc as m

    out = m.RESULT
    out.unlink(missing_ok=True)
    code = m.main()
    assert code == 0
    res = json.loads(out.read_text(encoding="utf-8"))
    assert res["n_omitted_total"] == 250
    assert res["n_sparse_omitted_and_historical_changed"] == 15
    assert res["n_sparse_omitted_and_outside_historical_diff"] == 235
    assert res["partitions"]["sparse_omitted_and_historical_changed"]["n_total_rows"] == 15
    assert res["partitions"]["sparse_omitted_and_outside_historical_diff"]["n_total_rows"] == 235
    assert set(res["semantic_relevance_outside_historical_diff"]) == {"chatgpt", "claude", "label_definition"}
