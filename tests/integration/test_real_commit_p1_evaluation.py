"""Integration tests for M4A-3 / P1 against the frozen real-commit corpus."""

from __future__ import annotations

from pathlib import Path

from benchmark.real_commits import p1_evaluation as p1

DATASET_DIR = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "real_commit_impact_v1"

EXPECTED_HELD_OUT = {
    "djangocms-rc-4307e1b8c2e2",
    "djangocms-rc-50c3576080be",
    "djangocms-rc-630a50361ada",
    "djangocms-rc-66c70394c9e1",
    "djangocms-rc-75978fb1c3ad",
    "djangocms-rc-8d50660e7bcf",
    "djangocms-rc-9e33db4f4660",
    "djangocms-rc-b39799f9fc1c",
    "djangocms-rc-ba16eb9a1d09",
    "djangocms-rc-fdda30c271f0",
}


def test_held_out_membership_frozen() -> None:
    assert set(p1.held_out_case_ids(DATASET_DIR)) == EXPECTED_HELD_OUT


def test_every_case_public_bundle_loads_and_proxy_separate() -> None:
    for cid in p1.held_out_case_ids(DATASET_DIR):
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        proxy = p1.load_hidden_proxy_paths(DATASET_DIR, cid)
        assert bundle.case_id == cid
        assert bundle.intent_text.strip()
        assert bundle.parent_commit
        assert len(bundle.candidate_paths) >= 100
        assert set(proxy) <= set(bundle.candidate_paths)


def test_no_hidden_proxy_marker_in_any_prompt() -> None:
    hidden_markers = (
        "observed_change_set_proxy",
        "observed-change-set",
        "changed_paths",
        "change_statuses",
        "target_diff",
        "target_commit_diff",
        "hidden/",
        "proxy_sha256",
    )
    for cid in p1.held_out_case_ids(DATASET_DIR):
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        for prompt in (
            p1.render_p1_full_prompt(case=bundle, mapping=mapping),
            p1.render_p1_sparse_prompt(case=bundle, mapping=mapping),
        ):
            assert not [m for m in hidden_markers if m in prompt], cid


def test_prompt_control_proof_all_cases() -> None:
    for cid in p1.held_out_case_ids(DATASET_DIR):
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        proof = p1.prompt_control_proof(
            p1.render_p1_full_prompt(case=bundle, mapping=mapping),
            p1.render_p1_sparse_prompt(case=bundle, mapping=mapping),
        )
        assert proof["PROMPT_CONTROLLED_DIFF"] == "PASS", cid


def test_manifest_60_cells_frozen_shape() -> None:
    rows = p1.build_p1_manifest(DATASET_DIR)
    assert len(rows) == 60
    assert len({r["run_id"] for r in rows}) == 60
    assert {r["case_id"] for r in rows} == EXPECTED_HELD_OUT
    assert {r["arm"] for r in rows} == {"full_v2", "sparse_v2"}
    for arm in ("full_v2", "sparse_v2"):
        assert all(
            sum(1 for r in rows if r["case_id"] == cid and r["arm"] == arm) == 3
            for cid in EXPECTED_HELD_OUT
        )


def test_fixture_pipeline_end_to_end_metrics_perfect() -> None:
    for cid in p1.held_out_case_ids(DATASET_DIR):
        bundle = p1.load_case_public_bundle(DATASET_DIR, cid)
        proxy_paths = set(p1.load_hidden_proxy_paths(DATASET_DIR, cid))
        mapping = p1.build_p1_candidate_map(bundle.candidate_paths)
        n = len(mapping.id_to_path)
        for arm in ("full_v2", "sparse_v2"):
            payload = p1.fixture_payload_for_arm(arm=arm, mapping=mapping, proxy_paths=proxy_paths)
            validator = (
                p1.validate_p1_full if arm == "full_v2" else p1.validate_p1_sparse
            )
            vres = validator(payload, candidate_count=n)
            assert vres["valid"], (cid, arm, vres["errors"])
            write_set = {mapping.path_for(i) for i in vres["decoded_write_set_ids"]}
            metrics = p1.p1_selection_metrics(write_set, proxy_paths)
            assert metrics["recall"] == 1.0 and metrics["fnr"] == 0.0, (cid, arm, metrics)
