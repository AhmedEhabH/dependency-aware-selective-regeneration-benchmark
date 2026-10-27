# -*- coding: utf-8 -*-
"""Resource accounting + fail-closed command execution.

- wall-clock timeout enforced from the parent (kill + terminate escalation)
- peak RSS measured where the platform allows (psutil, else resource on POSIX,
  else measured=None and recorded as such — never asserted)
- disk usage measured on the workspace + caller-provided scratch paths
- network: an injected sitecustomize gate patches socket.* to hard-fail the
  child; when active, network bytes are enforced at 0 (measured network is not
  asserted anyway: it is enforced)
"""
import json
import os
import shutil
import subprocess
import time

from .errors import CommandTimeout, NetworkBlocked, ResourceOverflow

GATE_SOURCE = '''
import socket as _s

class _BlockedSocket(_s.socket):
    def connect(self, *a, **k):
        raise OSError("C6_NETWORK_GATE: network access is prohibited")
    def sendall(self, *a, **k):
        raise OSError("C6_NETWORK_GATE: network access is prohibited")

def _block(*a, **k):
    raise OSError("C6_NETWORK_GATE: network access is prohibited")

_s.socket = _BlockedSocket
_s.create_connection = _block
_s.socketpair = _block
'''


class ResourceLimits:
    def __init__(self, timeout_s=1800.0, ram_mb=16384, disk_mb=5120,
                 scratch_paths=None):
        self.timeout_s = float(timeout_s)
        self.ram_mb = float(ram_mb)
        self.disk_mb = float(disk_mb)
        self.scratch_paths = list(scratch_paths or [])


def dir_size_mb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / (1024.0 * 1024.0)


class RunResult:
    def __init__(self):
        self.exit_code = None
        self.wall_s = None
        self.peak_rss_mb = None
        self.disk_mb_before = None
        self.disk_mb_after = None
        self.timeout = False
        self.resource_overflow = False
        self.blocked_reason = None
        # oracle truthfulness: None = NOT verified (never default True)
        self.assertions_ok = None
        self.oracle_parity = None
        # isolation truthfulness: sitecustomize is NOT OS-level
        self.python_gate_active = False
        self.os_isolation_active = False
        self.network_enforced = False
        self.memory_enforced = False
        self.disk_enforced = False
        self.pids_enforced = False
        self.backend = None
        self.vacuous_oracle = False
        self.stdout_path = None
        self.stderr_path = None
        self.returncode_reported = None
        # machine-readable pytest evidence (junit-xml) written by the executed
        # process inside the sandbox; sha256 of the final report bytes
        self.junit_path = None
        self.junit_sha256 = None
        self.cleanup_evidence = None
        self.effective_command = None

    def log_digest(self, path):
        return log_digest(path)


def _try_peak_rss_mb():
    try:
        import psutil
        p = psutil.Process()
        return p.memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        try:
            import resource
            return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024.0
        except Exception:
            return None


