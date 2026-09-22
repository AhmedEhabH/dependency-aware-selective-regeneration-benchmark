"""WP-1b git gates (AC-4 / AC-10) and launcher gates (tag, pricing, config errors).

ZERO API: git runs against a local bare "origin" in tmp_path; the pricing
metadata call is monkeypatched. The launcher is imported, never run paid.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark.wp1b import git_gate as gg

PROJECT = Path(__file__).resolve().parents[2]


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


@pytest.fixture()
def repo_with_origin(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    _git(tmp_path, "init", "-q", "--bare", str(origin))
    work = tmp_path / "work"
    work.mkdir()
    _git(work, "init", "-q")
    _git(work, "config", "user.email", "t@example.invalid")
    _git(work, "config", "user.name", "t")
    _git(work, "config", "core.autocrlf", "false")
    # isolate from the developer's global git config (signing, hooks)
    _git(work, "config", "commit.gpgsign", "false")
    _git(work, "config", "tag.gpgSign", "false")
    _git(work, "config", "core.hooksPath", str(tmp_path / "no-hooks"))
    (work / "src").mkdir()
    (work / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
    (work / "freeze.json").write_text('{"x": 1}\n', encoding="utf-8")
    _git(work, "add", "-A")
    _git(work, "commit", "-qm", "base")
    _git(work, "remote", "add", "origin", str(origin))
    _git(work, "push", "-q", "origin", "HEAD:refs/heads/main")
    return work


def test_skip_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(gg.SKIP_ENV, raising=False)
    assert gg.skip_allowed(False) is False
    with pytest.raises(gg.GitGateError, match="tests only"):
        gg.skip_allowed(True)
    monkeypatch.setenv(gg.SKIP_ENV, "1")
    assert gg.skip_allowed(True) is True


def test_annotated_tag_on_origin_ok_and_file_in_tag(repo_with_origin: Path) -> None:
    work = repo_with_origin
    _git(work, "tag", "-a", "t1", "-m", "x")
    with pytest.raises(gg.GitGateError, match="not on origin"):
        gg.verify_tag_on_origin(work, "t1")
    _git(work, "push", "-q", "origin", "t1")
    info = gg.verify_tag_on_origin(work, "t1")
    assert info["commit"] == _git(work, "rev-parse", "HEAD")
    # CRLF working copy of a tagged LF file still matches (Windows autocrlf checkouts)
    (work / "freeze.json").write_bytes(b'{"x": 1}\r\n')
    assert gg.verify_file_in_tag(work, "t1", work / "freeze.json")
    (work / "freeze.json").write_text('{"x": 2}\n', encoding="utf-8")
    with pytest.raises(gg.GitGateError, match="!= working tree"):
        gg.verify_file_in_tag(work, "t1", work / "freeze.json")


def test_tag_moved_locally_is_a_failure(repo_with_origin: Path) -> None:
    work = repo_with_origin
    _git(work, "tag", "-a", "t2", "-m", "x")
    _git(work, "push", "-q", "origin", "t2")
    (work / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
    _git(work, "commit", "-qam", "later")
    _git(work, "tag", "-f", "-a", "t2", "-m", "moved")  # re-pointed locally, origin still old
    with pytest.raises(gg.GitGateError, match="differs between local"):
        gg.verify_tag_on_origin(work, "t2")


def test_missing_local_tag_and_unreachable_origin(repo_with_origin: Path, tmp_path: Path) -> None:
    work = repo_with_origin
    with pytest.raises(gg.GitGateError, match="does not exist locally"):
        gg.verify_tag_on_origin(work, "nope")
    _git(work, "tag", "t3")
    _git(work, "remote", "set-url", "origin", str(tmp_path / "does-not-exist.git"))
    with pytest.raises(gg.GitRemoteUnavailableError):
        gg.verify_tag_on_origin(work, "t3")


def test_tree_matches_tag_detects_edits_and_untracked(repo_with_origin: Path) -> None:
    work = repo_with_origin
    _git(work, "tag", "t4")
    gg.verify_tree_matches_tag(work, "t4", ("src",))
    (work / "src" / "new.py").write_text("n = 1\n", encoding="utf-8")
    with pytest.raises(gg.GitGateError, match="untracked"):
        gg.verify_tree_matches_tag(work, "t4", ("src",))
    (work / "src" / "new.py").unlink()
    (work / "src" / "a.py").write_text("a = 3\n", encoding="utf-8")  # uncommitted edit
    with pytest.raises(gg.GitGateError, match="differs from tag"):
        gg.verify_tree_matches_tag(work, "t4", ("src",))


# --------------------------------------------------------------------------- launcher gates
def _cli():  # type: ignore[no-untyped-def]
    sys.path.insert(0, str(PROJECT / "scripts"))
    import wp1b_main_run as cli  # type: ignore[import-not-found]

    return cli


def test_paid_kind_requires_tag() -> None:
    cli = _cli()
    assert cli._tag_gate(None, "main297") == 3
    assert cli._tag_gate(None, "variance") == 3
    assert cli._tag_gate(None, "dry_run") is None
    assert cli._tag_gate("wp1b-this-tag-does-not-exist-anywhere", "main297") == 3


def _record(live: bool, route: bool, ok: bool) -> tuple[bool, dict[str, object]]:
    rec: dict[str, object] = {"live_metadata_available": live, "deepinfra_turbo_present": route, "no_drift": ok}
    return ok, rec


@pytest.mark.parametrize(
    ("resume", "live", "route", "ok", "expected"),
    [
        (False, True, True, True, None),
        (False, False, False, False, 4),   # fresh: metadata unreachable -> retry later
        (False, True, False, False, 3),    # fresh: route missing -> STOP
        (False, True, True, False, 3),     # fresh: list-price drift -> STOP
        (True, False, False, False, None),  # resume: unreachable -> continue
        (True, True, False, False, 4),     # resume: route missing -> resumable infra halt
        (True, True, True, False, None),   # resume: price drift -> recorded, continue
    ],
)
def test_pricing_gate_fresh_vs_resume(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, resume: bool,
                                      live: bool, route: bool, ok: bool, expected: int | None) -> None:
    cli = _cli()
    out = tmp_path / "run"
    out.mkdir()
    if resume:
        (out / "pricing_preflight.json").write_text('{"no_drift": true}', encoding="utf-8")
        (out / "run_state.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(cli, "_pricing_preflight", lambda: _record(live, route, ok))
    extra: dict[str, object] = {}
    assert cli._pricing_gate(out, extra, skip=False) == expected
    target = "pricing_preflight_last_resume.json" if resume else "pricing_preflight.json"
    assert target in extra  # the fresh-run record is never overwritten on resume


def test_launcher_config_error_is_exit_3_not_traceback(tmp_path: Path) -> None:
    driver = tmp_path / "drv.py"
    driver.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(PROJECT)!r}); sys.path.insert(0, {str(PROJECT / 'src')!r})\n"
        f"sys.path.insert(0, {str(PROJECT / 'scripts')!r})\n"
        "import wp1b_main_run as cli\n"
        "from benchmark.wp1b import main_runner as mr\n"
        "def boom(*a, **k):\n"
        "    raise mr.ManifestError('synthetic manifest failure')\n"
        "mr.load_main297_items = boom\n"
        f"print('EXIT', cli.main(['--kind', 'dry_run', '--out-dir', {str(tmp_path / 'o')!r}]))\n",
        encoding="utf-8")
    env = {k: v for k, v in os.environ.items() if k != gg.SKIP_ENV}
    out = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True, timeout=300, env=env)
    assert "EXIT 3" in out.stdout and "CONFIG ERROR" in out.stdout, out.stdout + out.stderr


def test_key_usage_remaining_is_min_of_sources() -> None:
    sys.path.insert(0, str(PROJECT / "scripts"))
    import wp1b_openrouter_key_usage as ku  # type: ignore[import-not-found]

    assert ku.remaining_usd({}) is None
    assert ku.remaining_usd({"limit_remaining_usd": 30.0}) == 30.0
    assert ku.remaining_usd({"limit_remaining_usd": None, "credits_total_usd": 50, "credits_used_usd": 40}) == 10.0
    assert ku.remaining_usd({"limit_remaining_usd": 30.0, "credits_total_usd": 50, "credits_used_usd": 40}) == 10.0


def test_key_usage_gate_without_key_is_exit_4(tmp_path: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k != "OPENROUTER_API_KEY"}
    cmd = [sys.executable, str(PROJECT / "scripts" / "wp1b_openrouter_key_usage.py"),
           "--out", str(tmp_path / "k.json"), "--require-remaining-usd", "25"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    assert out.returncode == 4, out.stdout + out.stderr
    cmd_no_gate = cmd[:4]
    assert subprocess.run(cmd_no_gate, capture_output=True, text=True, timeout=120, env=env).returncode == 0
