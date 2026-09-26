#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1: full-text root-cause audit (ZERO API).

Re-parses FULL <error>/<failure> text from:
- C4 DEV Linux V2 JUnit (research/wp2/oracle_confirmation_linux_v2_2026-09-23/junit);
- C2 MAIN rescue archive (c2_junit_rescue_2026-09-23.tar.gz);
- Mission-09 P2P-U ENG (research/wp2/p2p_u_v2_eng_2026-09-25).

Fixes the Mission-10A truncation limitation ([:1200]/[:4000]) and the
merged-repetition node->text map. Produces per-(node, rep) full-text records,
node-level causal attribution (STABLE_CAUSE / MIXED_CAUSE / MISSING_EVIDENCE),
reconciliation tables, and verification of the independent-review hypotheses.

Usage:
    python scripts/wp2_m10b_phase1_audit.py [--out DIR]
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

from benchmark.wp2.m10b_fulltext import (  # noqa: E402
    RepEvidence,
    attribute_node_target_reps,
    cause_family,
    classify_error_v3,
    final_exception_line,
    merge_rep_junit,
    reconcile_counts,
    sha256_text,
)

V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
ENG_ROOT = PROJECT / "research" / "wp2" / "p2p_u_v2_eng_2026-09-25"
OLD_C2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22"
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
C2_TAR = V2_ROOT / "c2_junit_rescue_2026-09-23.tar.gz"

AUTH_C4_TOI = 3727
AUTH_C4_ERROR = 3682
AUTH_C4_FAILED = 45
AUTH_P2PU_CAP200_CE = 41


def _now_utc() -> str:
    import datetime

    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# C4
