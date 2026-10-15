#!/usr/bin/env python3
"""R4 Framework-Semantics Audit over the exact frozen Full-D7 population (144/219).

Mission: M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144 (read-mostly audit).

Deterministic, read-only audit of historical Django/framework semantics for every
exact target commit represented by the frozen Full-D7 population.  It:

1. verifies the frozen population identity / ordered-membership hash / counts;
2. reads exact historical Git objects from the local WSL Saleor object store
   (``/opt/wp2_v2/saleor-cache``) — never a working tree;
3. classifies, per distinct target commit, the repository-authored Django
   settings semantics for manage commands and for pytest execution;
4. compares them with the CURRENT hardcoded framework-gate semantics in the
   qualified behavioral runner
   (``scripts/r4_behavioral_calibration_n12_r2.py`` line 861:
   ``python manage.py check --settings=saleor.tests.settings``);
5. defines a small deterministic framework-semantics signature set and maps the
   exact unit/task membership of every signature;
6. computes the exact CURRENT_GATE_MATCH / CURRENT_GATE_MISMATCH /
   SEMANTICS_UNRESOLVED impact sets (with separate 1..55 / 56 / 57..144 views);
7. inventories every hardcoded current-harness assumption that can vary
   historically and classifies each assumption's historical validity.

This mission NEVER repairs the gate, never runs a unit, never uses Docker, and
never acquires anything over the network.  It only generates additive audit
evidence for Phase-2 design review.

The Git-object probe is deterministic: the same WSL object store and the same
commit list always produce byte-identical raw evidence (only the frozen
generation timestamp is excluded from the deterministic payload).
"""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
R4_DIR = PROJECT / "research" / "env-canon-r4"
CENSUS_PATH = R4_DIR / "R4_I6_CORRECTED_ZERO_CONTAINER_CENSUS_144.json"
PROBE_TSV = R4_DIR / "R4_FRAMEWORK_SEMANTICS_PROBE_219.tsv"
RUNNER = PROJECT / "scripts" / "r4_behavioral_calibration_n12_r2.py"

WSL_DISTRO = "Ubuntu-24.04"
WSL_REPO = "/opt/wp2_v2/saleor-cache"

EXPECTED_POPULATION_IDENTITY = "ce51d2ec0eb28f6b720fbab13a852618e2de0f0a1111a3cc19dc64b1d19defac"
EXPECTED_MEMBERSHIP_HASH = "8eb4a7242e12bb03715adac5fffdea2e4340585843fc137ececd38952ad6a19e"
EXPECTED_N_UNITS = 144
EXPECTED_N_TASKS = 219

# Current hardcoded framework-gate semantics (qualified Attempt-6 runner).
CURRENT_MANAGE_GATE_CMD = "python manage.py check --settings=saleor.tests.settings"
CURRENT_MANAGE_GATE_SETTINGS = "saleor.tests.settings"
CURRENT_MANAGE_GATE_LINE = "scripts/r4_behavioral_calibration_n12_r2.py:861"
CURRENT_PYTEST_GATE_CMD = "python -m pytest --collect-only -q"
CURRENT_PYTEST_GATE_LINE = "scripts/r4_behavioral_calibration_n12_r2.py:868"
CURRENT_IMPORT_GATE_CMD = "python -c \"import saleor\""
CURRENT_IMPORT_GATE_LINE = "scripts/r4_behavioral_calibration_n12_r2.py:857"

SCHEMA_VERSION = "env-canon-r4/framework-semantics-audit/1.0"


