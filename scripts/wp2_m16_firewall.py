#!/usr/bin/env python3
"""WP2 M16 selector-input firewall (brain-authored). ZERO model API.

Installed (once per process, irreversibly) by every selector-blind M16 subcommand
(guard, adapter, dry-run, oracle, eligibility, evaluator sets, readiness, READY freeze).
A Python audit hook (PEP 578) raises FirewallViolation when the process tries to
  * open() any frozen MAIN selector artifact, or a copy of one anywhere (cold mirror, LIGHT
    extraction), or any .zip export in the project's parent directory;
  * start a subprocess (Popen / os.system / exec* / posix_spawn / spawn*) whose argv
    mentions such a path (e.g. `git show HEAD:<path>`, `wsl cat <path>`);
  * open a network connection to a non-loopback address (no model API, no network I/O from
    the engine itself; Docker/WSL children are separate processes and are not Python).
    AF_UNIX sockets are exempt (local IPC). The network rule alone ("network" mode) is also
    installed in the selector-reading phases Q08-Q12, so EVERY M16 engine process is no-network.
Paths are normalised (fspath, abspath, normcase, forward slashes, lower case) before matching.
The engine never spawns a child Python interpreter in these phases (static test), so the
hook covers every Python-level read. Limits (out-of-band human reads) are stated in the
design freeze, section "proof".
"""
from __future__ import annotations

import ipaddress
import os
import socket
import sys
import threading
from pathlib import Path

BLOCKED_FILES = (
    "research/wp1a/sip_rmcss_per_task_predictions.json",
    "research/stage5-v2-final/deployment_artifact.json",
    "research/wp2/wp2_main_census_metadata_v2_2026-09-23.json",
    "exports/WP1A_WP1B_SCIENTIFIC_CLOSURE_2026-09-21/research__wp1a__sip_rmcss_per_task_predictions.json",
)
BLOCKED_DIRS = (
    "research/wp1b/main-297-2026-09-22/",
    "research/wp1b/variance-15x3-2026-09-22/",
    "research/wp2/m16_v1/scopes/",
    "research/wp2/m16_v1/opws/",
)
BLOCKED_SUFFIXES = (".zip",)            # LIGHT/project exports: blocked inside the project's parent dir
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
SPAWN_EVENTS = ("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn")

_STATE = {"installed": False, "project": "", "violations": [], "mode": ""}
_LOCAL = threading.local()          # per-thread re-entrancy guard
MODES = ("full", "network")


class FirewallViolation(RuntimeError):
    """A selector-blind phase touched a selector artifact or the network."""


def _norm(p: object, project: str) -> str:
    s = os.fspath(p) if isinstance(p, (str, bytes, os.PathLike)) else str(p)
    if isinstance(s, bytes):
        s = s.decode("utf-8", "replace")
    if not os.path.isabs(s):
        s = os.path.join(os.getcwd(), s)
    return os.path.normcase(os.path.abspath(s)).replace("\\", "/").lower()


def _rel_patterns() -> list[str]:
    return [x.lower() for x in BLOCKED_FILES + BLOCKED_DIRS]


def path_blocked(path: object, project: str | None = None) -> bool:
    """Pure predicate (unit-tested). Selector artifacts are matched ANYWHERE in the normalised
    path (so copies in the cold mirror, LIGHT extractions or worktrees are blocked too)."""
    proj = (project if project is not None else _STATE["project"]).replace("\\", "/").lower().rstrip("/")
    n = "/" + _norm(path, proj).lstrip("/")
    parent = proj.rsplit("/", 1)[0] if "/" in proj else proj
    if n.endswith(BLOCKED_SUFFIXES) and parent and n.startswith("/" + parent.lstrip("/") + "/"):
        return True
    for pat in _rel_patterns():
        if pat.endswith("/"):
            if ("/" + pat) in n or n.endswith("/" + pat.rstrip("/")):
                return True
        elif n.endswith("/" + pat):
            return True
    return False


def argv_blocked(argv: object) -> bool:
    """Pure predicate: any argv element mentions a blocked relative path or the cold mirror."""
    items = argv if isinstance(argv, (list, tuple)) else [argv]
    flat = []
    for x in items:
        if isinstance(x, (list, tuple)):
            flat += list(x)
        else:
            flat.append(x)
    text = " ".join(os.fspath(x) if isinstance(x, (str, os.PathLike)) else str(x)
                    for x in flat).replace("\\", "/").lower()
    return any(p.rstrip("/") in text for p in _rel_patterns())


def host_blocked(address: object) -> bool:
    host = address[0] if isinstance(address, tuple) and address else address
    if not isinstance(host, str):
        return True                     # unknown address shapes are refused (AF_UNIX is exempted by family)
    if host in LOCAL_HOSTS:
        return False
    try:
        return not ipaddress.ip_address(host).is_loopback
    except ValueError:
        return True                     # unresolved host names are refused


def _is_unix(sock: object) -> bool:
    fam = getattr(sock, "family", None)
    return hasattr(socket, "AF_UNIX") and fam == socket.AF_UNIX


def _hook(event: str, args: tuple) -> None:
    if getattr(_LOCAL, "busy", False):
        return
    try:
        _LOCAL.busy = True
        if event == "socket.connect" and len(args) >= 2:
            if not _is_unix(args[0]) and host_blocked(args[1]):
                _STATE["violations"].append(("socket.connect", str(args[1])))
                raise FirewallViolation(f"M16 firewall: network connection refused {args[1]}")
        elif _STATE["mode"] != "full":
            return
        elif event == "open" and args and not isinstance(args[0], int):
            if path_blocked(args[0]):
                _STATE["violations"].append(("open", str(args[0])))
                raise FirewallViolation(f"M16 firewall: selector artifact opened {args[0]}")
        elif event.startswith(SPAWN_EVENTS):
            if argv_blocked(list(args[:2])):        # (executable/path, argv); never env or cwd
                _STATE["violations"].append((event, str(args)[:300]))
                raise FirewallViolation(f"M16 firewall: subprocess mentions a selector artifact {event}")
    finally:
        _LOCAL.busy = False


def install(project: Path, mode: str = "full") -> dict:
    """Install the hook once for this process (irreversible). mode="full": selector-file, argv and
    network rules (selector-blind phases); mode="network": non-loopback network rule only (Q08-Q12,
    which must read the selector files). A process can only be tightened, never loosened."""
    if mode not in MODES:
        raise ValueError(mode)
    if not _STATE["installed"]:
        _STATE["project"] = os.path.normcase(os.path.abspath(str(project))).replace("\\", "/").lower()
        sys.addaudithook(_hook)
        _STATE["installed"] = True
    if mode == "full" or not _STATE["mode"]:
        _STATE["mode"] = mode
    return config()


def config() -> dict:
    return {"installed": _STATE["installed"], "mode": _STATE["mode"], "blocked_files": list(BLOCKED_FILES),
            "blocked_dirs": list(BLOCKED_DIRS), "blocked_suffixes": list(BLOCKED_SUFFIXES),
            "network": "loopback only", "events": ["open", *SPAWN_EVENTS, "socket.connect"]}


def violations() -> list:
    return list(_STATE["violations"])
