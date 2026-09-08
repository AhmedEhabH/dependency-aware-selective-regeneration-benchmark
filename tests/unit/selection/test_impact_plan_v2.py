from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from benchmark.core.enums import ActionKind, ArtifactType
from benchmark.core.models import ArtifactRef, ArtifactUniverse, RequirementChange
from benchmark.external_validity.study_runtime import (
    CANDIDATE_UNIVERSE_PATH,
    HIDDEN_GOLD_PATH,
)
from benchmark.selection import impact_planner as v1
from benchmark.selection import impact_planner_v2 as v2
from benchmark.selection.impact_planner_v2 import (
    IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS,
    V2_ALLOWED_ACTIONS,
    ImpactPlanV2Error,
    build_candidate_id_map,
    decode_v2_policy,
    derive_candidate_id_map,
    impact_plan_v2_from_json,
    verify_candidate_id_map_artifact,
)

_MAPPING = derive_candidate_id_map()
_PATHS = _MAPPING.paths()


def _parsed(items: list[dict[str, object]]) -> dict[str, object]:
    return {
        "decisions": items,
        "validation_obligations": [],
        "architecture_checks": [],
        "escalation_reason": "",
    }


def _decision(
    candidate_id: int,
    action: str,
    *,
    confidence: float = 0.9,
    rationale: str = "r",
) -> dict[str, object]:
    return {
        "id": candidate_id,
        "action": action,
        "rationale": rationale,
        "confidence": confidence,
        "reason_codes": ["test_v2"],
        "evidence": [
            {"source": "mock_v2_evidence", "description": "deterministic v2 evidence"}
        ],
    }


class TestCandidateIdMap:
    def test_exactly_144_candidate_ids(self) -> None:
        assert len(_MAPPING.id_to_path) == 144
        assert [i for i, _ in _MAPPING.id_to_path] == list(range(1, 145))
        assert len(_PATHS) == 144

    def test_deterministic_id_ordering(self) -> None:
        again = derive_candidate_id_map()
        assert again.id_to_path == _MAPPING.id_to_path
        assert tuple(sorted(_PATHS)) == _PATHS
        assert again.path_to_id == _MAPPING.path_to_id

    def test_stable_id_mapping_sha256(self) -> None:
        again = derive_candidate_id_map()
        assert again.sha256 == _MAPPING.sha256 == "9d33e163505722e2cfe602ca165777d3d5accbaf5b9f7a82d1b30068ca9d1ca6"
        assert verify_candidate_id_map_artifact()["passed"]

    def test_mapping_universe_hash_matches_frozen(self) -> None:
        assert _MAPPING.universe_canonical_sha256 == "43f4279bdf228745b1f6b289c81cda141b089ab5be4f4af63bb8f39f837c4410"

    def test_hidden_gold_never_affects_mapping(self) -> None:
        records = json.loads(Path(CANDIDATE_UNIVERSE_PATH).read_text(encoding="utf-8"))
        gold_paths = {
            p
            for rec in json.loads(Path(HIDDEN_GOLD_PATH).read_text(encoding="utf-8"))
            for p in rec.get("source_files", [])
        }
        # Mapping derives from universe records only (path-sorted), independent
        # of hidden gold content/order.
        derived = build_candidate_id_map(records)
        assert derived.id_to_path == _MAPPING.id_to_path
        assert gold_paths <= set(_PATHS)

    def test_mapping_ids_bidirectional(self) -> None:
        for i, p in _MAPPING.id_to_path:
            assert _MAPPING.path_for(i) == p
            assert _MAPPING.id_for(p) == i

    def test_build_rejects_wrong_count(self) -> None:
        with pytest.raises(ValueError):
            build_candidate_id_map([{"path": "a.py"}, {"path": "b.py"}])


