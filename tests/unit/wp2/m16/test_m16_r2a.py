"""M16 amendment R2A: historical-schema-aware R2 adapter verification and the R2A guard gate.

Runs the REAL scripts/wp2_m16_run.py::adapter_verify against a fake world (no Docker, no WSL, no network,
no frozen benchmark import) and the REAL r2a_gate/pushed_tag against a throw-away git repo + bare origin.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_r2a as r2a  # noqa: E402
from scripts import wp2_m16_run as run  # noqa: E402

CLOSURE = {"mechanism": "poetry", "pins": ["pytest-mock==3.6.1", "pytest-django-queries==1.2.0"],
           "unsupported": [], "pins_sha256": "ab" * 32, "era_key": "py39", "python_version": "3.9", "note": ""}
RECORDED = {"mechanism": "poetry", "n_pins": 2, "pins_sha256": "ab" * 32, "n_unsupported": 0}
DEV_PYPROJECT = "[tool.poetry.dev-dependencies]\npytest-mock = '3.6.1'\n"


def tgt(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:40]


def hist_row(t: str, status: str = "DONE", closure: object = "absent", **manifest) -> dict:
    m = {"install_mode": "LOCK_EXACT", "lockfile_sha256": "L-lock-" + tgt(t), **manifest}
    if closure != "absent":
        m["dev_test_closure"] = closure
    return {"task_id": t, "status": status, "target_commit": tgt(t), "manifest": m}


class FakeWorld:
    """Deterministic stand-in for RealWorld's R2 surface (frozen V3.1 closure, lookups, manifests)."""

    def __init__(self, tasks: list[str], main_rows: dict[str, dict]) -> None:
        self.frozen = {t: copy.deepcopy(CLOSURE) for t in [*tasks, *main_rows]}
        self.adapted = copy.deepcopy(self.frozen)
        self.lookups = {t: {"parent": "d" * 40, "target": tgt(t), "era": "py39"} for t in tasks}
        self.adapted_lookups = copy.deepcopy(self.lookups)
        self.adapted_lookups.update({t: {"parent": r["parent_commit"], "target": r["target_commit"],
                                         "era": r["era_key"]} for t, r in main_rows.items()})
        self.calls: list[str] = []

    def closure(self, t: str, adapted: bool) -> dict:
        return copy.deepcopy((self.adapted if adapted else self.frozen)[t])

    def frozen_lookup(self, t: str) -> dict:
        return dict(self.lookups[t])

    def adapted_lookup(self, t: str) -> dict:
        return dict(self.adapted_lookups[t])

    def target_manifests(self, target: str) -> dict:
        return {"pyproject.toml": DEV_PYPROJECT, "poetry.lock": "lock-" + target}

    def install_mode(self, mf: dict) -> str:
        return "LOCK_EXACT"

    def lock_signature(self, mf: dict) -> str:
        return "L-" + mf["poetry.lock"]

    def commits_exist(self, shas: list[str]) -> dict:
        self.calls.append("commits_exist")
        return {"windows_missing": [], "wsl_missing": []}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated project root: synthetic history file, 2 MAIN rows, fake world; the verifier itself is real."""
    proj = tmp_path / "proj"
    (proj / "research/wp2/harness_v3_2026-09-26").mkdir(parents=True)
    rows = {f"saleor-main-{i}": {"parent_commit": f"{i:040x}", "target_commit": f"{i + 9:040x}",
                                "era_key": "py39"} for i in (1, 2)}
    monkeypatch.setattr(run, "PROJECT", proj)
    monkeypatch.setattr(run, "ADAPTER_REPORT", proj / "research/wp2/m16_v1/adapter/adapter_report.json")
    monkeypatch.setattr(run, "design", lambda: {})
    monkeypatch.setattr(run, "rows220", lambda: copy.deepcopy(rows))
    monkeypatch.setattr(run.adapter, "build_shadow", lambda project, shadow: {"files": {}})
    monkeypatch.setattr(run.adapter, "declares_dev_group",
                        lambda mf: "[tool.poetry.dev-dependencies]" in mf.get("pyproject.toml", ""))

    def setup(records: list[dict]) -> FakeWorld:
        (proj / r2a.HIST_REL).write_text("".join(json.dumps(r) + "\n" for r in records),
                                         encoding="utf-8", newline="\n")
        w = FakeWorld(sorted({r["task_id"] for r in records}), rows)
        monkeypatch.setattr(run, "WORLD", w)
        return w
    return proj, setup


def _run_verify(proj: Path, w: FakeWorld) -> tuple[int | None, dict, str | None]:
    try:
        rc, err = run.adapter_verify(), None
    except run.adapter.AdapterError as exc:
        rc, err = None, str(exc)
    return rc, json.loads(run.ADAPTER_REPORT.read_text(encoding="utf-8")), err


def _hist_bytes(proj: Path) -> str:
    return hashlib.sha256((proj / r2a.HIST_REL).read_bytes()).hexdigest()


# ------------------------------------------------------------------ required regression tests (1-5)
def test_1_historical_record_with_dev_test_closure_is_compared_and_passes(env):
    proj, setup = env
    w = setup([hist_row("eng-a", closure=RECORDED)])
    rc, rep, err = _run_verify(proj, w)
    assert rc == 0 and err is None and rep["verdict"] == "PASS"
    e = rep["eng_identity"]["eng-a"]
    assert e["recorded_closure"] == "MATCH" and e["closure_identical"]
    assert e["recorded_closure_keys_compared"] == list(r2a.BRIEF_KEYS)
    assert rep["r2a"]["provenance_coverage"]["recorded_closure_compared"] == 1


def test_2_historical_record_without_dev_test_closure_passes_on_identity_and_is_not_backfilled(env):
    proj, setup = env
    w = setup([hist_row("eng-a", closure=RECORDED), hist_row("eng-b", status="ENV_INSTALL_BLOCKED"),
               hist_row("eng-c", closure=None)])
    before = _hist_bytes(proj)
    rc, rep, err = _run_verify(proj, w)
    assert rc == 0 and rep["verdict"] == "PASS", err
    assert _hist_bytes(proj) == before                                   # history read, never written
    assert rep["eng_identity"]["eng-b"]["recorded_closure"] == r2a.ABSENT
    assert rep["eng_identity"]["eng-c"]["recorded_closure"] == r2a.NULL
    assert all(rep["eng_identity"][t]["closure_identical"] for t in ("eng-a", "eng-b", "eng-c"))
    sch = rep["r2a"]["historical_schema"]
    assert sch["tasks_without_recorded_closure"] == ["eng-b", "eng-c"]
    assert sch["by_status"]["ENV_INSTALL_BLOCKED"] == {"n": 1, r2a.RECORDED: 0, r2a.ABSENT: 1, r2a.NULL: 0,
                                                       r2a.UNKNOWN: 0}
    cov = rep["r2a"]["provenance_coverage"]
    assert cov["identity_tested"] == 3 and cov["recorded_closure_compared"] == 1


@pytest.mark.parametrize("closure", [RECORDED, "absent"])
def test_3_frozen_adapted_closure_mismatch_fails_with_or_without_recorded_closure(env, closure):
    proj, setup = env
    w = setup([hist_row("eng-a", closure=closure)])
    w.adapted["eng-a"]["pins"] = w.adapted["eng-a"]["pins"][:1]          # adapter changed the closure
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and rep["verdict"] == "FAIL" and "R2 fail-closed" in err
    assert "CLOSURE_FROZEN_ADAPTED_DIFFER" in rep["eng_identity"]["eng-a"]["violations"]


def test_4_recorded_closure_mismatch_fails_where_historical_closure_exists(env):
    proj, setup = env
    w = setup([hist_row("eng-a", closure={**RECORDED, "pins_sha256": "cd" * 32}), hist_row("eng-b")])
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and rep["verdict"] == "FAIL"
    e = rep["eng_identity"]["eng-a"]
    assert e["closure_identical"] and e["recorded_closure"] == "MISMATCH"
    assert e["recorded_closure_mismatch"] == {"pins_sha256": ["cd" * 32, "ab" * 32]}
    assert rep["eng_identity"]["eng-b"]["violations"] == []
    assert any(v.startswith("ENG_IDENTITY:eng-a:RECORDED_CLOSURE_MISMATCH") for v in rep["violations"])


def test_5_main_declared_dev_group_with_mechanism_none_fails(env):
    proj, setup = env
    w = setup([hist_row("eng-a", closure=RECORDED)])
    w.adapted["saleor-main-2"] = {"mechanism": "none", "pins": [], "unsupported": [], "era_key": "py39",
                                  "note": ""}
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and rep["verdict"] == "FAIL"
    assert "DEV_GROUP_DECLARED_BUT_MECHANISM_NONE" in rep["main"]["saleor-main-2"]["violations"]
    assert rep["main"]["saleor-main-1"]["violations"] == [] and len(rep["main"]) == 2


# ------------------------------------------------------------------ preserved independent checks
@pytest.mark.parametrize("breakage,token", [
    ("lookup", "LOOKUP_FROZEN_ADAPTED_DIFFER"),
    ("install_mode", "INSTALL_MODE_DIFFERS_FROM_RECORD"),
    ("lockfile", "LOCKFILE_SHA_DIFFERS_FROM_RECORD")])
def test_preserved_lookup_install_mode_and_lockfile_checks(env, breakage, token):
    proj, setup = env
    row = hist_row("eng-a")
    if breakage == "install_mode":
        row["manifest"]["install_mode"] = "REQUIREMENTS_ONLY"
    if breakage == "lockfile":
        row["manifest"]["lockfile_sha256"] = "other"
    w = setup([row])
    if breakage == "lookup":
        w.adapted_lookups["eng-a"]["era"] = "py312"
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and token in rep["eng_identity"]["eng-a"]["violations"]


def test_main_lookup_mismatch_and_all_rows_still_checked(env):
    proj, setup = env
    w = setup([hist_row("eng-a")])
    w.adapted_lookups["saleor-main-1"]["era"] = "py312"                     # adapter disagrees with the frozen row
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and any(v.startswith("LOOKUP_MISMATCH") for v in rep["main"]["saleor-main-1"]["violations"])
    assert set(rep["main"]) == {"saleor-main-1", "saleor-main-2"} and "commits_exist" in w.calls


@pytest.mark.parametrize("mutate,needle", [
    (lambda r: r["manifest"].pop("install_mode"), "manifest.install_mode"),
    (lambda r: r["manifest"].pop("lockfile_sha256"), "manifest.lockfile_sha256"),
    (lambda r: r.pop("target_commit"), "target_commit"),
    (lambda r: r.pop("manifest"), "manifest"),
    (lambda r: r["manifest"].__setitem__("dev_test_closure", ["poetry"]), "unknown shape")])
def test_schema_outside_the_rule_fails_closed_with_report(env, mutate, needle):
    proj, setup = env
    row = hist_row("eng-a")
    mutate(row)
    w = setup([row, hist_row("eng-b")])
    rc, rep, err = _run_verify(proj, w)
    assert rc is None and rep["verdict"] == "FAIL"
    assert any(v.startswith("HIST_SCHEMA:") and needle in v for v in rep["violations"]), rep["violations"]


def test_parse_history_census_duplicates_and_garbage():
    text = "\n".join([json.dumps(hist_row("a", closure=RECORDED)), "", json.dumps(hist_row("b")),
                      json.dumps(hist_row("a", status="ENV_INSTALL_BLOCKED")), "{not json", "[1]"]) + "\n"
    recs, c = r2a.parse_history(text)
    assert set(recs) == {"a", "b"} and recs["a"]["status"] == "ENV_INSTALL_BLOCKED"   # last wins (kit semantics)
    assert c["duplicates"] == {"a": [1, 4]} and c["n_nonblank_lines"] == 5
    assert c["tasks_with_recorded_closure"] == [] and c["tasks_without_recorded_closure"] == ["a", "b"]
    assert len(c["fatal"]) == 2 and len(c["per_line"]) == 3
    assert r2a.parse_history("")[1]["fatal"] == ["historical file has no records"]


def test_r2a_module_is_pure():
    import ast
    tree = ast.parse((P / "scripts/wp2_m16_r2a.py").read_text(encoding="utf-8"))
    mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
           {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert mods <= {"__future__", "hashlib", "json", "collections", "typing"}, mods


# ------------------------------------------------------------------ amendment record + restart plan
def test_shipped_amendment_record_and_restart_plan():
    rec = json.loads((P / "research/wp2/m16_v1/m16_r2a_adapter_verifier_amendment.json").read_text(encoding="utf-8"))
    assert run.hash_ok(rec) and rec["rule_id"] == r2a.RULE_ID and rec["tag"] == r2a.TAG
    assert rec["amends"]["design_artifact_sha256"] == run.DESIGN_SHA
    assert rec["amends"]["adapter_version"] == run.adapter.ADAPTER_VERSION
    files = set(rec["amended_files"]) | set(rec["added_files"])
    shas = {f: run.norm_sha(P / f) for f in files}
    assert r2a.record_problems(rec, kit_commit=rec["amends"]["kit_commit"], design_sha=run.DESIGN_SHA,
                               files_lf_sha=shas) == []
    old = json.loads((P / "controller/plan_m16_v1_dryrun.json").read_text(encoding="utf-8"))
    new = json.loads((P / "controller/plan_m16_v1_dryrun_r2a.json").read_text(encoding="utf-8"))
    assert new["phases"] == old["phases"]                               # identical phases, rerun from R00
    assert new["id"] != old["id"]
    s_old, s_new = old["settings"], new["settings"]
    assert s_new["state_file"] != s_old["state_file"] and s_new["report_dir"] != s_old["report_dir"]
    assert {k: v for k, v in s_new.items() if k not in ("state_file", "report_dir")} == \
           {k: v for k, v in s_old.items() if k not in ("state_file", "report_dir")}


# ------------------------------------------------------------------ R2A guard gate (real git, bare origin)
def _git(cwd: Path, *a: str) -> str:
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=True).stdout


class _GitGate:
    """Minimal git_gate stand-in with the documented semantics (tag on origin; file in tag == worktree)."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def verify_tag_on_origin(self, project, tag):
        loc = _git(project, "rev-parse", f"refs/tags/{tag}").strip()
        rem = _git(project, "ls-remote", "origin", f"refs/tags/{tag}").split()
        if not rem or rem[0] != loc:
            raise RuntimeError("tag not on origin")
        return {"object": loc}

    def verify_file_in_tag(self, project, tag, path):
        rel = Path(path).resolve().relative_to(Path(project).resolve()).as_posix()
        blob = subprocess.run(["git", "show", f"{tag}:{rel}"], cwd=project, capture_output=True, check=True).stdout
        if blob.replace(b"\r\n", b"\n") != Path(path).read_bytes().replace(b"\r\n", b"\n"):
            raise RuntimeError(f"{rel} differs from {tag}")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root, origin = tmp_path / "r", tmp_path / "o.git"
    root.mkdir()
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    _git(root, "init", "-q", "-b", "main")
    for k, v in (("user.email", "t@x"), ("user.name", "t"), ("core.autocrlf", "false")):
        _git(root, "config", k, v)
    (root / "scripts").mkdir()
    (root / "research/wp2/m16_v1").mkdir(parents=True)
    (root / "scripts/wp2_m16_run.py").write_text("v1\n", encoding="utf-8")
    (root / "scripts/wp2_m16_stats.py").write_text("s\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "kit")
    _git(root, "remote", "add", "origin", str(origin))
    _git(root, "push", "-q", "origin", "main")
    _git(root, "tag", "-a", run.TAGS["kit"], "-m", "kit")
    _git(root, "push", "-q", "origin", f"refs/tags/{run.TAGS['kit']}")
    kit_commit = _git(root, "rev-parse", "HEAD").strip()
    monkeypatch.setattr(run, "PROJECT", root)
    monkeypatch.setattr(run, "R2A_RECORD", root / "research/wp2/m16_v1/m16_r2a_adapter_verifier_amendment.json")
    monkeypatch.setattr(run, "DESIGN_SHA", "d" * 64)
    monkeypatch.setattr(run, "gg", lambda: _GitGate(root))

    def amend(*, push_tag: bool = True, kit: str | None = None) -> dict:
        (root / "scripts/wp2_m16_run.py").write_text("v2-r2a\n", encoding="utf-8")
        (root / "scripts/wp2_m16_r2a.py").write_text("rule\n", encoding="utf-8")
        rec = run.self_hash({
            "artifact": "m16_r2a_adapter_verifier_amendment", "artifact_sha256": "", "rule_id": r2a.RULE_ID,
            "tag": r2a.TAG, "rule_constants_sha256": r2a.rule_constants_sha(),
            "amends": {"kit_commit": kit or kit_commit, "design_artifact_sha256": "d" * 64},
            "amended_files": {"scripts/wp2_m16_run.py": {"kit_lf_sha256": run.text_sha("v1\n"),
                                                         "r2a_lf_sha256": run.text_sha("v2-r2a\n")}},
            "added_files": {"scripts/wp2_m16_r2a.py": run.text_sha("rule\n")}})
        run.write(run.R2A_RECORD, rec)
        _git(root, "add", "-A")
        _git(root, "commit", "-qm", "r2a")
        _git(root, "push", "-q", "origin", "main")
        _git(root, "tag", "-a", r2a.TAG, "-m", "r2a")
        if push_tag:
            _git(root, "push", "-q", "origin", f"refs/tags/{r2a.TAG}")
        return rec
    return root, kit_commit, amend


DESIGN_FILES = {"kit_code_files": ["scripts/wp2_m16_run.py", "scripts/wp2_m16_stats.py"]}


def test_guard_gate_without_record_is_the_original_behaviour(repo):
    root, kit_commit, amend = repo
    assert run.r2a_gate(DESIGN_FILES) == {}


def test_guard_gate_accepts_a_pushed_r2a_tag_descending_from_the_kit(repo):
    root, kit_commit, amend = repo
    amend()
    info = run.r2a_gate(DESIGN_FILES)
    assert info["rule_id"] == r2a.RULE_ID and list(info["amended_files"]) == ["scripts/wp2_m16_run.py"]
    assert run.is_ancestor(kit_commit, info["commit"])
    run.pushed_tag(run.TAGS["kit"], [root / "scripts/wp2_m16_stats.py"])          # unamended file: kit tag
    with pytest.raises(run.Stop):                                                 # amended file != kit tag
        run.pushed_tag(run.TAGS["kit"], [root / "scripts/wp2_m16_run.py"])


def test_guard_gate_refuses_unpushed_tag_tampering_and_wrong_kit(repo):
    root, kit_commit, amend = repo
    amend(push_tag=False)
    with pytest.raises(run.Stop) as e:
        run.r2a_gate(DESIGN_FILES)
    assert e.value.code == run.EXIT_TAG
    _git(root, "push", "-q", "origin", f"refs/tags/{r2a.TAG}")
    run.r2a_gate(DESIGN_FILES)
    (root / "scripts/wp2_m16_run.py").write_text("v3-silent-edit\n", encoding="utf-8")
    with pytest.raises(run.Stop, match="amended file drift"):
        run.r2a_gate(DESIGN_FILES)
    (root / "scripts/wp2_m16_run.py").write_text("v2-r2a\n", encoding="utf-8")
    rec = json.loads(run.R2A_RECORD.read_text(encoding="utf-8"))
    rec["amends"]["kit_commit"] = "0" * 40
    run.write(run.R2A_RECORD, run.self_hash(rec))
    with pytest.raises(run.Stop, match="amends kit commit"):
        run.r2a_gate(DESIGN_FILES)
