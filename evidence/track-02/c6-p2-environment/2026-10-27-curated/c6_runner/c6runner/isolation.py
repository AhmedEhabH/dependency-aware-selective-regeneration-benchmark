# -*- coding: utf-8 -*-
"""OS-level isolation backends for candidate execution.

The python `sitecustomize` socket gate (resources.GATE_SOURCE) is retained ONLY
as defense-in-depth for python children; it is NOT an OS-level isolation
mechanism and must never be reported as one.

Genuine mechanisms implemented here:
  - docker (preferred): `docker run --network none --memory <cap> --pids-limit
    <n> --cpus <q> --read-only` — OS/container-level network, RAM, pid and CPU
    enforcement supplied by the container runtime.
  - job-object (Windows): hard process-memory limit via Job Objects; network is
    NOT enforceable at job level, so this backend can never satisfy a
    network_bytes == 0 plan (execution stays BLOCKED for such plans).

Resolution rules (fail-closed):
  - A plan whose `network_bytes == 0` requires a backend that provably
    enforces zero network (docker). If none resolves -> BLOCKED(...), never an
    unenforced run.
  - run_limited() records {python_gate_active, os_isolation_active,
    network_enforced, memory_enforced, disk_enforced, backend} truthfully.
"""
import os
import re
import shutil
import subprocess

from .errors import Blocked

PROBE_SCAN_TIMEOUT_S = 30


class IsolationDescriptor:
    def __init__(self, backend, memory, network, disk, pids, cpu, detail):
        self.backend = backend
        self.memory = memory
        self.network = network
        self.disk = disk
        self.pids = pids
        self.cpu = cpu
        self.detail = detail

    def as_dict(self):
        return {"backend": self.backend, "memory_enforced": self.memory,
                "network_enforced": self.network, "disk_enforced": self.disk,
                "pids_enforced": self.pids, "cpu_enforced": self.cpu,
                "detail": self.detail}

    def satisfies(self, plan) -> bool:
        """Can this backend enforce everything the plan demands?"""
        if plan.resources.get("network_bytes", 0) == 0 and not self.network:
            return False
        if plan.resources.get("ram_mb", 0) and not self.memory:
            return False
        if plan.resources.get("pids_limit") and not self.pids:
            return False
        return True


def _docker_available(detail=True):
    docker = shutil.which("docker")
    if not docker:
        return None
    try:
        out = subprocess.run(["docker", "info", "--format",
                              "{{.ServerVersion}}"],
                             capture_output=True, text=True, timeout=15,
                             check=False)
        if out.returncode != 0:
            return None
        return docker
    except (OSError, subprocess.TimeoutExpired):
        return None


def detect_backends() -> dict:
    """Probe and report every available OS-level isolation backend (read-only)."""
    res = {}
    d = _docker_available()
    if d:
        res["docker"] = IsolationDescriptor(
            "docker", memory=True, network=True, disk=False,
            pids=True, cpu=True, detail=f"docker CLI={d} daemon reachable")
    try:
        import win32job  # noqa: F401
        res["job-object"] = IsolationDescriptor(
            "job-object", memory=True, network=False, disk=False,
            pids=True, cpu=False,
            detail="pywin32 Job Objects: memory/pids hard caps; no network")
    except Exception:
        pass
    return res


def resolve_backend(plan) -> IsolationDescriptor:
    """Resolve the plan's required backend and prove it can enforce the plan.
    Fail-closed: return the descriptor only if satisfiable."""
    avail = detect_backends()
    wanted = getattr(plan, "isolation_backend", "docker")
    if wanted == "python-process":
        # harness-only backend: acknowledged in receipt, never satisfies
        # network_bytes==0 plans outside the harness. The runner refuses any
        # non-harness plan on this backend (BLOCKED, fail-closed).
        return IsolationDescriptor("python-process", memory=False,
                                   network=False, disk=False, pids=False,
                                   cpu=False,
                                   detail="harness backend (no OS enforcement)")
    desc = avail.get(wanted)
    if desc is None:
        raise Blocked("isolation_backend_unavailable",
                      f"backend={wanted} probed={sorted(avail)}")
    if not desc.satisfies(plan):
        raise Blocked("isolation_constraints_unmet",
                      f"backend={wanted} caps={desc.as_dict()} "
                      f"plan resources={plan.resources}")
    return desc


