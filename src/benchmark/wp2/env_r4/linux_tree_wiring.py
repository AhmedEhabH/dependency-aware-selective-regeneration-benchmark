"""R4 materialization wiring seam — routes to the qualified R4-C materializer.

Mission ``M17_D7_R4_I2_LINUX_MATERIALIZATION_WIRING`` wires the already
qualified R4-C Linux-faithful materializer
(``benchmark.wp2.env_r4.linux_tree_materialize``) into the smallest R4-facing
execution/materialization seam that later I4 convergence and the corrected R4
census/calibration driver can consume.

This facade:

- accepts the explicit repository/source information required by the qualified
  R4-C ``Materializer`` (Linux-side Git repository path and a local image);
- accepts an explicit Git commit/object identity;
- accepts the explicit Linux-side destination/materialization target (Docker
  volume) exactly as the R4-C C API requires;
- delegates repository-tree creation entirely to R4-C
  (``Materializer.materialize``), which is object-authoritative (local Git
  ``ls-tree`` / ``cat-file``) and preserves Git modes and Linux-valid paths;
- NEVER silently falls back to Windows working-tree copying,
  ``shutil.copytree`` from the Windows checkout, NTFS as repository authority,
  or host-working-tree executable bits;
- preserves R4-C fail-closed behavior (``MaterializeError`` propagates
  unchanged; blank inputs fail closed at the seam);
- contains no task-ID / repository-ID / commit-ID special cases;
- is deterministic for identical inputs (frozen source descriptor, verbatim
  commit/volume pass-through, no mutable state).

This module is track-owned wiring.  It does NOT modify the frozen shared
interface (``contracts.py`` / ``__init__.py``) and does not import it.
"""
from __future__ import annotations

from dataclasses import dataclass

from benchmark.wp2.env_r4.linux_tree_materialize import MaterializeError, Materializer
from benchmark.wp2.linux_adapter import LinuxBackend


def _require_non_blank(value: str, label: str) -> str:
    if not value or not value.strip():
        raise MaterializeError(f"{label} must not be blank (fail closed)")
    return value


@dataclass(frozen=True)
class R4MaterializationSource:
    """Explicit repository/source information required by R4-C.

    ``repo_linux_path`` is the local Git repository as seen inside the Linux
    backend (e.g. ``/opt/wp2_v2/saleor-cache``); it is mounted read-only into
    each container and is the object-authoritative source.  ``image`` must
    already exist locally; R4-C never pulls it.
    """

    image: str
    repo_linux_path: str
    mount_src: str = "/src"
    mount_out: str = "/out"
    image_verified: bool = False

    def __post_init__(self) -> None:
        _require_non_blank(self.image, "image")
        _require_non_blank(self.repo_linux_path, "repo_linux_path")
        _require_non_blank(self.mount_src, "mount_src")
        _require_non_blank(self.mount_out, "mount_out")


class LinuxTreeWiring:
    """Single R4-facing materialization entry point backed by qualified R4-C.

    ``materializer`` is a test-only injection seam; by default the qualified
    R4-C ``Materializer`` is constructed from the explicit ``source``.
    """

    def __init__(
        self,
        backend: LinuxBackend,
        source: R4MaterializationSource,
        *,
        materializer: Materializer | None = None,
    ) -> None:
        self.source = source
        if materializer is None:
            materializer = Materializer(
                backend=backend,
                image=source.image,
                repo_linux_path=source.repo_linux_path,
                mount_src=source.mount_src,
                mount_out=source.mount_out,
                image_verified=source.image_verified,
            )
        self._materializer = materializer

    @property
    def materializer(self) -> Materializer:
        """The qualified R4-C materializer this seam delegates to."""
        return self._materializer

    def materialize(self, commit: str, volume: str) -> int:
        """Materialize ``commit`` into the existing empty Linux ``volume``.

        Delegates repository-tree creation verbatim to the qualified R4-C
        materializer.  Fails closed (``MaterializeError``) on blank inputs at
        the seam and on any R4-C materialization failure; never falls back to
        a Windows working-tree copy.
        """
        commit = _require_non_blank(commit, "commit")
        volume = _require_non_blank(volume, "volume")
        return self._materializer.materialize(commit, volume)
