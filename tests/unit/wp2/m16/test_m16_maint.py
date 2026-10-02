"""M16 S3 maintenance helper: nothing protected can ever reach the deletion allow-list."""
from __future__ import annotations

import sys
from pathlib import Path

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_maint as M  # noqa: E402

ANON = "a" * 64


def test_only_anonymous_unreferenced_unprotected_volumes_are_deletable():
    assert M.classify_volume(ANON, [], set())["delete_allowed"] is True
    assert M.classify_volume(ANON, [], set())["classification"] == "REBUILDABLE_CACHE"
    for name, refs, pcv, why in [("wp2-uv-cache", [], set(), "PROTECTED_NAME"),
                                 (ANON, ["wp2-pg"], set(), "REFERENCED_BY_CONTAINER"),
                                 (ANON, [], {ANON}, "USED_BY_PROTECTED_CONTAINER"),
                                 ("pgdata", [], set(), "NAMED_VOLUME"),
                                 ("b" * 63, [], set(), "NAMED_VOLUME"),
                                 (ANON, ["kind_ptolemy"], set(), "REFERENCED_BY_CONTAINER")]:
        c = M.classify_volume(name, refs, pcv)
        assert c["delete_allowed"] is False and why in c["reasons"], (name, c)


def test_no_prune_and_no_compaction_command_is_ever_executed():
    src = (P / "scripts/wp2_m16_maint.py").read_text(encoding="utf-8")
    code = src.split('"""', 2)[2]                       # skip the module docstring
    for bad in ("volume prune", "system prune", "image prune", "container prune"):
        assert bad not in code
    executed = [ln for ln in code.splitlines() if "run([" in ln or "wsl(f" in ln or 'wsl("' in ln]
    for ln in executed:
        assert "Optimize-VHD -Path" not in ln and "compact vdisk" not in ln and "--shutdown" not in ln


def test_size_parser():
    assert M._bytes("1.5GB") == 1_500_000_000 and M._bytes("10MB") == 10_000_000 and M._bytes("0B") == 0
    assert M._bytes(None) is None and M._bytes("n/a") is None


def test_protected_container_inspect_failure_fails_closed(monkeypatch):
    import subprocess

    import pytest
    monkeypatch.setattr(M, "wsl", lambda s, t=300: subprocess.CompletedProcess(s, 1, "", "no such container"))
    with pytest.raises(SystemExit):
        M.protected_container_volumes()
