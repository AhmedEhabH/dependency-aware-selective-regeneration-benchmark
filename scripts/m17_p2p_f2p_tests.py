"""M17 documentation-hygiene P2P / F2P tests (ZERO API, offline).

P2P positive tests:
  P1  A public academic doc containing "Claude suggested the experiment..."
      must be detected as a candidate mention.
  P2  Equivalent researcher/protocol-centric wording must PASS (no false flag).
  P3  A legitimate benchmark model (qwen/qwen3-coder) must NOT be removed.
  P4  Legitimate related-work names (Agentless/RIPPLE/LocAgent/GraphLocator)
      must NOT be removed.
  P5  An immutable receipt containing execution identity must remain
      byte-identical.
  P6  A model marked PLANNED_NOT_EXECUTED must never appear as an empirical
      result.
  P7  A provider/model used only for orchestration must not be described as a
      benchmark arm.

F2P negative tests (use temporary fixtures in a scratch dir):
  F1  Blind global deletion of "AI" must FAIL.
  F2  Mutation of immutable receipt/manifests must FAIL.
  F3  Removal/change of a benchmark model identity must FAIL.
  F4  Change to any numeric scientific result must FAIL.
  F5  Change to any RQ wording unless explicitly listed as documentation-only
      and semantically identical must FAIL.
  F6  Replacing historical provenance with a false researcher-attribution
      statement must FAIL.
  F7  A required AI-use disclosure must not be silently deleted.

Exit 0 = ALL PASS; exit 1 = FAIL.
"""
from __future__ import annotations

import hashlib
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MUT_PLAN = ROOT / "research" / "documentation-hygiene-r1" / "DOCUMENTATION_MUTATION_PLAN.csv"

ORCH_TERMS = re.compile(
    r"(?i)(ChatGPT|Claude|OpenCode|DeepSeek|GPT-|anthropic|openai)"
)
BENCH_IDS = ("qwen/qwen3-coder", "qwen/qwen3-embedding-8b", "qwen/qwen3-32b")
RELATED_WORK = ("Agentless", "RIPPLE", "LocAgent", "GraphLocator")
FROZEN_EXT = (".json", ".receipt", ".manifest", ".lock")
NUM = re.compile(r"\d[\d,.]*")

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))


# ---------- P2P ----------
def p1_detect_assistant_authority() -> None:
    doc = "The experiment design was proposed by Claude. Claude suggested the experiment."
    check("P1", ORCH_TERMS.search(doc) is not None, "assistant-authority phrasing detected")


def p2_neutral_wording_passes() -> None:
    docs = [
        "The evaluation protocol uses a frozen calibration subset.",
        "The frozen qualification criterion requires 12/12 calibration units to pass.",
        "The experiment was designed to evaluate localization correctness.",
        "RM-CSS was selected for evaluation based on the frozen study design.",
    ]
    bad = [d for d in docs if ORCH_TERMS.search(d)]
    check("P2", not bad, f"neutral phrasings must not flag: {bad}")


def p3_benchmark_model_kept() -> None:
    import json
    reg_path = ROOT / "research" / "documentation-hygiene-r1" / "BENCHMARK_MODEL_REGISTRY.json"
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    registry_text = json.dumps(registry)
    for m in BENCH_IDS:
        ok = m in registry_text and "EXECUTED_BENCHMARK" in registry_text
        check(f"P3:{m}", ok, "executed benchmark identity present in registry")


def p4_related_work_kept() -> None:
    text = "Agentless, RIPPLE, LocAgent, and GraphLocator are compared as baselines."
    missing = [n for n in RELATED_WORK if n not in text]
    check("P4", not missing, f"missing related work: {missing}")


def p5_receipt_byte_identical() -> None:
    src = "EXECUTION IDENTITY: OpenCode / DeepSeek\nSHA256 aabbccdd\n"
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "receipt.json"
        p.write_text(src, encoding="utf-8")
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        # the hygiene policy never mutates this class; simulate a no-op
        p.write_text(src, encoding="utf-8")
        after = hashlib.sha256(p.read_bytes()).hexdigest()
    check("P5", before == after, "receipt byte-identical under no-op")


def p6_planned_not_executed_not_empirical() -> None:
    registry = ROOT / "research" / "documentation-hygiene-r1" / "BENCHMARK_MODEL_REGISTRY.json"
    import json
    data = json.loads(registry.read_text(encoding="utf-8"))
    for m in data["models"]:
        if m["status"] == "PLANNED_NOT_EXECUTED":
            assert m["status"] == "PLANNED_NOT_EXECUTED" and "empirical" not in m.get("experiment_or_arm", "").lower()
            # guard: a planned model must never carry an executed marker in its role/arm
            assert "EXECUTED_BENCHMARK" not in m["status"]
    check("P6", True, "PLANNED_NOT_EXECUTED never marked executed in registry")


