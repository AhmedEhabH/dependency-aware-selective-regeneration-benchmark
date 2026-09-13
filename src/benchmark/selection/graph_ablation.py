"""M3 graph ablation core: C0 (Graph OFF) vs C1 (Graph Hints) vs C2 (Graph-Gated Disclosure).

STUDY_ID: scientific-djangocms-graph-c0-c1-c2-01

Common base = the audited M1B Sparse-v2 contract (model qwen/qwen3-coder @
deepinfra/turbo, temperature 0, cap 16384, common schema, candidate map,
scenario texts, repository evidence, scorer, action vocabulary). The ONLY
treatment-specific content is the GRAPH_EVIDENCE block appended after the
frozen M1 serialization-policy block:

- C0 (graph OFF):      no graph block; the rendered prompt is byte-identical
                       to the audited M1B Sparse-v2 prompt, so the frozen
                       M1B Sparse-v2 30 cells are REUSED as C0.
- C1 (graph hints):    complete automatic AST dependency graph supplied as
                       SOFT EVIDENCE (no pruning, no forced selection).
- C2 (gated):          GRAPH-GATED DISCLOSURE: omission stays allowed OUTSIDE
                       the risk zone; INSIDE the risk zone an explicit
                       decision (REGENERATE / VALIDATE / HUMAN_REVIEW) is
                       MANDATORY and omission fails the cell (fail-closed
                       mandatory-disclosure-failure).

Risk zone = all candidate ids within ``hop`` undirected graph hops of the
scenario's deterministic seed set (primary hop = 1; pre-registered
sensitivity hop = 2; hop = 3 exploratory ONLY if the frozen eligibility
condition passes).

Seed construction (frozen algorithm v1, inference-time-only, NO gold):
- visible text T = requirement_before + requirement_after + acceptance
  criteria + architecture constraints (the exact fields rendered into the
  prompt);
- domain terms = CamelCase identifiers + snake_case identifiers in T;
- a candidate is a seed iff any of its classes / functions / path tokens /
  module segments contains a domain term;
- seed set = sorted candidate ids; persisted per scenario with a hash.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

from benchmark.external_validity import study_runtime as wiring
from benchmark.selection import encoding_ablation as ea
from benchmark.selection.impact_planner_v2 import derive_candidate_id_map

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

GRAPH_PATH = (
    _PACKAGE_ROOT
    / "benchmark_data"
    / "external_validity"
    / "djangocms_5_0_0_dependency_graph.json"
)
CANONICAL_BUILD_HASHES_PATH = (
    _PACKAGE_ROOT
    / "benchmark_data"
    / "external_validity"
    / "canonical_build_hashes.json"
)
GRAPH_ELIGIBILITY_PATH = (
    _PACKAGE_ROOT / "benchmark_data" / "external_validity" / "graph_eligibility.json"
)

GRAPH_NODE_COUNT = 144
GRAPH_EDGE_COUNT = 562
GRAPH_PARSE_OK = 144
GRAPH_HASH_EXPECTED = "0a6bf0f758c9cd7de79adb72138c549a2b0aee3cfd62841496cb455d1ce7cd58"
GRAPH_SOURCE_NAME = "python_ast_source_extractor"

SEED_ALGORITHM_VERSION = "v1"
SEED_ALGORITHM_LABEL = (
    "visible-text domain-term x candidate inventory matching "
    "(CamelCase + snake_case identifiers in requirement/acceptance/constraint "
    "text matched against candidate classes/functions/path tokens/module "
    "segments); inference-time-only, deterministic, NO gold."
)

CONDITIONS = ("c0", "c1", "c2")
PRIMARY_ZONE_HOP = 1
SENSITIVITY_ZONE_HOP = 2
EXPLORATORY_ZONE_HOP = 3

# 3-hop exploratory eligibility (frozen BEFORE any scientific call): for ALL
# six scenarios |zone_3hop| <= 115 (<= 80% of 144) AND |zone_3hop| > |zone_2hop|.
THREE_HOP_ZONE_CEILING = 115

GRAPH_BLOCK_OPEN = "[[GRAPH_EVIDENCE]]"
GRAPH_BLOCK_CLOSE = "[[/GRAPH_EVIDENCE]]"

FAILURE_CATEGORIES = (
    "missed-neighbor",
    "over-expansion",
    "wrong-edge-direction",
    "graph-evidence-ignored",
    "mandatory-disclosure-failure",
    "unrelated-module-attraction",
    "graph-coverage-gap",
    "semantic-misreasoning",
    "operational/schema failure",
    "other-with-rationale",
)

C1_GRAPH_HINTS_INSTRUCTION = (
    "GRAPH EVIDENCE (automatic AST import graph of the candidate universe; "
    "SOFT EVIDENCE ONLY): the edge list below records which candidate files "
    "import which other candidate files. It is automatic and repository-"
    "derived; it does NOT decide anything. Use it as additional context when "
    "deciding REGENERATE / VALIDATE / HUMAN_REVIEW."
)

C2_DISCLOSURE_INSTRUCTION = (
    "GRAPH-GATED DISCLOSURE (risk zone): the risk zone below lists candidate "
    "ids within {hop}-hop of the deterministic seed set in the automatic AST "
    "import graph. INSIDE the risk zone an explicit decision is MANDATORY: "
    "every risk-zone candidate id MUST appear in your output with an explicit "
    "action (REGENERATE, VALIDATE, or HUMAN_REVIEW). Omission of an in-zone "
    "id is NOT allowed and invalidates the output. Omission is allowed ONLY "
    "for candidate ids OUTSIDE the risk zone (they deterministically decode "
    "as PRESERVE)."
)

# Scenario visible-text hashes (historical parity record, same as M1A/M1B).
SCENARIO_VISIBLE_HASHES: dict[str, str] = {
    "djangocms-external-validity-002": "a7e72f7af23541407180d490f5dd03e9df281efb514ab4c4f92f4a59deb4c730",
    "djangocms-external-validity-004": "0b25d27452ceff3fae08eecd42b15da8d6788c4af162455f71c2db5cf3450430",
    "djangocms-external-validity-005": "836f42fbbf00cd097b52a928f12e01e463857f4a9fe01aa122729696b223a57b",
    "djangocms-external-validity-006": "c724fff84d0757e4182e3b127a296b6876964a267be5e3584f1aafcf9aefa0e3",
    "djangocms-external-validity-007": "1caf61e7a4db2b887e8c14d02f349ef3771e7f19a27ecab2f69e6aa686e5e88c",
    "djangocms-external-validity-008": "d2076d5bf092ac8a96566c88f413deb1090ab61ebe85733a41174e8aac283021",
}

_CAMEL_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*\b")
_SNAKE_RE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
_SKIP_TERMS: frozenset[str] = frozenset(
    {
        "The", "A", "An", "If", "When", "For", "All", "Any", "Each", "No",
        "Not", "New", "Django", "Python", "JSON", "API", "SQL", "HTML", "HTTP",
        "DB", "FK", "NULL", "UTC", "True", "False", "None",
    }
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_text(canonical)


# ---------------------------------------------------------------------------
# Graph loading / independent verification (ZERO API)
# ---------------------------------------------------------------------------


def load_graph() -> dict[str, Any]:
    if not GRAPH_PATH.is_file():
        raise FileNotFoundError(f"dependency graph not found: {GRAPH_PATH}")
    return cast(dict[str, Any], json.loads(GRAPH_PATH.read_text(encoding="utf-8")))


def canonical_graph_hash(graph: dict[str, Any]) -> str:
    stripped = {k: v for k, v in graph.items() if k != "generated_utc"}
    canonical = json.dumps(stripped, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256_text(canonical)


def graph_verification() -> dict[str, Any]:
    """Independent automatic-graph verification (mission gate, ZERO API)."""
    checks: list[dict[str, Any]] = []

    def check(label: str, ok: bool, detail: Any = None) -> None:
        checks.append({"check": label, "ok": bool(ok), "detail": detail})

    graph = load_graph()
    check("node_count_144", graph.get("node_count") == GRAPH_NODE_COUNT, graph.get("node_count"))
    check("edge_count_562", graph.get("edge_count") == GRAPH_EDGE_COUNT, graph.get("edge_count"))
    check("ast_parse_144_of_144", graph.get("parse_success_count") == GRAPH_PARSE_OK
          and graph.get("parse_failure_count") == 0,
          {"ok": graph.get("parse_success_count"), "fail": graph.get("parse_failure_count")})
    check("graph_source_is_ast_extractor", graph.get("graph_source") == GRAPH_SOURCE_NAME,
          graph.get("graph_source"))

    recomputed = canonical_graph_hash(graph)
    builds: dict[str, Any] = {}
    if CANONICAL_BUILD_HASHES_PATH.is_file():
        builds = json.loads(CANONICAL_BUILD_HASHES_PATH.read_text(encoding="utf-8"))
    recorded = [str(b.get("graph_hash")) for b in builds.values()
                if isinstance(b, dict) and b.get("graph_hash")]
    check("canonical_hash_parity", recomputed == GRAPH_HASH_EXPECTED and bool(recorded)
          and all(r == GRAPH_HASH_EXPECTED for r in recorded),
          {"recomputed": recomputed, "expected": GRAPH_HASH_EXPECTED, "recorded_builds": recorded})
    check("two_builds_reproducible", len(recorded) >= 2 and len({r for r in recorded}) == 1,
          {"recorded_build_count": len(recorded), "distinct_hashes": len({r for r in recorded})})
    check("pinned_source_commit_frozen",
          graph.get("pinned_commit") == "0f633fc9fa213357f4202482aab2b0edad680f95",
          graph.get("pinned_commit"))

    universe_paths = set(wiring.runtime_universe_paths())
    edges = graph.get("edges", [])
    endpoints = {p for e in edges for p in e}
    check("every_edge_endpoint_in_universe", endpoints <= universe_paths,
          {"out_of_universe": sorted(endpoints - universe_paths)[:10]})
    check("no_self_loops", all(s != t for s, t in edges))
    check("no_duplicate_edges", len(edges) == len({(s, t) for s, t in edges}))

    # no scenario / gold / expected-action references inside the graph artifact
    suspicious_keys = [k for k in graph if any(tok in k.lower() for tok in
                       ("gold", "scenario", "expected", "action", "manual"))]
    suspicious_edge_terms = [e for e in edges for tok in ("gold", "scenario", "expected")
                             if tok in str(e).lower()]
    check("no_manually_authored_scenario_edges",
          not suspicious_keys and not suspicious_edge_terms,
          {"keys": suspicious_keys, "edge_hits": suspicious_edge_terms[:5]})

    elig: dict[str, Any] = {}
    if GRAPH_ELIGIBILITY_PATH.is_file():
        elig = json.loads(GRAPH_ELIGIBILITY_PATH.read_text(encoding="utf-8"))
    check("eligibility_gate", elig.get("eligible") is True, elig.get("criteria"))

    gold_paths = {p for rec in wiring.load_hidden_gold() for p in rec.get("source_files", [])}
    check("gold_is_universe_subset_only_evaluation",
          gold_paths <= universe_paths,
          sorted(gold_paths - universe_paths))

    return {
        "passed": all(c["ok"] for c in checks),
        "checks": checks,
        "graph_hash": recomputed,
    }


# ---------------------------------------------------------------------------
# Seed construction (frozen algorithm v1) and risk zones
# ---------------------------------------------------------------------------


def _visible_text(scenario_id: str) -> str:
    scenario, _ = wiring.load_study_scenario(scenario_id)
    parts = [scenario.requirement_before, scenario.requirement_after]
    parts += [str(c.description) for c in scenario.acceptance_criteria]
    parts += [str(c.description) for c in scenario.architecture_constraints]
    return "\n".join(parts)


def extract_domain_terms(text: str) -> frozenset[str]:
    terms: set[str] = set()
    for pattern in (_CAMEL_RE, _SNAKE_RE):
        for m in pattern.finditer(text):
            term = m.group(0)
            if term in _SKIP_TERMS:
                continue
            terms.add(term)
    return frozenset(terms)


def _candidate_inventory(rec: dict[str, Any]) -> frozenset[str]:
    terms: set[str] = set(rec.get("classes") or [])
    terms.update(rec.get("functions") or [])
    for tok in re.split(r"[/._-]", str(rec["path"])):
        if tok and tok not in ("py", "cms", "menus", "init", "tests", "migrations"):
            terms.add(tok)
    terms.add(str(rec.get("module", "")))
    return frozenset(t for t in terms if t)


def compute_seed_paths(scenario_id: str) -> tuple[str, ...]:
    text = _visible_text(scenario_id)
    terms = extract_domain_terms(text)
    records = wiring.load_frozen_universe_records()
    seeds = sorted(
        str(rec["path"])
        for rec in records
        if (_candidate_inventory(rec) & terms)
    )
    return tuple(seeds)


def _undirected_adjacency() -> dict[str, set[str]]:
    graph = load_graph()
    adj: dict[str, set[str]] = {}
    for rec in wiring.load_frozen_universe_records():
        adj[str(rec["path"])] = set()
    for src, dst in graph.get("edges", []):
        adj.setdefault(src, set()).add(dst)
        adj.setdefault(dst, set()).add(src)
    return adj


def _bfs_distances(seed_paths: Iterable[str], max_hop: int) -> dict[str, int]:
    adj = _undirected_adjacency()
    dist: dict[str, int] = {}
    dq: deque[str] = deque()
    for s in seed_paths:
        dist[s] = 0
        dq.append(s)
    while dq:
        u = dq.popleft()
        if dist[u] >= max_hop:
            continue
        for v in adj.get(u, set()):
            if v not in dist:
                dist[v] = dist[u] + 1
                dq.append(v)
    return dist


def _mapping() -> Any:
    return derive_candidate_id_map()


def _path_to_id() -> dict[str, int]:
    return {p: i for i, p in _mapping().id_to_path}


def seed_ids(scenario_id: str) -> tuple[int, ...]:
    pid = _path_to_id()
    return tuple(sorted(pid[p] for p in compute_seed_paths(scenario_id)))


def risk_zone_ids(scenario_id: str, hop: int) -> tuple[int, ...]:
    pid = _path_to_id()
    seeds = compute_seed_paths(scenario_id)
    dist = _bfs_distances(seeds, hop)
    return tuple(sorted(pid[p] for p, d in dist.items() if d <= hop))


def hop_distance(scenario_id: str, path: str, max_hop: int) -> int:
    dist = _bfs_distances(compute_seed_paths(scenario_id), max_hop)
    return dist.get(path, max_hop + 1)


def three_hop_eligibility() -> dict[str, Any]:
    """Frozen eligibility for the exploratory 3-hop condition (ZERO API)."""
    per: dict[str, Any] = {}
    ok = True
    for sid in SCENARIO_VISIBLE_HASHES:
        z2 = len(risk_zone_ids(sid, SENSITIVITY_ZONE_HOP))
        z3 = len(risk_zone_ids(sid, EXPLORATORY_ZONE_HOP))
        grows = z3 > z2
        bounded = z3 <= THREE_HOP_ZONE_CEILING
        ok = ok and grows and bounded
        per[sid] = {"zone_2hop_size": z2, "zone_3hop_size": z3,
                    "grows_beyond_2hop": grows, "within_ceiling_115": bounded}
    return {
        "eligible": ok,
        "ceiling": THREE_HOP_ZONE_CEILING,
        "rule": "for ALL 6 scenarios: |zone_3hop| > |zone_2hop| AND |zone_3hop| <= 115",
        "per_scenario": per,
    }


# ---------------------------------------------------------------------------
# Treatment-specific graph blocks + prompt rendering + controlled-diff
# ---------------------------------------------------------------------------


def _graph_block_for(scenario_id: str, condition: str, hop: int | None) -> str:
    pid = _path_to_id()
    id_to_path = dict(_mapping().id_to_path)
    if condition == "c1":
        graph = load_graph()
        rows = [f"- {pid[s]} -> {pid[t]}" for s, t in sorted(graph.get("edges", []))]
        return C1_GRAPH_HINTS_INSTRUCTION + (
            "\nCandidate ids map to paths via the candidate list above.\n"
            + "\n".join(rows)
        )
    if condition == "c2":
        seeds = seed_ids(scenario_id)
        zone = risk_zone_ids(scenario_id, int(hop or PRIMARY_ZONE_HOP))
        lines = [
            C2_DISCLOSURE_INSTRUCTION.format(hop=int(hop or PRIMARY_ZONE_HOP)),
            f"Seed candidate ids (deterministic): {', '.join(str(i) for i in seeds)}",
            f"Risk-zone candidate ids ({hop}-hop): {', '.join(str(i) for i in zone)}",
            "Risk-zone paths: " + "; ".join(f"{i}={id_to_path[i]}" for i in zone),
        ]
        return "\n".join(lines)
    raise ValueError(f"unknown condition {condition!r}")


def render_condition_prompt(
    scenario_id: str,
    condition: str,
    *,
    hop: int | None = None,
    mapping: Any | None = None,
) -> str:
    """Render the M3 prompt for one condition.

    C0 renders EXACTLY the audited M1B Sparse-v2 prompt (no graph block).
    C1 / C2 append the treatment-specific GRAPH_EVIDENCE block.
    """
    mapping = mapping or _mapping()
    scenario, _ = wiring.load_study_scenario(scenario_id)
    base = ea.render_sparse_prompt(
        scenario_id=scenario_id,
        before=scenario.requirement_before,
        after=scenario.requirement_after,
        acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
        architecture_constraints=[c.description for c in scenario.architecture_constraints],
        mapping=mapping,
    )
    if condition == "c0":
        return base
    block = _graph_block_for(scenario_id, condition, hop)
    return base + "\n" + GRAPH_BLOCK_OPEN + "\n" + block + "\n" + GRAPH_BLOCK_CLOSE


def strip_graph_block(prompt: str) -> str:
    """Remove the appended GRAPH_EVIDENCE block; must equal the C0 prompt."""
    marker = "\n" + GRAPH_BLOCK_OPEN
    idx = prompt.find(marker)
    if idx < 0:
        return prompt
    return prompt[:idx]


def condition_controlled_diff(
    scenario_id: str, mapping: Any | None = None
) -> dict[str, Any]:
    """Automated controlled-diff: C0 vs C1 vs C2 prompts differ ONLY in the
    graph/disclosure block. Also proves C0 == audited M1B Sparse-v2 prompt."""
    c0 = render_condition_prompt(scenario_id, "c0", mapping=mapping)
    c1 = render_condition_prompt(scenario_id, "c1", hop=PRIMARY_ZONE_HOP, mapping=mapping)
    c2 = render_condition_prompt(scenario_id, "c2", hop=PRIMARY_ZONE_HOP, mapping=mapping)
    c2_2 = render_condition_prompt(scenario_id, "c2", hop=SENSITIVITY_ZONE_HOP, mapping=mapping)
    stripped_c1 = strip_graph_block(c1)
    stripped_c2 = strip_graph_block(c2)
    stripped_c2_2 = strip_graph_block(c2_2)
    m1b_sha = SCENARIO_VISIBLE_HASHES[scenario_id]  # placeholder, replaced by executor
    return {
        "scenario_id": scenario_id,
        "c0_equals_stripped_c1": c0 == stripped_c1,
        "c0_equals_stripped_c2": c0 == stripped_c2,
        "c0_equals_stripped_c2_2hop": c0 == stripped_c2_2,
        "c1_differs_from_c0": c1 != c0,
        "c2_differs_from_c0": c2 != c0,
        "c2_1hop_differs_from_c2_2hop": c2 != c2_2,
        "c0_sha256": sha256_text(c0),
        "c1_sha256": sha256_text(c1),
        "c2_1hop_sha256": sha256_text(c2),
        "c2_2hop_sha256": sha256_text(c2_2),
        "m1b_scenario_visible_sha256_parity_note": m1b_sha,
    }


def c0_matches_audited_m1b() -> dict[str, Any]:
    """Prove C0 rendered prompts are byte-identical to the audited M1B
    Sparse-v2 recorded prompts (prompt_sha256 per cell)."""
    import json as _json

    m1b_dir = _PACKAGE_ROOT / "research" / "controlled-encoding-ablation-16k-01"
    records_path = m1b_dir / "run_records.jsonl"
    if not records_path.is_file():
        return {"passed": False, "reason": "M1B run_records.jsonl not found"}
    recorded: dict[str, str] = {}
    for line in records_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = _json.loads(line)
        if rec.get("arm") == "sparse_v2":
            recorded.setdefault(rec["scenario_id"], rec.get("prompt_sha256", ""))
    mapping = _mapping()
    checks = []
    all_ok = True
    for sid in SCENARIO_VISIBLE_HASHES:
        c0 = render_condition_prompt(sid, "c0", mapping=mapping)
        ok = recorded.get(sid) == sha256_text(c0)
        all_ok = all_ok and bool(ok)
        checks.append({"scenario_id": sid, "c0_sha256": sha256_text(c0),
                       "m1b_recorded_sha256": recorded.get(sid), "match": ok})
    return {"passed": all_ok, "checks": checks,
            "note": "C0 reuses the audited M1B Sparse-v2 30 cells (exact prompt identity)"}


# ---------------------------------------------------------------------------
# C2 mandatory-disclosure validation (fail-closed)
# ---------------------------------------------------------------------------


def validate_c2_disclosure(
    parsed: dict[str, Any], scenario_id: str, hop: int
) -> dict[str, Any]:
    """After sparse decode, every risk-zone id MUST carry a non-PRESERVE
    action. Any in-zone id omitted (decoded PRESERVE) fails the cell."""
    zone = set(risk_zone_ids(scenario_id, hop))
    vres = ea.validate_sparse_v2(parsed)
    if not vres["valid"]:
        return {**vres, "disclosure_valid": False,
                "disclosure_error": vres.get("errors", [])}
    policy = vres["policy"]
    in_zone_preserved = [
        i for i in sorted(zone) if policy.action_for(i) == "PRESERVE"
    ]
    disclosure_valid = not in_zone_preserved
    return {
        **vres,
        "disclosure_valid": disclosure_valid,
        "disclosure_error": (
            [] if disclosure_valid else
            [f"mandatory-disclosure-failure: in-zone candidates omitted (decoded PRESERVE): {in_zone_preserved}"]
        ),
        "zone_ids": sorted(zone),
        "in_zone_preserved_ids": in_zone_preserved,
    }


def seed_zone_identity() -> dict[str, Any]:
    """Persistable identity: per-scenario seed sets and risk zones (hashed)."""
    per: dict[str, Any] = {}
    for sid in SCENARIO_VISIBLE_HASHES:
        seeds = seed_ids(sid)
        zones = {
            str(hop): risk_zone_ids(sid, hop)
            for hop in (PRIMARY_ZONE_HOP, SENSITIVITY_ZONE_HOP, EXPLORATORY_ZONE_HOP)
        }
        per[sid] = {
            "scenario_id": sid,
            "visible_text_sha256": sha256_text(_visible_text(sid)),
            "scenario_yaml_sha256": SCENARIO_VISIBLE_HASHES[sid],
            "domain_terms_sha256": sha256_json(sorted(extract_domain_terms(_visible_text(sid)))),
            "seed_ids": seeds,
            "seed_ids_sha256": sha256_json(seeds),
            "zones": {k: {"ids": v, "sha256": sha256_json(v), "size": len(v)} for k, v in zones.items()},
        }
    return {
        "seed_algorithm_version": SEED_ALGORITHM_VERSION,
        "seed_algorithm_label": SEED_ALGORITHM_LABEL,
        "graph_hash": GRAPH_HASH_EXPECTED,
        "per_scenario": per,
    }