# ---------------------------------------------------------------------------
# Deterministic git-object probe (WSL, read-only)
# ---------------------------------------------------------------------------
PROBE_SCRIPT = r"""
cd /opt/wp2_v2/saleor-cache || exit 2
probe() {
  local commit="$1"
  local manage_present=0 setup_cfg_present=0 pytest_ini_present=0
  local pyproject_present=0 tox_ini_present=0
  local saleor_settings_present=0 tests_settings_present=0 saleor_tests_settings_present=0
  local saleor_init_present=0 tests_init_present=0 saleor_tests_init_present=0
  local conftest_present=0
  local manage_b64="" setup_cfg_b64="" pytest_ini_b64="" pyproject_b64="" tox_ini_b64=""

  git cat-file -e "$commit:manage.py" 2>/dev/null && manage_present=1
  git cat-file -e "$commit:setup.cfg" 2>/dev/null && setup_cfg_present=1
  git cat-file -e "$commit:pytest.ini" 2>/dev/null && pytest_ini_present=1
  git cat-file -e "$commit:pyproject.toml" 2>/dev/null && pyproject_present=1
  git cat-file -e "$commit:tox.ini" 2>/dev/null && tox_ini_present=1
  git cat-file -e "$commit:saleor/settings.py" 2>/dev/null && saleor_settings_present=1
  git cat-file -e "$commit:tests/settings.py" 2>/dev/null && tests_settings_present=1
  git cat-file -e "$commit:saleor/tests/settings.py" 2>/dev/null && saleor_tests_settings_present=1
  git cat-file -e "$commit:saleor/__init__.py" 2>/dev/null && saleor_init_present=1
  git cat-file -e "$commit:tests/__init__.py" 2>/dev/null && tests_init_present=1
  git cat-file -e "$commit:saleor/tests/__init__.py" 2>/dev/null && saleor_tests_init_present=1
  git cat-file -e "$commit:conftest.py" 2>/dev/null && conftest_present=1

  [ "$manage_present" = "1" ] && manage_b64=$(git show "$commit:manage.py" | base64 -w0)
  [ "$setup_cfg_present" = "1" ] && setup_cfg_b64=$(git show "$commit:setup.cfg" | base64 -w0)
  [ "$pytest_ini_present" = "1" ] && pytest_ini_b64=$(git show "$commit:pytest.ini" | base64 -w0)
  [ "$pyproject_present" = "1" ] && pyproject_b64=$(git show "$commit:pyproject.toml" | base64 -w0)
  [ "$tox_ini_present" = "1" ] && tox_ini_b64=$(git show "$commit:tox.ini" | base64 -w0)

  local cdate=""
  cdate=$(git show -s --format=%ci "$commit" 2>/dev/null | tr -d '\n')

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$commit" "$manage_present" "$setup_cfg_present" "$pytest_ini_present" \
    "$pyproject_present" "$tox_ini_present" "$saleor_settings_present" \
    "$tests_settings_present" "$saleor_tests_settings_present" "$saleor_init_present" \
    "$tests_init_present" "$saleor_tests_init_present" "$conftest_present" \
    "$cdate" "$manage_b64" "$setup_cfg_b64" "$pytest_ini_b64" "$pyproject_b64" "$tox_ini_b64"
}

while IFS= read -r c; do
  [ -z "$c" ] && continue
  probe "$c"
done < "$1"
"""


def probe_git_objects(commits: list[str]) -> list[dict[str, str]]:
    """Run the deterministic git-object probe in WSL; return raw evidence rows.

    ``commits`` must be LF-only lines.  Fail closed on any WSL error or on a
    row-count mismatch (a missing probe is never silently skipped).
    """
    import tempfile

    temp_dir = Path(tempfile.gettempdir()) / "opencode"
    temp_dir.mkdir(parents=True, exist_ok=True)
    commits_path = temp_dir / "r4_fs_audit_commits.txt"
    script_path = temp_dir / "r4_fs_audit_probe.sh"
    commits_path.write_text("\n".join(sorted(set(commits))) + "\n", encoding="utf-8", newline="\n")
    script_path.write_text(PROBE_SCRIPT, encoding="utf-8", newline="\n")
    linux_script = _translate_windows_to_linux(script_path)
    linux_commits = _translate_windows_to_linux(commits_path)
    r = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", linux_script, linux_commits],
        capture_output=True,
        text=True,
        timeout=600,
    )
    if r.returncode != 0:
        raise RuntimeError(f"WSL probe failed rc={r.returncode}: {r.stderr[:4000]}")
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    if len(lines) != len(set(commits)):
        raise RuntimeError(
            f"probe row count {len(lines)} != distinct commits {len(set(commits))}"
        )
    cols = [
        "commit", "manage", "setup_cfg", "pytest_ini", "pyproject", "tox_ini",
        "saleor_settings", "tests_settings", "saleor_tests_settings", "saleor_init",
        "tests_init", "saleor_tests_init", "conftest", "cdate",
        "manage_b64", "setup_cfg_b64", "pytest_ini_b64", "pyproject_b64", "tox_ini_b64",
    ]
    out: list[dict[str, str]] = []
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) != len(cols):
            raise RuntimeError(f"probe row column mismatch ({len(parts)} != {len(cols)}): {ln[:200]}")
        out.append(dict(zip(cols, parts, strict=False)))
    return out


