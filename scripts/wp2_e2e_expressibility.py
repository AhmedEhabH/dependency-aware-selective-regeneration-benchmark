#!/usr/bin/env python3
"""Mission-12 H: expressibility freeze (Interface-v2 denominator).

Mechanically derives which GOLD target patches are representable by the
Interface-v2 SEARCH/REPLACE format (envelope extraction + exact or
whitespace-tolerant matching ladder). Persists
research/wp2/e2e_smoke_eng_v2/controls/expressible_population.json.

The denominator is frozen BEFORE any control outcome is read (Mission-12 H4).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))

V2_ROOT = PROJECT / "research" / "wp2" / "e2e_smoke_eng_v2"
SALEOR_CACHE = PROJECT / "dist" / "pilot-repo-cache" / "saleor"

from benchmark.wp2.e2e.patch_format import apply_patch_v2, parse_multi_file_patch_v2  # noqa: E402
from benchmark.wp2.e2e.scopes import commits_of, editable_filter, gold_raw_scope  # noqa: E402
from benchmark.wp2.e2e.spec import SMOKE_TASKS  # noqa: E402
from benchmark.wp2.oracle_semantics_v2 import is_test_path_v2  # noqa: E402


def _git(commit: str, path: str) -> str | None:
    r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "show", f"{commit}:{path}"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def _diff_to_p1(diff_text: str, path: str) -> str:
    hunks: list[tuple[list[str], list[str]]] = []
    old_lines: list[str] = []
    new_lines: list[str] = []
    in_hunk = False
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("@@"):
            if in_hunk and (old_lines or new_lines):
                hunks.append((old_lines, new_lines))
            old_lines, new_lines = [], []
            in_hunk = True
            continue
        if not in_hunk or line.startswith(("diff ", "index ", "---", "+++")):
            continue
        if line.startswith("-"):
            old_lines.append(line[1:])
        elif line.startswith("+"):
            new_lines.append(line[1:])
        else:
            old_lines.append(line[1:])
            new_lines.append(line[1:])
    if in_hunk and (old_lines or new_lines):
        hunks.append((old_lines, new_lines))
    blocks: list[str] = []
    for old, new in hunks:
        blocks.append("<<<<<<< SEARCH\n" + "".join(old) + "=======\n" + "".join(new) + ">>>>>>> REPLACE\n")
    return "FILE: " + path + "\n" + "\n".join(blocks)


def _try_convert_v2(path: str, parent: str, target: str, old: str) -> tuple[str | None, str]:
    """Build P1 with increasing context; verify it parses + applies under v2 ladder."""
    for context in (3, 10, 40, 120, 400):
        ud = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", f"--unified={context}",
                             parent, target, "--", path],
                            capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
        p1 = _diff_to_p1(ud, path)
        try:
            sections, stats = parse_multi_file_patch_v2(p1)
            out, results = apply_patch_v2({path: old}, sections, {path})
            if out[path] == _git(target, path):
                return p1, ""
        except ValueError:
            pass
    return None, "FORMAT_NOT_EXPRESSIBLE"


def main() -> int:
    out = {"artifact": "expressible_population", "head": subprocess.run(
        ["git", "-C", str(PROJECT), "rev-parse", "HEAD"], capture_output=True,
        text=True).stdout.strip(), "per_task": {}, "summary": {}}
    for tid in SMOKE_TASKS:
        parent, target = commits_of(tid)
        r = subprocess.run(["git", "-C", str(SALEOR_CACHE), "diff", "--name-status", parent, target],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        scope = editable_filter(tid, gold_raw_scope(tid))
        editable = set(scope["editable"])
        per_path: dict[str, dict] = {}
        expressible_paths: list[str] = []
        for line in r.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            st, path = parts[0], parts[-1]
            if st != "M":
                per_path[path] = {"reason": f"status={st}", "expressible": False}
                continue
            if is_test_path_v2(path):
                per_path[path] = {"reason": "test-path", "expressible": False}
                continue
            if path not in editable:
                per_path[path] = {"reason": "not-in-editable", "expressible": False}
                continue
            old = _git(parent, path)
            new = _git(target, path)
            if old is None or new is None:
                per_path[path] = {"reason": "missing-at-parent-or-target", "expressible": False}
                continue
            p1, err = _try_convert_v2(path, parent, target, old)
            if p1 is None:
                per_path[path] = {"reason": err, "expressible": False}
                continue
            digest = hashlib.sha256(p1.encode("utf-8")).hexdigest()
            per_path[path] = {"expressible": True, "p1_sha256": digest, "reason": "ok"}
            expressible_paths.append(path)
        out["per_task"][tid] = {
            "paths": per_path,
            "expressible_paths": sorted(expressible_paths),
            "expressible_count": len(expressible_paths),
            "total_modified_non_test": sum(1 for v in per_path.values()
                                           if v["reason"] not in ("status=", "test-path")),
        }
    total_expr = sum(t["expressible_count"] for t in out["per_task"].values())
    total_mod = sum(t["total_modified_non_test"] for t in out["per_task"].values())
    out["summary"] = {"expressible_count": total_expr, "modified_non_test_count": total_mod,
                      "denominator_frozen_before_controls": True}
    (V2_ROOT / "controls").mkdir(parents=True, exist_ok=True)
    dest = V2_ROOT / "controls" / "expressible_population.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"EXPRESSIBLE_POPULATION={dest}")
    print(f"EXPRESSIBLE={total_expr} / MODIFIED_NON_TEST={total_mod}")
    print("HASH=" + hashlib.sha256(dest.read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