def immutable_ref(digest) -> str:
    """Immutable docker reference from a digest: docker image IDs are LOWERCASE
    hex, so an uppercase identity must never be handed to the docker CLI as the
    launch image (docker would treat it as a missing repo and attempt a pull)."""
    return "sha256:" + str(digest).lower()


def resolve_image_digest(image_ref) -> str:
    """Resolve the immutable local digest (docker image inspect, offline, no
    pull) for an image reference. Returns a 64-hex digest string or None when
    the image is not present locally / daemon unreachable."""
    if not image_ref:
        return None
    if image_ref.startswith("sha256:") and len(image_ref) == 64 + 7:
        return image_ref[7:].upper()
    try:
        out = subprocess.run(["docker", "image", "inspect", image_ref,
                              "--format", "{{.Id}}"],
                             capture_output=True, text=True, timeout=30,
                             check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    ident = (out.stdout or "").strip()
    if ident.startswith("sha256:"):
        ident = ident[7:]
    return ident.upper() if len(ident) == 64 else None


_IMAGE_PROBE_CACHE = {}


def probe_interpreter_version(image_ref, interpreter="python",
                              timeout_s=120):
    """Resolve the interpreter version INSIDE the pinned image with a tiny
    disposable probe container (--network none, read-only; never part of a
    candidate run). Cached per (image, interpreter)."""
    key = (image_ref, interpreter)
    if key in _IMAGE_PROBE_CACHE:
        return _IMAGE_PROBE_CACHE[key]
    try:
        out = subprocess.run(
            ["docker", "run", "--rm", "--network", "none", "--read-only",
             image_ref, interpreter, "--version"],
            capture_output=True, text=True, timeout=timeout_s, check=False)
    except (OSError, subprocess.TimeoutExpired):
        _IMAGE_PROBE_CACHE[key] = None
        return None
    text = (out.stdout or "") + (out.stderr or "")
    m = re.search(r"Python\s+(\d+\.\d+\.\d+[0-9a-zA-Z.]*)", text)
    ver = m.group(1) if m else None
    _IMAGE_PROBE_CACHE[key] = ver
    return ver


def docker_run(command, cwd, scratch_dir, limits, logs_dir, plan):
    """Execute `command` inside a fresh, disposable container with:
    --network none, --memory/--memory-swap hard caps, --pids-limit, --cpus,
    read-only rootfs, P tree mounted read-only at /work, scratch at /scratch.

    Deterministic identity and cleanup (finding F5):
      - the container is launched with `--cidfile <path>` and
        `--label c6.task=<task-sha12>`;
      - on timeout the CONTAINER id (from the cidfile, never the CLI host pid)
        is killed, waited and force-removed;
      - a bounded label sweep proves no orphaned container survives.

    Returns (exit_code, wall_s, kind, cleanup_evidence) or raises Blocked."""
    import time

    img = plan.image_digest
    if not img:
        raise Blocked("docker_image_not_pinned",
                      "plan.image_digest required for docker backend")
    image_ref = immutable_ref(img)
    if not limits:
        raise Blocked("docker_exec_infra", "limits required")
    os.makedirs(scratch_dir, exist_ok=True)
    cidpath = os.path.join(scratch_dir, "container.cid")
    if os.path.exists(cidpath):
        os.remove(cidpath)
    env_block = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTEST_ADDOPTS": "-p no:cacheprovider",
        "C6_ISOLATION": "docker",
        "C6_SCRATCH": "/scratch",
        "C6_WORKSPACE": "/work",
    }
    ram_m = int(max((plan.resources or {}).get("ram_mb", 0), 64))
    pids = int((plan.resources or {}).get("pids_limit", 512))
    cpus = str((plan.resources or {}).get("cpu_quota", 1.0))
    scratch_m = int((plan.resources or {}).get("scratch_mb", 5120))
    label = f"c6.task={str(plan.task)[:12]}"
    args = ["docker", "run", "--rm", "--network", "none",
            "--memory", f"{ram_m}m", "--memory-swap", f"{ram_m}m",
            "--pids-limit", str(pids), "--cpus", cpus,
            "--read-only",
            "--cidfile", cidpath,
            "--label", label,
            "--tmpfs", f"/scratch:rw,size={scratch_m}m,mode=1777",
            "--mount", f"type=bind,src={cwd},dst=/work,readonly",
            "--mount", f"type=bind,src={scratch_dir},dst=/scratch-dir",
            "--workdir", "/work"]
    for k, v in env_block.items():
        args += ["--env", f"{k}={v}"]
    args += [image_ref] + list(command)

    out_path = os.path.join(logs_dir, "stdout.log")
    err_path = os.path.join(logs_dir, "stderr.log")
    t0 = time.monotonic()
    cleanup = {}
    try:
        with open(out_path, "wb") as so, open(err_path, "wb") as se:
            proc = subprocess.Popen(args, stdout=so, stderr=se)
            try:
                proc.wait(timeout=float((plan.resources or {}).get("timeout_s", 1800)))
            except subprocess.TimeoutExpired:
                wall = time.monotonic() - t0
                cid = _read_cidfile(cidpath, label, 3.0)
                cleanup = _force_cleanup(cid, label)
                try:
                    proc.wait(timeout=15)   # bounded cancellation
                except subprocess.TimeoutExpired:
                    pass
                return 137, wall, "timeout", cleanup
            rc = proc.returncode
        # post-run orphan sweep (bounded; normally empty because of --rm)
        cleanup = _force_cleanup(None, label)
        return rc, time.monotonic() - t0, None, cleanup
    except Exception as e:  # noqa: BLE001 infra
        raise Blocked("docker_exec_infra", f"{type(e).__name__}: {e}") from e


