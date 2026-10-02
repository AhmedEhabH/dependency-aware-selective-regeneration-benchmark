"""Synthetic world for the M16 zero-Docker / zero-API simulation (NOT used by the real engine).

Replaces every Docker/WSL/Saleor-git effect of `RealWorld` with deterministic synthetic
behaviour driven by `world.json` (written by the simulation driver). Fault injection is
controlled by `faults.json` + a counter file so behaviour persists across engine processes.
Synthetic task ids only (`saleor-rc-sim...`): no real MAIN task, gold set or selection is used.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from benchmark.wp2.oracle_semantics_v2 import classify_node_v2, task_eligibility_v2

SIM = Path(os.environ["M16_SIM_DIR"])


def _load(name: str) -> dict:
    p = SIM / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _bump(key: str) -> int:
    p = SIM / "counters.json"
    c = _load("counters.json")
    c[key] = c.get(key, 0) + 1
    p.write_text(json.dumps(c), encoding="utf-8")
    return c[key]


def _h(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


class FakeWorld:
    def __init__(self) -> None:
        self.w = _load("world.json")
        self.f = _load("faults.json")
        self.c_free = float(_load("disk.json").get("c_free_gib", 60.0))

    # ---------------------------------------------------------------- R2
    def target_manifests(self, target: str) -> dict:
        return {"pyproject.toml": "[tool.poetry.dev-dependencies]\npytest-mock='1'\n\n[x]\n", "poetry.lock": "L" + target[:6]}

    def closure(self, task_id: str, adapted: bool) -> dict:
        if task_id in self.w["dev_ids"]:
            return {"mechanism": "poetry", "pins": ["pytest-mock==1"], "unsupported": [], "era_key": "py39",
                    "pins_sha256": "p", "python_version": "3.9", "note": ""}
        if not adapted or task_id in self.f.get("closure_none", []):
            return {"mechanism": "none", "pins": [], "unsupported": [], "era_key": None, "note": "task not in census"}
        return {"mechanism": "poetry", "pins": ["pytest-mock==1"], "unsupported": [], "pins_sha256": "p",
                "era_key": self.w["tasks"][task_id]["era"], "python_version": "3.9", "note": ""}

    def adapted_lookup(self, t: str) -> dict:
        if t in self.w["dev_ids"]:
            return self.frozen_lookup(t)
        r = self.w["tasks"][t]
        return {"parent": r["parent"], "target": r["target"], "era": r["era"]}

    def frozen_lookup(self, t: str) -> dict:
        return {"parent": "d" * 40, "target": "e" * 40, "era": "py39"}

    def install_mode(self, manifests: dict) -> str:
        return "LOCK_EXACT_MAIN_PLUS_DEV"

    def lock_signature(self, manifests: dict) -> str:
        return hashlib.sha256(manifests.get("poetry.lock", "").encode()).hexdigest()[:16]

    def commits_exist(self, shas: list[str]) -> dict:
        return {"windows_missing": [], "wsl_missing": []}

    # ---------------------------------------------------------------- oracle (R1 semantics)
    def oracle_task(self, task_id: str, row: dict, raw_root: Path, between=None) -> dict:
        if os.environ.get("M16_SIM_FIREWALL_PROBE"):
            open(Path.cwd() / "research/wp1a/sip_rmcss_per_task_predictions.json").read(10)
        r = self.w["tasks"][task_id]
        for st in ("t", "p"):
            if between:
                between(f"before_{st}")
            self.c_free -= self.f.get("gib_per_state", 0.001)
            (SIM / "disk.json").write_text(json.dumps({"c_free_gib": self.c_free}), encoding="utf-8")
            if between:
                between(f"after_{st}")
        n = _bump(f"oracle:{task_id}")
        limit = self.f.get("infra_attempts_by_task", {}).get(task_id, self.f.get("infra_attempts", 2))
        if task_id in self.f.get("oracle_infra_first", []) and n <= limit:
            return {"task_id": task_id, "status": "INFRA", "infra_reasons": ["t:CONTAINER_INCOMPLETE rc=125"]}
        if r["kind"] == "install_blocked":
            return {"task_id": task_id, "status": "ENV_INSTALL_BLOCKED", "infra_reasons": [], "era_key": r["era"],
                    "dev_test_closure": {"mechanism": "poetry"}, "frozen_status": "ENV_INSTALL_BLOCKED"}
        raw_root.mkdir(parents=True, exist_ok=True)
        (raw_root / "t").mkdir(exist_ok=True)
        (raw_root / "t" / "x.xml").write_text("<testsuites/>", encoding="utf-8")
        nrs, counts = [], {k: 0 for k in ("BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P", "PARENT_COLLECTION_ERROR",
                                         "FLAKY", "TARGET_ORACLE_INVALID", "P2P_ONLY", "OTHER_REVIEW_REQUIRED")}
        texts = {}
        for node in r["f2p"]:
            p_out = ["failed"] * 3
            t_out = (["passed"] * 3 if r["kind"] in ("behavioral", "behavioral_not_ready")
                     else ["passed", "failed", "passed"])
            cls = classify_node_v2(target_outcomes=t_out, parent_outcomes=p_out, parent_failure_text="AssertionError",
                                   parent_collects_node=True, shared_test_support_failed=False)
            texts[node] = "AssertionError"
            nrs.append({"node_id": node, "v3_class": cls, "target_outcomes": t_out, "parent_outcomes": p_out})
            counts[cls] += 1
        for node in r["p2ps"]:
            cls = classify_node_v2(target_outcomes=["passed"] * 3, parent_outcomes=["passed"] * 3,
                                   parent_failure_text="", parent_collects_node=True)
            nrs.append({"node_id": node, "v3_class": cls, "target_outcomes": ["passed"] * 3,
                        "parent_outcomes": ["passed"] * 3})
            counts[cls] += 1
        flags = task_eligibility_v2(n_behavioral_f2p=counts["BEHAVIORAL_F2P"],
                                    n_symbol_absence_f2p=counts["SYMBOL_ABSENCE_F2P"],
                                    n_parent_collection_error=counts["PARENT_COLLECTION_ERROR"],
                                    environment_valid=True, task_collection_failure=False)
        return {"task_id": task_id, "status": "DONE", "rule_id": "M16_R1_REPETITION_RETENTION_V1",
                "era_key": r["era"], "infra_reasons": [], "counts": counts, "eligibility": flags,
                "classification": "BEHAVIORAL_F2P" if flags["PRIMARY_BEHAVIORAL_F2P_ELIGIBLE"] else "NOT_PRIMARY",
                "node_records": nrs, "parent_failure_text": texts, "n_nodes": len(nrs),
                "dev_test_closure": {"mechanism": "poetry"}, "install_mode": "LOCK_EXACT_MAIN_PLUS_DEV"}

    def snapshot(self, label: str, heavy: bool = True) -> dict:
        d = _load("disk.json")
        free = float(d.get("c_free_gib", self.c_free))
        return {"label": label, "c_free_gib": free,
                "vhdx": {"path": "sim.vhdx", "size_bytes": None,
                         "allocated_bytes": int((100.0 - free) * 1024 ** 3)},
                "uv_cache_bytes": 21 * 10 ** 9 if heavy else None}

    def leftovers(self, tid: str) -> dict:
        return {"worktrees": 0, "containers": 0, "databases": 0}

    # ---------------------------------------------------------------- evaluator sets
    def p2pu_unit(self, task_id: str) -> tuple[dict, dict]:
        r = self.w["tasks"][task_id]
        n = _bump(f"p2pu:{task_id}")
        if task_id in self.f.get("p2pu_infra_always", []):
            return {"rediscovery_sha256": "x"}, {"status": "ENV_FAIL_P2PU"}
        if task_id in self.f.get("p2pu_infra_first", []) and n == 1:
            return {"rediscovery_sha256": "x"}, {"status": "ENV_FAIL_P2PU"}
        classes = {u: "STABLE_P2P" for u in r["p2pu"]}
        status = "DONE" if classes else "UNDEFINED"
        return ({"rediscovery_sha256": "r" + task_id[-6:], "v3_selection": {"composition_cap200": {"proximal": 1}}},
                {"status": status, "node_classes": classes, "evidence_sha256": "u" + task_id[-6:],
                 "class_counts": {"STABLE_P2P": len(classes)}, "n_selected": len(classes)})

    def p2pu_discard(self, task_id: str) -> None:
        return None

    # ---------------------------------------------------------------- scopes / evaluation
    def gold_raw(self, t: str) -> list[str]:
        return sorted(self.w["tasks"][t]["gold"])

    def gold_scope(self, t: str) -> tuple[list[str], dict]:
        g = self.gold_raw(t)
        return g, self.editable(t, g)

    def editable(self, t: str, raw: list[str]) -> dict:
        repo = set(self.w["tasks"][t]["repo_files"])
        large = set(self.w["tasks"][t].get("large", []))
        ed = sorted(p for p in raw if p in repo and p not in large and "/tests/" not in p)
        return {"editable": ed, "excluded_large": sorted(p for p in raw if p in large), "excluded_budget": [],
                "raw": sorted(raw)}

    def scoped_gold_diff(self, t: str, files: list[str]) -> str:
        return "".join(f"diff --git a/{f} b/{f}\n--- a/{f}\n+++ b/{f}\n@@ -1 +1 @@\n-a\n+b\n" for f in files)

    def evaluate(self, t: str, label: str, diff: str, *, e1: bool, diag, parent_starts_ok: bool):
        r = self.w["tasks"][t]
        if label.startswith("u_"):
            n = _bump(f"eval:{t}:{label}")
            if t in self.f.get("opws_infra_always", []):
                raise RuntimeError("synthetic evaluation container did not finish")
            if t in self.f.get("opws_infra_first", []) and n == 1:
                raise RuntimeError("synthetic evaluation container did not finish")
        files = {ln.split()[2][2:] for ln in diff.splitlines() if ln.startswith("diff --git ")}
        essential = set(r["essential"])
        f2p_pass = bool(diff.strip()) and essential <= files
        if label == "rpos" and r["kind"] == "behavioral_not_ready":
            f2p_pass = False
        breaks = bool(files) and bool(set(r.get("breaks_if_partial", [])) & files) and not set(r["gold"]) <= files
        groups = {"C": {}, "U": {}}
        for n in r["f2p"]:
            groups["C"][n] = ["passed"] * 3 if f2p_pass else ["failed"] * 3
        for n in r["p2ps"]:
            groups["C"][n] = ["failed"] * 3 if breaks else ["passed"] * 3
        for n in r["p2pu"]:
            groups["U"][n] = ["passed"] * 3
        e1d = "ALL_JUNIT_PRESENT"
        if e1 and t in self.f.get("e1a1_tasks", []) and label.startswith("u_") and not f2p_pass:
            e1d = "PATCH_STARTUP_FAILURE_E1A1"
            groups = {g: {n: ["missing"] * 3 for n in v} for g, v in groups.items()}
        return groups, "tree" + hashlib.sha256((t + diff).encode()).hexdigest()[:12], e1d
