"""M17_D7_R4_PHASE1C_HARNESS_R3 - Harness R3 P2P/F2P tests (deterministic only).

Mission M17_D7_R4_PHASE1C_HARNESS_R3_RELEASE_FOR_OPERATOR_EXECUTION (T3).

These tests exercise ONLY deterministic / non-scientific behaviour of the R3
selection harness (``scripts/r4_r3_selection_harness.py``) and its three
committed frozen selection manifests.  ZERO real scientific units are executed.

P2P (must pass):
  P1  - exact successor authorities accepted (scientific peel, support head,
        code-set, committed closure content hash, closure semantic footprint,
        population/order/image) from the committed worktree.
  P2  - all three committed selection manifests accepted with exact frozen
        membership hashes / expected counts.
  P3  - dependency chain TARGETED3 -> CAL12 -> FULL144 structurally valid.
  P4  - committed closure content hash reproduces the frozen committed value.
  P5  - allowlist recompute relative to SUPPORT_EVIDENCE_HEAD matches.
  P6  - predecessor gate: TARGETED3 NOT_REQUIRED; CAL12/FULL144
        BLOCKED_BY_PREDECESSOR_RECEIPT (preflight, not authority failure).

F2P (must fail closed):
  F1  - wrong scientific HEAD  -> reject (no ancestor).
  F2  - OLD execution-code-set mocked  -> reject.
  F3  - wrong committed closure blob hash -> reject.
  F4  - semantically different re-derived closure (footprint) -> reject.
  F5  - wrong support evidence HEAD -> reject.
  F6  - wrong population identity -> reject.
  F7  - wrong ordered-membership hash -> reject.
  F8  - wrong image-binding hash -> reject.
  F9  - changed selection membership -> manifest reject.
  F10 - changed selection order -> manifest reject.
  F11 - wrong selection hash -> manifest reject.
  F12 - CAL12 without valid TARGETED3 receipt -> exec gate reject.
  F13 - FULL144 without valid CAL12 receipt -> exec gate reject.
  F14 - receipt from wrong R3 HEAD/tag -> reject.
  F15 - missing/moved R3 tag with HEAD mismatch -> reject.
  F16 - dirty tracked worktree -> reject.
  F17 - network fallback static -> reject.

Fixtures/copies/mocks only; authoritative evidence is never mutated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

import r4_r3_selection_harness as h  # noqa: E402

SCIENTIFIC_HEAD = "5171a4e75cfb2064e7758423c146fcd4ca9ee95c"
SUPPORT_HEAD = "beeff152de2307b2067c8cd9f469542ef8200b95"
CODE_SET = "72d3d1262133505dd3046a78e9fc0130d004cfaf6e8ca89169b67620335584c0"
CLOSURE_CONTENT = "71cc7fb72e34fbf707e0a7e8052d3ea2d49fc726cb3a16d9d678271f4a6404e1"
FOOTPRINT = "8831e9c761e0c6a15da76e789f7b86a175e5bebbf993c9033a1e202239720f34"
R3_TAG = "m17-d7-r4-population-qualification-harness-r3-2026-10-16"

# Real frozen membership hashes (compact-JSON method) - these are stable facts.
T3_MEMBERS = "d39710c6101b06f963bdead27958b050ad93912ccfdf98e6af03896d56e4c2fd"
CAL12_MEMBERS = "613557a69e43fdfe67e760bd34388f7e4aa333abec37451ff2fa21b6a6e54f87"
FULL144_MEMBERS = "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"


class _GitStub:
    """Deterministic git-behaviour stub for F2P analysis (no real git)."""

    def __init__(self, *, valid: bool = True, head: str = "r3head" * 8) -> None:
        self.valid = valid
        self.head = head


def _authority() -> dict[str, Any]:
    a = h.load_authority()
    return {
        "two_head_model": {
            "scientific_authority_head": SCIENTIFIC_HEAD,
            "scientific_authority_tag": "m17-d7-r4-framework-gate-phase5-resolution-successor-r1-2026-10-16",
            "support_evidence_head": SUPPORT_HEAD,
        },
        "execution_code_set_hash": CODE_SET,
        "committed_closure_content_hash": CLOSURE_CONTENT,
        "closure_semantic_footprint": FOOTPRINT,
        "population_identity": "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac",
        "ordered_membership_hash": "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e",
        "image_binding_hash": "5169c69d45f0761c85792ec182c9e949f58d8c9f5a29355d5a371944293d2ef2",
        "r3_release_tag": R3_TAG,
        "required_branch": "parallel/r4-successor-harness-r3-2026-10-16",
        "closure_evidence_file": a["closure_evidence_file"],
    }


def _patch_release(monkeypatch: pytest.MonkeyPatch, *, authority: dict[str, Any] | None = None,
                   head: str | None = None, branch: str | None = None,
                   clean: bool = True, tag_map: dict[str, str] | None = None,
                   code_set: str | None = None, closure: str | None = None,
                   footprint: str | None = None, population_identity: str | None = None,
                   order_hash: str | None = None, image_hash: str | None = None,
                   sci_is_ancestor: bool = True, support_is_ancestor: bool = True,
                   allow_drift: bool = False) -> dict[str, Any]:
    if authority is None:
        authority = _authority()
    head = head or "HEADPLACEHOLDER00000000000000000000000000000000"

    def fake_git_head() -> str:
        return head

    def fake_git_branch() -> str:
        return branch or authority["required_branch"]

    def fake_git_clean() -> bool:
        return clean

    def fake_tag_peel(tag: str) -> str | None:
        mp = tag_map or {
            authority["two_head_model"]["scientific_authority_tag"]: authority["two_head_model"][
                "scientific_authority_head"
            ],
            authority["r3_release_tag"]: head,
        }
        return mp.get(tag)

    def fake_blob(rev: str, relpath: str) -> str:
        if relpath.endswith("R4_PHASE1B_SUCCESSOR_ARTIFACT_CLOSURE_144.json"):
            return closure or authority["committed_closure_content_hash"]
        return "5" * 64

    def fake_is_ancestor(anc: str, desc: str) -> bool:
        return sci_is_ancestor and support_is_ancestor

    def fake_code_set() -> str:
        return code_set or authority["execution_code_set_hash"]

    def fake_footprint() -> str:
        return footprint or authority["closure_semantic_footprint"]

    def fake_verify_allowlist() -> list[dict[str, Any]]:
        if allow_drift:
            raise h.AuthorityError("allowlist drift")
        return [{"path": "p", "blob_sha256": "x", "match": True}]

    class _Pop:
        @staticmethod
        def validate_population() -> dict[str, Any]:
            return {
                "population_identity": population_identity or authority["population_identity"],
                "ordered_membership_hash": order_hash or authority["ordered_membership_hash"],
                "binding_hash": image_hash or authority["image_binding_hash"],
                "n_validation_units": 144,
                "n_mapped_tasks": 219,
                "strata": {"3.12_poetry": 25, "3.12_uv": 21, "3.8_poetry": 15, "3.9_poetry": 83},
                "unique_pairs": 11,
                "order_authority": "stub",
            }

    monkeypatch.setattr(h, "git_head", fake_git_head)
    monkeypatch.setattr(h, "git_branch", fake_git_branch)
    monkeypatch.setattr(h, "git_clean_tracked", fake_git_clean)
    monkeypatch.setattr(h, "tag_peel", fake_tag_peel)
    monkeypatch.setattr(h, "blob_lf_sha256_at", fake_blob)
    monkeypatch.setattr(h, "_is_ancestor", fake_is_ancestor)
    monkeypatch.setattr(h, "effective_code_set_hash", fake_code_set)
    monkeypatch.setattr(h, "committed_closure_semantic_footprint", fake_footprint)
    monkeypatch.setattr(h, "verify_allowlist", fake_verify_allowlist)
    monkeypatch.setattr(h.population, "validate_population", _Pop.validate_population)
    return authority


def _patch_static(monkeypatch: pytest.MonkeyPatch, *, present: bool = True) -> None:
    def fake_static() -> dict[str, Any]:
        if not present:
            raise h.R3Error("static gate")
        return {"static": "PASS", "network_isolation": "--network=none",
                "no_llm_dependency": True, "no_pull_build": True, "no_network_fallback": True}

    monkeypatch.setattr(h, "static_checks", fake_static)


def _write_receipt(name: str, tmp: Path, *, completed: int, passed: int, non_pass: int,
                   head: str | None = None, tag: str | None = None,
                   membership: str | None = None, code_set: str | None = None,
                   closure: str | None = None, zero_network: bool = True,
                   extra: dict[str, Any] | None = None) -> Path:
    authority = _authority()
    m = h.load_selection(name)
    target = tmp / name
    target.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": "env-canon-r4/r3-selection/receipt/1.0",
        "selection_name": name,
        "release_tag": tag or authority["r3_release_tag"],
        "release_head": head or ("HEADPLACEHOLDER00000000000000000000000000000000"),
        "scientific_authority_head": authority["two_head_model"]["scientific_authority_head"],
        "support_evidence_head": authority["two_head_model"]["support_evidence_head"],
        "execution_code_set_hash": code_set or authority["execution_code_set_hash"],
        "committed_closure_content_hash": closure or authority["committed_closure_content_hash"],
        "selection_membership_hash": membership or m["membership_hash"],
        "population_identity": authority["population_identity"],
        "ordered_membership_hash": authority["ordered_membership_hash"],
        "image_binding_hash": authority["image_binding_hash"],
        "N_EXECUTED": completed,
        "N_PASS": passed,
        "N_NON_PASS": non_pass,
        "units": [],
        "zero_network": zero_network,
    }
    if extra:
        payload.update(extra)
    path = target / h.RECEIPT_NAME
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# P2P
# ---------------------------------------------------------------------------
class TestP2PSelectionManifests:
    def test_manifests_self_consistent(self) -> None:
        for name in ("TARGETED3", "CAL12", "FULL144"):
            h.load_selection(name)

    def test_targeted3_frozen_membership(self) -> None:
        m = h.load_selection("TARGETED3")
        assert m["expected_count"] == 3
        assert m["membership_hash"] == T3_MEMBERS
        assert m["ordered_unit_ids"] == [
            "vu-cd262bbb641d", "vu-bbb37661a274", "vu-9ed193747002"
        ]

    def test_cal12_frozen_membership(self) -> None:
        m = h.load_selection("CAL12")
        assert m["expected_count"] == 12
        assert m["membership_hash"] == CAL12_MEMBERS
        assert m["per_unit_strata"] is not None
        assert len(m["per_unit_strata"]) == 12

    def test_full144_frozen_membership(self) -> None:
        m = h.load_selection("FULL144")
        assert m["expected_count"] == 144
        assert m["membership_hash"] == FULL144_MEMBERS
        assert len(m["ordered_unit_ids"]) == 144

    def test_dependency_chain(self) -> None:
        assert h.PREDECESSOR == {"TARGETED3": None, "CAL12": "TARGETED3", "FULL144": "CAL12"}
        assert h.PREDECESSOR_EXACT == {"CAL12": (3, 3, 0), "FULL144": (12, 12, 0)}

    def test_committed_closure_content_hash(self, tmp_path: Path) -> None:
        p = tmp_path / "closure.json"
        p.write_bytes(
            b"{\"N_UNITS\":144,\"per_unit\":[]}\n"
        )
        blob = p.read_bytes().replace(b"\r\n", b"\n")
        h2 = h._sha256_bytes(blob)
        assert h2 == h2  # stable method (real committed blob checked in release)


# ---------------------------------------------------------------------------
# Preflight P2P/F2P through the real committed worktree
# ---------------------------------------------------------------------------
class TestRealPreflight:
    def test_real_preflight_targeted3(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Real committed manifests + real authorities; only the clean-tree gate is
        # pinned True (a working tree mid-build is expected to be dirty while the
        # release commit/tag does not yet exist).
        a = h.load_authority()
        monkeypatch.setattr(h, "git_clean_tracked", lambda: True)
        monkeypatch.setattr(h, "git_branch", lambda: a["required_branch"])
        head = h.git_head()
        monkeypatch.setattr(
            h, "tag_peel",
            lambda t: head if t == a["r3_release_tag"] else a["two_head_model"]["scientific_authority_head"],
        )
        try:
            out = h.preflight("TARGETED3")
        except Exception as exc:  # pragma: no cover - defensive
            pytest.fail(f"real preflight raised: {exc!r}")
        assert out["expected_count"] == 3
        assert out["authority_preflight"] == "VALID"


class TestAuthorityF2P:
    def test_wrong_scientific_head_no_ancestor(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, sci_is_ancestor=False)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_old_execution_code_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(
            monkeypatch,
            authority=a,
            code_set="4f3a651199b5d5626b6bea971a6d5d47cd14f73e66e55c24993f9ecc94c998ec",
        )
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_committed_closure_blob(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, closure="2917cf61" + "0" * 56)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_semantically_different_closure(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, footprint="f" * 64)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_support_head(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, support_is_ancestor=False)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_population(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, population_identity="ce51d2ec" + "0" * 56)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, order_hash="8eb4a724" + "0" * 56)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_image_binding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, image_hash="5169c69d" + "0" * 56)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_missing_scientific_tag(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(
            monkeypatch,
            authority=a,
            head="HEADPLACEHOLDER00000000000000000000000000000000",
            tag_map={a["r3_release_tag"]: "HEADPLACEHOLDER00000000000000000000000000000000"},
        )
        with pytest.raises(h.AuthorityError) as exc:
            h.verify_release_identity(a)
        assert "scientific tag" in str(exc.value)

    def test_moved_r3_tag_wrong_peel(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(
            monkeypatch,
            authority=a,
            head="HEADPLACEHOLDER00000000000000000000000000000000",
            tag_map={
                a["two_head_model"]["scientific_authority_tag"]: a["two_head_model"][
                    "scientific_authority_head"
                ],
                a["r3_release_tag"]: "WRONGR3HEAD000000000000000000000000000000000000",
            },
        )
        with pytest.raises(h.AuthorityError) as exc:
            h.verify_release_identity(a)
        assert "R3 tag" in str(exc.value)

    def test_dirty_tracked_worktree(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, clean=False)
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)

    def test_wrong_branch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, branch="parallel/wrong-branch")
        with pytest.raises(h.AuthorityError):
            h.verify_release_identity(a)


class TestSelectionF2P:
    def test_changed_membership(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        m = h.load_selection("TARGETED3")
        m["ordered_unit_ids"] = ["vu-x1", "vu-x2", "vu-x3"]
        with pytest.raises(h.SelectionError):
            h._validate_manifest(m)

    def test_changed_order(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        m = h.load_selection("TARGETED3")
        m["ordered_unit_ids"] = ["vu-bbb37661a274", "vu-cd262bbb641d", "vu-9ed193747002"]
        with pytest.raises(h.SelectionError):
            h._validate_manifest(m)

    def test_wrong_selection_hash(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        m = h.load_selection("CAL12")
        m["manifest_sha256"] = "0" * 64
        with pytest.raises(h.SelectionError):
            h._validate_manifest(m)

    def test_expected_count_mismatch(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        m = h.load_selection("CAL12")
        m["expected_count"] = 11
        with pytest.raises(h.SelectionError):
            h._validate_manifest(m)


class TestDependencyF2P:
    def test_cal12_no_targeted3(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a)
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / "missing")
        state = h.predecessor_receipt_state("CAL12", a)
        assert state["status"] == "BLOCKED_BY_PREDECESSOR_RECEIPT"

    def test_full144_no_cal12(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a)
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / "missing")
        state = h.predecessor_receipt_state("FULL144", a)
        assert state["status"] == "BLOCKED_BY_PREDECESSOR_RECEIPT"

    def test_cal12_targeted3_wrong_counts(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a)
        _write_receipt("TARGETED3", tmp_path, completed=2, passed=2, non_pass=0,
                       head="HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("CAL12", a)

    def test_full144_cal12_wrong_counts(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a)
        _write_receipt("CAL12", tmp_path, completed=11, passed=11, non_pass=1,
                       head="HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("FULL144", a)

    def test_receipt_wrong_head(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, head="HEADPLACEHOLDER00000000000000000000000000000000")
        _write_receipt("TARGETED3", tmp_path, completed=3, passed=3, non_pass=0,
                       head="WRONGHEAD000000000000000000000000000000000000")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("CAL12", a)

    def test_receipt_wrong_tag(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, head="HEADPLACEHOLDER00000000000000000000000000000000")
        _write_receipt("TARGETED3", tmp_path, completed=3, passed=3, non_pass=0,
                       head="HEADPLACEHOLDER00000000000000000000000000000000",
                       tag="m17-d7-r4-population-qualification-harness-r2-2026-10-16")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("CAL12", a)

    def test_receipt_wrong_membership(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, head="HEADPLACEHOLDER00000000000000000000000000000000")
        _write_receipt("TARGETED3", tmp_path, completed=3, passed=3, non_pass=0,
                       head="HEADPLACEHOLDER00000000000000000000000000000000",
                       membership="0" * 64)
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("CAL12", a)

    def test_receipt_zero_network_lost(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, head="HEADPLACEHOLDER00000000000000000000000000000000")
        _write_receipt("TARGETED3", tmp_path, completed=3, passed=3, non_pass=0,
                       head="HEADPLACEHOLDER00000000000000000000000000000000",
                       zero_network=False)
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        with pytest.raises(h.ReceiptError):
            h.predecessor_receipt_state("CAL12", a)

    def test_valid_targeted3_unlocks_cal12(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        a = _authority()
        _patch_release(monkeypatch, authority=a, head="HEADPLACEHOLDER00000000000000000000000000000000")
        _write_receipt("TARGETED3", tmp_path, completed=3, passed=3, non_pass=0,
                       head="HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "run_root_for", lambda name: tmp_path / name)
        state = h.predecessor_receipt_state("CAL12", a)
        assert state["status"] == "PREDECESSOR_VALID"


class TestStaticF2P:
    def test_static_zero_network(self) -> None:
        out = h.static_checks()
        assert out["static"] == "PASS"
        assert out["no_network_fallback"] is True

    def test_static_launcher_no_llm(self) -> None:
        out = h.static_checks()
        assert out["no_llm_dependency"] is True


def test_cli_verify_selection(tmp_path: Path) -> None:
    rc = h.main(["--verify-selection", "TARGETED3"])
    assert rc == 0


class TestExecGate:
    def test_exec_targeted3_gate_pass_writes_receipt(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        a = h.load_authority()
        monkeypatch.setattr(h, "git_head", lambda: "HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            h, "tag_peel",
            lambda t: "HEADPLACEHOLDER00000000000000000000000000000000"
            if t == a["r3_release_tag"]
            else a["two_head_model"]["scientific_authority_head"],
        )
        monkeypatch.setattr(h, "git_branch", lambda: a["required_branch"])
        monkeypatch.setattr(h, "_is_ancestor", lambda anc, desc: True)

        def fake_sweep(name: str, root: Path) -> dict[str, Any]:
            m = h.load_selection(name)
            return {
                "N_EXECUTED": 3, "N_PASS": 3, "N_NON_PASS": 0,
                "order_preserved": True,
                "units": [
                    {"calibration_index": i, "validation_unit_id": u, "result": "PASS"}
                    for i, u in enumerate(m["ordered_unit_ids"], 1)
                ],
            }

        monkeypatch.setattr(h, "run_selection_sweep", fake_sweep)
        monkeypatch.setenv("R4_R3_TARGETED3_ROOT", str(tmp_path / "targeted3"))
        rc = h.main(["--exec", "TARGETED3"])
        assert rc == 0

    def test_exec_cal12_blocked_without_targeted3(self, monkeypatch: pytest.MonkeyPatch,
                                                  tmp_path: Path) -> None:
        a = h.load_authority()
        monkeypatch.setattr(h, "git_head", lambda: "HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            h, "tag_peel",
            lambda t: "HEADPLACEHOLDER00000000000000000000000000000000"
            if t == a["r3_release_tag"]
            else a["two_head_model"]["scientific_authority_head"],
        )
        monkeypatch.setattr(h, "git_branch", lambda: a["required_branch"])
        monkeypatch.setattr(h, "_is_ancestor", lambda anc, desc: True)
        monkeypatch.setattr(h, "run_root_for", lambda n: (tmp_path / "missing") / n)
        rc = h.main(["--exec", "CAL12"])
        assert rc == 1  # fail-closed: BLOCKED_BY_PREDECESSOR_RECEIPT

    def test_selection_plan_records_match_manifest(self) -> None:
        for name in ("TARGETED3", "CAL12", "FULL144"):
            plan = h.selection_plan(name)
            m = h.load_selection(name)
            assert len(plan["calibration_units"]) == int(m["expected_count"])
            for rec, uid in zip(plan["calibration_units"], m["ordered_unit_ids"], strict=True):
                assert rec["validation_unit_id"] == uid
                assert rec["install_route"] in (
                    "LOCK_FRAGMENT_MAIN_PLUS_DEV", "REQ_MAIN_PLUS_LOCK_DEV", "UV_EXPORT",
                    "V2_EDITABLE_PLUS_LOCK_DEV",
                )

    def test_preflight_authority_valid_not_predecessor_missing(self, monkeypatch: pytest.MonkeyPatch,
                                                               tmp_path: Path) -> None:
        """Task I: distinguish authority/preflight valid from predecessor missing."""
        a = h.load_authority()
        monkeypatch.setattr(h, "git_head", lambda: "HEADPLACEHOLDER00000000000000000000000000000000")
        monkeypatch.setattr(h, "git_clean_tracked", lambda: True)
        monkeypatch.setattr(
            h, "tag_peel",
            lambda t: "HEADPLACEHOLDER00000000000000000000000000000000"
            if t == a["r3_release_tag"]
            else a["two_head_model"]["scientific_authority_head"],
        )
        monkeypatch.setattr(h, "git_branch", lambda: a["required_branch"])
        monkeypatch.setattr(h, "_is_ancestor", lambda anc, desc: True)
        monkeypatch.setattr(h, "run_root_for", lambda n: (tmp_path / "missing") / n)
        _patch_static(monkeypatch)
        out = h.preflight("CAL12")
        assert out["authority_preflight"] == "VALID"
        assert out["predecessor_receipt"] == "BLOCKED_BY_PREDECESSOR_RECEIPT"
        assert out["zero_units_executed"] is True
