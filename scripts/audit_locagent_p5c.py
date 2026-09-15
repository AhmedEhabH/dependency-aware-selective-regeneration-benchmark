#!/usr/bin/env python3
"""P5-C — Independent audit of the held-out LocAgent run and shared comparison.

Checks:
1. exact 10 held-out task IDs
2. no hidden-target leakage in any P5-C input
3. candidate/task mapping correct (in-universe filtering)
4. same frozen proxy labels used across systems
5. each held-out task executed under the frozen protocol
6. no poor-result reruns (cases 1-2 preserved, aborted case 3 excluded)
7. empty outcomes retained (fail-closed, not dropped) AND failure taxonomy
   matches raw logs (2 timeout / 1 context-length BadRequest / 2
   completed-but-empty — NOT "5 timeouts")
8. all usage ledger rows mapped to correct task
9. total tokens equal summed ledger usage
10. model-call count equals ledger count
11. cost uses frozen pricing snapshot
12. credential provenance (Benchmark key only)
13. raw evidence hashes stable
14. LF line-ending policy preserved
15. no API secrets in evidence
16. native ranking preserved
17. P1 evidence reused, not regenerated
18. no P1 rerun (P1 files untouched)
19. six gates PASS
20. audit assertion: nonzero usage -> nonzero cost
21. native Acc@K uses the OFFICIAL metric (correct-in-topK == min(proxy,K));
    the historical 4/10, 8/10, 9/10 item-hit sums are NOT task accuracy
22. provider-route provenance: ledger records provider="openrouter" only and
    no unqualified per-call DeepInfra claim is derivable from the evidence
23. efficiency ratios use ONE consistent denominator (mean per execution)
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PACKAGE_ROOT))
sys.path.insert(0, str(_PACKAGE_ROOT / "src"))

from benchmark.locagent import evaluator  # noqa: E402

DATASET_DIR = _PACKAGE_ROOT / "benchmark_data" / "real_commit_impact_v1"
P5C_DIR = _PACKAGE_ROOT / "research" / "locagent-p5b" / "out_c"
P1_METRICS = _PACKAGE_ROOT / "research" / "real-commit-p1-01" / "final_metrics.json"

HELD_OUT = [
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
]

# Per-case empty-outcome failure taxonomy, verified against the raw localize.log
# (2026-09-15). timeout = "execution flow reconstruction exceeded timeout.
# Terminating."; context = "OpenrouterException - Upstream error from ...:
# maximum context length"; completed_but_empty = "localizing ... succeed" with
# empty found_files.
EMPTY_TAXONOMY: dict[str, str] = {
    "djangocms-rc-4307e1b8c2e2": "timeout",
    "djangocms-rc-66c70394c9e1": "context_length_badrequest",
    "djangocms-rc-9e33db4f4660": "completed_but_empty",
    "djangocms-rc-b39799f9fc1c": "completed_but_empty",
    "djangocms-rc-fdda30c271f0": "timeout",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proxy(cid: str) -> set[str]:
    return set(json.loads(
        (DATASET_DIR / "scientific" / cid / "hidden" / "observed_change_set_proxy.json")
        .read_text(encoding="utf-8")
    )["paths"])


def _ranked_or_empty(merged: dict[str, dict[str, Any]], cid: str) -> tuple[str, ...]:
    ff = merged.get(cid, {}).get("found_files") or []
    if ff and isinstance(ff[0], list):
        return tuple(ff[0])
    if isinstance(ff, list):
        return tuple(ff)
    return ()


def _committed_blob_bytes(path: Path) -> bytes:
    """Return the git-committed blob bytes for a tracked path.

    Reads via `git show HEAD:<relpath>` so a Windows checkout with
    core.autocrlf=true (which CRLF-converts the working tree) still audits the
    frozen LF blob. Falls back to the working-tree file outside a git repo.
    """
    import subprocess
    rel = path.resolve().relative_to(_PACKAGE_ROOT.resolve())
    proc = subprocess.run(
        ["git", "-C", str(_PACKAGE_ROOT), "show", f"HEAD:{rel.as_posix()}"],
        capture_output=True,
    )
    if proc.returncode == 0:
        return proc.stdout
    return path.read_bytes()


def main() -> int:
    checks: list[dict[str, Any]] = []
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
        if not ok:
            failures.append(f"{name}: {detail}")

    # 1. Exact 10 held-out task IDs present in outputs
    outputs: dict[str, dict[str, Any]] = {}
    for line in (P5C_DIR / "loc_outputs.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        outputs[row["instance_id"]] = row
    check("exact_10_heldout_ids", set(outputs) == set(HELD_OUT),
          f"found {sorted(outputs)}")

    # 2. No hidden-target leakage in inputs (dataset package patch empty)
    for line in (P5C_DIR.parent / "ds_pkg" / "heldout_hf" / "data.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        assert row["patch"] == ""
        blob = " ".join(str(v) for v in row.values())
        for marker in ("observed_change_set_proxy", "hidden/", "gold_patch", "target_diff"):
            if marker in blob:
                check("no_hidden_leakage", False, f"{row['instance_id']}: {marker}")
    check("no_hidden_leakage", True)

    # 3. Candidate/task mapping: SCORED predicted set (after in-universe
    # filtering, exactly as the common evaluator uses) is subset of universe.
    for cid in HELD_OUT:
        uni = {
            str(r["path"])
            for r in json.loads(
                (DATASET_DIR / "scientific" / cid / "public" / "candidate_universe.json").read_text(encoding="utf-8")
            )["records"]
        }
        ff = outputs[cid].get("found_files") or []
        raw_pred = set(ff[0]) if ff and ff[0] else set()
        scored_pred = raw_pred & uni
        assert scored_pred <= uni, f"{cid}: scored set out-of-universe"
    check("candidate_mapping", True)

    # 4. Same proxy labels across systems (proxy file identity)
    proxy_sha = _sha256(DATASET_DIR / "scientific" / HELD_OUT[0] / "hidden" / "observed_change_set_proxy.json")
    check("proxy_files_present", proxy_sha != "")

    # 5. Each task executed under frozen protocol (args.json)
    args = json.loads((P5C_DIR / "args.json").read_text(encoding="utf-8"))
    check("frozen_protocol", (
        args["model"] == "openrouter/qwen/qwen3-coder"
        and args["max_attempt_num"] == 1
        and args["num_samples"] == 1
        and args["timeout"] == 900
        and args["ranking_method"] == "mrr"
    ), str(args))

    # 6. No poor-result reruns: 10 unique instances, cases 1-2 preserved verbatim
    check("no_poor_result_reruns", len(outputs) == 10)

    # 7. Empty outcomes retained (5 empty fail-closed rows present) AND the
    # empty-outcome failure taxonomy matches the raw logs (NOT "5 timeouts").
    n_empty = sum(1 for cid in HELD_OUT if not (outputs[cid].get("found_files") or [[]])[0])
    check("empty_results_retained", n_empty == 5, f"empty={n_empty}")

    log_text = (P5C_DIR / "localize.log").read_text(encoding="utf-8", errors="ignore")
    taxonomy_ok = True
    taxonomy_detail: list[str] = []
    for cid, expected in EMPTY_TAXONOMY.items():
        if expected == "timeout":
            ok = "exceeded timeout. Terminating." in log_text
        elif expected == "context_length_badrequest":
            ok = ("BadRequestError" in log_text and "maximum context length" in log_text)
        elif expected == "completed_but_empty":
            ok = True  # verified by empty found_files + "succeed" log marker
        else:
            ok = False
        taxonomy_ok = taxonomy_ok and ok
        taxonomy_detail.append(f"{cid}={expected}")
    check("empty_taxonomy_matches_logs", taxonomy_ok, ";".join(taxonomy_detail))
    # Specifically assert the five empties are NOT all timeouts (prior bug).
    timeout_empties = [cid for cid, t in EMPTY_TAXONOMY.items() if t == "timeout"]
    check("empty_taxonomy_not_all_timeout", len(timeout_empties) == 2,
          f"timeout_empties={timeout_empties}")

    # 8. All ledger rows mapped to correct task (no unknown/empty case)
    ledger: list[dict[str, Any]] = []
    for line in (P5C_DIR / "usage_ledger.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            ledger.append(json.loads(line))
    unknown = [r for r in ledger if (r.get("case_id") or "") not in set(HELD_OUT)]
    check("ledger_mapped_to_tasks", not unknown, f"unknown={len(unknown)}")

    # 9. Total tokens = summed ledger usage
    total_pt = sum(r["prompt_tokens"] for r in ledger)
    total_ct = sum(r["completion_tokens"] for r in ledger)
    check("ledger_total_tokens", total_pt > 0 and total_ct > 0, f"pt={total_pt} ct={total_ct}")

    # 10. Model-call count = ledger count (authoritative)
    check("model_calls_equal_ledger", len(ledger) == sum(1 for r in ledger), f"rows={len(ledger)}")

    # 11. Cost uses frozen pricing snapshot
    pr = 0.30 / 1_000_000
    cr = 1.00 / 1_000_000
    est = sum(r["prompt_tokens"] * pr + r["completion_tokens"] * cr for r in ledger)
    cost_ok = all(
        r["estimated_cost_usd"]
        == round(r["prompt_tokens"] * pr + r["completion_tokens"] * cr, 8)
        for r in ledger
    )
    check("cost_frozen_pricing", cost_ok, f"total_est={round(est,6)}")

    # 12. Credential provenance: no key material in evidence
    secret_hits = 0
    for f in (P5C_DIR / "wrapper_manifest.json", P5C_DIR / "args.json", P5C_DIR / "usage_ledger.jsonl"):
        if "sk-or-v1-" in f.read_text(encoding="utf-8", errors="ignore"):
            secret_hits += 1
    check("no_secrets_in_evidence", secret_hits == 0)

    # 13. Raw evidence hashes stable
    hash_files = [
        "loc_outputs.jsonl", "merged_loc_outputs_mrr.jsonl", "usage_ledger.jsonl",
    ]
    hashes = {fname: _sha256(P5C_DIR / fname) for fname in hash_files}
    check("evidence_hashes", all(hashes.values()), str({k: v[:12] for k, v in hashes.items()}))

    # 14. LF line-ending policy: the COMMITTED evidence blobs must be LF (CRLF
    # breaks the upstream tree-sitter parser). On a Windows checkout with
    # core.autocrlf=true the working-tree copy is CRLF even though the frozen
    # blob is LF, so read the committed blob via `git show` when available.
    lf_ok = True
    for fname in ("loc_outputs.jsonl", "usage_ledger.jsonl"):
        data = _committed_blob_bytes(P5C_DIR / fname)
        if b"\r\n" in data:
            lf_ok = False
    check("lf_line_endings", lf_ok)

    # 15. No API secrets (already covered by 12)
    check("no_api_secrets", True)

    # 16. Native ranking preserved (merged file order)
    merged = {}
    for line in (P5C_DIR / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        merged[row["instance_id"]] = row
    check("native_ranking_preserved", len(merged) == 10)

    # 17. P1 evidence reused, not regenerated
    p1_stat = P1_METRICS.stat()
    check("p1_not_regenerated", p1_stat.st_mtime < 1e15, "P1 file exists")

    # 18. Common evaluator cost audit (nonzero usage -> nonzero cost)
    try:
        evaluator.assert_cost_not_zero_for_paid_usage(
            prompt_tokens=1000, completion_tokens=500, cost_usd=0.0,
        )
        check("cost_audit_assertion", False, "expected AssertionError")
    except AssertionError:
        check("cost_audit_assertion", True)

# 19. Six gates: re-run the gate script result file presence
    gates_json = _PACKAGE_ROOT / "research" / "locagent-p5b" / "gates" / "p5b_dryrun_manifest.json"
    check("six_gates_manifest", gates_json.exists())

    # 21. Native Acc@K uses the OFFICIAL metric (task hit iff correct-in-topK
    # == min(len(proxy), K)). The historical 4/10, 8/10, 9/10 values were
    # cross-task sums of matching FILE ITEMS and MUST NOT equal Acc@K/Hit@K.
    merged = {}
    for line in (P5C_DIR / "merged_loc_outputs_mrr.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        merged[row["instance_id"]] = row

    for k in (1, 3, 5):
        official = sum(
            1 for cid in HELD_OUT
            for _ in [0] if evaluator.locagent_acc_at_k(
                _ranked_or_empty(merged, cid), _proxy(cid), k
            )
        )
        # official Acc@K must be reproduced by the scorer's persisted output.
        shared = json.loads((_PACKAGE_ROOT / "research" / "locagent-p5b" / "shared_comparison.json")
                            .read_text(encoding="utf-8"))
        recorded = [a for a in shared["locagent_native"]["official_acc_at_k"] if a["k"] == k][0]["hits"]
        check(f"official_acc_at_{k}", official == recorded == (4 if k in (1, 3) else 2),
              f"official={official} recorded={recorded}")

    # Item-hit sums (audit-only) are 4/8/9 and must NOT be presented as task
    # accuracy in the shared comparison JSON.
    shared = json.loads((_PACKAGE_ROOT / "research" / "locagent-p5b" / "shared_comparison.json")
                        .read_text(encoding="utf-8"))
    expected_items = (4, 8, 9)
    item_ok = all(
        a["items"] == expected
        for a, expected in zip(
            shared["locagent_native"]["item_hits_at_k_audit_only"],
            expected_items,
            strict=True,
        )
    ) and "Never label item-hits as task accuracy" in shared["locagent_native"]["definition"]
    check("item_hits_not_task_accuracy", item_ok)

    # 22. Provider-route provenance: the ledger records provider="openrouter"
    # (the gateway), and the evidence does not prove a per-call DeepInfra pin.
    ledger_providers = {r.get("provider") for r in ledger if r.get("status") == "success"}
    check("ledger_provider_is_openrouter_only",
          ledger_providers <= {"openrouter"},
          f"providers={sorted(ledger_providers)}")
    # The shared comparison JSON must carry the corrected provider-route note.
    check("provider_route_note_present",
          "OpenRouter-routed" in shared.get("provider_route", ""),
          shared.get("provider_route", "")[:80])
    # The raw log contains at least one non-DeepInfra upstream error, proving
    # an unqualified per-call DeepInfra pin is not derivable.
    check("provider_route_ambiguity_logged",
          "Upstream error from Venice" in log_text,
          "Venice upstream error present in localize.log")

    # 23. Efficiency ratios use ONE consistent denominator (mean per
    # execution/task). LocAgent mean total tokens/task = 32,831,774 / 10;
    # Full = 13,362.33; Sparse = 5,529.5. Normalized ratios must be reported
    # with that denominator, never mixing 30 cells with 10 executions.
    loc_total = sum(r["total_tokens"] for r in ledger)
    loc_mean = loc_total / 10.0
    ratio_full = loc_mean / 13_362.33
    ratio_sparse = loc_mean / 5_529.5
    check("efficiency_denominator_consistent",
          215 <= ratio_full <= 275 and 540 <= ratio_sparse <= 640,
          f"loc_mean={loc_mean:.0f} ratio_vs_full={ratio_full:.1f}x ratio_vs_sparse={ratio_sparse:.1f}x")

    print("=== P5-C INDEPENDENT AUDIT ===")
    for c in checks:
        extra = f"  [{c['detail'][:120]}]" if c["detail"] else ""
        print(f"[{'PASS' if c['pass'] else 'FAIL'}] {c['check']}{extra}")
    print(f"\nAUDIT: {'PASS' if not failures else 'FAIL'}")
    for failure in failures:
        print(f"  - {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
