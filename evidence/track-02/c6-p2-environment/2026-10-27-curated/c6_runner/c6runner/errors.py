# -*- coding: utf-8 -*-
"""Deterministic failure taxonomy for the C6 runner (fail-closed)."""


class C6Stop(Exception):
    """Global STOP gate. Any occurrence halts the run and preserves receipts."""

    CLASSIFICATION = "C6_STOP"

    def __init__(self, classification, detail, context=None):
        super().__init__(f"{classification}: {detail}")
        self.classification = classification
        self.detail = detail
        self.context = context or {}


class NotAuthorized(C6Stop):
    CLASSIFICATION = "NOT_AUTHORIZED"


class FrozenInputDrift(C6Stop):
    CLASSIFICATION = "FROZEN_INPUT_DRIFT"


class MissingApproval(C6Stop):
    CLASSIFICATION = "MISSING_APPROVAL"


class BudgetExceeded(C6Stop):
    CLASSIFICATION = "BUDGET_EXCEEDED"


class LeakageDetected(C6Stop):
    CLASSIFICATION = "LEAKAGE_DETECTED"


class Blocked(C6Stop):
    """Infrastructure/fixture blockage for ONE task: BLOCKED, never PASS/FAIL."""

    CLASSIFICATION = "BLOCKED"


class EnvDrift(C6Stop):
    """The resolved runtime (image digest, interpreter, wheelhouse) drifts
    from the operator-frozen pins: GLOBAL STOP ENV_DRIFT."""

    CLASSIFICATION = "ENV_DRIFT"


class C6TaskError(Exception):
    """Non-stop per-task infra error (converted to BLOCKED, never silent)."""


class CommandTimeout(Exception):
    pass


class ResourceOverflow(Exception):
    pass


class NetworkBlocked(Exception):
    """Raised by the injected offline gate inside a child process."""