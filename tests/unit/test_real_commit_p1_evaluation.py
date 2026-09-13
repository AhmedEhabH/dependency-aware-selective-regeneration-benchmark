"""Unit tests for M4A-3 / P1 real-commit evaluation core (ZERO API)."""

from __future__ import annotations

from benchmark.real_commits import p1_evaluation as p1


def test_p1_candidate_map_deterministic() -> None:
    paths = ["cms/b.py", "cms/a.py", "menus/x.py"]
    m1 = p1.build_p1_candidate_map(paths)
    m2 = p1.build_p1_candidate_map(reversed(paths))
    assert m1.id_to_path == m2.id_to_path
    assert m1.paths() == ("cms/a.py", "cms/b.py", "menus/x.py")
    assert m1.path_for(1) == "cms/a.py"
    assert m1.sha256 == m2.sha256


def test_p1_candidate_map_rejects_duplicate_paths() -> None:
    m = p1.build_p1_candidate_map(["cms/a.py", "cms/a.py"])
    assert len(m.id_to_path) == 1


def test_p1_common_schema_parameterized() -> None:
    schema = p1.p1_common_schema(140)
    assert schema["properties"]["decisions"]["maxItems"] == 140
    schema2 = p1.p1_common_schema(152)
    assert schema2["properties"]["decisions"]["maxItems"] == 152


def test_prompt_control_proof_identical_after_policy_strip() -> None:
    from types import SimpleNamespace

    case = SimpleNamespace(
        case_id="djangocms-rc-8d50660e7bcf",
        intent_text="fix: slug uniqueness",
        candidate_paths=("cms/a.py", "cms/b.py", "cms/c.py"),
        candidate_records=tuple({"path": p} for p in ("cms/a.py", "cms/b.py", "cms/c.py")),
        graph_edges=(("cms/a.py", "cms/b.py"),),
        repository="djangocms",
        repository_url="https://github.com/django-cms/django-cms",
        parent_commit="p" * 40,
        target_commit="t" * 40,
        public_bundle_sha256="x",
    )
    mapping = p1.build_p1_candidate_map(case.candidate_paths)
    full = p1.render_p1_full_prompt(case=case, mapping=mapping)
    sparse = p1.render_p1_sparse_prompt(case=case, mapping=mapping)
    proof = p1.prompt_control_proof(full, sparse)
    assert proof["PROMPT_CONTROLLED_DIFF"] == "PASS"
    assert proof["byte_identical_after_policy_strip"]


def test_p1_full_roundtrip() -> None:
    mapping = p1.build_p1_candidate_map(["cms/a.py", "cms/b.py", "cms/c.py"])
    proxy = {"cms/a.py"}
    payload = p1.fixture_payload_for_arm(arm="full_v2", mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_full(payload, candidate_count=3)
    assert vres["valid"]
    assert vres["decoded_candidate_count"] == 3
    assert vres["decoded_write_set_ids"] == [1]


def test_p1_sparse_roundtrip() -> None:
    mapping = p1.build_p1_candidate_map(["cms/a.py", "cms/b.py", "cms/c.py"])
    proxy = {"cms/a.py", "cms/c.py"}
    payload = p1.fixture_payload_for_arm(arm="sparse_v2", mapping=mapping, proxy_paths=proxy)
    vres = p1.validate_p1_sparse(payload, candidate_count=3)
    assert vres["valid"]
    assert vres["decoded_candidate_count"] == 3
    assert vres["decoded_write_set_ids"] == [1, 3]


def test_p1_full_requires_all_ids() -> None:
    try:
        p1.decode_p1_full({"decisions": [{"id": 1, "action": "REGENERATE"}]}, candidate_count=5)
        raised = False
    except p1.P1DecodeError:
        raised = True
    assert raised


def test_p1_sparse_rejects_explicit_preserve() -> None:
    try:
        p1.decode_p1_sparse(
            {"decisions": [{"id": 1, "action": "PRESERVE"}]}, candidate_count=5
        )
        raised = False
    except p1.P1DecodeError:
        raised = True
    assert raised


def test_p1_sparse_rejects_duplicate_ids() -> None:
    try:
        p1.decode_p1_sparse(
            {
                "decisions": [
                    {"id": 1, "action": "REGENERATE"},
                    {"id": 1, "action": "VALIDATE"},
                ]
            },
            candidate_count=5,
        )
        raised = False
    except p1.P1DecodeError:
        raised = True
    assert raised


def test_p1_sparse_rejects_unknown_action() -> None:
    try:
        p1.decode_p1_sparse(
            {"decisions": [{"id": 1, "action": "FROB"}]}, candidate_count=5
        )
        raised = False
    except p1.P1DecodeError:
        raised = True
    assert raised


def test_p1_sparse_rejects_id_out_of_range() -> None:
    try:
        p1.decode_p1_sparse(
            {"decisions": [{"id": 99, "action": "REGENERATE"}]}, candidate_count=5
        )
        raised = False
    except p1.P1DecodeError:
        raised = True
    assert raised


def test_p1_metrics_perfect_and_imperfect() -> None:
    perfect = p1.p1_selection_metrics({"a", "b"}, {"a", "b"})
    assert perfect["precision"] == 1.0 and perfect["recall"] == 1.0 and perfect["fnr"] == 0.0
    imperfect = p1.p1_selection_metrics({"a", "b", "c"}, {"a", "d"})
    assert imperfect["tp"] == 1 and imperfect["fp"] == 2 and imperfect["fn"] == 1
    assert abs(imperfect["precision"] - 1 / 3) < 1e-9
    assert abs(imperfect["recall"] - 0.5) < 1e-9
    assert abs(imperfect["fnr"] - 0.5) < 1e-9


def test_p1_protocol_constants_frozen() -> None:
    assert p1.P1_MODEL == "qwen/qwen3-coder"
    assert p1.P1_PROVIDER_TAG == "deepinfra/turbo"
    assert p1.P1_TEMPERATURE == 0.0
    assert p1.P1_MAX_COMPLETION_TOKENS == 4096
    assert p1.P1_REPETITIONS == 3
    assert p1.P1_ACTION_VOCAB == ("PRESERVE", "REGENERATE", "VALIDATE", "HUMAN_REVIEW")
