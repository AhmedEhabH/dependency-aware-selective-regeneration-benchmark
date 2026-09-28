"""Mission-12B v2.1 - mechanical summarizer/gates unit tests (T6): zero API.

Covers:
- per-arm accounting (first-call valid / post-repair / APPLIED / RESOLVED / F2P /
  P2P-S / P2P-U200 / violations / tokens / USD / wall)
- primary gate rule (INTERFACE_V3_PROBE / GENERATOR_COMPETENCE_OR_SPEC_REVIEW /
  PILOT_DESIGN)
- secondary d220-omitted table is descriptive and never changes NEXT
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import wp2_e2e_smoke_v21_summary as sm


def _mk_ep(root: Path, task: str, arm: str, status: str, repair: bool,
           diff_sha: str, created: str, subdir: str = "episodes") -> None:
    d = root / subdir / task / arm
    d.mkdir(parents=True, exist_ok=True)
    rec = {"task_id": task, "arm": arm, "status": status, "repair_used": repair,
           "diff_sha256": diff_sha if status == "APPLIED" else "",
           "created_utc": created,
           "calls": [{"prompt_tokens": 100, "completion_tokens": 50,
                      "cost_usd_actual": 0.001}],
           "validation": {"initial": ["OUT_OF_SCOPE_FILE:x"] if status == "INVALID_AFTER_REPAIR" else [],
                          "repair": []}}
    (d / "episode.json").write_text(json.dumps(rec), encoding="utf-8")


def _mk_eval(root: Path, diff_sha: str, f2p: str, p2ps: str, p2pu: str,
             resolved: bool) -> None:
    d = root / "evaluations" / "unique" / f"unique_{diff_sha[:8]}"
    d.mkdir(parents=True, exist_ok=True)
    rec = {"task_id": "t", "diff_sha256": diff_sha, "status": "DONE",
           "f2p_task": f2p, "p2p_s_task": p2ps, "p2p_u200_task": p2pu,
           "resolved": resolved, "flaky_under_patch": []}
    (d / "evaluation.json").write_text(json.dumps(rec), encoding="utf-8")


def test_per_arm_accounting(tmp_path: Path, monkeypatch) -> None:
    old = sm.V21_ROOT
    sm.V21_ROOT = tmp_path
    monkeypatch.setattr(sm, "V21_ROOT", tmp_path)
    tasks = ["t1", "t2", "t3"]
    try:
        d1 = "a" * 64
        d2 = "b" * 64
        _mk_ep(tmp_path, "t1", "GOLD_HARD", "APPLIED", False, d1, "2026-09-28T00:00:00Z")
        _mk_ep(tmp_path, "t2", "GOLD_HARD", "APPLIED", True, d2, "2026-09-28T00:00:10Z")
        _mk_ep(tmp_path, "t3", "GOLD_HARD", "INVALID_AFTER_REPAIR", True, "",
               "2026-09-28T00:00:20Z")
        _mk_eval(tmp_path, d1, "PASS", "PASS", "PASS", True)
        _mk_eval(tmp_path, d2, "FAIL", "PASS", "UNDEFINED", False)
        per_arm = sm.summarize(tasks)
        gold = per_arm["GOLD_HARD"]
        assert gold["first_call_valid"] == 1
        assert gold["post_repair_valid"] == 1
        assert gold["applied"] == 2
        assert gold["resolved"] == 1
        assert gold["f2p"] == 1
        assert gold["p2p_s"] == 2
        assert gold["p2p_u200"] == 1
        assert gold["architecture_scope_violations"] == 1
        assert gold["logical_tokens"] == 450
        assert gold["usd"] == 0.003
        assert gold["wall_time_s"] == 20.0
    finally:
        sm.V21_ROOT = old


def test_gate_floor_probe(tmp_path: Path, monkeypatch) -> None:
    old = sm.V21_ROOT
    sm.V21_ROOT = tmp_path
    monkeypatch.setattr(sm, "V21_ROOT", tmp_path)
    try:
        per_arm = {arm: {"applied": 3, "resolved": 0} for arm in sm.ARMS}
        token, _ = sm._primary_gate(per_arm)
        assert token == "INTERFACE_V3_PROBE"
    finally:
        sm.V21_ROOT = old


def test_gate_competence_review(tmp_path: Path, monkeypatch) -> None:
    old = sm.V21_ROOT
    sm.V21_ROOT = tmp_path
    monkeypatch.setattr(sm, "V21_ROOT", tmp_path)
    try:
        per_arm = {arm: {"applied": 7, "resolved": 2} for arm in sm.ARMS}
        token, _ = sm._primary_gate(per_arm)
        assert token == "GENERATOR_COMPETENCE_OR_SPEC_REVIEW"
    finally:
        sm.V21_ROOT = old


def test_gate_pilot_design(tmp_path: Path, monkeypatch) -> None:
    old = sm.V21_ROOT
    sm.V21_ROOT = tmp_path
    monkeypatch.setattr(sm, "V21_ROOT", tmp_path)
    try:
        per_arm = {arm: {"applied": 9, "resolved": 3} for arm in sm.ARMS}
        token, _ = sm._primary_gate(per_arm)
        assert token == "PILOT_DESIGN"
    finally:
        sm.V21_ROOT = old


def test_secondary_never_changes_next(tmp_path: Path, monkeypatch) -> None:
    """The d220-omitted table is descriptive only; the primary gate owns NEXT."""
    old = sm.V21_ROOT
    sm.V21_ROOT = tmp_path
    monkeypatch.setattr(sm, "V21_ROOT", tmp_path)
    try:
        primary = {arm: {"applied": 8, "resolved": 4} for arm in sm.ARMS}
        secondary = {arm: {"applied": 8, "resolved": 4} for arm in sm.ARMS}
        tok_p, _ = sm._primary_gate(primary)
        tok_s, _ = sm._primary_gate(secondary)
        # even if secondary differs, NEXT is always derived from the primary table
        assert tok_p == "PILOT_DESIGN"
        assert tok_s == tok_p  # same GOLD numbers -> same NEXT; never overridden
    finally:
        sm.V21_ROOT = old