def _translate_windows_to_linux(path: Path) -> str:
    """Map a Windows temp path to the WSL /mnt path for the default distro."""
    p = str(path.resolve()).replace("\\", "/")
    if ":" in p.split("/", 1)[0]:
        drive, rest = p.split(":", 1)
        return f"/mnt/{drive.lower()}{rest}"
    return p


def _b64(text: str) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Deterministic semantics extraction (pure functions)
# ---------------------------------------------------------------------------
def manage_settings_semantics(manage_text: str) -> dict[str, str]:
    """Extract manage.py DJANGO_SETTINGS_MODULE behaviour (statically visible)."""
    if not manage_text.strip():
        return {"mode": "NO_MANAGE_CONTENT", "module": "UNRESOLVED"}
    setdefault = re.findall(
        r'setdefault\(\s*["\']DJANGO_SETTINGS_MODULE["\']\s*,\s*["\']([^"\']+)["\']',
        manage_text,
    )
    if setdefault:
        return {"mode": "SETDEFAULT_LITERAL", "module": setdefault[0]}
    assign = re.findall(r'DJANGO_SETTINGS_MODULE\s*=\s*["\']([^"\']+)["\']', manage_text)
    if assign:
        return {"mode": "ASSIGN_LITERAL", "module": assign[0]}
    if re.search(r"os\.environ\.(?:get|setdefault)\([\"']DJANGO_SETTINGS_MODULE", manage_text):
        return {"mode": "ENVIRONMENT_DYNAMIC", "module": "DYNAMIC"}
    if re.search(r"DJANGO_SETTINGS_MODULE", manage_text):
        return {"mode": "REFERENCED_NOT_LITERAL", "module": "UNRESOLVED"}
    return {"mode": "NONE_STATIC", "module": "NONE"}


def pytest_ds_modules(setup_cfg: str, pytest_ini: str, pyproject: str) -> list[str]:
    """Collect every ``--ds=<module>`` found in pytest config files (in order)."""
    found: list[str] = []
    for content in (setup_cfg, pytest_ini, pyproject):
        if not content:
            continue
        for m in re.finditer(r"--ds\s*=\s*([^\s\"',\]]+)", content):
            module = m.group(1).strip()
            if module not in found:
                found.append(module)
    return found


def mypy_django_settings(setup_cfg: str, pyproject: str) -> list[str]:
    """Collect ``django_settings_module`` references (mypy-django plugin)."""
    found: list[str] = []
    for content in (setup_cfg, pyproject):
        if not content:
            continue
        for m in re.finditer(r"django_settings_module\s*=\s*([^\s]+)", content):
            module = m.group(1).strip()
            if module not in found:
                found.append(module)
    return found


def tox_manage_commands(tox_ini: str) -> list[str]:
    """Collect manage.py / django-admin commands authored in tox.ini."""
    if not tox_ini:
        return []
    out: list[str] = []
    for m in re.finditer(r"(?:\bpython\s+)?(?:\./)?manage\.py\s+([a-z_]+)", tox_ini):
        cmd = m.group(1)
        if cmd not in out:
            out.append(cmd)
    return out


def settings_layout_family(row: dict[str, str]) -> str:
    """Deterministic settings-layout family from Git-tree existence evidence."""
    saleor_tests = row["saleor_tests_settings"] == "1"
    top_tests = row["tests_settings"] == "1"
    if saleor_tests and not top_tests:
        return "SALEOR_PACKAGE_TESTS_SETTINGS"
    if top_tests and not saleor_tests:
        return "TOP_LEVEL_TESTS_SETTINGS"
    if saleor_tests and top_tests:
        return "BOTH_SETTINGS_MODULES"
    return "SALEOR_SETTINGS_ONLY"


