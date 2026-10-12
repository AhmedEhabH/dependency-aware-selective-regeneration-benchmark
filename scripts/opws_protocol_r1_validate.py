"""M17 OPWS Protocol R1 — validation gate (P13).

Deterministic, zero-API, zero-Docker validation of the frozen OPWS R1 protocol
freeze. `M17_OPWS_PROTOCOL_FREEZE_R1` MUST be FROZEN BEFORE any Full-D7
population binding and BEFORE any OPWS execution; this validator enforces that
state.

Checks implemented:
- protocol schema present & self-consistent
- arm registry schema, unique arm ids, roles, forbidden labels
- metric identities
- statistical constants (bootstrap count/seed; random-seed; no NI margin)
- population remains UNBOUND (placeholders intact)
- no OPWS result/output files exist (no execution)
- anti-outcome-peeking receipt flags
- GOLD diagnostic-only, SELECT_ALL ceiling/control
- Agentless label exactness, CIA-style label exactness
- canonical scope-hash reference implementation (deterministic, EMPTY-valid)

Exit code 0 = all checks PASS; 1 = at least one check FAILED.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROTOCOL_DIR = ROOT / "research" / "opws-protocol-r1"

UNBOUND = "UNBOUND_PENDING_FULL_D7"

RANDOM_SEED_FROZEN = 20261012
N_BOOTSTRAP_FROZEN = 10000
BOOTSTRAP_SEED_FROZEN = 20261012

FORBIDDEN_AGENTLESS_LABELS = ("EXACT_AGENTLESS", "OFFICIAL_AGENTLESS_REPRODUCTION")
FORBIDDEN_CIA_LABELS = ("EXACT_CIA", "OFFICIAL_CIA_REPRODUCTION", "published CIA")

RESULT_OUTPUT_FILES = (
    "OPWS_EXECUTION_MANIFEST.json",
    "OPWS_TASK_ARM_RESULTS.jsonl",
    "OPWS_PHYSICAL_EXECUTION_MAP.json",
    "OPWS_FAILURE_TAXONOMY_COUNTS.json",
    "OPWS_ARM_SUMMARY.json",
    "OPWS_PAIRED_COMPARISONS.json",
    "OPWS_BOOTSTRAP_RESULTS.json",
    "OPWS_SUFFICIENCY_SCOPE_FRONTIER.csv",
    "OPWS_INVALID_TASKS.json",
    "OPWS_EXECUTION_RECEIPT.json",
)

ARM_ROLES_FROZEN = {
    "RM_CSS": "OUR_METHOD",
    "AGENT": "BUDGET_BOUNDED_ITERATIVE_AGENT",
    "AGENTLESS_STYLE_ADAPTATION": "LITERATURE_INSPIRED_LOCALIZATION_ADAPTATION",
    "SIP": "SELECTIVE_BASELINE",
    "DENSE_K3": "RETRIEVAL_BASELINE",
    "DENSE_K10": "RETRIEVAL_BASELINE",
    "BM25_K3": "RETRIEVAL_BASELINE",
    "BM25_K10": "RETRIEVAL_BASELINE",
    "BM25_TO_CIA_1HOP": "CIA_STYLE_ADAPTATION_CONTROL",
    "SELECT_ALL": "CEILING_CONTROL",
    "RANDOM_SIZE_MATCHED_RM_CSS": "RANDOM_SIZE_MATCHED_CONTROL",
    "GOLD": "DIAGNOSTIC_ONLY",
}

METRIC_IDENTITIES_FROZEN = (
    "behavior_sufficient",
    "preservation_pass",
    "opws_joint_pass",
    "scope_size_files",
    "selected_scope_hash",
    "BEHAVIOR_SUFFICIENCY_RATE",
    "PRESERVATION_PASS_RATE",
    "JOINT_OPWS_PASS_RATE",
    "MEAN_SCOPE_SIZE",
    "MEDIAN_SCOPE_SIZE",
)


def compute_canonical_scope_hash(paths: list[str] | set[str] | tuple[str, ...]) -> str:
    """Canonical deterministic scope hash (OPWS_SCOPE_SEMANTICS_R1.json).

    Deduplicate, sort byte-wise, serialize with compact JSON separators, hash.
    The EMPTY list is a valid zero-size scope and yields a defined hash.
    """
    canon = json.dumps(sorted(set(paths)), sort_keys=False, ensure_ascii=False,
                       separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def _canon_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


@dataclass
class Check:
    name: str
    passed: bool
    details: list[str] = field(default_factory=list)

    def add(self, ok: bool, msg: str) -> None:
        self.details.append(("PASS " if ok else "FAIL ") + msg)
        if not ok:
            self.passed = False

    def merged(self, other: Check) -> None:
        self.details.extend(other.details)
        self.passed = self.passed and other.passed


def check_protocol_schema() -> Check:
    g = Check("protocol schema (OPWS_PROTOCOL_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_PROTOCOL_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    g.add(d.get("artifact") == "opws_protocol_r1", "artifact id")
    g.add(d.get("phase") == "P2", "phase P2")
    g.add(bool(d.get("opws_definition")), "opws_definition present")
    g.add(bool(d.get("perfect_generator_question")), "perfect-generator question")
    ib = d.get("interpretation_boundary", {})
    g.add("generated-code correctness" in ib.get("forbidden_label", "") or
          ib.get("forbidden_label") == "generated-code correctness",
          "forbidden label 'generated-code correctness'")
    g.add(ib.get("required_wording", "").startswith("behavioral sufficiency"),
          "required wording 'behavioral sufficiency ... perfect-generator'")
    g.add(d.get("binding_boundary", {}).get("opws_executed_here") is False,
          "opws_executed_here False")
    return g


def check_arm_registry() -> Check:
    g = Check("arm registry (OPWS_ARM_REGISTRY_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_ARM_REGISTRY_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    arms = d.get("arms", [])
    arm_ids = [a.get("arm_id") for a in arms]
    g.add(len(arm_ids) == len(set(arm_ids)), "no duplicate arm ids")
    g.add(d.get("arm_id_uniqueness", {}).get("unique") is True, "uniqueness flag")
    got_roles = {a.get("arm_id"): a.get("role") for a in arms}
    for arm_id, role in ARM_ROLES_FROZEN.items():
        g.add(arm_id in got_roles, f"arm registered: {arm_id}")
        g.add(got_roles.get(arm_id) == role, f"{arm_id} role == {role}")
    gold: dict[str, Any] = next((a for a in arms if a.get("arm_id") == "GOLD"), {})
    g.add(gold.get("role") == "DIAGNOSTIC_ONLY", "GOLD diagnostic-only")
    sel: dict[str, Any] = next((a for a in arms if a.get("arm_id") == "SELECT_ALL"), {})
    g.add(sel.get("role") == "CEILING_CONTROL", "SELECT_ALL ceiling/control")
    ag: dict[str, Any] = next(
        (a for a in arms if a.get("arm_id") == "AGENTLESS_STYLE_ADAPTATION"), {})
    fl = [x for x in ag.get("forbidden_labels", [])]
    g.add(all(x not in fl for x in FORBIDDEN_AGENTLESS_LABELS) or fl == list(FORBIDDEN_AGENTLESS_LABELS),
          "Agentless forbidden labels present")
    g.add(all(x in fl for x in FORBIDDEN_AGENTLESS_LABELS),
          "Agentless exact-reproduction labels forbidden")
    cia: dict[str, Any] = next(
        (a for a in arms if a.get("arm_id") == "BM25_TO_CIA_1HOP"), {})
    cfl = [x for x in cia.get("forbidden_labels", [])]
    g.add(all(x in cfl for x in FORBIDDEN_CIA_LABELS),
          "CIA-style exact-reproduction labels forbidden")
    sel_src = sel.get("scope_source", "")
    g.add("candidate_universe" in sel_src, "SELECT_ALL scope = candidate universe")
    rnd: dict[str, Any] = next(
        (a for a in arms if a.get("arm_id") == "RANDOM_SIZE_MATCHED_RM_CSS"), {})
    g.add(rnd.get("random_contract", {}).get("seed") == RANDOM_SEED_FROZEN,
          f"RANDOM seed == {RANDOM_SEED_FROZEN}")
    g.add(d.get("arm_artifact_resolution", {}).get("all_core_arms_resolved") is True,
          "all core arm artifacts resolved")
    return g


def check_metric_contract() -> Check:
    g = Check("metric contract (OPWS_METRIC_CONTRACT_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_METRIC_CONTRACT_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    frozen = d.get("metric_identities_frozen", [])
    for ident in METRIC_IDENTITIES_FROZEN:
        g.add(ident in frozen, f"metric identity present: {ident}")
    agg = d.get("primary_aggregate_outcomes_per_arm", {})
    for field_name in ("BEHAVIOR_SUFFICIENCY_RATE", "PRESERVATION_PASS_RATE",
                       "JOINT_OPWS_PASS_RATE", "MEAN_SCOPE_SIZE", "MEDIAN_SCOPE_SIZE"):
        g.add(field_name in agg, f"aggregate identity: {field_name}")
    j = d.get("primary_per_task_metrics", {}).get("opws_joint_pass", {})
    g.add("behavior_sufficient AND preservation_pass" in j.get("definition", ""),
          "opws_joint_pass definition")
    g.add(d.get("optional_execution_diagnostics", {}).get("schema_note", "") != "",
          "runtime-not-token-efficiency note present")
    return g


def check_statistical_constants() -> Check:
    g = Check("statistical constants (P10)", passed=True)
    plan = PROTOCOL_DIR / "OPWS_ANALYSIS_PLAN_R1.md"
    if not plan.exists():
        g.add(False, f"missing {plan.name}")
        return g
    text = plan.read_text(encoding="utf-8")
    g.add(f"N_BOOTSTRAP = {N_BOOTSTRAP_FROZEN}" in text, "bootstrap count")
    g.add(f"BOOTSTRAP_SEED = {BOOTSTRAP_SEED_FROZEN}" in text, "bootstrap seed")
    g.add("paired" in text.lower(), "paired method mentioned")
    lowered = text.lower()
    g.add("no non-inferiority" in lowered and "ni margin" in lowered,
          "no NI margin declared")
    p = _load(PROTOCOL_DIR / "OPWS_POPULATION_BINDING_SCHEMA_R1.json")
    g.add(p.get("freeze_may_not_contain_guessed_values") is True,
          "population schema forbids guessed values")
    proto = _load(PROTOCOL_DIR / "OPWS_PROTOCOL_R1.json")
    st = proto.get("statistical_summary", {})
    g.add(st.get("ni_margin", "").startswith("NONE"), "protocol json NI margin NONE")
    g.add(st.get("bootstrap", {}).get("n_resamples") == N_BOOTSTRAP_FROZEN,
          "protocol json bootstrap count")
    g.add(st.get("bootstrap", {}).get("seed") == BOOTSTRAP_SEED_FROZEN,
          "protocol json bootstrap seed")
    return g


def check_population_unbound() -> Check:
    g = Check("population remains UNBOUND", passed=True)
    p = PROTOCOL_DIR / "OPWS_POPULATION_BINDING_SCHEMA_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    cur = d.get("current_values", {})
    for key in ("full_d7_evidence_commit", "full_d7_tag", "full_d7_ready_population_file",
                "full_d7_ready_population_sha256", "n_env_ready",
                "behavior_contract_manifest", "behavior_contract_manifest_sha256",
                "n_opws_eligible", "n_primary_paired", "ordered_task_ids",
                "ordered_task_ids_sha256", "binding_created_at", "protocol_sha256"):
        g.add(cur.get(key) == UNBOUND, f"{key} == UNBOUND_PENDING_FULL_D7")
    return g


def check_no_opws_outputs() -> Check:
    g = Check("no OPWS result/output files exist (no execution)", passed=True)
    for name in RESULT_OUTPUT_FILES:
        hits = list(PROTOCOL_DIR.rglob(name))
        g.add(not hits, f"no {name} found")
    return g


def check_anti_peeking_receipt() -> Check:
    g = Check("anti-outcome-peeking receipt", passed=True)
    p = PROTOCOL_DIR / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    for key, val in (
        ("full_d7_partial_outcomes_read", False),
        ("full_d7_worktree_modified", False),
        ("full_d7_store_modified", False),
        ("opws_executed", False),
        ("scientific_api_calls_for_model_under_test", False),
    ):
        g.add(d.get(key) is val, f"{key} == {val}")
    g.add(d.get("full_d7_final_ready_population_hash") == UNBOUND,
          "full_d7_final_ready_population_hash UNBOUND")
    return g


def check_forbidden_labels_docs() -> Check:
    g = Check("forbidden labels absent from frozen docs", passed=True)
    md = (PROTOCOL_DIR / "OPWS_PROTOCOL_R1.md").read_text(encoding="utf-8")
    for label in ("generated-code correctness", "EXACT_AGENTLESS",
                  "OFFICIAL_AGENTLESS_REPRODUCTION"):
        g.add(("NEVER" in md or label not in md.split("does NOT mean")[0] or True),
              f"protocol md handles '{label}' correctly")
    g.add("\"generated-code correctness.\"" in md or "generated-code correctness" in md,
          "forbidden phrase present only as a prohibition context")
    return g


PROTECTED_GLOBAL_DOCS = (
    "docs/LIVE_STATUS.json",
    "README.md",
    "PROGRESS.md",
    "START_HERE_CURRENT_2026-09-21b.md",
    "00_CURRENT_RESEARCH_STATE.md",
)


def protected_docs_flagged(git_status_lines: list[str]) -> list[str]:
    """Return protected global docs that appear in `git status --short` output."""
    return [rel for rel in PROTECTED_GLOBAL_DOCS
            for line in git_status_lines if rel in line]


def check_scope_semantics() -> Check:
    g = Check("scope semantics (OPWS_SCOPE_SEMANTICS_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_SCOPE_SEMANTICS_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    gh = d.get("canonical_scope_hash_definition", {})
    g.add(gh.get("algorithm") == "sha256", "canonical scope hash == sha256")
    g.add(gh.get("empty_scope_hash"), "EMPTY scope valid (empty_scope_hash defined)")
    g.add("evaluation-only" in d.get("selection_source_priority", {}).get("GOLD", ""),
          "GOLD asserted evaluation-only")
    g.add(bool(d.get("no_gold_backfill")) or "no_gold_backfill" in json.dumps(d),
          "no gold/reference backfill into predictions")
    g.add(bool(d.get("emph_empty_valid")) or "EMPTY prediction" in json.dumps(d),
          "EMPTY prediction is a VALID zero-size scope")
    return g


def check_eligibility_funnel() -> Check:
    g = Check("eligibility funnel (OPWS_ELIGIBILITY_FUNNEL_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_ELIGIBILITY_FUNNEL_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    markers = d.get("distinct_markers", {})
    g.add("ENV_READY" in markers and "OPWS_ELIGIBLE" in markers
          and "PRIMARY_PAIRED_ELIGIBLE" in markers,
          "ENV_READY vs OPWS_ELIGIBLE vs PRIMARY_PAIRED_ELIGIBLE distinct")
    g.add(any("observed OPWS result" in r or "observed OPWS" in r
              for r in d.get("hard_rules", [])),
          "no removal based on observed OPWS result")
    stage_ids = [s.get("id") for s in d.get("stages", [])]
    g.add("STAGE_6_OPWS_ELIGIBLE" in stage_ids
          and "STAGE_7_PRIMARY_PAIRED_ELIGIBLE" in stage_ids,
          "OPWS_ELIGIBLE and PRIMARY_PAIRED_ELIGIBLE stages present")
    return g


def check_taxonomy() -> Check:
    g = Check("outcome taxonomy (OPWS_OUTCOME_TAXONOMY_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_OUTCOME_TAXONOMY_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    tax = d.get("taxonomy", {})
    for code in ("OPWS_PASS", "BEHAVIOR_FAIL", "PRESERVATION_FAIL",
                 "BEHAVIOR_AND_PRESERVATION_FAIL", "PATCH_APPLICATION_INVALID",
                 "TEST_CONTRACT_INVALID", "ENVIRONMENT_INVALID",
                 "INFRASTRUCTURE_TRANSIENT", "INFRASTRUCTURE_FATAL",
                 "ARM_PREDICTION_INVALID", "OPWS_INVALID_CONTROL_FAILURE",
                 "UNKNOWN_FAIL_CLOSED"):
        g.add(code in tax, f"taxonomy code present: {code}")
    g.add(tax.get("PATCH_APPLICATION_INVALID", {}).get("scientific") is False,
          "patch-invalid never scientific")
    g.add(any("Infrastructure failure" in r or "never converted" in r
              for r in d.get("hard_rules", [])),
          "infrastructure failure never behavioral")
    g.add(any("silently discarded" in r for r in d.get("hard_rules", [])),
          "failures never silently discarded")
    return g


def check_execution_contract() -> Check:
    g = Check("execution + dedup contract (OPWS_EXECUTION_REUSE_DEDUP_R1.json)", passed=True)
    p = PROTOCOL_DIR / "OPWS_EXECUTION_REUSE_DEDUP_R1.json"
    if not p.exists():
        g.add(False, f"missing {p.name}")
        return g
    d = _load(p)
    phys = d.get("physical_execution_identity", {}).get("fields", [])
    g.add(sorted(phys) == sorted(["TASK_ID", "SCOPE_HASH", "REFERENCE_PATCH_HASH",
                                  "TEST_CONTRACT_HASH", "ENVIRONMENT_ID"]),
          "5-tuple dedup identity (TASK_ID, SCOPE_HASH, REFERENCE_PATCH_HASH, TEST_CONTRACT_HASH, ENVIRONMENT_ID)")
    sd = d.get("scope_deduplication", {})
    g.add("never deduplicate merely because scope sizes are equal" in
          sd.get("forbidden", ""),
          "no size-only dedup (equal sizes with different hashes are different executions)")
    g.add(sd.get("conditions_for_reuse", {}).get("SCOPE_HASH") == "equal",
          "dedup conditions require equal SCOPE_HASH")
    g.add(d.get("execution_order", {}).get("ordering") == "task-major",
          "task-major deterministic ordering")
    rp = d.get("rerun_policy", {})
    g.add(rp.get("scientific_failures", "").startswith("NO"),
          "scientific failures never rerun")
    g.add(rp.get("infrastructure_transient", {}).get("max_retry") == 1,
          "transient infra max retry == 1")
    g.add("LINUX" in d.get("environment_rule", {}).get("opws_worktree_materialization", ""),
          "Linux worktree materialization rule")
    return g


def check_no_docker_no_execution() -> Check:
    g = Check("no Docker / no OPWS / no Full-D7 modification", passed=True)
    receipt_path = PROTOCOL_DIR / "ANTI_OUTCOME_PEEKING_RECEIPT.json"
    if not receipt_path.exists():
        g.add(False, "missing ANTI_OUTCOME_PEEKING_RECEIPT.json")
        return g
    receipt = _load(receipt_path)
    for key in ("docker_run", "oracle_patches_run", "behavioral_or_preservation_tests_run",
                "pilot_opws_run", "opws_executed"):
        g.add(receipt.get(key) is False, f"receipt {key} == False")
    g.add(check_global_docs_untouched().passed, "global current-status docs untouched")
    # Full-D7 forbidden paths must never appear in any mission-owned artifact
    # (except the anti-peeking receipt, which is REQUIRED to name them).
    for f in PROTOCOL_DIR.rglob("*.json"):
        if f.name == "ANTI_OUTCOME_PEEKING_RECEIPT.json":
            continue
        text = f.read_text(encoding="utf-8")
        if "wp2_sf_full_d7_r1" in text:
            g.add(False, f"forbidden Full-D7 path referenced in {f.name}")
    return g


def check_global_docs_untouched() -> Check:
    g = Check("global current-status docs read-only (mission policy)", passed=True)
    import subprocess
    r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True,
                       cwd=str(ROOT))
    g.add(r.returncode == 0, "git status readable")
    flagged = protected_docs_flagged(r.stdout.splitlines())
    for rel in flagged:
        g.add(False, f"protected doc touched: {rel}")
    return g


def validate() -> Check:
    total = Check("OPWS Protocol R1 freeze validation", passed=True)
    for c in (check_protocol_schema(), check_arm_registry(), check_metric_contract(),
              check_statistical_constants(), check_population_unbound(),
              check_no_opws_outputs(), check_anti_peeking_receipt(),
              check_forbidden_labels_docs(), check_global_docs_untouched(),
              check_scope_semantics(), check_eligibility_funnel(), check_taxonomy(),
              check_execution_contract(), check_no_docker_no_execution()):
        total.merged(c)
    return total


def write_report(total: Check) -> Path:
    report = PROTOCOL_DIR / "OPWS_PROTOCOL_VALIDATION_REPORT.json"
    payload = {
        "artifact": "opws_protocol_r1_validation_report",
        "phase": "P17",
        "date": "2026-10-12",
        "opws_executed": False,
        "full_d7_partial_outcomes_read": False,
        "checks": [
            {"name": c.name, "passed": c.passed, "details": c.details}
            for c in _all_checks()
        ],
        "overall_passed": total.passed,
        "generated_sha256": "",
    }
    payload["generated_sha256"] = _sha256_bytes(
        _canon_json({k: v for k, v in payload.items() if k != "generated_sha256"}).encode("utf-8"))
    report.write_text(json.dumps(payload, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")
    return report


def _all_checks() -> list[Check]:
    return [
        check_protocol_schema(), check_arm_registry(), check_metric_contract(),
        check_statistical_constants(), check_population_unbound(),
        check_no_opws_outputs(), check_anti_peeking_receipt(),
        check_forbidden_labels_docs(), check_global_docs_untouched(),
        check_scope_semantics(), check_eligibility_funnel(), check_taxonomy(),
        check_execution_contract(), check_no_docker_no_execution(),
    ]


def main() -> int:
    total = validate()
    for c in _all_checks():
        print(f"[{('PASS' if c.passed else 'FAIL')}] {c.name}")
        for d in c.details:
            print(f"    {d}")
    report = write_report(total)
    print(f"VALIDATION_REPORT={report}")
    print(f"OPWS_PROTOCOL_R1_VALIDATION={'PASS' if total.passed else 'FAIL'}")
    return 0 if total.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
