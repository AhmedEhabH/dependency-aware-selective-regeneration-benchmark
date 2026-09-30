#!/usr/bin/env python3
"""WP2 M14R core (brain-authored). Pure, deterministic, unit-tested. ZERO model API.

Everything here is a pure function of its inputs (no git, WSL, Docker or network):

  * scoring:   strict (frozen Smoke v2.2 D50-D52, re-implemented and tested for identity)
               and robust (preservation node broken only if non-passing in >= 2 of 3 reps)
  * taxonomy:  mutually exclusive descriptive failure labels with fixed precedence
  * static:    STATIC_UNDEFINED_V1 = pyflakes undefined-name findings that are NEW relative
               to the parent version of the same file (generator side, label-free)
  * context:   IMPORT_OUTLINE_V1 = read-only one-hop import outlines built only from the
               parent snapshot (signatures and class-level attribute lines, verbatim)
  * decision:  frozen M14R variant selection and outcome token

No function here may read evaluator sets, tests, target commits or evaluation results,
except `score_*`, `classify_episode` and `decide`, which run after generation is frozen.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
from collections.abc import Callable
from typing import Any

VERSION = "m14r-core-v1"
REPS = 3
PASSISH = ("PASS", "UNDEFINED")

# ------------------------------------------------------------------ design constants
CONTEXTS = ("C0", "C2")                 # C0 = frozen G0 prompt; C2 = + IMPORT_OUTLINE_V1
VARIANTS = {"G0": ("C0", False), "G1": ("C0", True), "G2": ("C2", False), "G3": ("C2", True)}
VARIANT_ORDER = ("G0", "G1", "G2", "G3")
OUTLINE_MODULE_CAP = 6000
OUTLINE_TOTAL_CAP = 40000
STATIC_CLASSES = ("UndefinedName", "UndefinedLocal", "UndefinedExport")
STATIC_LINE_CAP = 200

DECISION = {
    "primary": "GOLD RESOLVED_ROBUST episodes per variant (3 replicates x member tasks)",
    "min_gain_vs_g0": 3,
    "max_extra_invalid_vs_g0": 3,
    "task_direction": "#tasks(variant > G0) >= #tasks(G0 > variant) on per-task robust counts",
    "tie_breakers": ["higher primary count", "lower mean provider tokens per GOLD episode",
                     "simpler variant in order G0 < G1 < G2 < G3"],
    "floor_episode_rate": 0.20,
    "floor_task_fraction": 1 / 3,
    "placebo_robust_max": 1,
}

SYSTEM_PROMPT_C2_INSERT = (
    "You may also receive READ-ONLY CONTEXT: outlines (signatures and class-level attribute "
    "lines) of repository modules that the editable files import. Use it only as a reference; "
    "never write FILE blocks for it.\n")
STATIC_REPAIR_TEMPLATE = (
    "Your edits apply cleanly, but a static check of the edited files found names that are "
    "used but never defined or imported:\n{findings}\n\n"
    "Return the COMPLETE corrected set of edit blocks for the whole change (not only the "
    "fixes), in the same format, applied to the ORIGINAL file contents shown above. Output "
    "only edit blocks.")


def sha_obj(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def design_constants() -> dict:
    return {"version": VERSION, "contexts": list(CONTEXTS),
            "variants": {k: list(v) for k, v in VARIANTS.items()},
            "outline_module_cap": OUTLINE_MODULE_CAP, "outline_total_cap": OUTLINE_TOTAL_CAP,
            "static_classes": list(STATIC_CLASSES), "decision": DECISION,
            "system_prompt_c2_insert": SYSTEM_PROMPT_C2_INSERT,
            "static_repair_template": STATIC_REPAIR_TEMPLATE, "reps": REPS}


# ------------------------------------------------------------------ scoring
def _npass(outcomes: list[str]) -> int:
    return sum(o == "passed" for o in outcomes)


def score_strict(t: dict, groups: dict) -> dict:
    """Frozen `benchmark.wp2.e2e.evaluate.score` semantics (identity tested)."""
    c, u = groups.get("C", {}), groups.get("U", {})

    def passed(o: list[str]) -> bool:
        return len(o) == REPS and all(x == "passed" for x in o)
    f2p = [n for n in t["behavioral_f2p_node_ids"] if n in c]
    f = "PASS" if f2p and all(passed(c[n]) for n in f2p) else ("UNDEFINED" if not f2p else "FAIL")
    sn = [n for n in t["p2p_s_node_ids"] if n in c]
    s = "PASS" if all(passed(c[n]) for n in sn) else ("UNDEFINED" if not sn else "FAIL")
    un = [n for n in t["p2p_u_cap200_stable_ids"] if n in u]
    uu = "PASS" if all(passed(u[n]) for n in un) else ("UNDEFINED" if not un else "FAIL")
    return {"f2p_task": f, "p2p_s_task": s, "p2p_u200_task": uu,
            "resolved": f == "PASS" and s in PASSISH and uu in PASSISH}


def score_robust(t: dict, groups: dict) -> dict:
    """F2P exactly as strict (every node passed in all 3 reps). A preservation node is broken
    only if it is non-passing (failed/error/skipped/missing) in >= 2 of the 3 reps."""
    c, u = groups.get("C", {}), groups.get("U", {})
    st = score_strict(t, groups)

    def broken(o: list[str]) -> bool:
        return len(o) - _npass(o) >= 2 or len(o) < 2

    sn = [n for n in t["p2p_s_node_ids"] if n in c]
    s = ("UNDEFINED" if not sn else "FAIL" if any(broken(c[n]) for n in sn) else "PASS")
    un = [n for n in t["p2p_u_cap200_stable_ids"] if n in u]
    uu = ("UNDEFINED" if not un else "FAIL" if any(broken(u[n]) for n in un) else "PASS")
    return {"f2p_task": st["f2p_task"], "p2p_s_task": s, "p2p_u200_task": uu,
            "resolved": st["f2p_task"] == "PASS" and s in PASSISH and uu in PASSISH}


def node_report(t: dict, groups: dict) -> dict:
    """Reporting-only split that replaces the misleading `flaky_under_patch` list."""
    c, u = groups.get("C", {}), groups.get("U", {})
    f2p = t["behavioral_f2p_node_ids"]

    def cls(o: list[str]) -> str:
        if o and all(x == "missing" for x in o):
            return "missing"
        k = _npass(o)
        return "pass3" if k == len(o) == REPS else "deterministic" if k == 0 else "intermittent"
    out = {"f2p_total": len(f2p), "f2p_pass3": 0, "f2p_intermittent": 0,
           "s_deterministic": 0, "s_intermittent": 0, "s_missing": 0,
           "u_deterministic": 0, "u_intermittent": 0, "u_missing": 0}
    for n in f2p:
        k = cls(c.get(n, ["missing"] * REPS))
        out["f2p_pass3"] += k == "pass3"
        out["f2p_intermittent"] += k == "intermittent"
    for g, ids, src in (("s", t["p2p_s_node_ids"], c), ("u", t["p2p_u_cap200_stable_ids"], u)):
        for n in ids:
            if n in src:
                k = cls(src[n])
                if k in ("deterministic", "intermittent", "missing"):
                    out[f"{g}_{k}"] += 1
    return out


# ------------------------------------------------------------------ taxonomy
TAXONOMY_PRECEDENCE = ("FORMAT_INVALID", "NO_SCOPE", "NO_OP", "PATCH_STARTUP_FAILURE",
                       "RESOLVED", "F2P_PASS_PRESERVATION_FAIL", "PARTIAL_F2P_PROGRESS",
                       "ZERO_F2P_PROGRESS")


def classify_episode(status: str, empty_diff: bool, e1_decision: str | None,
                     t: dict | None, groups: dict | None, strict: dict | None) -> dict:
    """Mutually exclusive label by fixed precedence (descriptive only, changes no gate)."""
    if status == "NO_SCOPE":
        return {"label": "NO_SCOPE", "detail": ""}
    if status != "APPLIED":
        return {"label": "FORMAT_INVALID", "detail": status}
    if empty_diff:
        return {"label": "NO_OP", "detail": ""}
    assert t is not None and groups is not None and strict is not None
    allmiss = bool(groups) and all(all(x == "missing" for x in v)
                                   for g in groups.values() for v in g.values())
    if e1_decision == "PATCH_STARTUP_FAILURE" or allmiss:
        return {"label": "PATCH_STARTUP_FAILURE", "detail": ""}
    if strict["resolved"]:
        return {"label": "RESOLVED", "detail": ""}
    r = node_report(t, groups)
    det = r["s_deterministic"] + r["u_deterministic"] + r["s_missing"] + r["u_missing"]
    if strict["f2p_task"] == "PASS":
        return {"label": "F2P_PASS_PRESERVATION_FAIL",
                "detail": "PRESERVATION_DETERMINISTIC" if det else "PRESERVATION_INTERMITTENT_ONLY"}
    lab = "PARTIAL_F2P_PROGRESS" if r["f2p_pass3"] > 0 else "ZERO_F2P_PROGRESS"
    return {"label": lab, "detail": "+DETERMINISTIC_PRESERVATION_BREAK" if det else ""}


# ------------------------------------------------------------------ static check
def undefined_findings(path: str, text: str) -> list[dict] | None:
    """pyflakes undefined-name findings; None if the text does not parse on this host."""
    from pyflakes import checker
    try:
        tree = ast.parse(text, filename=path)
    except (SyntaxError, ValueError):
        return None
    w = checker.Checker(tree, filename=path)
    lines = text.splitlines()
    out = []
    for m in w.messages:
        name = type(m).__name__
        if name not in STATIC_CLASSES:
            continue
        ln = int(getattr(m, "lineno", 0) or 0)
        src = lines[ln - 1].strip()[:STATIC_LINE_CAP] if 0 < ln <= len(lines) else ""
        out.append({"cls": name, "args": [str(a) for a in m.message_args], "lineno": ln,
                    "line": src, "path": path})
    return sorted(out, key=lambda d: (d["lineno"], d["cls"], d["args"]))


def new_static_findings(parent: dict[str, str], final: dict[str, str],
                        edited: list[str]) -> dict:
    """Findings in generated .py files whose (class, args) key is absent at parent."""
    new: list[dict] = []
    skipped: list[str] = []
    for p in sorted(edited):
        if not p.endswith(".py") or p not in final:
            continue
        g = undefined_findings(p, final[p])
        b = undefined_findings(p, parent.get(p, "")) if p in parent else []
        if g is None:
            skipped.append(p)
            continue
        base = {(d["cls"], tuple(d["args"])) for d in (b or [])}
        new += [d for d in g if (d["cls"], tuple(d["args"])) not in base]
    return {"new": new, "parse_skipped": skipped}


def static_repair_text(new: list[dict]) -> str:
    lines = [f"- {d['path']}: line {d['lineno']}: {d['cls']} "
             f"{', '.join(repr(a) for a in d['args'])}: {d['line']}" for d in new]
    return STATIC_REPAIR_TEMPLATE.format(findings="\n".join(lines))


# ------------------------------------------------------------------ read-only context
def _module_path(dotted: str, tracked: set[str]) -> str | None:
    base = dotted.replace(".", "/")
    for cand in (base + ".py", base + "/__init__.py"):
        if cand in tracked:
            return cand
    return None


def _package_of(path: str) -> list[str]:
    parts = path[:-3].split("/")
    return parts[:-1] if parts[-1] != "__init__" else parts[:-1]


def import_targets(path: str, text: str, tracked: set[str]) -> list[tuple[str, str | None]]:
    """[(module_path, symbol|None)] in source order; None = whole module."""
    try:
        tree = ast.parse(text, filename=path)
    except (SyntaxError, ValueError):
        return []
    nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    nodes.sort(key=lambda n: (n.lineno, n.col_offset))
    out: list[tuple[str, str | None]] = []
    pkg = _package_of(path)
    for n in nodes:
        if isinstance(n, ast.Import):
            for a in n.names:
                mp = _module_path(a.name, tracked)
                if mp:
                    out.append((mp, None))
            continue
        if n.level:
            if n.level - 1 > len(pkg):
                continue
            base = pkg[:len(pkg) - (n.level - 1)]
            mod = ".".join(base + ([n.module] if n.module else []))
        else:
            mod = n.module or ""
        for a in n.names:
            if a.name == "*":
                continue
            sub = _module_path(f"{mod}.{a.name}" if mod else a.name, tracked)
            if sub:
                out.append((sub, None))
                continue
            mp = _module_path(mod, tracked) if mod else None
            if mp:
                out.append((mp, a.name))
    return out


def _header_lines(node: ast.AST, lines: list[str]) -> list[str]:
    start = min([d.lineno for d in getattr(node, "decorator_list", [])] + [node.lineno])
    body = getattr(node, "body", [])
    end = body[0].lineno - 1 if body and body[0].lineno > node.lineno else node.lineno
    if isinstance(body[0] if body else None, ast.Expr) and \
            isinstance(getattr(body[0], "value", None), ast.Constant) and \
            isinstance(body[0].value.value, str) and body[0].lineno > node.lineno:
        end = body[0].lineno - 1
    return lines[start - 1:end]


def _class_outline(node: ast.ClassDef, lines: list[str], depth: int = 0) -> list[str]:
    out = _header_lines(node, lines)
    for st in node.body:
        if isinstance(st, (ast.Assign, ast.AnnAssign)):
            out.append(lines[st.lineno - 1])
        elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += _header_lines(st, lines)
        elif isinstance(st, ast.ClassDef) and depth == 0:
            out += _class_outline(st, lines, depth + 1)
    return out


def _defined_names(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return [node.name]
    if isinstance(node, ast.Assign):
        return [t.id for t in node.targets if isinstance(t, ast.Name)]
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id]
    return []


def module_outline(path: str, text: str, symbols: set[str] | None) -> tuple[list[str], str]:
    """Verbatim source lines outlining the module (symbols=None -> all public names)."""
    try:
        tree = ast.parse(text, filename=path)
    except (SyntaxError, ValueError):
        return [], "PARSE_SKIPPED"
    lines = text.splitlines()
    out: list[str] = []
    for node in tree.body:
        names = _defined_names(node)
        if not names:
            continue
        want = (any(not n.startswith("_") for n in names) if symbols is None
                else any(n in symbols for n in names))
        if not want:
            continue
        if isinstance(node, ast.ClassDef):
            out += _class_outline(node, lines)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out += _header_lines(node, lines)
        else:
            out.append(lines[node.lineno - 1])
    return out, "OK" if out else "EMPTY"


def build_readonly_context(editable: list[str], parent_text: Callable[[str], str | None],
                           tracked: set[str], is_test_path: Callable[[str], bool]) -> dict:
    """IMPORT_OUTLINE_V1. Deterministic, label-blind, parent-snapshot only."""
    order: list[str] = []
    wanted: dict[str, set[str] | None] = {}
    ed = set(editable)
    for p in sorted(editable):
        if not p.endswith(".py"):
            continue
        txt = parent_text(p)
        if txt is None:
            continue
        for mp, sym in import_targets(p, txt, tracked):
            if mp in ed or is_test_path(mp) or "/migrations/" in mp or not mp.endswith(".py"):
                continue
            if mp not in wanted:
                order.append(mp)
                wanted[mp] = None if sym is None else {sym}
            elif wanted[mp] is not None:
                if sym is None:
                    wanted[mp] = None
                else:
                    wanted[mp].add(sym)
    parts: list[str] = []
    meta: list[dict] = []
    total = 0
    for mp in order:
        txt = parent_text(mp)
        if txt is None:
            meta.append({"path": mp, "status": "MISSING_AT_PARENT"})
            continue
        lines, st = module_outline(mp, txt, wanted[mp])
        if not lines:
            meta.append({"path": mp, "status": st})
            continue
        body, used, trunc = [], 0, False
        for ln in lines:
            if used + len(ln) + 1 > OUTLINE_MODULE_CAP:
                trunc = True
                break
            body.append(ln)
            used += len(ln) + 1
        block = ([f"===== OUTLINE: {mp} (read-only) ====="] + body
                 + (["# [outline truncated]"] if trunc else [])
                 + [f"===== END OUTLINE: {mp} ====="])
        size = sum(len(x) + 1 for x in block)
        if total + size > OUTLINE_TOTAL_CAP:
            meta.append({"path": mp, "status": "TOTAL_CAP_REACHED"})
            continue
        total += size
        parts += block
        meta.append({"path": mp, "status": "INCLUDED", "lines": len(body), "truncated": trunc,
                     "symbols": sorted(wanted[mp]) if wanted[mp] is not None else "ALL_PUBLIC"})
    text = ""
    if parts:
        text = ("READ-ONLY CONTEXT (NOT EDITABLE): outlines of repository modules imported by "
                "the editable files\n" + "\n".join(parts))
    return {"text": text, "modules": meta, "chars": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}


def verbatim_audit(context_text: str, parent_text: Callable[[str], str | None]) -> list[str]:
    """Every non-marker line of the context must be a verbatim line of its parent module."""
    bad: list[str] = []
    cur: str | None = None
    src: set[str] = set()
    for ln in context_text.splitlines()[1:]:
        if ln.startswith("===== OUTLINE: "):
            cur = ln[len("===== OUTLINE: "):].split(" (read-only)")[0]
            src = set((parent_text(cur) or "").splitlines())
            continue
        if ln.startswith("===== END OUTLINE: ") or ln == "# [outline truncated]":
            continue
        if cur is None or ln not in src:
            bad.append(f"{cur}: {ln[:120]}")
    return bad


# ------------------------------------------------------------------ decision
def thresholds(n_tasks: int) -> dict:
    n = REPS * n_tasks
    return {"n_gold_episodes_per_variant": n, "min_gain_vs_g0": DECISION["min_gain_vs_g0"],
            "max_extra_invalid_vs_g0": DECISION["max_extra_invalid_vs_g0"],
            "floor_resolved_min": math.ceil(DECISION["floor_episode_rate"] * n),
            "floor_tasks_min": math.ceil(DECISION["floor_task_fraction"] * n_tasks),
            "placebo_robust_max": DECISION["placebo_robust_max"]}


def decide(metrics: dict[str, dict], per_task: dict[str, dict[str, int]], n_tasks: int,
           instrument_ok: bool) -> dict:
    """metrics[v] = {gold_robust, gold_invalid, gold_mean_tokens, placebo_robust, tasks_any};
    per_task[v][task] = robust GOLD resolved count over the 3 replicates."""
    th = thresholds(n_tasks)
    if not instrument_ok:
        return {"token": "M14R_INSTRUMENT_FIX", "winner": None, "eligible": [],
                "thresholds": th, "next": "BRAIN_INSTRUMENT_REVIEW"}
    if any(metrics[v]["placebo_robust"] > th["placebo_robust_max"] for v in VARIANT_ORDER):
        return {"token": "M14R_PLACEBO_LEAK_REVIEW", "winner": None, "eligible": [],
                "thresholds": th, "next": "HUMAN_DECISION"}
    g0 = metrics["G0"]
    eligible = []
    checks = {}
    for v in ("G1", "G2", "G3"):
        m = metrics[v]
        better = sum(per_task[v][t] > per_task["G0"][t] for t in per_task["G0"])
        worse = sum(per_task[v][t] < per_task["G0"][t] for t in per_task["G0"])
        ok = {"gain": m["gold_robust"] - g0["gold_robust"] >= th["min_gain_vs_g0"],
              "invalid": m["gold_invalid"] - g0["gold_invalid"] <= th["max_extra_invalid_vs_g0"],
              "direction": better >= worse}
        checks[v] = dict(ok, better_tasks=better, worse_tasks=worse)
        if all(ok.values()):
            eligible.append(v)
    if eligible:
        winner = sorted(eligible, key=lambda v: (-metrics[v]["gold_robust"],
                                                 metrics[v]["gold_mean_tokens"],
                                                 VARIANT_ORDER.index(v)))[0]
    else:
        winner = "G0"
    w = metrics[winner]
    floor = (w["gold_robust"] >= th["floor_resolved_min"]
             and w["tasks_any"] >= th["floor_tasks_min"])
    return {"token": "M14R_FLOOR_MET" if floor else "M14R_FLOOR_NOT_MET", "winner": winner,
            "eligible": eligible, "checks": checks, "thresholds": th,
            "next": ("HUMAN_DECISION_THEN_M15_DESIGN_AMENDMENT" if floor
                     else "HUMAN_DECISION_WP2_RESHAPE")}