def classify_commit(row: dict[str, str]) -> dict:
    """Deterministic per-commit framework-semantics record (STEP C)."""
    manage = manage_settings_semantics(_b64(row["manage_b64"]))
    setup_cfg = _b64(row["setup_cfg_b64"])
    pytest_ini = _b64(row["pytest_ini_b64"])
    pyproject = _b64(row["pyproject_b64"])
    tox_ini = _b64(row["tox_ini_b64"])

    pytest_modules = pytest_ds_modules(setup_cfg, pytest_ini, pyproject)
    mypy_modules = mypy_django_settings(setup_cfg, pyproject)

    forced_manage_settings_exists = row["saleor_tests_settings"] == "1"
    # Repository-authored pytest settings module (prefer the explicitly authored --ds).
    repo_pytest_module = pytest_modules[0] if pytest_modules else "NONE_AUTHORED"
    # current manage-gate settings module agrees with repo-authored pytest settings.
    current_manage_semantics = (
        "MATCH"
        if forced_manage_settings_exists and repo_pytest_module == CURRENT_MANAGE_GATE_SETTINGS
        else "MISMATCH"
    )
    if not forced_manage_settings_exists:
        current_manage_semantics = "MISMATCH"

    return {
        "commit": row["commit"],
        "commit_date": row["cdate"],
        "manage_py_present": row["manage"] == "1",
        "manage_settings_mode": manage["mode"],
        "manage_default_settings_module": manage["module"],
        "pytest_ini_present": row["pytest_ini"] == "1",
        "pyproject_present": row["pyproject"] == "1",
        "tox_ini_present": row["tox_ini"] == "1",
        "pytest_settings_modules_authored": pytest_modules,
        "repo_pytest_settings_module": repo_pytest_module,
        "mypy_django_settings_modules": mypy_modules,
        "tox_manage_commands": tox_manage_commands(tox_ini),
        "saleor_settings_present": row["saleor_settings"] == "1",
        "tests_settings_present": row["tests_settings"] == "1",
        "saleor_tests_settings_present": forced_manage_settings_exists,
        "current_forced_manage_settings_module": CURRENT_MANAGE_GATE_SETTINGS,
        "current_forced_manage_settings_exists": forced_manage_settings_exists,
        "current_manage_semantics_matches_repository": current_manage_semantics,
        "settings_layout_family": settings_layout_family(row),
    }


def commit_signature(rec: dict) -> str:
    """Deterministic signature id from the evidence-only semantics fields."""
    fields = [
        "manage_py_present",
        "manage_default_settings_module",
        "repo_pytest_settings_module",
        "current_forced_manage_settings_exists",
        "current_manage_semantics_matches_repository",
        "settings_layout_family",
    ]
    key = json.dumps([rec.get(f) for f in fields], sort_keys=True)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Population (reuse frozen census order; never resample)
# ---------------------------------------------------------------------------
def load_census_units() -> list[dict[str, Any]]:
    census = json.loads(CENSUS_PATH.read_text(encoding="utf-8"))
    if census.get("population_identity_sha256") != EXPECTED_POPULATION_IDENTITY:
        raise RuntimeError("census population identity mismatch")
    units = census["units"]
    if len(units) != EXPECTED_N_UNITS:
        raise RuntimeError(f"census units != {EXPECTED_N_UNITS}")
    ids = [str(u["validation_unit_id"]) for u in units]
    if hashlib.sha256(
        json.dumps(ids, separators=(",", ":")).encode("utf-8")
    ).hexdigest() != EXPECTED_MEMBERSHIP_HASH:
        raise RuntimeError("ordered membership hash mismatch")
    return list(units)


def unit_records() -> list[dict]:
    """Per-unit audit records (index, id, tasks, commits, era, route, lock)."""
    units = load_census_units()
    out = []
    for i, u in enumerate(units, start=1):
        member = u.get("member_task_records", [])
        out.append(
            {
                "calibration_index": i,
                "validation_unit_id": u["validation_unit_id"],
                "member_task_ids": list(u.get("member_tasks", [])),
                "member_target_commits": [m["target_commit"] for m in member],
                "python_era": u.get("python_era"),
                "python_version": u.get("python_version"),
                "lock_type": u.get("lock_type"),
                "install_route": u.get("install_route"),
                "docker_profile_id": u.get("docker_profile_id"),
                "native_profile_id": u.get("native_profile_id"),
                "terminal_classification": u.get("terminal_classification"),
            }
        )
    return out


def account_tasks() -> int:
    return sum(len(u["member_task_ids"]) for u in unit_records())


