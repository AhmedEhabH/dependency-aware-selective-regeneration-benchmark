"""WP-2 P2P-U V2 extended preservation rule (Mission-09) - ZERO API.

P2P-U V2 fixes V1's coarse top-level-app scaling problem with an
outcome-blind, proximity-aware, deterministic PRE-execution selection rule.

Frozen rule (Mission-09 sections 6-10):
- Candidate pool: the FINAL corrected Mission-08 frozen DEV unchanged-test
  discovered nodes (NO rediscovery).
- Proximity(test_file) = max over KNOWN touched production files of the longest
  common leading component count after ``saleor/``.
- UNKNOWN handling: touched paths whose frozen ``top_level_app(...)`` result is
  UNKNOWN contribute NO proximity score. If ALL touched production paths for a
  task are UNKNOWN, all candidates receive proximity=0 for ranking and
  ``all_touched_paths_unknown=true`` is flagged.
- PROXIMAL pool: file proximity >= 2 (same sub-package beyond merely sharing
  the top-level Saleor app). DISTAL pool: all remaining candidates
  (proximity <= 1, including proximity=0 / UNKNOWN-derived).
- Deterministic outcome-blind ordering under the frozen salt
  ``wp2-p2p-u-v2-2026-09-25``; round-robin one node per file per round;
  interleave P,P,P,D; first_200 subset first_400 exactly.
- PRE-execution cap: Primary K=200 (target 150 PROXIMAL / 50 DISTAL),
  ENG sensitivity K=400 (target 300 PROXIMAL / 100 DISTAL); if a pool is
  insufficient, consume all of that pool and deterministically backfill from
  the other; never invent candidates.

Evaluator-only: node identities, gold touched paths, test patch, cap
memberships, proximity, proximal/distal labels stay invisible to every future
generation/repair arm (Mission-09 section 14).
"""
from __future__ import annotations

import hashlib
import json

P2P_U_V2_VERSION = "p2p-u-v2-2026-09-25"
P2P_U_V2_SAMPLE_SALT = "wp2-p2p-u-v2-2026-09-25"
P2P_U_PRIMARY_CAP = 200
P2P_U_SENSITIVITY_CAP = 400
PRIMARY_PROXIMAL_TARGET = 150
PRIMARY_DISTAL_TARGET = 50
SENSITIVITY_PROXIMAL_TARGET = 300
SENSITIVITY_DISTAL_TARGET = 100
PROXIMAL_MIN_PROXIMITY = 2
DISTAL_MAX_PROXIMITY = 1