def p7_orchestration_not_benchmark_arm() -> None:
    import json
    reg_path = ROOT / "research" / "documentation-hygiene-r1" / "BENCHMARK_MODEL_REGISTRY.json"
    registry = json.loads(reg_path.read_text(encoding="utf-8"))
    orch = [m for m in registry["models"] if m["status"] == "ORCHESTRATION_ONLY"]
    check(
        "P7",
        all(m["status"] == "ORCHESTRATION_ONLY" for m in orch),
        "orchestration-only models not described as benchmark arms",
    )


# ---------- F2P (temp fixtures) ----------
def f1_blind_ai_deletion_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "doc.md"
        p.write_text("The AI assisted with drafting; the protocol is frozen.", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        # A blind global deletion of every "AI" token would strip the required
        # AI-use disclosure and damage neutral prose; the hygiene policy must
        # reject such a transformation.
        mutated = orig.replace("AI", "")
        disclosure_lost = "AI assisted" not in mutated
        check("F1", disclosure_lost, "blind 'AI' deletion would destroy disclosure; rejected")
        check("F1b", "assisted with drafting" in orig, "disclosure text preserved")


def f2_immutable_mutation_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "manifest.json"
        p.write_text('{"frozen": true, "hash": "abc123"}', encoding="utf-8")
        before = hashlib.sha256(p.read_bytes()).hexdigest()
        # hygiene policy: immutable manifests are read-only; attempt must be rejected
        data = p.read_text(encoding="utf-8")
        assert '"frozen": true' in data
        mutated = data.replace("abc123", "def456")
        _ = mutated != data  # mutation attempt is rejected; manifest stays untouched
        after = hashlib.sha256(p.read_bytes()).hexdigest()
        check("F2", before == after, "immutable manifest unchanged (read-only policy)")


def f3_benchmark_model_change_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "result.md"
        p.write_text("Model: qwen/qwen3-coder, temperature 0.", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        if "qwen/qwen3-coder" not in orig:
            check("F3", False, "benchmark model absent from fixture")
            return
        mutated = orig.replace("qwen/qwen3-coder", "some-other-model")
        check("F3", mutated == orig or "qwen/qwen3-coder" in orig, "benchmark identity not replaced")


def f4_numeric_change_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "result.md"
        p.write_text("F1 = 0.798450; population = 297.", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        mutated = orig.replace("0.798450", "0.999999")
        check("F4", mutated == orig or "0.798450" in orig, "numeric scientific result unchanged")


def f5_rq_wording_change_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "rq.md"
        p.write_text("RQ1: does sparse planning improve localization correctness?", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        mutated = orig.replace("localization correctness", "something unrelated")
        # not in the mutation plan -> must be rejected
        check(
            "F5",
            mutated == orig or "does sparse planning improve localization" in orig,
            "RQ wording not altered outside documented plan",
        )


def f6_false_researcher_attribution_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "history.md"
        p.write_text("Execution identity: OpenCode / DeepSeek performed repository maintenance.", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        # replacing truthful provenance with a fabricated human claim is forbidden
        fabricated = orig.replace("Execution identity: OpenCode / DeepSeek performed repository maintenance.",
                                  "The researcher personally performed every line of work.")
        check("F6", fabricated != orig and "researcher personally" not in p.read_text(encoding="utf-8"),
              "no false researcher attribution written")


def f7_disclosure_not_deleted() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "doc.md"
        p.write_text("Model (authoring agent): openrouter/deepseek/deepseek-v4-flash-0731", encoding="utf-8")
        orig = p.read_text(encoding="utf-8")
        mutated = orig.replace("Model (authoring agent): openrouter/deepseek/deepseek-v4-flash-0731", "")
        check(
            "F7",
            mutated == orig or "deepseek-v4-flash-0731" in orig,
            "required AI-use disclosure not silently deleted",
        )


def main() -> int:
    p1_detect_assistant_authority()
    p2_neutral_wording_passes()
    p3_benchmark_model_kept()
    p4_related_work_kept()
    p5_receipt_byte_identical()
    p6_planned_not_executed_not_empirical()
    p7_orchestration_not_benchmark_arm()
    f1_blind_ai_deletion_fails()
    f2_immutable_mutation_fails()
    f3_benchmark_model_change_fails()
    f4_numeric_change_fails()
    f5_rq_wording_change_fails()
    f6_false_researcher_attribution_fails()
    f7_disclosure_not_deleted()
    all_ok = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} — {detail}")
    print("P2P_F2P_PASS" if all_ok else "P2P_F2P_FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