# ---------------------------------------------------------------------------
# Harness assumption inventory (STEP E)
# ---------------------------------------------------------------------------
def assumption_inventory(rows: list[dict]) -> list[dict]:
    """Classify every current-harness Django/framework assumption historically.

    ``rows`` are the raw probe rows (one per commit) used for population-wide
    support evidence.  Classification is deterministic and evidence-backed.
    """
    n = len(rows)
    manage_present = sum(1 for r in rows if r["manage"] == "1")
    saleor_init = sum(1 for r in rows if r["saleor_init"] == "1")
    pyproject_present = sum(1 for r in rows if r["pyproject"] == "1")
    pytest_ini_present = sum(1 for r in rows if r["pytest_ini"] == "1")
    saleor_tests_present = sum(1 for r in rows if r["saleor_tests_settings"] == "1")

    def inv(name: str, classification: str, evidence: str) -> dict[str, str]:
        return {
            "assumption": name,
            "classification": classification,
            "population_evidence": evidence,
        }

    return [
        inv(
            "import package 'saleor' exists and imports (python -c 'import saleor')",
            "HISTORICALLY_UNIVERSAL",
            f"saleor/__init__.py present in {saleor_init}/{n} commits",
        ),
        inv(
            "manage.py exists at repository root (else MANAGE_RC=SKIP)",
            "HISTORICALLY_UNIVERSAL",
            f"manage.py present in {manage_present}/{n} commits",
        ),
        inv(
            "forced manage settings module 'saleor.tests.settings' exists and is a valid "
            "Django settings module (python manage.py check --settings=saleor.tests.settings)",
            "HISTORICALLY_FALSE_FOR_SOME_POPULATION",
            f"saleor/tests/settings.py present in {saleor_tests_present}/{n} commits; "
            "absent in the remaining commits (includes Unit-56 commit 8220a53473bb)",
        ),
        inv(
            "pytest triggered only when pytest.ini OR pyproject.toml exists "
            "(python -m pytest --collect-only -q)",
            "HISTORICALLY_CONDITIONAL",
            f"pyproject.toml present in {pyproject_present}/{n}; pytest.ini in "
            f"{pytest_ini_present}/{n} (gate fires when either exists)",
        ),
        inv(
            "pytest --collect-only inherits repository-authored pytest --ds config "
            "(gate does not force a settings module)",
            "HISTORICALLY_UNIVERSAL",
            "no forced --ds in CURRENT_PYTEST_GATE_CMD; repository-authored --ds "
            "resolves within each exact tree (verified per commit)",
        ),
        inv(
            "working directory = each materialized member-task worktree root before smoke",
            "HISTORICALLY_UNIVERSAL",
            "smoke cd's into /wt{i} for each member task; manage.py + configs probed "
            "at root of each exact tree",
        ),
        inv(
            "import/manage/pytest smoke rc parsing keys map 1:1 to repository-authored "
            "semantics (no silent remap)",
            "HISTORICALLY_UNIVERSAL",
            "IMPORT_RC_/MANAGE_RC_/PYTEST_RC_ markers parsed per worktree without "
            "semantic reinterpretation",
        ),
    ]