RULE_TEXT = (
    "P2P-U V2 EXTENDED PRESERVATION (unchanged-test regression oracle). "
    "V1 remains immutable historical evidence. V2 fixes V1's coarse "
    "Saleor top-level-app scaling problem with an outcome-blind, "
    "proximity-aware, deterministic PRE-execution selection rule. "
    "CANDIDATE POOL: the FINAL corrected Mission-08 frozen DEV unchanged-test "
    "discovered nodes; no rediscovery. "
    "PROXIMITY: for each candidate test file, proximity(test_file) = max over "
    "KNOWN touched production files of the longest common leading component "
    "count after 'saleor/'. Touched paths whose frozen top_level_app result is "
    "UNKNOWN contribute NO proximity score (not silently reinterpreted); if "
    "ALL touched production paths for a task are UNKNOWN, all candidates "
    "receive proximity=0 for ranking and all_touched_paths_unknown=true is "
    "flagged. No outcome information is used in proximity computation. "
    "POOLS: PROXIMAL = candidates whose file proximity >= 2 (same sub-package "
    "beyond merely sharing the top-level Saleor app); DISTAL = all remaining "
    "candidates in the frozen V1 candidate pool (proximity <= 1, including "
    "proximity=0 / UNKNOWN-derived). This prevents the cap from being filled "
    "only with tests nearest to gold files. "
    "SALT (frozen BEFORE any V2 outcome execution, never changed afterwards): "
    f"'{P2P_U_V2_SAMPLE_SALT}'. "
    "ORDERING within PROXIMAL: (1) group files by proximity score descending; "
    "(2) within each proximity stratum order FILES by sha256(salt|file_path); "
    "(3) within each file order NODES by sha256(salt|node_id); "
    "(4) round-robin one node per file per round within the current stratum; "
    "(5) exhaust higher proximity strata before lower. "
    "ORDERING within DISTAL: (1) order FILES by sha256(salt|file_path); "
    "(2) order nodes within each file by sha256(salt|node_id); "
    "(3) round-robin one node per file per round. "
    "Do NOT alphabetically order ties as the scientific ordering rule. "
    "FINAL ORDER: interleave P,P,P,D,P,P,P,D,... exhausting one list then "
    "continuing with the other. The final candidate list must satisfy "
    "first_200 subset first_400 exactly. "
    "CAPS (pre-execution, outcome-blind; never depend on pass/fail, flaky, "
    "model/arm output, future generated patch, or observed F2P result): "
    f"PRIMARY K={P2P_U_PRIMARY_CAP} (target composition "
    f"{PRIMARY_PROXIMAL_TARGET} PROXIMAL / {PRIMARY_DISTAL_TARGET} DISTAL); "
    f"ENG SENSITIVITY K={P2P_U_SENSITIVITY_CAP} (target composition "
    f"{SENSITIVITY_PROXIMAL_TARGET} PROXIMAL / {SENSITIVITY_DISTAL_TARGET} "
    "DISTAL). If fewer than K raw candidates: take all. If one pool is "
    "insufficient: consume all of that pool, deterministically backfill from "
    "the other pool, record requested vs achieved; never invent candidates. "
    "cap200 and cap400 MUST be executed independently (no inferring cap200 "
    "outcomes from cap400). "
    "EXECUTION: PARENT = parent commit + SAME frozen test patch used by Linux "
    "V2 F2P (TEST_PATCH_APPLIED_ON_PARENT=true); TARGET = target commit; "
    "3 parent + 3 target complete repetitions, no early stopping; workers=1; "
    "prefer ONE pytest invocation per state-repetition with explicit node IDs "
    "(chunk deterministically if needed, identical chunks across "
    "states/repetitions). "
    "TAXONOMY (exactly one class per node, precedence): 1 FLAKY (either side "
    "non-stable/mixed) > 2 COLLECTION_ERROR (after excluding flaky, either "
    "side stable collection error) > 3 STABLE_P2P (parent STABLE_PASS, target "
    "STABLE_PASS) > 4 TARGET_BROKEN > 5 PARENT_BROKEN > 6 BOTH_FAIL. Only "
    "STABLE_P2P nodes become the frozen P2P-U preservation set. "
    "FIREWALL: node identities, gold touched paths, test patch, cap "
    "memberships, proximity scores, proximal/distal labels, target diff and "
    "target P2P outcomes remain invisible to every generation/repair arm; "
    "evaluator sets frozen before any generation; all future arms use the "
    "same frozen evaluator."
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_sha256(payload: dict) -> str:
    """Canonical SHA-256 over a JSON payload (sorted keys)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def path_components_after_saleor(path: str) -> list[str] | None:
    """Components after the first ``saleor/``; None when no ``saleor/`` prefix.

    Example: ``saleor/graphql/order/mutations/order_update.py`` ->
    ``["graphql", "order", "mutations", "order_update.py"]``.
    """
    parts = [p for p in path.split("/") if p]
    for idx, part in enumerate(parts):
        if part == "saleor" and idx + 1 < len(parts):
            return parts[idx + 1 :]
    return None


def longest_common_leading_count(a: list[str], b: list[str]) -> int:
    """Longest common leading component count between two component lists."""
    count = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        count += 1
    return count


def file_path_of(node_id: str) -> str:
    """File path portion of a pytest node id."""
    return node_id.split("::", 1)[0]


def is_known_touched_path(path: str) -> bool:
    """A touched production path is KNOWN iff it has a saleor/ component.

    Mirrors the frozen ``top_level_app(...)`` UNKNOWN outcome: root-level files
    (CHANGELOG.md, README.md, SECURITY.md, root conftest.py) are UNKNOWN.
    """
    return path_components_after_saleor(path) is not None


def proximity_of_file(test_file: str, touched_production_files: list[str]) -> int:
    """proximity(test_file) = max over KNOWN touched production files of the
    longest common leading component count after ``saleor/``.

    UNKNOWN touched paths contribute NO proximity score (excluded from the
    max). Outcome-blind: only paths, never outcomes.
    """
    test_components = path_components_after_saleor(test_file)
    if test_components is None:
        return 0
    best = 0
    for touched in touched_production_files:
        touched_components = path_components_after_saleor(touched)
        if touched_components is None:
            continue  # UNKNOWN touched path contributes no score
        best = max(best, longest_common_leading_count(test_components, touched_components))
    return best


def proximity_by_file_for_task(
    candidate_node_ids: list[str],
    touched_production_files: list[str],
) -> tuple[dict[str, int], bool]:
    """Per-file proximity + all_touched_paths_unknown flag.

    ``all_touched_paths_unknown = True`` iff every touched production path for
    the task is UNKNOWN (then all candidates receive proximity=0).
    """
    known = [p for p in touched_production_files if is_known_touched_path(p)]
    all_unknown = len(known) == 0
    effective_touched = [] if all_unknown else touched_production_files
    result: dict[str, int] = {}
    for node_id in candidate_node_ids:
        fpath = file_path_of(node_id)
        if fpath not in result:
            result[fpath] = proximity_of_file(fpath, effective_touched) if not all_unknown else 0
    return result, all_unknown


def split_proximal_distal(
    candidate_node_ids: list[str], file_proximity: dict[str, int]
) -> tuple[list[str], list[str]]:
    """PROXIMAL (file proximity >= 2) and DISTAL (<= 1) node partitions.

    Order of nodes within each returned list is NOT scientific here; the
    deterministic ordering is applied separately.
    """
    proximal: list[str] = []
    distal: list[str] = []
    for node_id in candidate_node_ids:
        fpath = file_path_of(node_id)
        prox = file_proximity.get(fpath, 0)
        if prox >= PROXIMAL_MIN_PROXIMITY:
            proximal.append(node_id)
        else:
            distal.append(node_id)
    return proximal, distal


def order_round_robin(files: list[tuple[str, list[str]]]) -> list[str]:
    """Round-robin one node per file per round.

    ``files`` is a list of (file_path, nodes_already_ordered) where the caller
    has already applied the within-file node ordering. Files are consumed in
    the given order (caller pre-sorts). Returns the interleaved node list.
    """
    ordered: list[str] = []
    idx = 0
    while True:
        progressed = False
        for _fpath, nodes in files:
            if idx < len(nodes):
                ordered.append(nodes[idx])
                progressed = True
        if not progressed:
            break
        idx += 1
    return ordered


def order_proximal_pool(
    proximal_nodes: list[str], file_proximity: dict[str, int], salt: str
) -> list[str]:
    """Deterministic ordering of the PROXIMAL pool.

    1. group files by proximity score DESCENDING;
    2. within each proximity stratum, order FILES by sha256(salt | file_path);
    3. within each file, order NODES by sha256(salt | node_id);
    4. round-robin one node per file per round within the current stratum;
    5. exhaust higher proximity strata before lower.
    """
    nodes_by_file: dict[str, list[str]] = {}
    for node_id in proximal_nodes:
        nodes_by_file.setdefault(file_path_of(node_id), []).append(node_id)
    strata: dict[int, list[tuple[str, list[str]]]] = {}
    for fpath, nodes in nodes_by_file.items():
        prox = file_proximity.get(fpath, 0)
        ordered_nodes = sorted(nodes, key=lambda n: _sha256_text(f"{salt}|{n}"))
        strata.setdefault(prox, []).append((fpath, ordered_nodes))
    result: list[str] = []
    for prox in sorted(strata.keys(), reverse=True):
        files = sorted(strata[prox], key=lambda f: _sha256_text(f"{salt}|{f[0]}"))
        result.extend(order_round_robin(files))
    return result


def order_distal_pool(distal_nodes: list[str], salt: str) -> list[str]:
    """Deterministic ordering of the DISTAL pool.

    1. order FILES by sha256(salt | file_path);
    2. order nodes within each file by sha256(salt | node_id);
    3. round-robin one node per file per round.
    """
    nodes_by_file: dict[str, list[str]] = {}
    for node_id in distal_nodes:
        nodes_by_file.setdefault(file_path_of(node_id), []).append(node_id)
    files = sorted(
        [(f, sorted(nodes, key=lambda n: _sha256_text(f"{salt}|{n}"))) for f, nodes in nodes_by_file.items()],
        key=lambda f: _sha256_text(f"{salt}|{f[0]}"),
    )
    return order_round_robin(files)


def interleave_ppd(proximal: list[str], distal: list[str]) -> list[str]:
    """Construct ONE deterministic final ordered list interleaving:
    P, P, P, D, P, P, P, D, ...
    If one list exhausts, continue with the other list.
    """
    result: list[str] = []
    pi, di = 0, 0
    while pi < len(proximal) or di < len(distal):
        for _ in range(3):
            if pi < len(proximal):
                result.append(proximal[pi])
                pi += 1
        if di < len(distal):
            result.append(distal[di])
            di += 1
    return result


def compute_composition(ordered: list[str], file_proximity: dict[str, int]) -> dict:
    """Requested vs achieved proximal/distal composition of an ordered list."""
    n_prox = sum(1 for n in ordered if file_proximity.get(file_path_of(n), 0) >= PROXIMAL_MIN_PROXIMITY)
    return {
        "n_total": len(ordered),
        "n_proximal": n_prox,
        "n_distal": len(ordered) - n_prox,
    }


def build_task_selection(
    *,
    task_id: str,
    candidate_node_ids: list[str],
    touched_production_files: list[str],
    salt: str = P2P_U_V2_SAMPLE_SALT,
    primary_cap: int = P2P_U_PRIMARY_CAP,
    sensitivity_cap: int = P2P_U_SENSITIVITY_CAP,
) -> dict:
    """Deterministic outcome-blind selection for one task.

    Returns the full per-task selection record: raw candidates, proximity,
    proximal/distal labels, deterministic ordered list, cap200 and cap400
    membership (both prefixes of the same ordered list, so
    first_200 subset first_400 exactly), and composition targets.
    """
    file_proximity, all_unknown = proximity_by_file_for_task(candidate_node_ids, touched_production_files)
    proximal_nodes, distal_nodes = split_proximal_distal(candidate_node_ids, file_proximity)
    ordered_proximal = order_proximal_pool(proximal_nodes, file_proximity, salt)
    ordered_distal = order_distal_pool(distal_nodes, salt)
    ordered = interleave_ppd(ordered_proximal, ordered_distal)
    cap_primary = ordered[:primary_cap]
    cap_sensitivity = ordered[:sensitivity_cap]
    unknown_touched = sorted(p for p in touched_production_files if not is_known_touched_path(p))
    return {
        "task_id": task_id,
        "n_raw_candidates": len(candidate_node_ids),
        "all_touched_paths_unknown": all_unknown,
        "unknown_touched_paths": unknown_touched,
        "n_known_touched_paths": len(touched_production_files) - len(unknown_touched),
        "proximity_by_file": {k: file_proximity[k] for k in sorted(file_proximity)},
        "proximal_nodes": proximal_nodes,
        "distal_nodes": distal_nodes,
        "n_proximal_pool": len(proximal_nodes),
        "n_distal_pool": len(distal_nodes),
        "ordered_node_ids": ordered,
        "primary_cap": primary_cap,
        "sensitivity_cap": sensitivity_cap,
        "cap200_node_ids": cap_primary,
        "cap400_node_ids": cap_sensitivity,
        "composition_cap200": compute_composition(cap_primary, file_proximity),
        "composition_cap400": compute_composition(cap_sensitivity, file_proximity),
        "target_composition_cap200": {
            "proximal": PRIMARY_PROXIMAL_TARGET,
            "distal": PRIMARY_DISTAL_TARGET,
        },
        "target_composition_cap400": {
            "proximal": SENSITIVITY_PROXIMAL_TARGET,
            "distal": SENSITIVITY_DISTAL_TARGET,
        },
        "evaluator_only": True,
        "invisible_to_generation": True,
    }


def verify_task_selection(selection: dict) -> dict:
    """Independent verification of one task's selection record."""
    cap200 = selection["cap200_node_ids"]
    cap400 = selection["cap400_node_ids"]
    ordered = selection["ordered_node_ids"]
    checks = {
        "cap200_subset_cap400": all(n in set(cap400) for n in cap200),
        "cap200_len": len(cap200) <= selection["primary_cap"],
        "cap400_len": len(cap400) <= selection["sensitivity_cap"],
        "cap200_prefix_of_ordered": cap200 == ordered[: selection["primary_cap"]],
        "cap400_prefix_of_ordered": cap400 == ordered[: selection["sensitivity_cap"]],
        "no_duplicates": len(ordered) == len(set(ordered)),
        "all_candidates_used_once": sorted(ordered) == sorted(selection["proximal_nodes"] + selection["distal_nodes"]),
        "nested_membership_identity": len(set(cap200) & set(cap400)) == len(set(cap200)),
        "cap200_achieved_composition": (
            selection["composition_cap200"]["n_total"] == len(cap200)
        ),
        "cap400_achieved_composition": (
            selection["composition_cap400"]["n_total"] == len(cap400)
        ),
    }
    # membership = proximal OR distal; no overlap
    prox_set = set(selection["proximal_nodes"])
    dist_set = set(selection["distal_nodes"])
    checks["proximal_distal_disjoint"] = len(prox_set & dist_set) == 0
    checks["proximal_distal_cover_raw"] = len(prox_set | dist_set) == len(selection["ordered_node_ids"])
    return {"checks": checks, "all_pass": all(checks.values())}


def changed_test_contamination(
    ordered_node_ids: list[str], changed_test_files: list[str]
) -> list[str]:
    """Candidate node ids whose file is in the changed (test-patch) set.

    The frozen candidate pool is unchanged-test only; any overlap is a
    contamination defect (Mission-09 section 24).
    """
    changed = set(changed_test_files)
    return sorted(
        n for n in ordered_node_ids if file_path_of(n) in changed
    )


def verify_freeze(membership_payload: dict) -> dict:
    """Verify the whole frozen membership artifact."""
    per_task_checks = {
        tid: verify_task_selection(sel)["all_pass"]
        for tid, sel in membership_payload["tasks"].items()
    }
    nested_ok = all(
        set(sel["cap200_node_ids"]) <= set(sel["cap400_node_ids"])
        for sel in membership_payload["tasks"].values()
    )
    zero_undefined = [
        tid for tid, sel in membership_payload["tasks"].items() if sel["n_raw_candidates"] == 0
    ]
    return {
        "all_task_checks_pass": all(per_task_checks.values()),
        "n_tasks": len(membership_payload["tasks"]),
        "per_task_failures": [tid for tid, ok in per_task_checks.items() if not ok],
        "global_cap200_subset_cap400": nested_ok,
        "zero_candidate_undefined_tasks": zero_undefined,
        "all_pass": all(per_task_checks.values()) and nested_ok,
    }
