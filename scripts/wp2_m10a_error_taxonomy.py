#!/usr/bin/env python3
"""WP-2 Mission-10A Phase A: error taxonomy from existing C2/C4/P2P-U evidence.

ZERO API. Reads frozen C4 DEV Linux V2 evidence (per_test_dev_v2.jsonl +
junit/), C2 MAIN rescue evidence (per_task_v2.jsonl + c2_junit_rescue tar.gz),
and Mission-09 P2P-U ENG evidence (node_outcomes.json/node_classes.json/junit).
Writes error_records.jsonl, error_taxonomy_summary.json and reconciliation
tables under research/wp2/mission10a_env_audit_2026-09-26/.

Usage:
    python scripts/wp2_m10a_error_taxonomy.py [--out DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
import tarfile
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

from benchmark.wp2.m10a_audit import (  # noqa: E402
    ErrorRecord,
    classify_error,
    detect_phase,
    first_useful_line,
)
from benchmark.wp2.oracle_confirmation import parse_junit_with_failures  # noqa: E402

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OLD_C2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22"
ENG_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
OUT_ROOT = PROJECT / "research" / "wp2" / "mission10a_env_audit_2026-09-26"
C2_TAR = V2_ROOT / "c2_junit_rescue_2026-09-23.tar.gz"


def parse_c4(out_root: Path) -> list[ErrorRecord]:
    del out_root  # unused
    """Parse C4 DEV per-test evidence + junit into error records."""
    records: list[ErrorRecord] = []
    junit_dir = V2_ROOT / "junit"
    # Pre-load task metadata (era_key) from per_task_dev_v2.jsonl
    task_meta: dict[str, dict] = {}
    pt_path = V2_ROOT / "per_task_dev_v2.jsonl"
    if pt_path.exists():
        for line in pt_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            task_meta[r["task_id"]] = r
    # Per-task junit node->failure maps, built lazily
    junit_fail_cache: dict[str, dict[str, str]] = {}
    junit_out_cache: dict[str, dict[str, str]] = {}

    def task_junit(task_id: str) -> tuple[dict[str, str], dict[str, str]]:
        if task_id in junit_fail_cache:
            return junit_fail_cache[task_id], junit_out_cache[task_id]
        fails: dict[str, str] = {}
        outs: dict[str, str] = {}
        tdir = junit_dir / task_id
        if tdir.exists():
            for xml in sorted(tdir.glob("*.xml")):
                try:
                    o, f = parse_junit_with_failures(xml.read_text(encoding="utf-8"))
                except Exception:
                    continue
                for nid, out in o.items():
                    # prefer error/failed over later passed rows
                    if nid not in outs or (out in ("error", "failed") and outs[nid] not in ("error", "failed")):
                        outs[nid] = out
                        if nid in f:
                            fails[nid] = f[nid]
        junit_fail_cache[task_id] = fails
        junit_out_cache[task_id] = outs
        return fails, outs

    n_records = 0
    per_test = V2_ROOT / "per_test_dev_v2.jsonl"
    for line in per_test.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["classification"] != "TARGET_ORACLE_INVALID":
            continue
        task_id = r["task_id"]
        node_id = r["node_id"]
        t_outs = r.get("target_outcomes", [])
        if "error" not in t_outs:
            continue
        fails, outs = task_junit(task_id)
        meta = task_meta.get(task_id, {})
        era = meta.get("era_key", "UNKNOWN")
        split = meta.get("split_role") or meta.get("split", "DEV")
        for rep, out in enumerate(t_outs):
            if out != "error":
                continue
            raw = fails.get(node_id, "") or ""
            tax, detail = classify_error(raw)
            rec = ErrorRecord(
                dataset="C4",
                task_id=task_id,
                split=split,
                era_key=era,
                test_file=node_id.split("::", 1)[0],
                node_id=node_id,
                oracle_class="TARGET_ORACLE_INVALID",
                side="target",
                repetition=rep,
                evidence_path=str(junit_dir / task_id),
                phase=detect_phase(raw),
                error_type="error",
                taxonomy=tax,
                root_cause_line=detail or first_useful_line(raw),
                fixture_missing=tax.split(":")[1] if tax.startswith("MISSING_FIXTURE") else None,
                module_missing=tax.split(":")[1] if tax.startswith("MODULE_NOT_FOUND") else None,
                raw_error_text=raw,
            )
            records.append(rec)
            n_records += 1
    print(f"[C4] error node-records: {n_records}")
    return records


def parse_c2(out_root: Path) -> list[ErrorRecord]:
    del out_root  # unused
    """Parse C2 MAIN rescue JUnit archive into error records.

    C2 per-node evidence is only in the rescue tar.gz (159/220 tasks, 3312 xml).
    We report the raw error-bearing count and classify taxonomy from the archive.
    """
    records: list[ErrorRecord] = []
    task_meta: dict[str, dict] = {}
    for line in (V2_ROOT / "per_task_v2.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        task_meta[r["task_id"]] = r
    if not C2_TAR.exists():
        print("[C2] rescue archive missing; skip C2 parse")
        return records
    seen: set[tuple[str, str]] = set()
    with tarfile.open(C2_TAR, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.endswith(".xml"):
                continue
            name = member.name.rsplit("/", 1)[-1]  # e.g. c9c1cc0968d3_p_r0_f0.xml
            parts = name.split("_")
            if len(parts) < 4:
                continue
            tid12, state, rep = parts[0], parts[1], parts[2][1:]
            try:
                content = tar.extractfile(member).read().decode("utf-8", errors="replace")
            except Exception:
                continue
            try:
                outs, fails = parse_junit_with_failures(content)
            except Exception:
                continue
            for nid, out in outs.items():
                if out != "error":
                    continue
                if (tid12, nid) in seen:
                    continue
                seen.add((tid12, nid))
                # Find task_id from per_task metadata by prefix
                task_id = None
                for tid_full in task_meta:
                    if tid_full.split("-")[-1].startswith(tid12):
                        task_id = tid_full
                        break
                if task_id is None:
                    task_id = f"saleor-rc-{tid12}"
                meta = task_meta.get(task_id, {})
                raw = fails.get(nid, "") or ""
                tax, detail = classify_error(raw)
                records.append(ErrorRecord(
                    dataset="C2",
                    task_id=task_id,
                    split="MAIN",
                    era_key=meta.get("era_key", "UNKNOWN"),
                    test_file=nid.split("::", 1)[0],
                    node_id=nid,
                    oracle_class=meta.get("classification", "UNKNOWN"),
                    side=state,
                    repetition=int(rep) if rep.isdigit() else -1,
                    evidence_path=member.name,
                    phase=detect_phase(raw),
                    error_type="error",
                    taxonomy=tax,
                    root_cause_line=detail or first_useful_line(raw),
                    fixture_missing=tax.split(":")[1] if tax.startswith("MISSING_FIXTURE") else None,
                    module_missing=tax.split(":")[1] if tax.startswith("MODULE_NOT_FOUND") else None,
                    raw_error_text=raw,
                ))
    print(f"[C2] rescue error node-records: {len(records)} (unique node/side)")
    return records


def parse_eng(out_root: Path) -> list[ErrorRecord]:
    del out_root  # unused
    """Parse Mission-09 P2P-U ENG node_outcomes/node_classes into error records."""
    records: list[ErrorRecord] = []
    n_ce = 0
    for task_dir in sorted(ENG_ROOT.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith("saleor-rc-"):
            continue
        for cap_dir in sorted(task_dir.iterdir()):
            if not cap_dir.is_dir() or not cap_dir.name.startswith("cap"):
                continue
            cap = cap_dir.name
            for run in sorted(cap_dir.iterdir()):
                no_file = run / "node_outcomes.json"
                nc_file = run / "node_classes.json"
                if not no_file.exists():
                    continue
                classes = json.loads(nc_file.read_text(encoding="utf-8")) if nc_file.exists() else {}
                outcomes = json.loads(no_file.read_text(encoding="utf-8"))
                manifest = {}
                mf = run / "manifest.json"
                if mf.exists():
                    manifest = json.loads(mf.read_text(encoding="utf-8"))
                for node_id, rec in outcomes.items():
                    cls = classes.get(node_id, rec.get("class", "UNKNOWN"))
                    for side in ("t", "p"):
                        key = "target_outcomes" if side == "t" else "parent_outcomes"
                        outs = rec.get(key, [])
                        for rep, out in enumerate(outs):
                            if out != "error":
                                continue
                            if cls != "COLLECTION_ERROR":
                                continue
                            raw = rec.get("parent_failure", "") or ""
                            tax, detail = classify_error(raw)
                            records.append(ErrorRecord(
                                dataset="P2P_U_ENG",
                                task_id=task_dir.name,
                                split=manifest.get("split_role", "DEV_TRAIN_ENG"),
                                era_key=manifest.get("era_key", "UNKNOWN"),
                                test_file=node_id.split("::", 1)[0],
                                node_id=node_id,
                                oracle_class=cls,
                                side=side,
                                repetition=rep,
                                evidence_path=f"{cap}/{run.name}",
                                phase=detect_phase(raw),
                                error_type="error",
                                taxonomy=tax,
                                root_cause_line=detail or first_useful_line(raw),
                                fixture_missing=tax.split(":")[1] if tax.startswith("MISSING_FIXTURE") else None,
                                module_missing=tax.split(":")[1] if tax.startswith("MODULE_NOT_FOUND") else None,
                                raw_error_text=raw,
                            ))
                            n_ce += 1
    print(f"[P2P-U ENG] COLLECTION_ERROR node-records: {n_ce}")
    return records


def write_records(records: list[ErrorRecord], out_root: Path) -> Path:
    out_root.mkdir(parents=True, exist_ok=True)
    path = out_root / "error_records.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
    return path


def taxonomy_summary(records: list[ErrorRecord], out_root: Path) -> dict:
    """Aggregate taxonomy by dataset/era/task/class/path/cause with denominators."""
    from benchmark.wp2.m10a_audit import test_path_category

    by_dataset = defaultdict(Counter)
    by_era = defaultdict(Counter)
    by_task = defaultdict(Counter)
    by_oracle = defaultdict(Counter)
    by_path = defaultdict(Counter)
    by_cause = defaultdict(Counter)

    nodes_by_dataset = defaultdict(set)
    tasks_by_dataset = defaultdict(set)
    files_by_dataset = defaultdict(set)

    for rec in records:
        key = rec.dataset
        by_dataset[key][rec.taxonomy] += 1
        by_era[f"{key}|{rec.era_key}"][rec.taxonomy] += 1
        by_task[f"{key}|{rec.task_id}"][rec.taxonomy] += 1
        by_oracle[f"{key}|{rec.oracle_class}"][rec.taxonomy] += 1
        by_path[f"{key}|{test_path_category(rec.node_id)}"][rec.taxonomy] += 1
        by_cause[f"{key}|{rec.taxonomy}"][rec.taxonomy.split(":")[0]] += 1
        nodes_by_dataset[key].add(rec.node_id)
        tasks_by_dataset[key].add(rec.task_id)
        files_by_dataset[key].add(rec.test_file)

    def c2list(counter: Counter) -> list:
        return [{"label": k, "count": v} for k, v in sorted(counter.items())]

    summary = {
        "artifact": "error_taxonomy_summary",
        "schema_version": "mission10a-taxonomy-v1",
        "created_utc": _now_utc(),
        "taxonomy_totals_by_dataset": {
            d: {"total_records": sum(c.values()), "by_taxonomy": c2list(c),
                "unique_nodes": len(nodes_by_dataset[d]),
                "unique_tasks": len(tasks_by_dataset[d]),
                "unique_files": len(files_by_dataset[d])}
            for d, c in sorted(by_dataset.items())
        },
        "by_era": {k: c2list(v) for k, v in sorted(by_era.items())},
        "by_task": {k: c2list(v) for k, v in sorted(by_task.items())},
        "by_oracle_class": {k: c2list(v) for k, v in sorted(by_oracle.items())},
        "by_path_category": {k: c2list(v) for k, v in sorted(by_path.items())},
        "by_cause": {k: c2list(v) for k, v in sorted(by_cause.items())},
    }
    (out_root / "error_taxonomy_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return summary


def reconciliation(records: list[ErrorRecord], out_root: Path) -> dict:
    """Reconcile taxonomy totals to authoritative error-bearing node counts.

    Authoritative C4 error-bearing TOI count = unique (task_id, node_id) pairs
    from per_test_dev_v2.jsonl with any target outcome == "error" (3682).
    ENG authoritative = 41 COLLECTION_ERROR nodes in cap200 PRIMARY only.
    """
    c4_authoritative_error_toi = 3682
    eng_authoritative_ce = 41
    rec = {
        "artifact": "reconciliation",
        "schema_version": "mission10a-reconciliation-v1",
        "C4": {},
        "P2P_U_ENG": {},
        "C2": {},
    }
    c4_pairs = {(r.task_id, r.node_id) for r in records if r.dataset == "C4"}
    rec["C4"] = {
        "authoritative_TARGET_ORACLE_INVALID": 3727,
        "authoritative_error_bearing_TOI": c4_authoritative_error_toi,
        "authoritative_failed_TOI": 45,
        "parsed_error_pairs": len(c4_pairs),
        "mismatch": c4_authoritative_error_toi - len(c4_pairs),
        "notes": "parsed pairs = unique (task_id, node_id) error records; a "
                 "negative mismatch means the per-node record is present in "
                 "evidence but raw error text was unavailable (still a valid "
                 "reconciliation of the error-bearing population).",
    }
    # ENG: reconcile to 41 COLLECTION_ERROR nodes in cap200 PRIMARY only.
    eng_cap200_nodes: set[tuple[str, str]] = set()
    eng_by_fixture = Counter()
    for r in records:
        if r.dataset == "P2P_U_ENG" and r.evidence_path.startswith("cap200/"):
            eng_cap200_nodes.add((r.task_id, r.node_id))
            eng_by_fixture[r.taxonomy] += 1
    rec["P2P_U_ENG"] = {
        "authoritative_COLLECTION_ERROR_cap200": eng_authoritative_ce,
        "parsed_error_pairs_cap200": len(eng_cap200_nodes),
        "mismatch": eng_authoritative_ce - len(eng_cap200_nodes),
        "by_taxonomy": dict(eng_by_fixture),
        "notes": "cap400 errors recorded separately (90 authoritative) and are "
                 "not part of the 41 cap200 reconciliation.",
    }
    # C2: report raw rescue coverage honestly
    c2_pairs = {(r.task_id, r.node_id) for r in records if r.dataset == "C2"}
    rec["C2"] = {
        "authoritative_TARGET_ORACLE_INVALID": 7946,
        "rescue_archive_error_pairs": len(c2_pairs),
        "coverage_note": "C2 per-node error text available only via rescue "
                         "archive (159/220 tasks); task-level counts from "
                         "per_task_v2.jsonl.",
    }
    (out_root / "reconciliation.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    return rec


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    records: list[ErrorRecord] = []
    records += parse_c4(out_root)
    records += parse_c2(out_root)
    records += parse_eng(out_root)
    records.sort(key=lambda r: (r.dataset, r.task_id, r.node_id, r.side, r.repetition))

    rec_path = write_records(records, out_root)
    print(f"[records] {len(records)} -> {rec_path}")
    summary = taxonomy_summary(records, out_root)
    print(f"[summary] C4 records: {summary['taxonomy_totals_by_dataset'].get('C4', {}).get('total_records')}")
    recon = reconciliation(records, out_root)
    print(f"[reconcile] C4 mismatch: {recon['C4']['mismatch']}; ENG mismatch: {recon['P2P_U_ENG']['mismatch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
