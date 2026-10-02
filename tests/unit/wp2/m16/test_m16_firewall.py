"""M16 selector-input firewall: pure predicates in-process, the real audit hook in subprocesses."""
from __future__ import annotations

import socket
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts import wp2_m16_firewall as fw  # noqa: E402

PROJ = str(P)


def test_path_predicate():
    assert fw.path_blocked(P / "research/wp1a/sip_rmcss_per_task_predictions.json", PROJ)
    assert fw.path_blocked(P / "research/wp1b/main-297-2026-09-22/agent_run_records.jsonl", PROJ)
    assert fw.path_blocked(P / "research/wp1b/variance-15x3-2026-09-22/wp1b_agent_predictions.json", PROJ)
    assert fw.path_blocked(P / "research/wp2/m16_v1/opws/plan.json", PROJ)
    assert fw.path_blocked(P.parent / "project-LIGHT-X.zip", PROJ)
    assert fw.path_blocked("D:/wp2_cold/m16_v1/wp2-m16-v1-scopes/research/wp2/m16_v1/opws/plan.json", PROJ)
    assert fw.path_blocked("/x/extract/research/wp1a/sip_rmcss_per_task_predictions.json", PROJ)
    assert not fw.path_blocked("D:/wp2_cold/m16_v1/wp2-m16-v1-ready/research/wp2/m16_v1/m16_ready_membership.json", PROJ)
    assert not fw.path_blocked(P / "research/wp2/wp2_saleor_main297_census_2026-09-22.json", PROJ)
    assert not fw.path_blocked(P / "research/wp1b/wp1b_main_297_manifest.json", PROJ)
    assert not fw.path_blocked(P / "research/wp2/m16_v1/m16_ready_membership.json", PROJ)


def test_argv_and_host_predicates():
    assert fw.argv_blocked(["git", "show", "HEAD:research/wp1a/sip_rmcss_per_task_predictions.json"])
    assert fw.argv_blocked(["wsl", "cat", "/mnt/c/x/research/wp1b/main-297-2026-09-22/a.jsonl"])
    assert not fw.argv_blocked(["git", "rev-parse", "HEAD:research/wp1b"])
    assert fw.host_blocked(("8.8.8.8", 443)) and fw.host_blocked(("api.openrouter.ai", 443))
    assert not fw.host_blocked(("127.0.0.1", 5433)) and not fw.host_blocked(("::1", 1))


def _child(body: str) -> subprocess.CompletedProcess:
    code = textwrap.dedent(f"""
        import sys, os, socket, subprocess
        sys.path[:0] = [{PROJ!r}, {PROJ + '/src'!r}]
        from pathlib import Path
        from scripts import wp2_m16_firewall as fw
        fw.install(Path({PROJ!r}))
        """) + textwrap.dedent(body)
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=PROJ, timeout=120)


def test_hook_blocks_selector_open_but_allows_frozen_inputs():
    r = _child("""
        open(Path(sys.path[0]) / 'research/wp2/wp2_saleor_main297_census_2026-09-22.json').read(10)
        try:
            open(Path(sys.path[0]) / 'research/wp1a/sip_rmcss_per_task_predictions.json')
        except fw.FirewallViolation:
            print('BLOCKED_OPEN')
        try:
            Path(sys.path[0], 'research/wp1b/main-297-2026-09-22/agent_run_records.jsonl').read_text()
        except fw.FirewallViolation:
            print('BLOCKED_PATHLIB')
    """)
    assert "BLOCKED_OPEN" in r.stdout and "BLOCKED_PATHLIB" in r.stdout, r.stderr


def test_hook_blocks_subprocess_and_network():
    r = _child("""
        try:
            subprocess.run(['git', 'show', 'HEAD:research/wp1a/sip_rmcss_per_task_predictions.json'])
        except fw.FirewallViolation:
            print('BLOCKED_SUBPROCESS')
        try:
            s = socket.socket(); s.settimeout(0.1); s.connect(('203.0.113.1', 443))
        except fw.FirewallViolation:
            print('BLOCKED_NET')
        except OSError:
            print('NOT_BLOCKED_NET')
        print('VIOLATIONS', len(fw.violations()))
    """)
    assert "BLOCKED_SUBPROCESS" in r.stdout and "BLOCKED_NET" in r.stdout, r.stdout + r.stderr


def test_selector_blind_commands_install_the_firewall_and_selector_code_is_post_q08():
    src = (P / "scripts/wp2_m16_run.py").read_text(encoding="utf-8")
    for c in ("guard", "adapter-verify", "oracle", "evalsets", "readiness", "ready-freeze"):
        assert f'"{c}"' in src.split("SELECTOR_BLIND = {")[1].split("}")[0]
    for c in ("scopes", "opws-evaluate", "analyze"):
        assert f'"{c}"' not in src.split("SELECTOR_BLIND = {")[1].split("}")[0]
    selector_funcs = src.split("def selector_raw")[0]
    for pathconst in ("WP1A_PRED)", "WP1B_MAIN)", "WP1B_VAR)"):
        assert pathconst not in selector_funcs.split("WP1B_VAR = ")[1]   # only defined, never opened earlier
    assert "sys.executable" not in src                                    # no child Python interpreters