# ---------------------------------------------------------------------------
# Audit driver
# ---------------------------------------------------------------------------
def audit(run_probe: bool = True) -> dict:
    """Run the full deterministic audit and return the payload."""
    units = unit_records()
    distinct_commits = sorted({c for u in units for c in u["member_target_commits"]})
    if len(distinct_commits) != EXPECTED_N_TASKS:
        raise RuntimeError(f"distinct commits {len(distinct_commits)} != 219")

    rows = probe_git_objects(distinct_commits) if run_probe else _read_probe_tsv(distinct_commits)

    if len(rows) != len(distinct_commits):
        raise RuntimeError(f"probe rows {len(rows)} != distinct commits {len(distinct_commits)}")
    by_commit = {r["commit"]: r for r in rows}
    for c in distinct_commits:
        if c not in by_commit:
            raise RuntimeError(f"missing probe evidence for {c} (fail closed)")

    commit_records: dict[str, dict] = {}
    signatures: dict[str, list[str]] = {}
    for c in distinct_commits:
        rec = classify_commit(by_commit[c])
        commit_records[c] = rec
        sig = commit_signature(rec)
        signatures.setdefault(sig, []).append(c)

    sig_defs: dict[str, dict] = {}
    for sig, commits in sorted(signatures.items()):
        exemplar = commit_records[commits[0]]
        sig_defs[sig] = {
            "signature_id": sig,
            "n_commits": len(commits),
            "n_tasks": len(commits),
            "fields": {
                "manage_py_present": exemplar["manage_py_present"],
                "manage_default_settings_module": exemplar["manage_default_settings_module"],
                "repo_pytest_settings_module": exemplar["repo_pytest_settings_module"],
                "current_forced_manage_settings_exists": exemplar["current_forced_manage_settings_exists"],
                "current_manage_semantics_matches_repository": exemplar[
                    "current_manage_semantics_matches_repository"
                ],
                "settings_layout_family": exemplar["settings_layout_family"],
            },
        }

    # per-unit signature membership + impact classification
    per_unit: list[dict] = []
    impact: dict[str, list[int]] = {"CURRENT_GATE_MATCH": [], "CURRENT_GATE_MISMATCH": [], "SEMANTICS_UNRESOLVED": []}
    for u in units:
        idx = u["calibration_index"]
        commit_sigs = []
        semantics_states = []
        for c in u["member_target_commits"]:
            rec = commit_records[c]
            commit_sigs.append(commit_signature(rec))
            semantics_states.append(rec["current_manage_semantics_matches_repository"])
        state = "CURRENT_GATE_MATCH"
        if any(s == "MISMATCH" for s in semantics_states):
            state = "CURRENT_GATE_MISMATCH"
        elif any(s == "UNRESOLVED" for s in semantics_states):
            state = "SEMANTICS_UNRESOLVED"
        impact[state].append(idx)
        per_unit.append(
            {
                **u,
                "commit_signatures": commit_sigs,
                "per_commit_semantics": semantics_states,
                "impact_class": state,
            }
        )

    ranges = {
        "units_1_55": [i for i in impact["CURRENT_GATE_MISMATCH"] if 1 <= i <= 55],
        "unit_56": [i for i in impact["CURRENT_GATE_MISMATCH"] if i == 56],
        "units_57_144": [i for i in impact["CURRENT_GATE_MISMATCH"] if 57 <= i <= 144],
    }

    strata_counts: Counter[str] = Counter()
    for u in unit_records():
        strata_counts[f"{u['python_era']}_{u['lock_type']}"] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "mission_id": "M17_D7_R4_FRAMEWORK_SEMANTICS_AUDIT_144",
        "frozen_source_head": "def15aefde83ba9d590133b5215413bff183aa11",
        "population_identity": EXPECTED_POPULATION_IDENTITY,
        "ordered_membership_hash": EXPECTED_MEMBERSHIP_HASH,
        "wsl_repo_path": WSL_REPO,
        "audit_method": "deterministic git-object census over exact frozen population; "
        "no worktree materialization, no Docker, no network, no unit execution, no repair",
        "current_framework_gate": {
            "manage_command": CURRENT_MANAGE_GATE_CMD,
            "manage_command_location": CURRENT_MANAGE_GATE_LINE,
            "forced_manage_settings_module": CURRENT_MANAGE_GATE_SETTINGS,
            "pytest_command": CURRENT_PYTEST_GATE_CMD,
            "pytest_command_location": CURRENT_PYTEST_GATE_LINE,
            "import_command": CURRENT_IMPORT_GATE_CMD,
            "import_command_location": CURRENT_IMPORT_GATE_LINE,
        },
        "accounting": {
            "n_validation_units": len(units),
            "n_mapped_tasks": EXPECTED_N_TASKS,
            "n_distinct_commits": len(distinct_commits),
            "strata_counts": dict(sorted(strata_counts.items())),
        },
        "per_commit_records": commit_records,
        "per_unit_records": per_unit,
        "signature_definitions": sig_defs,
        "signature_membership": {s: sorted(cs) for s, cs in sorted(signatures.items())},
        "signature_unit_counts": {
            s: sum(1 for u in per_unit if s in u["commit_signatures"]) for s in sorted(sig_defs)
        },
        "hardcoded_assumption_inventory": assumption_inventory(rows),
        "impact_sets": {k: sorted(v) for k, v in impact.items()},
        "impact_ranges": ranges,
        "unresolved_cases": [],
        "evidence_files": {
            "probe_tsv": str(PROBE_TSV.relative_to(PROJECT)),
            "probe_tsv_sha256": _sha256_file(PROBE_TSV),
        },
        "generated_utc": datetime.now(UTC).isoformat(),
    }


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_probe_tsv(distinct_commits: list[str]) -> list[dict[str, str]]:
    """Read the frozen probe evidence TSV (deterministic rerun without WSL)."""
    if not PROBE_TSV.is_file():
        raise RuntimeError(f"frozen probe TSV missing: {PROBE_TSV} (fail closed)")
    cols = [
        "commit", "manage", "setup_cfg", "pytest_ini", "pyproject", "tox_ini",
        "saleor_settings", "tests_settings", "saleor_tests_settings", "saleor_init",
        "tests_init", "saleor_tests_init", "conftest", "cdate",
        "manage_b64", "setup_cfg_b64", "pytest_ini_b64", "pyproject_b64", "tox_ini_b64",
    ]
    rows: list[dict[str, str]] = []
    with PROBE_TSV.open(encoding="utf-8", newline="") as fh:
        for parts in csv.reader(fh, delimiter="\t"):
            if not parts or not parts[0].strip():
                continue
            if len(parts) != len(cols):
                raise RuntimeError(f"probe TSV column mismatch: {len(parts)}")
            rows.append(dict(zip(cols, parts, strict=False)))
    got = {r["commit"] for r in rows}
    want = set(distinct_commits)
    if got != want:
        raise RuntimeError(f"probe TSV coverage mismatch: missing {sorted(want - got)}")
    return rows