class TestSparseDecode:
    def test_omitted_candidate_decodes_to_preserve(self) -> None:
        parsed = _parsed([_decision(5, "REGENERATE")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert pol.action_for(5) == ActionKind.regenerate
        assert pol.action_for(1) == ActionKind.preserve
        assert 5 not in pol.decoded_preserve_ids
        assert 1 in pol.decoded_preserve_ids

    def test_explicit_regenerate_decoding(self) -> None:
        parsed = _parsed([_decision(42, "REGENERATE")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert pol.action_for(42) == ActionKind.regenerate
        assert len(pol.decoded_preserve_ids) == 143

    def test_explicit_validate_decoding(self) -> None:
        parsed = _parsed([_decision(7, "VALIDATE")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert pol.action_for(7) == ActionKind.validate_only

    def test_explicit_human_review_decoding(self) -> None:
        parsed = _parsed([_decision(99, "HUMAN_REVIEW")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert pol.action_for(99) == ActionKind.human_review

    def test_several_simultaneous_sparse_decisions(self) -> None:
        parsed = _parsed(
            [
                _decision(1, "REGENERATE"),
                _decision(2, "VALIDATE"),
                _decision(3, "HUMAN_REVIEW"),
                _decision(144, "REGENERATE"),
            ]
        )
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert pol.emitted_decision_count == 4
        assert pol.action_for(1) == ActionKind.regenerate
        assert pol.action_for(2) == ActionKind.validate_only
        assert pol.action_for(3) == ActionKind.human_review
        assert pol.action_for(144) == ActionKind.regenerate
        assert len(pol.decoded_preserve_ids) == 140

    def test_exactly_144_decoded_candidates(self) -> None:
        parsed = _parsed([_decision(10, "REGENERATE")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert len(pol.action_by_id) == 144

    def test_no_invented_no_lost_candidate(self) -> None:
        parsed = _parsed([_decision(1, "REGENERATE"), _decision(144, "HUMAN_REVIEW")])
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        decoded_paths = {_MAPPING.path_for(i) for i, _ in pol.action_by_id}
        assert decoded_paths == set(_PATHS)
        assert len(decoded_paths) == 144

    def test_duplicate_id_rejection(self) -> None:
        parsed = _parsed(
            [_decision(5, "REGENERATE"), _decision(5, "REGENERATE")]
        )
        with pytest.raises(ImpactPlanV2Error) as exc:
            decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert "duplicate" in str(exc.value)

    def test_conflicting_decision_rejection(self) -> None:
        parsed = _parsed(
            [_decision(5, "REGENERATE"), _decision(5, "HUMAN_REVIEW")]
        )
        with pytest.raises(ImpactPlanV2Error) as exc:
            decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert "conflict" in str(exc.value)

    def test_id_zero_rejection(self) -> None:
        parsed = _parsed([_decision(0, "REGENERATE")])
        with pytest.raises(ImpactPlanV2Error) as exc:
            decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert "invalid" in str(exc.value)

    def test_id_145_rejection(self) -> None:
        parsed = _parsed([_decision(145, "REGENERATE")])
        with pytest.raises(ImpactPlanV2Error) as exc:
            decode_v2_policy(parsed, _MAPPING, _PATHS)
        assert "invalid" in str(exc.value)

    def test_malformed_structured_output_rejection(self) -> None:
        with pytest.raises(ImpactPlanV2Error):
            decode_v2_policy({"decisions": "nope"}, _MAPPING, _PATHS)
        with pytest.raises(ImpactPlanV2Error):
            decode_v2_policy({"decisions": [42]}, _MAPPING, _PATHS)
        with pytest.raises(ImpactPlanV2Error):
            decode_v2_policy({"decisions": [{"action": "REGENERATE"}]}, _MAPPING, _PATHS)

    def test_unsupported_action_rejection(self) -> None:
        for action in ("PRESERVE", "PRESERVE_ONLY", "DELETE", "REGEN"):
            parsed = _parsed([_decision(1, action)])
            with pytest.raises(ImpactPlanV2Error) as exc:
                decode_v2_policy(parsed, _MAPPING, _PATHS)
            assert "unsupported action" in str(exc.value)

    def test_allowed_actions_are_exactly_rvh(self) -> None:
        assert set(V2_ALLOWED_ACTIONS) == {"REGENERATE", "VALIDATE", "HUMAN_REVIEW"}

    def test_pairwise_disjoint_action_sets(self) -> None:
        parsed = _parsed(
            [
                _decision(1, "REGENERATE"),
                _decision(2, "VALIDATE"),
                _decision(3, "HUMAN_REVIEW"),
            ]
        )
        pol = decode_v2_policy(parsed, _MAPPING, _PATHS)
        r = {i for i, a in pol.action_by_id if a == ActionKind.regenerate}
        p = {i for i, a in pol.action_by_id if a == ActionKind.preserve}
        v = {i for i, a in pol.action_by_id if a == ActionKind.validate_only}
        h = {i for i, a in pol.action_by_id if a == ActionKind.human_review}
        assert r.isdisjoint(p) and r.isdisjoint(v) and r.isdisjoint(h)
        assert p.isdisjoint(v) and p.isdisjoint(h) and v.isdisjoint(h)
        assert r | p | v | h == set(range(1, 145))

    def test_empty_sparse_output_decodes_all_preserve(self) -> None:
        pol = decode_v2_policy(_parsed([]), _MAPPING, _PATHS)
        assert pol.emitted_decision_count == 0
        assert len(pol.decoded_preserve_ids) == 144
        assert all(a == ActionKind.preserve for _, a in pol.action_by_id)


class TestPlanReconstruction:
    def _plan(self, items: list[dict[str, object]]) -> object:
        return impact_plan_v2_from_json(
            _parsed(items),
            mapping=_MAPPING,
            run_id="r1",
            scenario_id="djangocms-external-validity-004",
            source_commit="abc123",
        )

    def test_full_144_decision_plan(self) -> None:
        plan = self._plan([_decision(1, "REGENERATE"), _decision(2, "VALIDATE")])
        assert len(plan.decisions) == 144
        assert set(plan.write_set) == {_MAPPING.path_for(1)}
        assert set(plan.validate_set) == {_MAPPING.path_for(2)}
        assert len(plan.preserve_set) == 142
        assert plan.plan_hash

    def test_rationale_confidence_reason_evidence_retained(self) -> None:
        plan = self._plan([_decision(9, "REGENERATE", confidence=0.83, rationale="because")])
        decision = next(d for d in plan.decisions if d.artifact.path == _MAPPING.path_for(9))
        assert decision.action == ActionKind.regenerate
        assert decision.confidence == 0.83
        assert decision.rationale == "because"
        assert decision.reason_codes == ("test_v2",)
        assert decision.supporting_evidence[0].source == "mock_v2_evidence"

    def test_omitted_decision_has_no_rationale_but_preserve(self) -> None:
        plan = self._plan([_decision(9, "REGENERATE")])
        decision = next(d for d in plan.decisions if d.artifact.path == _MAPPING.path_for(10))
        assert decision.action == ActionKind.preserve


class TestV1Unchanged:
    def test_v1_prompt_and_schema_hashes_reproducible(self) -> None:
        prompt_hash = hashlib.sha256(v1.PLANNER_PROMPT_TEMPLATE.encode("utf-8")).hexdigest()
        schema_hash = hashlib.sha256(
            json.dumps(v1.IMPACT_PLAN_SCHEMA, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        assert prompt_hash == v2.V1_PLANNER_PROMPT_SHA256
        assert schema_hash == v2.V1_PLANNER_SCHEMA_SHA256

    def test_v1_prompt_still_requires_full_explicit_classification(self) -> None:
        assert "Classify EVERY candidate path exactly once." in v1.PLANNER_PROMPT_TEMPLATE
        assert "PRESERVE" in v1.IMPACT_PLAN_SCHEMA["properties"]["decisions"]["items"]["properties"]["action"]["enum"]

    def test_v1_default_cap_remains_4096(self) -> None:
        assert v1.IMPACT_PLAN_MAX_COMPLETION_TOKENS == 4096

    def test_v2_cap_equals_v1_default_cap(self) -> None:
        assert IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS == 4096
        assert IMPACT_PLAN_V2_MAX_COMPLETION_TOKENS == v1.IMPACT_PLAN_MAX_COMPLETION_TOKENS

    def test_v2_prompt_and_schema_hashes_persisted(self) -> None:
        identity = v2.impact_plan_v2_identity()
        assert identity["v2_planner_prompt_sha256"] == v2.V2_PLANNER_PROMPT_SHA256
        assert identity["v2_planner_schema_sha256"] == v2.V2_PLANNER_SCHEMA_SHA256
        assert len(v2.V2_PLANNER_PROMPT_SHA256) == 64
        assert len(v2.V2_PLANNER_SCHEMA_SHA256) == 64

    def test_v2_schema_ids_bounded_1_144(self) -> None:
        items = v2.IMPACT_PLAN_V2_SCHEMA["properties"]["decisions"]["items"]["properties"]
        assert items["id"]["type"] == "integer"
        assert items["id"]["minimum"] == 1
        assert items["id"]["maximum"] == 144
        enum = items["action"]["enum"]
        assert enum == ["REGENERATE", "VALIDATE", "HUMAN_REVIEW"]
        assert "PRESERVE" not in enum


class TestNoGraphInjection:
    def test_v2_module_has_no_dependency_graph_usage(self) -> None:
        source = (v2.__file__ and __import__("pathlib").Path(v2.__file__).read_text(encoding="utf-8")) or ""
        assert "DependencyGraph" not in source
        assert "load_dependency_graph" not in source
        assert "dependency_scope" not in source
        assert "source_graph" not in source

    def test_v2_schema_has_no_graph_fields(self) -> None:
        assert "graph" not in json.dumps(v2.IMPACT_PLAN_V2_SCHEMA)

    def test_v2_prompt_has_no_graph_instruction(self) -> None:
        assert "graph" not in v2.IMPACT_PLAN_V2_PROMPT_TEMPLATE.lower().replace("dependency-graph assistance", "")


class TestMockPlannerV2:
    def test_mock_planner_v2_no_model_calls(self) -> None:
        planner = v2.MockImpactPlannerV2(r_paths=frozenset({_PATHS[0]}))
        inp = _planner_input()
        plan = planner.plan(inp)
        assert planner.model_calls == 0
        assert set(plan.write_set) == {_PATHS[0]}
        assert len(plan.decisions) == 144

    def test_mock_planner_v2_disjointness(self) -> None:
        with pytest.raises(ValueError):
            v2.MockImpactPlannerV2(r_paths=frozenset({_PATHS[0]}), v_paths=frozenset({_PATHS[0]}))


def _planner_input() -> object:
    class _Input:
        pass

    inp = _Input()
    inp.requirement_change = RequirementChange(
        before="no versioning", after="versioning with drafts", acceptance_criteria=()
    )
    inp.artifact_universe = ArtifactUniverse(
        artifacts=tuple(
            ArtifactRef(path=p, artifact_type=ArtifactType.source) for p in _PATHS
        )
    )
    inp.evidence = ()
    inp.run_id = "r1"
    inp.scenario_id = "djangocms-external-validity-004"
    inp.source_commit = "abc123"
    inp.extra_architecture_constraints = ()
    inp.prior_plan_summary = None
    inp.parent_plan_hash = None
    return inp
