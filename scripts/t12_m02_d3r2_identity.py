#!/usr/bin/env python3
"""T12 M02-D3-R2 — Option-B physical execution identity + real worktree admission.

Mission: T12_M02_D3R2_OPTION_B_PROCESS_20261028 (Track 1.2, D3-R2).  OFFLINE
engineering module.  Nothing here starts a container, a database, a pytest run
or a model call; docker interactions are READ-ONLY and bounded.

WHY THIS MODULE EXISTS (source-grounded defects, from the committed D3-R1 code)
------------------------------------------------------------------------------
1. ``run_bridge`` executed every arm inside ONE Python interpreter whose single
   ``os.getpid()`` was recorded per arm — bare PID equality/inequality is not a
   physical-process identity certificate (PIDs recycle; the audit requires
   *verified process birth* evidence, not PID uniqueness alone).
2. ``wt = Path(wt_linux)`` on Windows Python turns a WSL path such as
   ``/root/m19b_r3_20261024/wt_t`` into a meaningless Windows path; a Linux
   tree must be validated on the OS that owns it (WSL) using the same pinned
   git/stat primitives the frozen engine uses.
3. ``_worktree_tree_oid`` proves ``HEAD^{tree}`` only.  A worktree admits an arm
   only when its WORKING FILES are clean/stable (no staged, unstaged or
   untracked content), the frozen ``effective_tree_oid`` matches, and the
   scope/common-test patch bytes are the frozen ones — checked on the owning OS
   BEFORE and AFTER use.
4. Receipt construction seeded live receipts from the ``sample_run_receipt``
   TEST fixture and overwrote some fields.  Live receipts must be built from
   measured evidence only; any surviving fixture marker is a STOP
   (``assert_live_receipt`` / ``detect_synthetic_fixture_fields``).
5. ``resources.network_bytes = 0`` was emitted without a sampler; unmeasured
   resources must be ``NOT_MEASURED`` (or numeric WITH sampler provenance).
6. ``process.container_oci_id`` is an IMAGE digest, not a container INSTANCE.
   Container-instance evidence needs runtime events tied to the arm window
   (``capture_docker_events_window``); an image digest is never presented as a
   container instance (``CONTAINER_INSTANCE_NOT_MEASURED`` otherwise).

NO FROZEN-ENGINE MODIFICATION: the frozen harness (``harness_v3``,
``opws_isolated_runtime_v1``, ``runtime_image_compat_v1``) is imported READ-ONLY
at run time by other D3-R2 modules; this module only supplies identity /
admission primitives and the minimal REVERSIBLE scratch-only per-arm tree
builder the mission explicitly authorizes (distinct arm parent dirs, basename
``wt_t``, private scratch output, exact input pins, no writes to any source
repo or frozen worktree).

Everything is unit-testable with injected runners; tests never touch WSL or
Docker.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import secrets
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Pinned runtime facts (VERIFIED READ-ONLY on 2026-10-28; the evidence trail
# lives in the D3-R2 audit directory, see IDENTITIES_AND_WORKTREE_GATE.md)
# ---------------------------------------------------------------------------
WSL_DISTRO = "Ubuntu-24.04"
# Docker is invoked ONLY as verified WSL root (frozen engine rule: the default
# user has no socket access; chmod/docker-group membership are forbidden).
WSL_ROOT_ARGS: list[str] = ["-d", WSL_DISTRO, "-u", "root", "--"]

# Frozen execution worktree pattern (isolated runtime requires basename wt_t).
WORKTREE_PATTERN_LINUX = "/root/m19b_r3_20261024/wt_t"
WORKTREE_BASENAME = "wt_t"

# The bare Saleor object cache the frozen R7/M19B worktrees belong to.
# Host-specific paths are never embedded in this PUBLIC repository: they are
# supplied by the operator as environment variables at execution time, and the
# exact values used by a run are recorded ONLY in that run's evidence
# directory (never here).  Fallbacks are deliberately non-real placeholders.
LINUX_CACHE_REPO = os.environ.get("T12_M02_GIT_CACHE_LINUX") or "/mnt/<cache-drive-unspecified>/saleor.git"
WINDOWS_CACHE_REPO = Path(os.environ.get("T12_M02_GIT_CACHE_WINDOWS") or r"<cache-drive-unspecified>\saleor.git")

# Frozen py312 OCI digest + isolated mode fixtures (M3 receipts; read-only
# probes only).
PINNED_PY312_OCI_ID = "sha256:a6e743589b60a4c15676eece07f52ed8347dc501bc782cc53ddffb7200d06c4c"
PG_FIXTURE = "wp2-opws-pg-smoke"
PG_FIXTURE_IMAGE_ID = "sha256:f7d23353e1b15400d22ebe31189f4d314b87a4c129cc400c8c2d8d4ca127bf81"
RUN_NETWORK = "opws-m3-private-2026-10-26"

# Fixture markers from ``t12_m02_receipts.sample_run_receipt`` (a TEST/demo
# fixture).  Any of these surviving into a LIVE receipt is a STOP.
FIXTURE_HOST = "OPWS-RUNTIME-COMPAT-2026-10-26"
FIXTURE_ENV_ID = "5186f584ed178ef10e02e919f15716096a01fe0bdac2f8f99238889187d81048"
FIXTURE_START_UTC = "2026-11-02T08:00:00Z"
FIXTURE_END_UTC = "2026-11-02T08:04:10Z"
FIXTURE_SAMPLER = "resource_sampler_v1 (pinned host sampler, frozen stage)"
# sample_run_receipt's exact db identity is
# ``opws_<arm8>_<task8>_083233_ab12cd34ef56`` — only the EXACT fixture
# name (timestamp + suffix) is a marker, never a generic suffix.
FIXTURE_DB_IDENTITY_TAIL = "_083233_ab12cd34ef56"
FIXTURE_PID_RANGE = (4242, 5241)

NOT_MEASURED = "NOT_MEASURED"
WITNESS_SCHEMA = "t12_m02_d3r2_witness_v1"


# ---------------------------------------------------------------------------
# Command runner (typed, injectable)
# ---------------------------------------------------------------------------
@dataclass
class CmdResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str
    started_utc: str
    ended_utc: str
    elapsed_s: float = 0.0

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def utc_now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def utc_seconds() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def monotonic_birth_ns() -> int:
    """Boot-relative monotonic timestamp (per-process unique birth marker).

    On Windows ``time.monotonic_ns()`` is GetTickCount64-based (system-boot
    relative); on Linux it is CLOCK_MONOTONIC.  A (pid, monotonic_ns) pair is a
    process-birth certificate; two arms with the SAME pid and DIFFERENT
    monotonic births show OS pid recycling, which is two distinct processes.
    """
    return time.monotonic_ns()


def new_nonce() -> str:
    return secrets.token_hex(16)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def argv_digest(argv: list[str]) -> str:
    return hashlib.sha256("\x00".join(argv).encode("utf-8")).hexdigest()


_WSL_METACHAR = re.compile(r"[\s|&;<>()$`\"']")


def _quote_wsl_arg(arg: str) -> str:
    """Quote one argv token for the wsl.exe -> inner-shell boundary (the
    frozen ``opws_isolated_runtime_v1.quote_wsl_arg`` primitive): tokens with
    spaces, pipes or other shell metacharacters must survive the re-split."""
    if _WSL_METACHAR.search(arg):
        return "'" + arg.replace("'", "'\\''") + "'"
    return arg


def make_wsl_root_runner(
    distro: str = WSL_DISTRO,
    *,
    wsl_exe: str | None = None,
    timeout_s: int = 300,
) -> Callable[..., CmdResult]:
    """Return a runner that executes ``argv`` under WSL root (the frozen
    engine's exact bridge: ``wsl.exe -d <distro> -u root -- <argv>``)."""
    exe = wsl_exe or os.environ.get("T12_M02_WSL_EXE", "wsl")

    def run(
        argv: list[str],
        input_text: str | None = None,
        tp_timeout: int = timeout_s,
        cwd: Any = None,
    ) -> CmdResult:
        full = [exe, "-d", distro, "-u", "root", "--", *[_quote_wsl_arg(a) for a in argv]]
        started = utc_now()
        t0 = time.monotonic()
        try:
            p = subprocess.run(
                full,
                input=input_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=tp_timeout,
                cwd=cwd,
                check=False,
            )
            rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
        except subprocess.TimeoutExpired as exc:
            rc, out, err = -999, str(exc.stdout or ""), str(exc.stderr or "") + f"\nTIMEOUT_AFTER_{tp_timeout}s"
        except FileNotFoundError:
            rc, out, err = -127, "", f"wsl executable not found: {exe!r}"
        return CmdResult(
            argv=full,
            returncode=rc,
            stdout=str(out),
            stderr=str(err),
            started_utc=started,
            ended_utc=utc_now(),
            elapsed_s=time.monotonic() - t0,
        )

    return run


def make_host_runner(timeout_s: int = 300) -> Callable[..., CmdResult]:
    """Host-side runner (plain subprocess, no WSL) used for Windows host
    primitives (PowerShell process-start queries, pytest-free reads)."""

    def run(
        argv: list[str],
        input_text: str | None = None,
        tp_timeout: int = timeout_s,
        cwd: Any = None,
    ) -> CmdResult:
        started = utc_now()
        t0 = time.monotonic()
        try:
            p = subprocess.run(
                argv,
                input=input_text,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=tp_timeout,
                cwd=cwd,
                check=False,
            )
            rc, out, err = p.returncode, p.stdout or "", p.stderr or ""
        except subprocess.TimeoutExpired as exc:
            rc, out, err = -999, str(exc.stdout or ""), str(exc.stderr or "") + f"\nTIMEOUT_AFTER_{tp_timeout}s"
        except FileNotFoundError:
            rc, out, err = -127, "", f"command not found: {argv[0]!r}"
        return CmdResult(
            argv=list(argv),
            returncode=rc,
            stdout=str(out),
            stderr=str(err),
            started_utc=started,
            ended_utc=utc_now(),
            elapsed_s=time.monotonic() - t0,
        )

    return run


# ---------------------------------------------------------------------------
# Platform boundary (1): typed cross-OS verification
# ---------------------------------------------------------------------------
class PlatformProbe:
    """Read-only proof of WHERE the executor runs and which OS owns what.

    The frozen harness (``harness_v3``) runs in WINDOWS Python and bridges
    every Linux command through ``wsl.exe -d Ubuntu-24.04`` (root for docker).
    A Linux path is therefore NEVER a valid Windows ``pathlib.Path``; all Linux
    filesystem/git evidence is collected on WSL.
    """

    def __init__(self, runner: Callable[..., CmdResult] | None = None) -> None:
        self.runner = runner or make_wsl_root_runner()

    def host_python_kind(self) -> str:
        return "windows" if os.name == "nt" else "posix"

    def windows_executor(self) -> bool:
        return os.name == "nt"

    def distro_present(self) -> dict[str, Any]:
        r = make_host_runner(60)(["wsl", "-l", "-q"], None, 60)
        # ``wsl -l`` emits UTF-16LE with NUL bytes on Windows; normalize.
        norm = (r.stdout or "").replace("\x00", "")
        return {
            "probe": "wsl -l -q",
            "present": r.returncode == 0 and WSL_DISTRO in norm,
            "raw_tail": [ln.strip() for ln in norm.strip().splitlines()[-3:]],
            "stdout": norm[-500:],
            "stderr": (r.stderr or "")[-200:],
        }

    def root_reachable(self) -> dict[str, Any]:
        r = self.runner(["id", "-u"], None, 60)
        uid = (r.stdout or "").strip()
        return {
            "probe": f"wsl -d {WSL_DISTRO} -u root -- id -u",
            "reachable": r.returncode == 0 and uid == "0",
            "uid": uid,
            "returncode": r.returncode,
            "stderr_tail": (r.stderr or "")[-200:],
        }

    def linux_path_type(self, linux_path: str) -> dict[str, Any]:
        """Typed existence probe for a LINUX path (never Windows Path)."""
        # three plain-argv ``test`` calls: no inline shell, so the wsl.exe
        # argv->shell re-join boundary cannot corrupt the command.
        def _test(flag: str) -> bool:
            r = self.runner(["test", flag, linux_path], None, 60)
            return r.returncode == 0

        return {
            "path": linux_path,
            "probe": "wsl root test -e/-d/-f (owning OS; never Windows Path)",
            "exists": _test("-e"),
            "is_dir": _test("-d"),
            "is_file": _test("-f"),
            "returncode": 0,
            "stderr_tail": "",
        }

    def linux_git(self, repo_linux: str, *args: str,
                  trust_path: str | None = None) -> CmdResult:
        """READ-ONLY git inside WSL (git -C <repo> <args>) — the owning OS.

        ``trust_path`` enables the NARROW, per-invocation
        ``-c safe.directory=<exact path>`` override in front of ``-C``: it is
        used ONLY to let the read-only probes run when git 2.43 refuses a
        repo as ``dubious ownership``.  Never global, never wildcard, never
        writes git config, and it does NOT relax identity/cleanliness checks
        (the caller still requires a measured tree OID == frozen and a
        readable, empty status/staged diff).
        """
        argv = ["git"]
        if trust_path:
            argv += ["-c", f"safe.directory={trust_path}"]
        argv += ["-C", repo_linux, *args]
        return self.runner(argv, None, 120)

    def measure_clocks(self, n_samples: int = 3) -> dict[str, Any]:
        """Midpoint-method host<->WSL UTC skew (same pinned primitive the
        frozen ``harness_v3.measure_host_wsl_skew`` uses: ``date +%s.%N``)."""
        samples: list[float] = []
        for _ in range(n_samples):
            t0 = time.monotonic()
            r = self.runner(["date", "+%s.%N"], None, 30)
            w = float((r.stdout or "").strip())
            t1 = time.monotonic()
            if r.returncode == 0:
                # host epoch reflected into the same frame via monotonic delta
                host_epoch_at_wsl = time.time() - (t1 - t0) / 2
                samples.append(w - host_epoch_at_wsl)
        if not samples:
            return {"status": "NOT_MEASURED", "reason": "no WSL clock samples available"}
        s = sorted(samples)
        median = s[len(s) // 2]
        return {
            "status": "MEASURED",
            "n_samples": n_samples,
            "median_skew_s": round(median, 6),
            "samples": [round(x, 6) for x in samples],
            "verdict": "PASS" if abs(median) <= 0.5 else "WARN",
            "note": "WSL guest clock is NTP-authoritative (frozen V3 docs); host offset is recorded evidence only",
        }

    def docker_readonly(self, argv: list[str], timeout_s: int = 120) -> CmdResult:
        """Read-only docker CLI via the frozen verified-root bridge."""
        return self.runner(["docker", *argv], None, timeout_s)

    def docker_preflight_reads(self) -> dict[str, Any]:
        """Bounded READ-ONLY daemon probes (never starts anything)."""
        out: dict[str, Any] = {"probes": "read-only; no container/db started"}
        ver = self.docker_readonly(["version", "--format", "{{.Server.Version}}"], 60)
        out["server_version"] = (ver.stdout or "").strip() if ver.ok else NOT_MEASURED
        out["server_ok"] = ver.ok
        img = self.docker_readonly(
            ["image", "inspect", PINNED_PY312_OCI_ID, "--format", "{{.Id}}"], 60)
        out["pinned_image"] = {
            "id": (img.stdout or "").strip(),
            "present": img.ok and PINNED_PY312_OCI_ID in (img.stdout or ""),
        }
        fix = self.docker_readonly(
            ["inspect", PG_FIXTURE, "--format", "{{.State.Status}}|{{.Image}}"], 60)
        raw = (fix.stdout or "").strip()
        status, image = (raw.split("|", 1) + ["", ""])[:2]
        out["pg_fixture"] = {
            "name": PG_FIXTURE,
            "status": status,
            "image_matches": image == PG_FIXTURE_IMAGE_ID,
            "image": image,
        }
        net = self.docker_readonly(
            ["network", "inspect", RUN_NETWORK, "--format", "{{.Internal}}|{{.Driver}}"], 60)
        iraw = (net.stdout or "").strip()
        internal, driver = (iraw.split("|", 1) + ["", ""])[:2]
        out["network"] = {
            "name": RUN_NETWORK,
            "internal": internal == "true",
            "driver": driver == "bridge",
        }
        return out


# ---------------------------------------------------------------------------
# Worktree admission (2): content identity, not just HEAD^{tree}
# ---------------------------------------------------------------------------
def linux_worktree_ownership(probe: PlatformProbe, wt_linux: str) -> dict[str, Any]:
    """READ-ONLY ownership evidence for the EXACT worktree path (``stat`` on
    the owning OS, never Windows ``pathlib``).  Used ONLY to decide whether the
    narrow per-invocation ``git -c safe.directory=<exact path>`` override is
    admissible: the path must exist as a directory.  Ownership is recorded as
    evidence; the adapter never chowns, never changes mode, never writes
    config, and the actual tree identity is verified by ``linux_worktree_gate``
    AFTER the override (a wrong OID or dirty tree stays STOP)."""
    r = probe.runner(["stat", "-c", "%U|%u|%g|%F|%a", wt_linux], None, 60)
    ok = bool(r.returncode == 0 and (r.stdout or "").strip())
    owner = uid = gid = file_type = mode = ""
    if ok:
        parts = (r.stdout or "").strip().split("|")
        if len(parts) == 5:
            owner, uid, gid, file_type, mode = parts
    return {
        "path": wt_linux,
        "probe": "wsl root stat -c '%U|%u|%g|%F|%a' (owning OS)",
        "stat_ok": ok,
        "is_dir": file_type == "directory",
        "owner": owner,
        "uid": uid,
        "gid": gid,
        "file_type": file_type,
        "mode": mode,
        "stderr_tail": (r.stderr or "")[-200:],
    }


def resolve_worktree_git_trust(
    probe: PlatformProbe,
    operator_trust: str | None,
    wt_linux: str,
) -> str | None:
    """Admit the NARROW per-invocation ``git -c safe.directory=<exact path>``
    override for ONE arm worktree, mirroring the D5 preflight rule.

    The override is applied ONLY when BOTH hold:
      * the operator-supplied trust path EXACTLY equals this arm's resolved
        ``wt_linux`` (never a different path, never a wildcard, never a
        prefix); and
      * the WSL ``stat`` probe verified the path exists as a directory
        (ownership evidence; the adapter never chowns or writes config).

    It NEVER weakens the identity gate: the caller still requires the
    measured tree OID to equal the frozen value and readable+empty status /
    staged-diff.  Returns the exact path when admissible, else None.
    """
    if not operator_trust or operator_trust != wt_linux:
        return None
    own = linux_worktree_ownership(probe, wt_linux)
    if not (bool(own.get("stat_ok")) and bool(own.get("is_dir"))):
        return None
    return wt_linux


def linux_worktree_gate(
    probe: PlatformProbe,
    wt_linux: str,
    expected_tree_oid: str,
    *,
    require_basename: str = WORKTREE_BASENAME,
    git_trust_path: str | None = None,
) -> dict[str, Any]:
    """Admit one arm's execution worktree ONLY with clean/stable bytes on the
    OS that owns it (WSL).  Checks, all read-only:

    * path exists and is a directory on WSL (never Windows ``Path.is_dir()``);
    * basename == ``wt_t`` (frozen ``OpwsIsolatedRuntime.validate``);
    * ``git rev-parse HEAD^{tree}`` == the arm's frozen ``effective_tree_oid``
      (byte identity of the checked-out tree);
    * ``git status --porcelain --untracked-files=all`` is EMPTY (no staged,
      unstaged or untracked content) — the HEAD^{tree} check alone cannot see
      uncommitted edits;
    * the scope/common-test patch bytes are the frozen ones (via the tree OID
      plus deterministic materializer pins, cross-checked by the caller).

    ``git_trust_path`` enables the NARROW per-invocation ``-c safe.directory``
    override on the read-only git argv (see ``PlatformProbe.linux_git``); it
    exists so a verified frozen worktree that git 2.43+ mislabels as "dubious
    ownership" can still be MEASURED instead of failing unreadably.  The
    override is accepted ONLY when the caller has stat-verified the exact path
    and its ownership first, and it NEVER weakens the identity gate: the tree
    OID must still be measured and equal the frozen value, and the status +
    staged-diff probes must still be read AND empty.  D5: unreadable Git
    status or staged diff is NEVER treated as proof of a clean tree
    (``clean`` is false unless both probes were READABLE and empty)."""
    reasons: list[str] = []
    pt = probe.linux_path_type(wt_linux)
    path_ok = pt["exists"] and pt["is_dir"]
    if not pt["exists"]:
        reasons.append("WORKTREE_MISSING_ON_LINUX")
    elif not pt["is_dir"]:
        reasons.append("WORKTREE_NOT_A_DIR_ON_LINUX")
    base = wt_linux.rstrip("/").rsplit("/", 1)[-1]
    basename_ok = base == require_basename
    if not basename_ok:
        reasons.append(f"WORKTREE_BASENAME_UNEXPECTED:{base} (frozen runtime requires {require_basename})")

    tree_oid: str | None = None
    tree_matches = False
    status_lines: list[str] = []
    staged_lines: list[str] = []
    staged_diff_ok = True
    status_readable = False
    staged_readable = False
    if path_ok and basename_ok:
        r = probe.linux_git(wt_linux, "rev-parse", "HEAD^{tree}",
                            trust_path=git_trust_path)
        if r.ok:
            tree_oid = (r.stdout or "").strip()
            tree_matches = tree_oid == expected_tree_oid
        else:
            reasons.append("WORKTREE_OID_UNVERIFIABLE:" + (r.stderr or "")[-200:])
        if not tree_matches:
            reasons.append(f"WORKTREE_OID_MISMATCH:{tree_oid} != {expected_tree_oid}")
        s = probe.linux_git(wt_linux, "status", "--porcelain", "--untracked-files=all",
                            trust_path=git_trust_path)
        if s.ok:
            status_lines = [ln for ln in (s.stdout or "").splitlines() if ln.strip()]
            status_readable = True
        else:
            reasons.append("WORKTREE_STATUS_UNREADABLE:" + (s.stderr or "")[-200:])
        d = probe.linux_git(wt_linux, "diff", "--cached", "--name-only",
                            trust_path=git_trust_path)
        if d.ok:
            staged_lines = [ln for ln in (d.stdout or "").splitlines() if ln.strip()]
            staged_readable = True
        else:
            reasons.append("WORKTREE_STAGED_DIFF_UNREADABLE:" + (d.stderr or "")[-200:])
        staged_diff_ok = not staged_lines
    # D5: clean state is PROVEN only when BOTH probes were readable and both
    # empty.  Unreadable status/staged diff is never clean evidence.
    clean = status_readable and staged_readable and not status_lines and staged_diff_ok
    if not clean and status_readable and staged_readable and (status_lines or staged_lines):
        reasons.append(
            "WORKTREE_NOT_CLEAN: unstaged/untracked=" + ",".join(status_lines[:8])
            + ((" staged=" + ",".join(staged_lines[:8])) if staged_lines else "")
        )
    ok = path_ok and basename_ok and tree_matches and clean and not reasons
    return {
        "pass": ok,
        "reasons": reasons,
        "wt_linux": wt_linux,
        "expected_tree_oid": expected_tree_oid,
        "tree_oid": tree_oid,
        "tree_matches": tree_matches,
        "basename_ok": basename_ok,
        "clean": clean,
        "status_lines_sample": status_lines[:8],
        "staged_lines_sample": staged_lines[:8],
        "checked_via": "wsl root git/stat (owning OS)",  # never Windows Path
        "checked_at_utc": utc_now(),
    }


# ---------------------------------------------------------------------------
# Scratch-only per-arm tree builder (2): frozen inputs -> private scratch trees
# ---------------------------------------------------------------------------
def _load_frozen_module(worktree: Path, rel: str, name: str) -> Any:
    """Import ONE frozen module read-only from the frozen stage (mirrors the
    D3-R1 executor loader; no writes: caller sets PYTHONDONTWRITEBYTECODE)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, worktree / rel)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    import sys

    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def materializer_patches(
    *,
    frozen_stage: Path,
    arm: str,
    scope_json: Path,
    classification: dict[str, str],
    test_authority: dict[str, Any],
    source_repo: Path,
    parent_commit: str,
    target_commit: str,
    task_id: str,
    ref_pin_sha256: str,
    ref_pin_bytes: int,
    scope_hash_pin: str,
) -> dict[str, Any]:
    """Compute the arm's frozen reference + common-test patches from the REAL
    frozen materializer (offline, read-only git).  The reference patch's hash
    and byte count MUST equal the frozen matrix pins; the scope hash MUST equal
    the arm's scope_hash pin; the TEST patch MUST be identical for every arm
    (the common-contract test patch)."""
    mat = _load_frozen_module(frozen_stage, "scripts/opws_phase3b_patch_materialize.py",
                              "benchmark_opws_phase3b_patch_materialize")
    authority = mat.TestPathAuthority(
        changed_paths=frozenset(test_authority["changed_paths"]),
        test_paths=frozenset(test_authority["test_paths"]),
    )
    if arm == "FULL_REFERENCE":
        res = mat.materialize_full_reference(
            task_id=task_id, repo=source_repo, parent_commit=parent_commit,
            target_commit=target_commit, test_path_authority=authority)
    else:
        scope = json.loads(scope_json.read_text(encoding="utf-8"))
        res = mat.materialize_scoped_reference_patch(
            task_id=task_id, repo=source_repo, parent_commit=parent_commit,
            target_commit=target_commit, scope_paths=list(scope.get("scope") or []),
            classification=dict(classification), test_path_authority=authority)
    issues: list[str] = []
    if res.reference_patch_hash != ref_pin_sha256:
        issues.append(f"REF_PATCH_SHA_MISMATCH:{res.reference_patch_hash} != {ref_pin_sha256}")
    if len(res.reference_patch_bytes) != ref_pin_bytes:
        issues.append(f"REF_PATCH_BYTES_MISMATCH:{len(res.reference_patch_bytes)} != {ref_pin_bytes}")
    if res.selected_scope_hash != scope_hash_pin:
        issues.append(f"SCOPE_HASH_MISMATCH:{res.selected_scope_hash} != {scope_hash_pin}")
    if res.invalid_prediction_paths:
        issues.append("INVALID_PREDICTION_PATHS:" + json.dumps(res.invalid_prediction_paths[:3]))
    return {
        "arm": arm,
        "reference_patch_sha256": res.reference_patch_hash,
        "reference_patch_bytes": bytes(res.reference_patch_bytes),
        "reference_patch_len": len(res.reference_patch_bytes),
        "test_patch_sha256": res.test_patch_hash,
        "test_patch_bytes": bytes(res.test_patch_bytes),
        "test_patch_len": len(res.test_patch_bytes),
        "scope_hash": res.selected_scope_hash,
        "per_path_status": dict(res.per_path_status),
        "files_changed": list(res.files_changed),
        "split_invariants": dict(res.split_invariants),
        "invalid_prediction_paths": list(res.invalid_prediction_paths),
        "unresolved_contracts": [u.get("status") for u in res.unresolved_contracts],
        "issues": issues,
        "pins_ok": not issues,
    }


def build_scratch_arm_trees(
    *,
    probe: PlatformProbe,
    scratch_root_windows: Path,
    scratch_root_linux: str,
    cache_repo_linux: str,
    parent_commit: str,
    patches_by_arm: dict[str, dict[str, Any]],
    matrix_by_arm: dict[str, dict[str, str]],
    arms: list[str],
) -> dict[str, Any]:
    """REVERSIBLE, PRIVATE scratch-only builder: per-arm execution trees.

    For every arm: ``git init --bare`` a fresh private repo under
    ``scratch_root``, fetch ONLY the frozen parent commit (and the target for
    FULL_REFERENCE) from the local bare cache (read-only source), add a
    detached worktree at ``<scratch>/arm_<ARM>/wt_t``, apply the arm's frozen
    reference patch then the common test patch with ``git apply --index``,
    commit (private ref ``refs/scratch/t12m02/<ARM>``) and VERIFY
    ``HEAD^{tree} == effective_tree_oid``.  Distinct arm parent dirs, basename
    ``wt_t`` everywhere; NO writes to any source repo or frozen worktree.

    Returned tree OIDs are only authoritative when ``all_match`` is True.
    """
    cache_linux = cache_repo_linux
    results: dict[str, Any] = {}
    scratch_root_windows.mkdir(parents=True, exist_ok=True)
    bare = f"{scratch_root_linux.rstrip('/')}/cache.git"
    mk = probe.runner(["mkdir", "-p", bare.rstrip("/")], None, 60)
    if not mk.ok:
        return {"all_match": False, "error": "SCRATCH_MKDIR_FAILED:" + (mk.stderr or "")[-400:],
                "scratch_root_linux": scratch_root_linux}
    r = probe.linux_git(cache_linux, "init", "--bare", "-q", bare)
    if not r.ok:
        return {"all_match": False, "error": "SCRATCH_INIT_FAILED:" + (r.stderr or "")[-400:],
                "scratch_root_linux": scratch_root_linux}
    # fetch parent + target (all arms derive from parent; FULL_REFERENCE == target tree)
    fetch_argv = ["--git-dir=" + bare, "fetch", "--no-tags", "--depth=1",
                  cache_linux, parent_commit, "7e42fc67ce72770720440781fc83685a48bd91b8"]
    rf = probe.linux_git(cache_linux, *fetch_argv)
    if not rf.ok:
        return {"all_match": False, "error": "SCRATCH_FETCH_FAILED:" + (rf.stderr or "")[-400:]}
    # Windows-side scratch dir is the /mnt/d view of the SAME filesystem, so
    # patch bytes are written by the host (no shell boundary) and copied to the
    # Linux scratch via plain argv ``cp``.
    patch_root_win = scratch_root_windows / "patches"
    patch_root_win.mkdir(parents=True, exist_ok=True)
    for arm, pbytes in patches_by_arm.items():
        (patch_root_win / f"{arm}.ref.patch").write_bytes(pbytes.get("reference_patch_bytes") or b"")
        (patch_root_win / f"{arm}.test.patch").write_bytes(pbytes.get("test_patch_bytes") or b"")
    for arm in arms:
        patch: dict[str, Any] | None = patches_by_arm.get(arm)
        mrow: dict[str, str] | None = matrix_by_arm.get(arm)
        rec: dict[str, Any] = {"arm": arm, "built": False, "tree_match": False}
        if patch is None or mrow is None or not patch.get("pins_ok"):
            rec["reason"] = "MISSING_OR_UNPINNED_PATCH"
            results[arm] = rec
            continue
        arm_dir_linux = f"{scratch_root_linux.rstrip('/')}/arm_{arm}"
        wt = f"{arm_dir_linux}/wt_t"
        ref_path = f"{arm_dir_linux}/arm.ref.patch"
        test_path = f"{arm_dir_linux}/arm.test.patch"
        wr = probe.runner(["mkdir", "-p", arm_dir_linux], None, 60)
        if not wr.ok:
            rec["reason"] = "SCRATCH_MKDIR_FAILED:" + (wr.stderr or "")[-200:]
            results[arm] = rec
            continue
        for src_name, dst in ((f"{arm}.ref.patch", ref_path), (f"{arm}.test.patch", test_path)):
            src = f"/mnt/{_windows_drive_rel(scratch_root_windows)}/patches/{src_name}"
            cp = probe.runner(["cp", src, dst], None, 60)
            if not cp.ok:
                rec["reason"] = "PATCH_CP_FAILED:" + (cp.stderr or "")[-200:]
                results[arm] = rec
                break
        if not rec.get("built") and rec.get("reason", "").startswith("PATCH_CP_FAILED"):
            continue
        wa = probe.linux_git(cache_linux, "--git-dir=" + bare, "worktree", "add", "--detach", wt, parent_commit)
        if not wa.ok:
            rec["reason"] = "WORKTREE_ADD_FAILED:" + (wa.stderr or "")[-400:]
            results[arm] = rec
            continue
        ref_empty = patch.get("reference_patch_len", 0) == 0 or len(patch.get("reference_patch_bytes") or b"") == 0
        ref_argv = ["apply", "--index"] + (["--allow-empty"] if ref_empty else []) + [ref_path]
        ap1 = probe.linux_git(wt, *ref_argv)
        ap2 = probe.linux_git(wt, "apply", "--index", test_path)
        if not ap1.ok:
            rec["reason"] = "REF_APPLY_FAILED:" + (ap1.stderr or "")[-400:]
        elif not ap2.ok:
            rec["reason"] = "TEST_APPLY_FAILED:" + (ap2.stderr or "")[-400:]
        else:
            commit_env = [
                "-c", "user.name=t12-scratch-build", "-c", "user.email=scratch@local.invalid",
                "-c", "commit.gpgsign=false",
            ]
            cm = probe.linux_git(wt, *commit_env, "commit", "-q", "-m", f"scratch arm {arm}")
            if not cm.ok:
                rec["reason"] = "SCRATCH_COMMIT_FAILED:" + (cm.stderr or "")[-400:]
            else:
                to = probe.linux_git(wt, "rev-parse", "HEAD^{tree}")
                head = probe.linux_git(wt, "rev-parse", "HEAD")
                oid = (to.stdout or "").strip() if to.ok else None
                rec["tree_oid"] = oid
                rec["commit"] = (head.stdout or "").strip() if head.ok else None
                rec["tree_match"] = oid == mrow.get("effective_tree_oid")
                rec["expected_tree_oid"] = mrow.get("effective_tree_oid")
                # private ref (still inside the private scratch repo)
                probe.linux_git(cache_linux, "--git-dir=" + bare, "update-ref",
                                f"refs/scratch/t12m02/{arm}", rec["commit"] or "")
                # final cleanliness gate on the OWNING OS
                gate = linux_worktree_gate(probe, wt, mrow.get("effective_tree_oid", ""))
                rec["final_gate"] = gate
                rec["built"] = True
        results[arm] = rec
    all_match = all(results.get(a, {}).get("tree_match") for a in arms)
    return {
        "all_match": all_match,
        "arms": results,
        "scratch_root_windows": str(scratch_root_windows),
        "scratch_root_linux": scratch_root_linux,
        "builder": "minimal scratch-only builder (private, reversible; no source-repo writes)",
        "built_at_utc": utc_now(),
    }


def _windows_drive_rel(p: Path) -> str:
    """Windows path -> lowercase-drive relative path (the /mnt/<d> view):
    ``D:\\x\\y`` -> ``d/x/y``."""
    drive = p.drive.rstrip(":\\")
    rel = p.as_posix().split(":", 1)[-1].lstrip("/")
    return f"{drive.lower()}/{rel}"


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


# ---------------------------------------------------------------------------
# Process identity (3): child-per-arm witness
# ---------------------------------------------------------------------------
def windows_os_process_start(pid: int, runner: Callable[..., CmdResult] | None = None) -> dict[str, Any]:
    """OS-verified creation time of a Windows process (PowerShell query).

    Truly distinct verified process births are REQUIRED for Option-B physical
    identity; a bare PID is not enough (PIDs recycle).  Unavailable ->
    ``{"status": "NOT_MEASURED"}`` (never an invented time)."""
    r = (runner or make_host_runner(60))(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         f"(Get-Process -Id {int(pid)} -ErrorAction Stop).StartTime.ToString('o')"],
        None, 60)
    if r.returncode != 0 or not (r.stdout or "").strip():
        return {
            "status": NOT_MEASURED,
            "pid": int(pid),
            "stderr_tail": (r.stderr or "")[-200:],
            "probe": "powershell Get-Process StartTime",
        }
    return {
        "status": "MEASURED",
        "pid": int(pid),
        "os_start_utc": (r.stdout or "").strip(),
        "probe": "powershell Get-Process StartTime",
    }


def span_witness(
    *,
    nonce: str,
    pid: int,
    parent_pid: int,
    argv: list[str],
    worker_script_path: Path | None,
    monotonic_start_ns: int,
    monotonic_end_ns: int,
    start_utc: str,
    end_utc: str,
    exit_code: int,
    worker_os_start: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """The truthful per-arm OS-process witness (schema v1).  Every field is
    measured (or explicitly NOT_MEASURED); nothing is invented."""
    w = {
        "schema": WITNESS_SCHEMA,
        "nonce": nonce,
        "pid": int(pid),
        "parent_pid": int(parent_pid),
        "argv": list(argv),
        "argv_digest": argv_digest(list(argv)),
        "worker_script_sha256": (
            file_sha256(worker_script_path) if worker_script_path and worker_script_path.is_file() else None),
        "process_birth": {
            "monotonic_start_ns": monotonic_start_ns,
            "monotonic_end_ns": monotonic_end_ns,
            "os_start": worker_os_start or {"status": NOT_MEASURED},
            "birth_basis": "monotonic(boot-relative) + OS process start; PID alone is not an identity certificate",
        },
        "times": {"start_utc": start_utc, "end_utc": end_utc, "monotonic": monotonic_end_ns >= monotonic_start_ns},
        "exit_code": int(exit_code),
    }
    if extra:
        w.update(extra)
    return w


def validate_witness(w: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed witness validation (identity certificates, no invention)."""
    issues: list[str] = []
    if w.get("schema") != WITNESS_SCHEMA:
        issues.append(f"witness schema {w.get('schema')!r} != {WITNESS_SCHEMA!r}")
    if not isinstance(w.get("nonce"), str) or len(w.get("nonce", "")) < 16:
        issues.append("witness nonce missing/short")
    if not isinstance(w.get("pid"), int) or w["pid"] <= 0:
        issues.append("witness pid invalid")
    if not isinstance(w.get("parent_pid"), int) or w["parent_pid"] <= 0:
        issues.append("witness parent_pid invalid")
    if not isinstance(w.get("argv_digest"), str) or len(w["argv_digest"]) != 64:
        issues.append("witness argv_digest invalid")
    pb = w.get("process_birth") or {}
    if not isinstance(pb.get("monotonic_start_ns"), int) or pb["monotonic_start_ns"] <= 0:
        issues.append("process_birth.monotonic_start_ns missing")
    if (not isinstance(pb.get("monotonic_end_ns"), int)
            or pb.get("monotonic_end_ns", 0) < pb.get("monotonic_start_ns", -1)):
        issues.append("process_birth non-monotonic end < start")
    osst = pb.get("os_start") or {}
    if osst.get("status") not in ("MEASURED", NOT_MEASURED):
        issues.append("process_birth.os_start.status invalid")
    elif osst.get("status") == "MEASURED" and not osst.get("os_start_utc"):
        issues.append("process_birth.os_start claims MEASURED without os_start_utc")
    t = w.get("times") or {}
    if isinstance(w.get("exit_code"), int) is False:
        issues.append("witness exit_code must be an integer")
    if not (t.get("start_utc") and t.get("end_utc")):
        issues.append("witness times.start_utc/end_utc required")
    return {"status": "STOP" if issues else "PASS", "issues": issues}


def bundle_identity_check(witnesses: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    """Cross-arm physical-process certificate check.

    * same pid + same verified birth -> SHARED_EXECUTION violation (STOP);
    * same pid + different verified births -> OS pid recycling, TWO distinct
      processes (PASS with signal, never flagged as reuse);
    * identical monotonic start across arms -> replay suspicion (STOP when
      births also coincide);
    * reused nonce -> STOP.
    """
    issues: list[str] = []
    signals: list[str] = []
    seen_nonce: dict[str, str] = {}
    seen_birth: dict[int, tuple[str, str]] = {}
    for arm, w in witnesses:
        nonce = w.get("nonce")
        if not isinstance(nonce, str):
            issues.append("NONCE_MISSING")
            nonce = None
        pid = w.get("pid")
        osst = (w.get("process_birth") or {}).get("os_start") or {}
        birth = osst.get("os_start_utc") or osst.get("monotonic_start_ns") or "NOT_MEASURED"
        if nonce is not None and nonce in seen_nonce and seen_nonce[nonce] != arm:
            issues.append(f"NONCE_REUSE:{arm} shares nonce with {seen_nonce[nonce]} (replayed witness)")
        if nonce is not None:
            seen_nonce[nonce] = arm
        if pid in seen_birth:
            prev_arm, prev_birth = seen_birth[pid]
            if (birth != "NOT_MEASURED" and prev_birth != "NOT_MEASURED"
                    and str(birth) != str(prev_birth)):
                signals.append(
                    f"PID_RECYCLED_DISTINCT_BIRTH:{arm} pid {pid} birth {birth} vs "
                    f"{prev_arm} birth {prev_birth} -> two distinct processes (OK, recorded)")
            elif str(birth) == str(prev_birth):
                issues.append(
                    f"SHARED_PROCESS_EVIDENCE:{arm} pid {pid} matches {prev_arm} with "
                    "identical process birth -> same physical process (Option B violation)")
        if isinstance(pid, int):
            seen_birth[pid] = (arm, str(birth))
    return {"status": "STOP" if issues else "PASS", "issues": issues, "signals": signals}


# ---------------------------------------------------------------------------
# Receipt honesty (4): live receipts only; fixture markers are a STOP
# ---------------------------------------------------------------------------
def detect_synthetic_fixture_fields(receipt: dict[str, Any]) -> list[str]:
    """Return every synthetic field left over from ``sample_run_receipt``.

    The demo fixture is used ONLY by unit tests; a LIVE receipt that still
    carries fixture values must fail the run (never ship test data as
    measurement)."""
    marks: list[str] = []
    times = receipt.get("times") or {}
    if times.get("start_utc") == FIXTURE_START_UTC:
        marks.append("times.start_utc == fixture 2026-11-02T08:00:00Z")
    if times.get("end_utc") == FIXTURE_END_UTC:
        marks.append("times.end_utc == fixture 2026-11-02T08:04:10Z")
    proc = receipt.get("process") or {}
    pid = proc.get("pid")
    if isinstance(pid, int) and FIXTURE_PID_RANGE[0] <= pid <= FIXTURE_PID_RANGE[1]:
        marks.append(f"process.pid {pid} in fixture range 4242..5241")
    if isinstance(proc.get("driver_argv"), list) and proc["driver_argv"][:3] == ["python", "t12_m02_driver.py", "run"]:
        marks.append("process.driver_argv == fixture default")
    db = receipt.get("database") or {}
    if db.get("engine") == "sqlite":
        marks.append("database.engine == fixture 'sqlite' (live engine is postgres isolated fixture)")
    if isinstance(db.get("db_identity"), str) and db["db_identity"].endswith(FIXTURE_DB_IDENTITY_TAIL):
        marks.append("database.db_identity == fixture identity (083233_ab12cd34ef56)")
    res = receipt.get("resources") or {}
    if res.get("sampler") == FIXTURE_SAMPLER:
        marks.append("resources.sampler == fixture 'resource_sampler_v1' claim")
    if res.get("cpu_seconds") == 96.4 or res.get("peak_ram_mb") == 1845.2 or res.get("disk_bytes") == 212401152:
        marks.append("resources == fixture numbers (96.4/1845.2/212401152)")
    if res.get("network_bytes") == 0 and res.get("sampler") not in (None, NOT_MEASURED):
        marks.append("resources.network_bytes == 0 without a sampler (unmeasured != 0)")
    host = receipt.get("host") or {}
    if host.get("hostname") == FIXTURE_HOST:
        marks.append("host.hostname == fixture OPWS-RUNTIME-COMPAT-2026-10-26")
    env = receipt.get("environment") or {}
    if isinstance(env, dict) and env.get("environment_id") == FIXTURE_ENV_ID:
        marks.append("environment.environment_id == fixture hash")
    return marks


def assert_live_receipt(receipt: dict[str, Any]) -> None:
    """Raise ValueError listing ANY synthetic fixture marker in a live receipt."""
    marks = detect_synthetic_fixture_fields(receipt)
    if marks:
        raise ValueError("LIVE_RECEIPT_CONTAINS_FIXTURE_FIELDS: " + " | ".join(marks[:12]))


def live_network_policy(measured_bytes: int | None, sampler: str | None) -> int | str:
    """network_bytes must be a MEASURED value with sampler provenance or
    NOT_MEASURED — never an invented 0."""
    if measured_bytes is None:
        return NOT_MEASURED
    if measured_bytes < 0 or not sampler:
        return NOT_MEASURED
    return int(measured_bytes)


# ---------------------------------------------------------------------------
# Container instance evidence (3): image digest != container instance
# ---------------------------------------------------------------------------
def capture_docker_events_window(
    probe: PlatformProbe,
    *,
    since_utc: str,
    until_utc: str,
    image_digest: str,
    timeout_s: int = 1200,
) -> dict[str, Any]:
    """Bounded READ-ONLY docker-events capture for ONE arm's window.

    ``docker events`` is a daemon event stream (no side effects; starts
    nothing).  Container events whose Image matches the pinned digest within
    the arm's exclusive window are recorded as the arm's container INSTANCE
    evidence.  The OCI digest itself is never presented as an instance id.
    Any capture failure -> ``CONTAINER_INSTANCE_NOT_MEASURED`` (typed).

    ``until_utc`` must be strictly inside/before the wall deadline; the capture
    is bounded by both ``--until`` and ``timeout_s``.
    """
    fmt = "{{json .}}"
    argv = ["docker", "events", "--format", fmt,
            "--since", since_utc, "--until", until_utc]
    r = probe.runner(argv, None, timeout_s)
    events: list[dict[str, Any]] = []
    if r.returncode != 0 and r.returncode != 124:
        return {
            "status": "CONTAINER_INSTANCE_NOT_MEASURED",
            "reason": f"docker events unavailable rc={r.returncode}: {(r.stderr or '')[-300:]}",
            "window": {"since_utc": since_utc, "until_utc": until_utc},
        }
    matched: list[dict[str, Any]] = []
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        events.append(ev)
        if str(ev.get("Action") or "") in ("create", "start"):
            idv = str(ev.get("id") or (ev.get("Actor") or {}).get("ID") or "")
            if image_digest.split(":")[-1][:12] in json.dumps(ev.get("Actor") or {}):
                matched.append({"container_id": idv, "action": str(ev.get("Action") or ""),
                                "time": ev.get("time")})
    if not matched:
        return {
            "status": "CONTAINER_INSTANCE_NOT_MEASURED",
            "reason": "no container create/start event with pinned image within arm window",
            "window": {"since_utc": since_utc, "until_utc": until_utc},
            "events_seen": len(events),
        }
    return {
        "status": "MEASURED",
        "instances": matched,
        "window": {"since_utc": since_utc, "until_utc": until_utc},
        "events_seen": len(events),
        "image_digest": image_digest,
        "note": "image digest never presented as an instance id; instance ids from daemon events only",
    }


def render_baseline(*, branch: str, head: str, origin_head: str,
                    frozen_stage_head: str, dirty: dict[str, Any]) -> dict[str, Any]:
    """Step-0 baseline record (identity of the mission start)."""
    return {
        "schema": "t12_m02_d3r2_baseline_v1",
        "branch": branch,
        "head": head,
        "origin_head": origin_head,
        "frozen_stage_head": frozen_stage_head,
        "frozen_stage_dirty_preserved": dirty,
        "recorded_at_utc": utc_now(),
    }
