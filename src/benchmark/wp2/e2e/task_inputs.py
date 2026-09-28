"""WP-2 Mission-11 E2E Smoke - task inputs (B2.2) - generator-visible, label-free.

Loads the stored SIP intent (byte-identical to the WP-1 agent text) and renders
the developer change description with the fixed Appendix P1 template. Commit ids
are carried for the evaluator / scope builder ONLY and never placed in a prompt.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
E2E_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v1"
CENSUS = json.loads((PROJECT / "research/wp2/oracle_confirmation_linux_v2_2026-09-23" /
                     "dev_census_2026-09-23.json").read_text(encoding="utf-8"))
INVENTORY = json.loads((PROJECT / "research/wp2/" /
                        "wp2_dev_unchanged_p2p_candidate_inventory_v1_2026-09-25.json").read_text(encoding="utf-8"))
INTENT_DIR = PROJECT / "benchmark_data" / "real_commit_impact_saleor" / "scientific"

PYTHON_REQUIREMENT = {"py38": "Python >= 3.8", "py39": "Python >= 3.9",
                      "py312": "Python >= 3.12"}


@dataclass(frozen=True)
class TaskInput:
    task_id: str
    era_key: str
    python_requirement: str
    parent_commit: str
    target_commit: str
    developer_change_description_rendered: str
    intent_source_sha256: str


def _intent_path(task_id: str) -> Path:
    return INTENT_DIR / task_id / "public" / "intent.json"


def load_intent(task_id: str) -> dict:
    p = _intent_path(task_id)
    if not p.exists():
        raise FileNotFoundError(f"intent not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def render_description(intent: dict) -> str:
    """Appendix P1 fixed rendering: structured fields if present, else verbatim."""
    text = intent.get("intent_text", "")
    structured = any(k in intent for k in ("title", "before", "after", "acceptance_criteria"))
    if not structured:
        return text
    lines = []
    if intent.get("title"):
        lines.append(f"Title: {intent['title']}")
    if intent.get("before"):
        lines.append(f"Current behavior: {intent['before']}")
    if intent.get("after"):
        lines.append(f"Required behavior: {intent['after']}")
    if intent.get("acceptance_criteria"):
        lines.append("Acceptance criteria:")
        for c in intent["acceptance_criteria"]:
            lines.append(f"- {c}")
    return "\n".join(lines)


def load_task_input(task_id: str) -> TaskInput:
    intent = load_intent(task_id)
    era = "UNKNOWN"
    for r in INVENTORY.get("tasks", []):
        if r["task_id"] == task_id:
            era = r.get("era_key", "UNKNOWN")
            break
    parent = target = None
    for c in CENSUS.get("tasks", []):
        if c["task_id"] == task_id:
            parent, target = c["parent_commit"], c["target_commit"]
            break
    if parent is None or target is None:
        raise KeyError(task_id)
    rendered = render_description(intent)
    intent_sha = hashlib.sha256(
        json.dumps(intent, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return TaskInput(
        task_id=task_id,
        era_key=era,
        python_requirement=PYTHON_REQUIREMENT.get(era, "Python 3.x"),
        parent_commit=parent,
        target_commit=target,
        developer_change_description_rendered=rendered,
        intent_source_sha256=intent_sha,
    )


def record_intent_source(union_tasks: list[str]) -> dict:
    """B2.1 check: one intent per union task; record path + sha256."""
    rec = {"artifact": "intent_source", "path": str(INTENT_DIR),
           "per_task": {}, "missing": []}
    for tid in union_tasks:
        try:
            intent = load_intent(tid)
            rec["per_task"][tid] = {
                "intent_path": str(_intent_path(tid)),
                "intent_sha256": hashlib.sha256(
                    json.dumps(intent, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
                "intent_source": intent.get("intent_source"),
            }
        except FileNotFoundError:
            rec["missing"].append(tid)
    out = E2E_ROOT / "inputs" / "intent_source.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    return rec