def deterministic_payload(payload: dict) -> str:
    """Canonical JSON of everything except the excluded timestamp field."""
    copy = dict(payload)
    copy.pop("generated_utc", None)
    return json.dumps(copy, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="R4 framework-semantics audit (144/219)")
    ap.add_argument("--no-probe", action="store_true", help="read frozen probe TSV instead of probing WSL")
    ap.add_argument("--write-tsv", metavar="PATH", help="write probe evidence TSV to PATH")
    args = ap.parse_args()

    units = unit_records()
    distinct_commits = sorted({c for u in units for c in u["member_target_commits"]})
    if args.write_tsv:
        rows = probe_git_objects(distinct_commits)
        with open(args.write_tsv, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t")
            for r in rows:
                w.writerow([r[k] for k in [
                    "commit", "manage", "setup_cfg", "pytest_ini", "pyproject", "tox_ini",
                    "saleor_settings", "tests_settings", "saleor_tests_settings", "saleor_init",
                    "tests_init", "saleor_tests_init", "conftest", "cdate",
                    "manage_b64", "setup_cfg_b64", "pytest_ini_b64", "pyproject_b64", "tox_ini_b64",
                ]])
        print(f"PROBE_TSV_WRITTEN {args.write_tsv} rows={len(rows)}")
        return 0

    payload = audit(run_probe=not args.no_probe)

    # emit additive evidence in the repo (signatures first: its hash is stable)
    out_json = R4_DIR / "R4_FRAMEWORK_SEMANTICS_AUDIT_144.json"
    out_sig = R4_DIR / "R4_FRAMEWORK_SEMANTICS_SIGNATURES_144.json"
    out_sig.write_text(
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "population_identity": EXPECTED_POPULATION_IDENTITY,
                "signature_definitions": payload["signature_definitions"],
                "signature_membership": payload["signature_membership"],
                "signature_unit_counts": payload["signature_unit_counts"],
                "impact_sets": payload["impact_sets"],
                "impact_ranges": payload["impact_ranges"],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # hashes of the generated evidence files (non-self-referential: probe TSV +
    # signatures JSON; the audit JSON itself is intentionally excluded because
    # embedding its own hash would be circular and break deterministic reruns).
    payload["evidence_files"].update(
        {
            "signatures_json": out_sig.name,
            "signatures_json_sha256": _sha256_file(out_sig),
        }
    )

    payload_hash = sha256_bytes(deterministic_payload(payload).encode("utf-8"))
    payload["deterministic_payload_sha256"] = payload_hash
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    impact = payload["impact_sets"]
    print(
        f"AUDIT_PASS units={len(units)} tasks={EXPECTED_N_TASKS} "
        f"commits={len(distinct_commits)} "
        f"match={len(impact['CURRENT_GATE_MATCH'])} "
        f"mismatch={len(impact['CURRENT_GATE_MISMATCH'])} "
        f"unresolved={len(impact['SEMANTICS_UNRESOLVED'])} "
        f"signatures={len(payload['signature_definitions'])} "
        f"payload_sha256={payload_hash}"
    )
    print(f"AUDIT_JSON {out_json}")
    print(f"SIGNATURES_JSON {out_sig}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
