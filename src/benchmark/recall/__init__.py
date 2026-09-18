"""First-pass recall bottleneck — DEVELOPMENT-only analysis (T3, ZERO API).

Submodules:
- data: frozen DEVELOPMENT task + FN-feature layer (parent-visible only)
- taxonomy: deterministic FN taxonomy
- ceilings: source-specific oracle recall ceilings
- queues: simple ADD-queue candidates
- gate: progression gate
"""
from __future__ import annotations

from .data import RecallTask, aggregate_tp_fp_fn, load_dev_tasks

__all__ = ["RecallTask", "aggregate_tp_fp_fn", "load_dev_tasks"]