def run_limited(command, cwd, limits: ResourceLimits, logs_dir,
                env_extra=None, offline_gate=True, backend=None,
                scratch_dir=None, plan=None):
    """Execute `command` (list of argv) fail-closed under quotas.

    `backend` (isolation.IsolationDescriptor) selects a genuine OS-level
    mechanism and `plan` supplies the pinned image + resources for the docker
    path. When a docker backend is supplied the command runs inside a
    container (--network none / --memory hard caps); the returned RunResult
    records os_isolation_active/network_enforced from the mechanism, never
    from the python sitecustomize gate alone.

    Queryable fields; max-resource overflow and timeout are BLOCKED-class
    outcomes (caller maps to verdict)."""
    res = RunResult()
    gate_dir = os.path.join(cwd, ".c6_netgate")
    if offline_gate:
        os.makedirs(gate_dir, exist_ok=True)
        with open(os.path.join(gate_dir, "sitecustomize.py"), "w", encoding="utf-8") as f:
            f.write(GATE_SOURCE)

    env = dict(os.environ)
    env["C6_WORKSPACE"] = cwd
    if offline_gate:
        env["PYTHONPATH"] = gate_dir + os.pathsep + env.get("PYTHONPATH", "")
        env["C6_NETWORK_GATE"] = "1"
    if env_extra:
        env.update(env_extra)

    from .oracle import inject_junitxml, is_pytest_command

    res.python_gate_active = offline_gate
    res.backend = backend.backend if backend else "local"
    if backend is not None and backend.backend == "docker":
        # genuine OS-level enforcement via the container runtime
        res.os_isolation_active = True
        res.network_enforced = True
        res.memory_enforced = True
        res.pids_enforced = bool(backend.pids)
        res.disk_enforced = False  # per-task scratch delta still measured
        from . import isolation as _iso
        sd = scratch_dir or os.path.join(cwd, ".scratch")
        os.makedirs(sd, exist_ok=True)
        res.disk_mb_before = dir_size_mb(sd)
        junit_container = (getattr(plan, "junitxml_path", None) or
                           "/scratch-dir/c6-junit.xml")
        eff_cmd = inject_junitxml(command, junit_container)
        res.effective_command = eff_cmd
        out_path = os.path.join(logs_dir, "stdout.log")
        err_path = os.path.join(logs_dir, "stderr.log")
        res.stdout_path, res.stderr_path = out_path, err_path
        rc, wall, kind, cleanup = _iso.docker_run(
            eff_cmd, cwd, sd, limits, logs_dir, plan)
        res.exit_code = rc
        res.wall_s = wall
        res.cleanup_evidence = cleanup
        if kind == "timeout":
            res.timeout = True
            res.blocked_reason = "timeout"
        elif rc in (137,):
            res.blocked_reason = "container_killed"
            res.resource_overflow = True
        res.disk_mb_after = dir_size_mb(sd)
        if (res.disk_mb_after - res.disk_mb_before) > limits.disk_mb:
            res.resource_overflow = True
            res.blocked_reason = "disk_overflow"
        res.peak_rss_mb = None  # container RSS not measurable from parent
        if is_pytest_command(eff_cmd):
            res.junit_path = os.path.join(sd, os.path.basename(junit_container))
            res.junit_sha256 = log_digest(res.junit_path)
        return res

    # local (non-OS-isolated) execution path: used by the synthetic harness
    # only; os_isolation_active stays False and network_enforced stays False
    # (sitecustomize gate is python-children-only, never claimed as OS).
    res.disk_mb_before = dir_size_mb(cwd)
    out_path = os.path.join(logs_dir, "stdout.log")
    err_path = os.path.join(logs_dir, "stderr.log")
    res.stdout_path, res.stderr_path = out_path, err_path
    sd = scratch_dir or os.path.join(cwd, ".scratch")
    os.makedirs(sd, exist_ok=True)
    eff_cmd = inject_junitxml(command, os.path.join(sd, "c6-junit-host.xml"))
    res.effective_command = eff_cmd
    if eff_cmd != list(command):
        res.junit_path = os.path.join(sd, "c6-junit-host.xml")

    t0 = time.monotonic()
    try:
        with open(out_path, "wb") as so, open(err_path, "wb") as se:
            proc = subprocess.Popen(eff_cmd, cwd=cwd, env=env,
                                    stdout=so, stderr=se)
            try:
                proc.wait(timeout=limits.timeout_s)
            except subprocess.TimeoutExpired:
                res.timeout = True
                _kill_tree(proc)
                res.blocked_reason = "timeout"
                proc.wait(timeout=10)
        res.exit_code = proc.returncode
    except Exception as e:  # noqa: BLE001 infra
        res.blocked_reason = f"exec_infra:{type(e).__name__}"
    res.wall_s = time.monotonic() - t0
    res.peak_rss_mb = _try_peak_rss_mb()
    if res.peak_rss_mb is not None and res.peak_rss_mb > limits.ram_mb:
        res.resource_overflow = True
        res.blocked_reason = "ram_overflow"
    res.disk_mb_after = dir_size_mb(cwd)
    if (res.disk_mb_after - res.disk_mb_before) > limits.disk_mb:
        res.resource_overflow = True
        res.blocked_reason = "disk_overflow"
    res.network_enforced = False  # never claim enforcement without OS mechanism
    if res.junit_path is not None:
        res.junit_sha256 = log_digest(res.junit_path)
    return res


def _kill_tree(proc):
    try:
        if hasattr(os, "killpg"):
            os.killpg(os.getpgid(proc.pid), 9)
        else:
            proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def read_log(path, max_bytes=1 << 20):
    try:
        with open(path, "rb") as f:
            data = f.read(max_bytes)
        return data.decode("utf-8", "replace")
    except OSError:
        return ""


def log_digest(path):
    from .hashes import sha256_file
    try:
        return sha256_file(path)
    except OSError:
        return None