def _read_cidfile(cidpath, label, wait_s):
    """Deterministic container identity: prefer the --cidfile value, fall back
    to a label query. Returns a container-id string or None."""
    import time as _t
    deadline = _t.monotonic() + wait_s
    while _t.monotonic() < deadline:
        if os.path.exists(cidpath):
            raw = open(cidpath, encoding="utf-8").read().strip()
            if raw:
                return raw
        _t.sleep(0.05)
    try:
        out = subprocess.run(["docker", "ps", "-aq", "--no-trunc",
                              "--filter", f"label={label}"],
                             capture_output=True, text=True, timeout=10,
                             check=False)
        ids = (out.stdout or "").strip().splitlines()
        return ids[0] if ids else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def _force_cleanup(cid, label):
    """Kill + wait + rm -f a specific container id, then sweep any remaining
    container with the task label (orphan proof). Returns evidence."""
    ev = {"container_id": cid, "killed": False, "waited": False,
          "removed": False, "orphans_detected": 0, "orphans_remaining": None}
    if cid:
        for cmd in (["docker", "kill", cid], ["docker", "wait", cid]):
            try:
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   timeout=15, check=False)
                ev["killed" if cmd[1] == "kill" else "waited"] = (r.returncode == 0)
            except (OSError, subprocess.TimeoutExpired):
                break
        try:
            r = subprocess.run(["docker", "rm", "-f", cid],
                               capture_output=True, text=True, timeout=15,
                               check=False)
            ev["removed"] = (r.returncode == 0)
        except (OSError, subprocess.TimeoutExpired):
            pass
    # bounded orphan sweep: ANY container still carrying this task label is
    # force-removed; the count proves no orphan survives.
    try:
        out = subprocess.run(["docker", "ps", "-aq", "--no-trunc",
                              "--filter", f"label={label}"],
                             capture_output=True, text=True, timeout=15,
                             check=False)
        leftovers = (out.stdout or "").strip().splitlines()
        ev["orphans_detected"] = len(leftovers)
    except (OSError, subprocess.TimeoutExpired):
        leftovers = []
    for lid in leftovers:
        subprocess.run(["docker", "rm", "-f", lid], capture_output=True,
                       timeout=15, check=False)
    try:
        out = subprocess.run(["docker", "ps", "-aq", "--no-trunc",
                              "--filter", f"label={label}"],
                             capture_output=True, text=True, timeout=15,
                             check=False)
        ev["orphans_remaining"] = len((out.stdout or "").strip().splitlines())
    except (OSError, subprocess.TimeoutExpired):
        ev["orphans_remaining"] = None
    return ev