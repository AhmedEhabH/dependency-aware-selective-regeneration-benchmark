"""M17_D7_R4_BEHAVIORAL_CALIBRATION_N12_R2 — Attempt-2 backend-contract regression.

OWNER-AUTHORIZED corrective instrumentation test (Attempt-2).

Purpose: catch exactly the Attempt-1 instrument defect.  ``WslDockerBackend.run``
prepends the ``docker`` CLI, so the behavioral command must begin with
``["run", ...]`` and NOT ``["docker", "run", ...]``.  If a call site ever passes
a leading ``"docker"``, the plan fails closed with ``unknown flag: --rm`` before
any scientific container runs.

This test exercises the REAL ``WslDockerBackend`` command path against an
already-local qualified image with a harmless ``run --rm --network=none ...
true`` smoke.  No network, no pull, no build, no target-repository behavioral
execution.  It skips cleanly when the local Linux substrate or image is
unavailable (portable suite).
"""
from __future__ import annotations

import pytest

from benchmark.wp2.linux_adapter import WslDockerBackend

IMAGE = "envcanon/saleor-env-base-py312-bookworm:latest"
DISTRO = "Ubuntu-24.04"

# Qualified local image only; never pulled, never built, network none.
LOCAL_IMAGE_IDS = {
    "envcanon/saleor-env-base-py312-bookworm:latest":
        "sha256:b9e35d98a9b119ac6c265732308231581a88ad60d8c33dbbfd214cb82bf80a27",
}


def _ready() -> tuple[bool, str]:
    try:
        backend = WslDockerBackend(distro=DISTRO)
        r = backend.run(["version", "--format", "{{.Server.Version}}"], timeout_s=60)
        if r.returncode != 0:
            return False, "docker engine unavailable"
        r = backend.run(["image", "inspect", IMAGE], timeout_s=60)
        if r.returncode != 0:
            return False, f"local image {IMAGE} not present"
        return True, ""
    except Exception as exc:  # pragma: no cover - defensive
        return False, str(exc)


READY, READY_REASON = _ready()


@pytest.mark.skipif(not READY, reason=READY_REASON)
class TestWslDockerBackendCommandContract:
    """Attempt-2 regression: behavioral command must begin with ``run``."""

    def test_run_first_is_valid_offline_smoke(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        cmd = [
            "run", "--rm", "--network=none",
            "--entrypoint", "sh", IMAGE, "-lc", "echo CONTRACT_OK",
        ]
        r = backend.run(cmd, timeout_s=120)
        assert r.returncode == 0, f"run-first smoke failed: {r.stdout} {r.stderr}"
        assert "CONTRACT_OK" in r.stdout

    def test_docker_docker_run_is_rejected(self) -> None:
        # Confirms the Attempt-1 instrument defect is actually caught by the backend.
        backend = WslDockerBackend(distro=DISTRO)
        cmd = [
            "docker", "run", "--rm", "--network=none",
            "--entrypoint", "sh", IMAGE, "-lc", "echo SHOULD_NOT_RUN",
        ]
        r = backend.run(cmd, timeout_s=120)
        assert r.returncode != 0, "dangerous double-docker argv unexpectedly accepted"
        assert "unknown flag" in r.stderr or "not a docker command" in r.stderr

    def test_local_image_identity(self) -> None:
        backend = WslDockerBackend(distro=DISTRO)
        r = backend.run(["image", "inspect", "-f", "{{.Id}}", IMAGE], timeout_s=60)
        assert r.returncode == 0, "could not inspect local qualified image"
        assert r.stdout.strip() == LOCAL_IMAGE_IDS[IMAGE]
