"""M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 — Attempt-3 worktree-volume probe.

OWNER-AUTHORIZED (Attempt-3) instrumentation integration probe.

Purpose: prove the real R4-C materializer + WslDockerBackend worktree-volume
contract BEFORE freezing Attempt-3.  It exercises:

1. materialize the exact Unit-1 Git commit into a fresh named Docker volume;
2. mount that same named volume read-only at /wt0 in the ALREADY-LOCAL Unit-1
   execution image;
3. run with --network=none;
4. verify + persist:  test -d /wt0 ; test -f /wt0/pyproject.toml ;
   test -d /wt0/saleor ;
5. record `ls -la /wt0` and the exact named-volume identity;
6. clean the probe-owned volume after evidence is saved.

Instrumentation-only: no dependency installation, no target tests, no package
downloads, no Docker pull/build, no scientific result.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from benchmark.wp2.env_r4.linux_tree_materialize import (
    encode_runner_script,
    ensure_empty_volume,
    remove_volume,
    volume_exists,
)
from benchmark.wp2.env_r4.linux_tree_wiring import LinuxTreeWiring, R4MaterializationSource
from benchmark.wp2.linux_adapter import WslDockerBackend

# Exact Unit-1 (vu-b9808f19ace4) member task test commit.
UNIT1_TASK = "saleor-rc-e6198146186d"
UNIT1_COMMIT = "e6198146186d1c782bf46f6c9439fa05b1049b2f"
# Unit-1 execution image (must be already-local; never pulled/built).
UNIT1_EXECUTION_IMAGE = "envcanon/saleor-env-native-nat-34c1a3756742:latest"
WSL_REPO = "/opt/wp2_v2/saleor-cache"
MATERIALIZE_IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"
DISTRO = "Ubuntu-24.04"
PROBE_ROOT = Path(r"D:\WP2\runs\r4-behavioral-calibration-n12-r2-attempt3-2026-10-13\probe")


def _ready() -> tuple[bool, str]:
    try:
        backend = WslDockerBackend(distro=DISTRO)
        r = backend.run(["version", "--format", "{{.Server.Version}}"], timeout_s=60)
        if r.returncode != 0:
            return False, "docker engine unavailable"
        for img in (UNIT1_EXECUTION_IMAGE, MATERIALIZE_IMAGE):
            r = backend.run(["image", "inspect", img], timeout_s=60)
            if r.returncode != 0:
                return False, f"local image {img} not present"
        r = backend.run(
            [
                "run", "--rm", "--network", "none",
                "-v", f"{WSL_REPO}:/src:ro",
                "--entrypoint", "bash", MATERIALIZE_IMAGE,
                "-lc", f"git -C /src rev-parse --verify '{UNIT1_COMMIT}'",
            ],
            timeout_s=120,
        )
        if r.returncode != 0:
            return False, f"target commit not reachable from {WSL_REPO}"
        return True, ""
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)


READY, READY_REASON = _ready()


@pytest.mark.skipif(not READY, reason=READY_REASON)
class TestWorktreeVolumeProbe:
    """Attempt-3 C: real materializer -> named volume -> /wt0 mount probe."""

    def test_materialize_and_mount_probe(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        volume = f"r4n12_probe_{uuid.uuid4().hex[:10]}"
        PROBE_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            ensure_empty_volume(backend, volume)
            wiring = LinuxTreeWiring(
                backend,
                R4MaterializationSource(
                    image=MATERIALIZE_IMAGE,
                    repo_linux_path=WSL_REPO,
                    image_verified=True,
                ),
            )
            count = wiring.materialize(UNIT1_COMMIT, volume)
            assert count > 0, "materialization produced zero files"
            probe_script = (
                "set -e\n"
                'echo "PROBE_IS_DIR_WT0=$(test -d /wt0 && echo 1 || echo 0)"\n'
                'echo "PROBE_PYPROJECT=$(test -f /wt0/pyproject.toml && echo 1 || echo 0)"\n'
                'echo "PROBE_SALEOR_DIR=$(test -d /wt0/saleor && echo 1 || echo 0)"\n'
                "echo '=== LS /wt0 ==='\n"
                "ls -la /wt0 | head -40\n"
            )
            # Base64 transport so WSL argv cannot mangle $(), &&, quotes
            # (identical to the R4-C / calibrated runner contract).
            r = backend.run(
                [
                    "run", "--rm", "--network=none",
                    "-v", f"{volume}:/wt0:ro",
                    "--entrypoint", "sh", UNIT1_EXECUTION_IMAGE,
                    "-lc", encode_runner_script(probe_script, entrypoint="sh"),
                ],
                timeout_s=180,
            )
            assert r.returncode == 0, f"probe container failed: {r.stdout} {r.stderr}"
            output = r.stdout
            assert "PROBE_IS_DIR_WT0=1" in output, f"/wt0 not a directory:\n{output}"
            assert "PROBE_PYPROJECT=1" in output, f"pyproject.toml missing:\n{output}"
            assert "PROBE_SALEOR_DIR=1" in output, f"saleor dir missing:\n{output}"
            evidence = {
                "probe": "worktree-volume contract",
                "task_id": UNIT1_TASK,
                "commit": UNIT1_COMMIT,
                "execution_image": UNIT1_EXECUTION_IMAGE,
                "materialize_image": MATERIALIZE_IMAGE,
                "volume": volume,
                "file_count": count,
                "returncode": r.returncode,
                "checks": {
                    "wt0_is_dir": "1",
                    "pyproject_toml": "1",
                    "saleor_dir": "1",
                },
                "ls_wt0": output.split("=== LS /wt0 ===")[-1][:2000],
                "network": "--network=none",
            }
            (PROBE_ROOT / "worktree_volume_probe_evidence.json").write_text(
                json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        finally:
            if volume_exists(backend, volume):
                remove_volume(backend, volume)
            assert not volume_exists(backend, volume), "probe volume not cleaned"
