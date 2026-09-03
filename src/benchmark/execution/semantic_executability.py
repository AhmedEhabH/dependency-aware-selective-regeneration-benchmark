"""D13 B4 — fail-closed semantic-executability gate.

A Pilot scenario is *semantically executable* against its pinned repository
base only when the base actually provides every capability the scenario's
acceptance criteria depend on.  Previously such scenarios could fail late at
build/validation time (or be silently mis-proven), e.g. ``saleor-loc-002`` asks
to expose a ``featuredProducts`` query filtering on ``is_featured=True``, but
the pinned Saleor base's ``Product`` model has no ``is_featured`` field — so
that scenario could never pass against the pinned base.

This gate is **fail-closed**:

* a scenario whose required capability is deterministically KNOWN to be absent
  from the pinned base is reported ``executable=False`` with the reason;
* a scenario whose required capability can only be verified from a staged
  repository (djangoCMS / Saleor) but whose repo is NOT locally available is
  reported ``verifiable=False`` (treated as not-PASS — it must be verified on
  target before launch, never silently claimed executable);
* only a scenario that is concretely verified — statically against a staged
  repo when available, or against a deterministically-true pinned fact — is
  reported ``executable=True``.

The gate never fabricates a PASS.  It is implemented as a small, deterministic
registry keyed on scenario capabilities so it runs the same everywhere the
scenario metadata is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from benchmark.core.models import Scenario


@dataclass(frozen=True)
class ExecutabilityVerdict:
    scenario_id: str
    executable: bool
    verifiable: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class _CapabilityProbe:
    name: str
    present_in_pinned_base: bool
    static_sentinel: str | None = None
    static_path: str | None = None


# Deterministic, pinned-base capability facts.  These encode what the FROZEN
# pinned repository bases provide.  ``present_in_pinned_base=False`` means the
# capability is CONFIRMED ABSENT from the pinned base → the scenario can never
# pass → fail-closed ``executable=False``.  ``True`` means the pinned base is
# structurally capable; where a staged repo is needed to confirm the exact
# sentinel the gate still requires local verification when a sentinel is set.
_PINNED_CAPABILITY_REGISTRY: dict[str, tuple[_CapabilityProbe, ...]] = {
    "todo-loc-001": (
        _CapabilityProbe(
            name="todo schema extensibility (Django models/serializers/views)",
            present_in_pinned_base=True,
            static_sentinel="class Task",
            static_path="todo/models.py",
        ),
    ),
    "saleor-loc-002": (
        _CapabilityProbe(
            name="pinned Saleor base provides a Product.is_featured field",
            present_in_pinned_base=False,
        ),
    ),
    "saleor-cross-007": (
        _CapabilityProbe(
            name="pinned Saleor base provides Product model + GraphQL schema infra",
            present_in_pinned_base=True,
            static_sentinel="class Product",
            static_path="saleor/product/models.py",
        ),
        _CapabilityProbe(
            name="pinned Saleor base provides webhook event infrastructure",
            present_in_pinned_base=True,
            static_sentinel="class WebhookEventType",
            static_path="saleor/webhook/event_types.py",
        ),
    ),
    "saleor-loc-001": (
        _CapabilityProbe(
            name="pinned Saleor base provides Product model + GraphQL schema infra",
            present_in_pinned_base=True,
            static_sentinel="class Product",
            static_path="saleor/product/models.py",
        ),
    ),
    "djangocms-cross-007": (
        _CapabilityProbe(
            name="pinned djangoCMS base provides editable page model + admin infra",
            present_in_pinned_base=True,
            static_sentinel="class Page",
            static_path="cms/models/pagemodel.py",
        ),
    ),
}


def _verify_static(
    probe: _CapabilityProbe,
    repository_root: Path | None,
) -> tuple[bool, bool]:
    """Return (present, verified).

    When a staged repository root is available and the probe declares a static
    sentinel, actually search for the marker in the pinned base.  Otherwise the
    probe can only be confirmed from the pinned-base fact table, and ``verified``
    reflects whether that fact alone is sufficient (i.e. no static sentinel was
    required).
    """
    if probe.static_sentinel is None:
        return probe.present_in_pinned_base, True
    if repository_root is None:
        return probe.present_in_pinned_base, False
    target = repository_root / (probe.static_path or "")
    if not target.is_file():
        return False, True
    try:
        present = probe.static_sentinel in target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False, True
    return present, True


def check_scenario_executability(
    scenario: Scenario,
    *,
    repository_root: str | Path | None = None,
) -> ExecutabilityVerdict:
    """Return a fail-closed executability verdict for a single scenario.

    The repository root is optional: when provided for a locally staged pinned
    base, static sentinel probes are run against the real artifacts.  When it is
    absent, only deterministically-known pinned-base facts are used, and any
    probe requiring an on-disk sentinel is left ``verifiable=False`` (fail-closed).
    """
    probes = _PINNED_CAPABILITY_REGISTRY.get(scenario.scenario_id, ())
    if not probes:
        return ExecutabilityVerdict(
            scenario_id=scenario.scenario_id,
            executable=False,
            verifiable=False,
            reasons=(
                "no pinned-base capability probes registered for this scenario "
                "(fail-closed)",
            ),
        )

    root: Path | None = Path(repository_root) if repository_root is not None else None
    reasons: list[str] = []
    all_present = True
    all_verified = True
    for probe in probes:
        present, verified = _verify_static(probe, root)
        if not present:
            all_present = False
            reasons.append(
                f"pinned base lacks required capability '{probe.name}'"
            )
        if not verified:
            all_verified = False
            reasons.append(
                f"capability '{probe.name}' requires an on-disk sentinel that "
                "could not be verified (no staged repository)"
            )

    executable = all_present and all_verified
    return ExecutabilityVerdict(
        scenario_id=scenario.scenario_id,
        executable=executable,
        verifiable=all_verified,
        reasons=tuple(reasons) if reasons else ("all pinned-base capabilities present",),
    )


def check_scenario_set_executability(
    scenarios: list[Scenario],
    *,
    repository_roots: dict[str, str | Path | None] | None = None,
) -> list[ExecutabilityVerdict]:
    roots = repository_roots or {}
    return [
        check_scenario_executability(s, repository_root=roots.get(s.repository))
        for s in scenarios
    ]