def test_no_model_client_or_http_library_in_m16_code():
    import ast
    banned = {"openai", "anthropic", "httpx", "requests", "urllib.request", "aiohttp", "http.client",
              "benchmark.wp2.e2e.llm_client", "benchmark.wp1b.resilient_backend", "benchmark.wp2.e2e.generate"}
    for f in sorted((P / "scripts").glob("wp2_m16_*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                assert not any(n == b or n.startswith(b + ".") for b in banned), (f.name, n)


def test_af_unix_is_exempt_and_unknown_hosts_refused():
    # Portable on every platform: Windows CPython has no socket.AF_UNIX (the firewall's _is_unix already
    # guards with hasattr); the unknown-address refusal is asserted unconditionally, never skipped.
    assert fw.host_blocked("/var/run/docker.sock") is True          # string address alone: refused
    r = _child("""
        import tempfile
        s = socket.socket(socket.AF_INET)                           # non-UNIX path, all platforms
        try:
            print('NON_UNIX', fw._is_unix(s))
            try:                                                    # exact socket.connect audit event through
                sys.audit('socket.connect', s, '/var/run/docker.sock')  # the installed hook; no syscall, no DNS
            except fw.FirewallViolation:
                print('BLOCKED_STR_ADDR')
        finally:
            s.close()
        if hasattr(socket, 'AF_UNIX'):                              # real AF_UNIX exemption where it exists
            p = os.path.join(tempfile.mkdtemp(), 's')
            srv = socket.socket(socket.AF_UNIX)
            c = socket.socket(socket.AF_UNIX)
            try:
                srv.bind(p); srv.listen(1); c.connect(p); print('UNIX_OK')
            finally:
                c.close(); srv.close()
        else:
            print('NO_AF_UNIX')
    """)
    assert "NON_UNIX False" in r.stdout and "BLOCKED_STR_ADDR" in r.stdout, r.stdout + r.stderr
    if hasattr(socket, "AF_UNIX"):
        assert "UNIX_OK" in r.stdout and "NO_AF_UNIX" not in r.stdout, r.stdout + r.stderr
    else:
        assert "NO_AF_UNIX" in r.stdout and "UNIX_OK" not in r.stdout, r.stdout + r.stderr


def test_network_mode_allows_selector_reads_but_refuses_network(tmp_path):
    decoy = tmp_path / "research/wp1a/sip_rmcss_per_task_predictions.json"    # never the real selector file
    decoy.parent.mkdir(parents=True)
    decoy.write_text("{}")
    assert fw.path_blocked(decoy, PROJ)
    code = textwrap.dedent(f"""
        import sys, socket
        sys.path[:0] = [{PROJ!r}, {PROJ + '/src'!r}]
        from pathlib import Path
        from scripts import wp2_m16_firewall as fw
        print(fw.install(Path({PROJ!r}), "network")["mode"])
        open({str(decoy)!r}).read(2)
        print('SELECTOR_READ_OK')
        try:
            socket.create_connection(("8.8.8.8", 443), timeout=1)
        except fw.FirewallViolation:
            print('BLOCKED_NET')
        print(fw.install(Path({PROJ!r}), "network")["mode"], fw.install(Path({PROJ!r}), "full")["mode"])
    """)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=PROJ, timeout=120)
    out = r.stdout.split()
    assert out[0] == "network" and "SELECTOR_READ_OK" in out and "BLOCKED_NET" in out, r.stderr
    assert out[-2:] == ["network", "full"]                          # can tighten, never loosen


@pytest.mark.parametrize("after", ["return 0", "raise run.Stop('later infra', run.EXIT_INFRA)"])
def test_swallowed_violation_is_surfaced_as_exit_36(tmp_path, after):
    decoy = tmp_path / "research/wp1a/sip_rmcss_per_task_predictions.json"    # blocked by pattern; not opened
    code = textwrap.dedent(f"""
        import sys
        sys.path[:0] = [{PROJ!r}, {PROJ + '/src'!r}]
        from scripts import wp2_m16_run as run
        def sneaky():
            try:
                open({str(decoy)!r})
            except Exception:
                pass                                                # frozen-style broad except
            {after}
        run.dryrun_select = sneaky
        sys.exit(run.main(["dryrun-select"]))
    """)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=PROJ, timeout=120)
    assert r.returncode == 36 and "M16_FIREWALL_VIOLATION" in r.stdout, (r.stdout, r.stderr)