# ---------------------------------------------------------------------------
def parse_c4(out_root: Path) -> dict:
    junit_dir = V2_ROOT / "junit"
    task_meta: dict[str, dict] = {}
    pt_path = V2_ROOT / "per_task_dev_v2.jsonl"
    if pt_path.exists():
        for line in pt_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            task_meta[r["task_id"]] = r

    split_meta: dict[str, str] = {}
    ds_path = V2_ROOT / "dev_split_v2_2026-09-23.json"
    if ds_path.exists():
        ds = json.loads(ds_path.read_text(encoding="utf-8"))
        for role, ids in ds.get("membership", {}).items():
            for tid in ids:
                split_meta[tid] = role

    # Group junit files per (task, side, rep) using filename shape.
    rep_groups: dict[tuple[str, str, int], list[tuple[str, str]]] = defaultdict(list)
    import re

    name_re = re.compile(r"^([a-f0-9]{12})_([pt])_r(\d+)_f(\d+)\.xml$")
    for task_dir in sorted(junit_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        for f in task_dir.glob("*.xml"):
            m = name_re.match(f.name)
            if not m:
                continue
            t12, side, rep = m.group(1), m.group(2), int(m.group(3))
            rep_groups[(t12, side, rep)].append((f.name, f.read_text(encoding="utf-8")))

    per_rep_cache: dict[tuple[str, str, int], dict[str, RepEvidence]] = {}

    def get_rep(t12: str, side: str, rep: int) -> dict[str, RepEvidence]:
        key = (t12, side, rep)
        if key in per_rep_cache:
            return per_rep_cache[key]
        files = rep_groups.get(key, [])
        merged = merge_rep_junit(task_id=f"saleor-rc-{t12}", side=side,
                                 repetition=rep, xml_files=files)
        per_rep_cache[key] = merged
        return merged

    fulltext_records: list[dict] = []
    attribution: dict[str, dict] = {}
    by_family = Counter()
    by_era = Counter()
    by_task = Counter()

    def node_key(task_id: str, node_id: str) -> str:
        return f"{task_id}::{node_id}"

    n_err_records = 0
    n_failed_nodes = 0
    per_test = V2_ROOT / "per_test_dev_v2.jsonl"
    for line in per_test.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["classification"] != "TARGET_ORACLE_INVALID":
            continue
        task_id = r["task_id"]
        node_id = r["node_id"]
        t_outs = r.get("target_outcomes", [])
        t12 = task_id.split("-")[-1]
        meta = task_meta.get(task_id, {})
        era = meta.get("era_key", "UNKNOWN")
        split = split_meta.get(task_id, "DEV_TRAIN")

        rep_evidences: list[RepEvidence | None] = [None, None, None]
        for rep, out in enumerate(t_outs):
            if out not in ("error", "failure"):
                continue
            merged = get_rep(t12, "t", rep)
            ev = merged.get(node_id)
            rep_evidences[rep] = ev
            if ev is not None and ev.full_text:
                tax, detail = classify_error_v3(ev.full_text, ev.message)
                fulltext_records.append({
                    "dataset": "C4",
                    "task_id": task_id,
                    "split": split,
                    "era_key": era,
                    "node_id": node_id,
                    "side": "target",
                    "repetition": rep,
                    "file": ev.evidence_path,
                    "phase": ev.phase,
                    "outcome": ev.outcome,
                    "message": ev.message[:500],
                    "final_exception": final_exception_line(ev.full_text, ev.message),
                    "taxonomy": tax,
                    "detail": detail,
                    "family": cause_family(tax),
                    "full_text_sha256": sha256_text(ev.full_text),
                    "full_text_len": len(ev.full_text),
                })
                n_err_records += 1
        # failed-only detection: all 3 target reps are 'failed'
        is_failed_only = bool(t_outs) and all(o == "failed" for o in t_outs)
        if is_failed_only:
            n_failed_nodes += 1
        attr = attribute_node_target_reps(rep_evidences)
        if is_failed_only:
            attr["stability"] = "FAILED_ONLY"
            attr["materiality"] = False
        attribution[node_key(task_id, node_id)] = {
            "task_id": task_id,
            "split": split,
            "era_key": era,
            "node_id": node_id,
            "target_outcomes": t_outs,
            "stability": attr["stability"],
            "stable_family": attr.get("stable_family"),
            "majority_families": attr.get("majority_families", []),
            "materiality": attr["materiality"],
            "per_rep": attr["per_rep"],
        }
        by_family[attr["stability"]] += 1
        by_era[f"{era}|{attr['stability']}"] += 1
        by_task[f"{task_id}|{attr['stability']}"] += 1
        if attr["materiality"]:
            pass

    recon = reconcile_counts(
        authoritative_total=AUTH_C4_TOI,
        authoritative_error=AUTH_C4_ERROR,
        authoritative_failed=AUTH_C4_FAILED,
        attributed=attribution,
    )
    recon["FAILED_ONLY_nodes"] = n_failed_nodes

    # materiality numerator (14.3): stable-cause nodes in materiality families
    materiality_nodes = [n for n, a in attribution.items() if a["materiality"]]
    num_fams = Counter(a["stable_family"] for n, a in attribution.items() if a["materiality"])
    n_missing_evidence = sum(1 for a in attribution.values() if a["stability"] == "MISSING_EVIDENCE")
    n_mixed = sum(1 for a in attribution.values() if a["stability"] == "MIXED_CAUSE")
    # denominator = error-bearing nodes with sufficient full evidence (14.3)
    denominator_sufficient = AUTH_C4_ERROR - n_missing_evidence
    numerator = len(materiality_nodes)

    # secondary >=2/3 majority-cause table (descriptive only, never the gate)
    majority_table: dict[str, int] = {}
    for a in attribution.values():
        fams = [p["family"] for p in a["per_rep"] if p is not None]
        for f in sorted(set(fams)):
            if fams.count(f) >= 2:
                majority_table[f] = majority_table.get(f, 0) + 1

    result = {
        "artifact": "m10b_phase1_c4_fulltext",
        "created_utc": _now_utc(),
        "authoritative": {"TOI": AUTH_C4_TOI, "error": AUTH_C4_ERROR, "failed_only": AUTH_C4_FAILED},
        "n_fulltext_records": n_err_records,
        "node_attribution": attribution,
        "reconciliation": recon,
        "materiality": {
            "numerator_stable_family_nodes": numerator,
            "by_family": dict(num_fams),
            "denominator_error_bearing": AUTH_C4_ERROR,
            "denominator_sufficient_evidence": denominator_sufficient,
            "share_of_error_bearing": round(numerator / AUTH_C4_ERROR, 4) if AUTH_C4_ERROR else None,
            "share_of_sufficient_evidence": round(
                numerator / denominator_sufficient, 4) if denominator_sufficient else None,
            "missing_evidence_count": n_missing_evidence,
            "mixed_cause_count": n_mixed,
        },
        "secondary_majority_2of3_table": majority_table,
        "stability_counts": dict(by_family),
    }
    (out_root / "phase1_c4_node_attribution.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    with (out_root / "phase1_c4_fulltext_records.jsonl").open("w", encoding="utf-8") as fh:
        for rec in fulltext_records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[C4] fulltext records: {n_err_records}; attribution nodes: {len(attribution)}")
    print(f"[C4] stability: {dict(by_family)}; reconciliation ok={recon['ok']} mismatch={recon['mismatch']}")
    return result


# ---------------------------------------------------------------------------
# C2 rescue
# ---------------------------------------------------------------------------
def parse_c2(out_root: Path) -> dict:
    task_meta: dict[str, dict] = {}
    pt_path = V2_ROOT / "per_task_v2.jsonl"
    if pt_path.exists():
        for line in pt_path.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            task_meta[r["task_id"]] = r

    if not C2_TAR.exists():
        print("[C2] rescue archive missing; skip")
        return {"artifact": "m10b_phase1_c2_rescue", "skipped": True}

    import re
    name_re = re.compile(r"^([a-f0-9]{12})_([pt])_r(\d+)_f(\d+)\.xml$")
    rep_groups: dict[tuple[str, str, int], list[tuple[str, str]]] = defaultdict(list)
    task12_names: dict[str, str] = {}
    with tarfile.open(C2_TAR, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.endswith(".xml"):
                continue
            base = member.name.rsplit("/", 1)[-1]
            m = name_re.match(base)
            if not m:
                continue
            t12, side, rep = m.group(1), m.group(2), int(m.group(3))
            content = tar.extractfile(member).read().decode("utf-8", errors="replace")
            rep_groups[(t12, side, rep)].append((base, content))
            task12_names.setdefault(t12, f"saleor-rc-{t12}")

    per_rep_cache: dict[tuple[str, str, int], dict[str, RepEvidence]] = {}

    def get_rep(t12: str, side: str, rep: int) -> dict[str, RepEvidence]:
        key = (t12, side, rep)
        if key in per_rep_cache:
            return per_rep_cache[key]
        merged = merge_rep_junit(task_id=f"saleor-rc-{t12}", side=side,
                                 repetition=rep, xml_files=rep_groups.get(key, []))
        per_rep_cache[key] = merged
        return merged

    # Node-level: union of error-bearing nodes across target reps, scoped to
    # rescue coverage. Attribution uses the 3 TARGET reps where available.
    node_keys: dict[tuple[str, str], dict[str, list]] = defaultdict(lambda: {"meta": None, "ev": [None, None, None]})
    for (t12, side, rep), _files in rep_groups.items():
        merged = get_rep(t12, side, rep)
        for node_id, ev in merged.items():
            if ev.outcome not in ("error", "failure"):
                continue
            nk = (t12, node_id)
            if side == "t":
                node_keys[nk]["ev"][rep] = ev
                node_keys[nk]["meta"] = (task12_names[t12], rep)

    attribution: dict[str, dict] = {}
    fulltext: list[dict] = []
    by_family = Counter()

    def node_key(task_id: str, node_id: str) -> str:
        return f"{task_id}::{node_id}"

    for (t12, node_id), info in sorted(node_keys.items()):
        task_id = task12_names[t12]
        meta = task_meta.get(task_id, {})
        era = meta.get("era_key", "UNKNOWN")
        attr = attribute_node_target_reps(info["ev"])
        attribution[node_key(task_id, node_id)] = {
            "task_id": task_id,
            "split": "MAIN",
            "era_key": era,
            "node_id": node_id,
            "stability": attr["stability"],
            "stable_family": attr.get("stable_family"),
            "majority_families": attr.get("majority_families", []),
            "materiality": attr["materiality"],
            "per_rep": attr["per_rep"],
        }
        by_family[attr["stability"]] += 1
        for rep, ev in enumerate(info["ev"]):
            if ev is None or not ev.full_text:
                continue
            tax, detail = classify_error_v3(ev.full_text, ev.message)
            fulltext.append({
                "dataset": "C2",
                "task_id": task_id,
                "split": "MAIN",
                "era_key": era,
                "node_id": node_id,
                "side": "target",
                "repetition": rep,
                "file": ev.evidence_path,
                "phase": ev.phase,
                "outcome": ev.outcome,
                "message": ev.message[:500],
                "final_exception": final_exception_line(ev.full_text, ev.message),
                "taxonomy": tax,
                "detail": detail,
                "family": cause_family(tax),
                "full_text_sha256": sha256_text(ev.full_text),
                "full_text_len": len(ev.full_text),
            })

    n_emfile_tasks = len({a["task_id"] for n, a in attribution.items()
                          if a["stable_family"] == "INFRA" or "INFRA" in a["majority_families"]})
    result = {
        "artifact": "m10b_phase1_c2_rescue",
        "created_utc": _now_utc(),
        "rescue_task_coverage": len(task12_names),
        "n_rescue_tasks_with_target_error_nodes": len({v["task_id"] for v in attribution.values()}),
        "n_fulltext_records": len(fulltext),
        "node_attribution": attribution,
        "stability_counts": dict(by_family),
        "emfile_task_count": n_emfile_tasks,
        "emfile_task_ids": sorted({a["task_id"] for n, a in attribution.items()
                                   if a["stable_family"] == "INFRA"
                                   or "INFRA" in a["majority_families"]}),
        "notes": "C2 node-level attribution scoped to rescue-archive coverage only (159 tasks); "
                 "task-level authoritative denominators come from per_task_v2.jsonl.",
    }
    (out_root / "phase1_c2_rescue_attribution.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    with (out_root / "phase1_c2_fulltext_records.jsonl").open("w", encoding="utf-8") as fh:
        for rec in fulltext:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[C2] rescue tasks: {len(task12_names)}; attribution nodes: {len(attribution)}; "
          f"stability: {dict(by_family)}; emfile tasks: {n_emfile_tasks}")
    return result


# ---------------------------------------------------------------------------
# P2P-U ENG (Mission-09) - 41 cap200 COLLECTION_ERROR nodes
# ---------------------------------------------------------------------------
def parse_eng(out_root: Path) -> dict:
    records: list[dict] = []
    by_family = Counter()
    tasks_seen: set[str] = set()
    n_nodes = 0
    for task_dir in sorted(ENG_ROOT.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith("saleor-rc-"):
            continue
        cap_dir = task_dir / "cap200"
        run = cap_dir / "A"
        nc_file = run / "node_classes.json"
        jdir = run / "junit"
        if not nc_file.exists():
            continue
        classes = json.loads(nc_file.read_text(encoding="utf-8"))
        manifest = {}
        mf = run / "manifest.json"
        if mf.exists():
            manifest = json.loads(mf.read_text(encoding="utf-8"))
        ce_nodes = [nid for nid, c in classes.items() if c == "COLLECTION_ERROR"]
        # build per (side, rep) junit maps from full junit dir
        import re
        name_re = re.compile(r"^([a-f0-9]{12})_c200_([pt])_r(\d+)_c(\d+)\.xml$")
        rep_groups: dict[tuple[str, int], list[tuple[str, str]]] = defaultdict(list)
        if jdir.exists():
            for f in jdir.glob("*.xml"):
                m = name_re.match(f.name)
                if not m:
                    continue
                side, rep = m.group(2), int(m.group(3))
                rep_groups[(side, rep)].append((f.name, f.read_text(encoding="utf-8")))
        cache: dict[tuple[str, int], dict[str, RepEvidence]] = {}
        groups_local = rep_groups
        task_dir_local = task_dir

        def get_rep(side: str, rep: int, _cache: dict = cache,
                    _groups: dict = groups_local,
                    _task_dir: Path = task_dir_local) -> dict[str, RepEvidence]:
            key = (side, rep)
            if key in _cache:
                return _cache[key]
            merged = merge_rep_junit(task_id=_task_dir.name, side=side,
                                     repetition=rep, xml_files=_groups.get(key, []))
            _cache[key] = merged
            return merged

        for node_id in ce_nodes:
            n_nodes += 1
            tasks_seen.add(task_dir.name)
            rep_evs: list[RepEvidence | None] = [None, None, None]
            for rep in range(3):
                ev = get_rep("t", rep).get(node_id) or get_rep("p", rep).get(node_id)
                rep_evs[rep] = ev
            attr = attribute_node_target_reps(rep_evs)
            by_family[attr["stability"]] += 1
            records.append({
                "dataset": "P2P_U_ENG",
                "task_id": task_dir.name,
                "split": manifest.get("split_role", "DEV_TRAIN_ENG"),
                "era_key": manifest.get("era_key", "UNKNOWN"),
                "node_id": node_id,
                "cap": "cap200",
                "stability": attr["stability"],
                "stable_family": attr.get("stable_family"),
                "materiality": attr["materiality"],
                "per_rep": attr["per_rep"],
            })

    recon = {
        "authoritative_cap200_COLLECTION_ERROR": AUTH_P2PU_CAP200_CE,
        "parsed_nodes": n_nodes,
        "unique_tasks": len(tasks_seen),
        "mismatch": AUTH_P2PU_CAP200_CE - n_nodes,
        "ok": n_nodes == AUTH_P2PU_CAP200_CE,
    }
    result = {
        "artifact": "m10b_phase1_p2pu_eng",
        "created_utc": _now_utc(),
        "node_attribution": records,
        "reconciliation": recon,
        "stability_counts": dict(by_family),
    }
    (out_root / "phase1_p2pu_eng_attribution.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[P2P-U ENG] nodes: {n_nodes}; tasks: {len(tasks_seen)}; "
          f"stability: {dict(by_family)}; mismatch: {recon['mismatch']}")
    return result


# ---------------------------------------------------------------------------
# Hypothesis verification (7.5)
# ---------------------------------------------------------------------------
def hypotheses(c4: dict, c2: dict, eng: dict, out_root: Path) -> dict:
    c4_attr = c4["node_attribution"]
    c4_records = [json.loads(ln) for ln in
                  (out_root / "phase1_c4_fulltext_records.jsonl").read_text(encoding="utf-8").splitlines()]

    # task co-occurrence: any node in task has INFRA family
    emfile_tasks = {a["task_id"] for a in c4_attr.values()
                    if any((p or {}).get("family") == "INFRA" for p in a["per_rep"])}
    emfile_record_count = sum(1 for r in c4_records if r["family"] == "INFRA")
    emfile_parent_target = Counter(r["side"] for r in c4_records if r["family"] == "INFRA")
    emfile_parent_target["total"] = emfile_record_count

    # node-level stable EMFILE share
    stable_emfile_nodes = [n for n, a in c4_attr.items()
                           if a["stability"] == "STABLE_CAUSE" and a["stable_family"] == "INFRA"]
    emfile_by_era = Counter(c4_attr[n]["era_key"] for n in stable_emfile_nodes)

    # WRONG_CONSTRAINTS
    wc_records = [r for r in c4_records if r["taxonomy"].startswith("DB:WRONG_CONSTRAINTS")]
    wc_tasks = {r["task_id"] for r in wc_records}
    wc_nodes = {r["node_id"] for r in wc_records}

    # ENG affected (10 hypothesis): ENG split tasks with INFRA/DB/MISSING_FIXTURE stable
    ds = json.loads((V2_ROOT / "dev_split_v2_2026-09-23.json").read_text(encoding="utf-8"))
    eng_ids = set(ds["membership"].get("DEV_TRAIN_ENG", []))
    eng_affected_nodes = []
    for r in c4_records:
        if r["task_id"] in eng_ids and r["family"] in ("INFRA", "DB", "MISSING_FIXTURE", "MODULE_NOT_FOUND"):
            eng_affected_nodes.append(r)
    eng_affected_tasks = {r["task_id"] for r in eng_affected_nodes}
    eng_affected_by_era = Counter()
    meta_map = {}
    for ln in (V2_ROOT / "per_task_dev_v2.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(ln)
        meta_map[m["task_id"]] = m
    for t in eng_affected_tasks:
        eng_affected_by_era[meta_map.get(t, {}).get("era_key", "UNKNOWN")] += 1

    # primary-eligible status of affected ENG tasks
    primary_status = {}
    for t in eng_affected_tasks:
        m = meta_map.get(t, {})
        primary_status[t] = {
            "classification": m.get("classification"),
            "primary_eligible": (m.get("eligibility", {}) or {}).get("PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"),
            "counts": m.get("counts"),
        }

    # C2 58/159 hypothesis (from rescue full-text records)
    c2_records = [json.loads(ln) for ln in
                  (out_root / "phase1_c2_fulltext_records.jsonl").read_text(encoding="utf-8").splitlines()]
    c2_emfile_tasks = {r["task_id"] for r in c2_records if r["family"] == "INFRA"}
    c2_attr_emfile = set(c2.get("emfile_task_ids", []) or [])
    if c2_attr_emfile:
        assert c2_emfile_tasks == c2_attr_emfile, (
            f"c2 emfile task mismatch: {len(c2_emfile_tasks)} vs {len(c2_attr_emfile)}"
        )
    _ = eng  # ENG reconciled in parse_eng; hypotheses focus on C4/C2/ENG task status

    result = {
        "artifact": "m10b_phase1_hypotheses",
        "created_utc": _now_utc(),
        "C4_EMFILE": {
            "task_cooccurrence_count": len(emfile_tasks),
            "task_ids": sorted(emfile_tasks),
            "parent_target_record_counts": dict(emfile_parent_target),
            "node_level_stable_share": {
                "numerator": len(stable_emfile_nodes),
                "denominator": AUTH_C4_ERROR,
                "share": round(len(stable_emfile_nodes) / AUTH_C4_ERROR, 4),
            },
            "by_era": dict(emfile_by_era),
        },
        "C4_WRONG_CONSTRAINTS": {
            "record_count": len(wc_records),
            "unique_tasks": len(wc_tasks),
            "unique_nodes": len(wc_nodes),
            "tasks": sorted(wc_tasks),
        },
        "C2_RESCUE_EMFILE": {
            "task_count": len(c2_emfile_tasks),
            "task_ids": sorted(c2_emfile_tasks),
            "hypothesis_58_of_159": "VERIFY" if len(c2_emfile_tasks) > 0 else "PENDING",
        },
        "ENG_AFFECTED": {
            "hypothesis_10_tasks": len(eng_affected_tasks),
            "task_ids": sorted(eng_affected_tasks),
            "by_era": dict(eng_affected_by_era),
            "primary_eligible_status": primary_status,
            "record_count": len(eng_affected_nodes),
        },
    }
    (out_root / "phase1_hypotheses_verification.json").write_text(
        json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[HYP] C4 EMFILE tasks: {len(emfile_tasks)}; stable EMFILE nodes: {len(stable_emfile_nodes)}; "
          f"WRONG_CONSTRAINTS records: {len(wc_records)}; C2 EMFILE tasks: {len(c2_emfile_tasks)}; "
          f"ENG affected tasks: {len(eng_affected_tasks)}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    c4 = parse_c4(out_root)
    c2 = parse_c2(out_root)
    eng = parse_eng(out_root)
    hyp = hypotheses(c4, c2, eng, out_root)

    summary = {
        "artifact": "m10b_phase1_summary",
        "created_utc": _now_utc(),
        "c4": {
            "fulltext_records": c4["n_fulltext_records"],
            "stability_counts": c4["stability_counts"],
            "reconciliation": c4["reconciliation"],
            "materiality": c4["materiality"],
        },
        "c2": {"rescue_tasks": c2.get("rescue_task_coverage"), "stability": c2["stability_counts"]},
        "p2pu_eng": {"stability": eng["stability_counts"], "reconciliation": eng["reconciliation"]},
        "hypotheses": hyp,
    }
    (out_root / "phase1_summary.json").write_text(
        json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[summary] written to {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
