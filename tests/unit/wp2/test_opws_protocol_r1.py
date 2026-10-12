"""M17 OPWS Protocol R1 — P2P (positive) tests + F2P (negative) tests (P14/P15).

P2P tests (P1..P23) assert a REQUIRED frozen property of the OPWS R1 protocol
freeze. F2P tests (F1..F18) copy the mission-owned artifacts into a tmp dir,
mutate the copy in a forbidden way, and assert that the frozen validator FAILS
on the mutation. Zero API, zero Docker.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[3]
for _p in (P, P / "src", P / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

PROTO = P / "research" / "opws-protocol-r1"


def _load(name: str) -> dict:
    return json.loads((PROTO / name).read_text(encoding="utf-8"))


def _load_validator() -> object:
    spec = importlib.util.spec_from_file_location(
        "opws_protocol_r1_validate_test_helper",
        P / "scripts" / "opws_protocol_r1_validate.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


V = _load_validator()


@pytest.fixture()
def proto_copy(tmp_path: Path):
    """Copy the frozen protocol dir so a test can mutate it without touching the real freeze."""
    dest = tmp_path / "opws-protocol-r1"
    shutil.copytree(PROTO, dest)
    return dest


# ---------------------------------------------------------------------------
# P1 .. P2  semantic boundary
# ---------------------------------------------------------------------------
def test_p1_definition_contains_perfect_generator_boundary() -> None:
    d = _load("OPWS_PROTOCOL_R1.json")
    q = d["perfect_generator_question"]
    assert "perfect generator" in q and "reference change" in q
    assert d["interpretation_boundary"]["required_wording"].startswith(
        "behavioral sufficiency")


def test_p2_generated_code_correctness_claim_forbidden() -> None:
    d = _load("OPWS_PROTOCOL_R1.json")
    ib = d["interpretation_boundary"]
    assert ib["forbidden_label"] == "generated-code correctness"
    assert any("functional correctness" in x for x in ib["opws_pass_does_not_mean"])


# ---------------------------------------------------------------------------
# P3 .. P4  population unbound + no peeking
# ---------------------------------------------------------------------------
def test_p3_full_d7_population_unbound() -> None:
    d = _load("OPWS_POPULATION_BINDING_SCHEMA_R1.json")
    for key, val in d["current_values"].items():
        assert val == "UNBOUND_PENDING_FULL_D7", key


def test_p4_full_d7_partial_outcomes_not_read() -> None:
    d = _load("ANTI_OUTCOME_PEEKING_RECEIPT.json")
    assert d["full_d7_partial_outcomes_read"] is False
    assert d["opws_executed"] is False


# ---------------------------------------------------------------------------
# P5 .. P8  arm registry identities
# ---------------------------------------------------------------------------
def test_p5_rm_css_registered_as_our_method() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["RM_CSS"]["role"] == "OUR_METHOD"


def test_p6_agent_registered() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["AGENT"]["role"] == "BUDGET_BOUNDED_ITERATIVE_AGENT"


def test_p7_agentless_label_exact() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    a = arms["AGENTLESS_STYLE_ADAPTATION"]
    assert a["role"] == "LITERATURE_INSPIRED_LOCALIZATION_ADAPTATION"
    assert "EXACT_AGENTLESS" in a["forbidden_labels"]
    assert "OFFICIAL_AGENTLESS_REPRODUCTION" in a["forbidden_labels"]


def test_p8_sip_registered() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["SIP"]["role"] == "SELECTIVE_BASELINE"


def test_p9_dense_k3_k10_registered() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["DENSE_K3"]["role"] == "RETRIEVAL_BASELINE"
    assert arms["DENSE_K10"]["role"] == "RETRIEVAL_BASELINE"


def test_p10_bm25_k3_k10_registered() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["BM25_K3"]["role"] == "RETRIEVAL_BASELINE"
    assert arms["BM25_K10"]["role"] == "RETRIEVAL_BASELINE"


def test_p11_select_all_ceiling_control() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["SELECT_ALL"]["role"] == "CEILING_CONTROL"


def test_p12_gold_diagnostic_only() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["GOLD"]["role"] == "DIAGNOSTIC_ONLY"


# ---------------------------------------------------------------------------
# P13 .. P16  statistical constants + primary comparison
# ---------------------------------------------------------------------------
def test_p13_random_seed() -> None:
    arms = {a["arm_id"]: a for a in _load("OPWS_ARM_REGISTRY_R1.json")["arms"]}
    assert arms["RANDOM_SIZE_MATCHED_RM_CSS"]["random_contract"]["seed"] == 20261012
    assert _load("OPWS_ARM_REGISTRY_R1.json")["constants"]["RANDOM_SEED"] == 20261012


def test_p14_bootstrap_iterations() -> None:
    plan = (PROTO / "OPWS_ANALYSIS_PLAN_R1.md").read_text(encoding="utf-8")
    assert "N_BOOTSTRAP = 10000" in plan


def test_p15_bootstrap_seed() -> None:
    plan = (PROTO / "OPWS_ANALYSIS_PLAN_R1.md").read_text(encoding="utf-8")
    assert "BOOTSTRAP_SEED = 20261012" in plan


def test_p16_primary_comparison_rmcss_vs_agent() -> None:
    plan = (PROTO / "OPWS_ANALYSIS_PLAN_R1.md").read_text(encoding="utf-8")
    assert "RM-CSS vs AGENT" in plan
    d = _load("OPWS_PROTOCOL_R1.json")
    assert d["statistical_summary"]["primary_inference"].startswith(
        "paired effect estimates")


# ---------------------------------------------------------------------------
# P17 .. P20  scope/dedup/control rules
# ---------------------------------------------------------------------------
def test_p17_scope_hash_deterministic() -> None:
    a = ["saleor/a.py", "saleor/b.py"]
    b = ["saleor/b.py", "saleor/a.py"]
    dup = ["saleor/a.py", "saleor/a.py"]
    assert V.compute_canonical_scope_hash(a) == V.compute_canonical_scope_hash(b)
    assert V.compute_canonical_scope_hash(a) != V.compute_canonical_scope_hash(dup)
    assert len(V.compute_canonical_scope_hash(a)) == 64


def test_p18_empty_scope_valid_size_zero() -> None:
    d = _load("OPWS_SCOPE_SEMANTICS_R1.json")
    text = json.dumps(d)
    assert "EMPTY" in d["canonical_scope_hash_definition"]["empty_scope_hash"]
    assert "VALID zero-size scope" in text
    assert "EMPTY prediction" in text
    empty_hash = V.compute_canonical_scope_hash([])
    assert len(empty_hash) == 64
    assert empty_hash != V.compute_canonical_scope_hash(["zz"])


def test_p19_logical_dedup_requires_identical_scope_hash() -> None:
    d = _load("OPWS_EXECUTION_REUSE_DEDUP_R1.json")
    id5 = d["physical_execution_identity"]["fields"]
    assert set(id5) == {"TASK_ID", "SCOPE_HASH", "REFERENCE_PATCH_HASH",
                        "TEST_CONTRACT_HASH", "ENVIRONMENT_ID"}
    assert "never deduplicate merely because scope sizes are equal" in \
        d["scope_deduplication"]["forbidden"]


def test_p20_gold_select_all_consistency_rule_exists() -> None:
    d = _load("OPWS_GOLD_SELECT_ALL_VALIDITY_R1.json")
    assert "HARNESS_CONSISTENCY_FAILURE" in json.dumps(d)
    assert any("identical" in r for r in d["predeclared_rules"])


# ---------------------------------------------------------------------------
# P21 .. P23  execution/peeking/global-status absence
# ---------------------------------------------------------------------------
def test_p21_opws_execution_absent() -> None:
    d = _load("ANTI_OUTCOME_PEEKING_RECEIPT.json")
    assert d["opws_executed"] is False
    assert not list(PROTO.rglob("OPWS_TASK_ARM_RESULTS.jsonl"))
    assert not list(PROTO.rglob("OPWS_EXECUTION_RECEIPT.json"))


def test_p22_docker_execution_absent() -> None:
    d = _load("ANTI_OUTCOME_PEEKING_RECEIPT.json")
    assert d["docker_run"] is False


def test_p23_global_current_status_docs_unchanged() -> None:
    import subprocess
    r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True,
                       cwd=str(P))
    assert r.returncode == 0
    assert not V.protected_docs_flagged(r.stdout.splitlines())
    for rel in V.PROTECTED_GLOBAL_DOCS:
        assert (P / rel).exists()


# ===========================================================================
# F2P tests (P15) — each mutation MUST make the frozen validator FAIL
# ===========================================================================
def _write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False),
                    encoding="utf-8", newline="\n")


def _mutate_validator_dir(monkeypatch, d: Path) -> None:
    monkeypatch.setattr(V, "PROTOCOL_DIR", d)


def test_f1_bind_fake_population_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_POPULATION_BINDING_SCHEMA_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["current_values"]["full_d7_ready_population_sha256"] = "deadbeef"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f2_read_in_progress_full_d7_store_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["full_d7_partial_outcomes_read"] = True
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f3_label_agentless_exact_reproduction_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_ARM_REGISTRY_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for arm in d["arms"]:
        if arm["arm_id"] == "AGENTLESS_STYLE_ADAPTATION":
            arm["role"] = "EXACT_AGENTLESS_REPRODUCTION"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f4_label_cia_style_exact_published_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_ARM_REGISTRY_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for arm in d["arms"]:
        if arm["arm_id"] == "BM25_TO_CIA_1HOP":
            arm["role"] = "EXACT_PUBLISHED_CIA"
            arm["forbidden_labels"] = []
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f5_treat_gold_as_competitor_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_ARM_REGISTRY_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for arm in d["arms"]:
        if arm["arm_id"] == "GOLD":
            arm["role"] = "COMPETITIVE_METHOD"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f6_claim_opws_is_generated_code_correctness_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_PROTOCOL_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    ib = d["interpretation_boundary"]
    ib["forbidden_label"] = "none"
    ib["required_wording"] = "generated-code correctness is proven"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f7_drop_empty_prediction_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_SCOPE_SEMANTICS_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["canonical_scope_hash_definition"].pop("empty_scope_hash", None)
    d["emph_empty_valid"] = "EMPTY prediction is dropped/omitted"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f8_add_gold_files_to_predictions_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_SCOPE_SEMANTICS_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["no_gold_backfill"] = True
    d["selection_source_priority"]["GOLD"] = "merged into RM_CSS selection"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f9_dedup_scopes_by_equal_size_only_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_EXECUTION_REUSE_DEDUP_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["scope_deduplication"]["forbidden"] = (
        "deduplicate whenever scope sizes are equal is ALLOWED")
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f10_rerun_scientific_failure_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_EXECUTION_REUSE_DEDUP_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["rerun_policy"]["scientific_failures"] = "rerun up to 3 times to seek a pass"
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f11_change_bootstrap_seed_after_outcomes_fails(monkeypatch, proto_copy) -> None:
    plan = proto_copy / "OPWS_ANALYSIS_PLAN_R1.md"
    text = plan.read_text(encoding="utf-8")
    plan.write_text(text.replace("BOOTSTRAP_SEED = 20261012", "BOOTSTRAP_SEED = 9999"),
                    encoding="utf-8", newline="\n")
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f12_change_arm_registry_after_opws_results_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_ARM_REGISTRY_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["registry_start_hash"] = "FFFF"
    d["arms"] = [a for a in d["arms"] if a["arm_id"] != "SIP"]
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f13_exclude_task_because_arm_failed_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_ELIGIBILITY_FUNNEL_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["hard_rules"] = [
        "A task whose arm failed scientifically may be dropped from the analysis"]
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f14_count_infrastructure_failure_as_behavioral_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "OPWS_OUTCOME_TAXONOMY_R1.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["taxonomy"]["PATCH_APPLICATION_INVALID"]["scientific"] = True
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f15_start_docker_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["docker_run"] = True
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f16_start_opws_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["opws_executed"] = True
    _write_json(p, d)
    (proto_copy / "OPWS_TASK_ARM_RESULTS.jsonl").write_text("{}", encoding="utf-8")
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f17_modify_full_d7_worktree_store_fails(monkeypatch, proto_copy) -> None:
    p = proto_copy / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["full_d7_worktree_modified"] = True
    _write_json(p, d)
    _mutate_validator_dir(monkeypatch, proto_copy)
    assert not V.validate().passed


def test_f18_modify_global_live_progress_docs_fails() -> None:
    assert "docs/LIVE_STATUS.json" in V.protected_docs_flagged(
        [" M docs/LIVE_STATUS.json"])
    assert "PROGRESS.md" in V.protected_docs_flagged([" M PROGRESS.md"])
    assert "00_CURRENT_RESEARCH_STATE.md" in V.protected_docs_flagged(
        [" M 00_CURRENT_RESEARCH_STATE.md"])
