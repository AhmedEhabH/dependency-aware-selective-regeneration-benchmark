"""WP-1a efficiency accounting - two RM-CSS cost views + arm accounting schema.

Per arm (repository_agent / SIP / RM-CSS): prompt tokens, completion tokens,
total tokens, model calls, wall time, USD, mean per task.

RM-CSS cost is reported in TWO logically distinct views (no double counting):
  A. Marginal / per-change operational cost: SIP inference call cost + query
     embedding/dense incremental cost + memory lookup/classifier incremental
     cost. Reusable indexes already built are NOT re-charged.
  B. Preprocessing / setup cost: one-time embedding corpus/index build +
     one-time repository-memory/index build (wall time + API/local compute
     provenance).

Amortized examples at N=50 and N=300: setup cost / N added to the marginal
per-task cost WITHOUT charging the full one-time build to every task.

Latency provenance rule: stored SIP/RM-CSS latency from an earlier
endpoint/machine is NOT directly same-machine comparable with fresh agent
latency; keep latency descriptive unless re-measured under a matched
environment without changing predictions.
"""
from __future__ import annotations

from dataclasses import dataclass

# Field contract for one arm's efficiency record.
ARM_EFFICIENCY_FIELDS: tuple[str, ...] = (
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "model_calls",
    "wall_seconds",
    "usd_cost",
    "mean_per_task_tokens",
    "mean_per_task_calls",
    "mean_per_task_usd",
    "mean_per_task_wall_seconds",
)

RMCSS_MARGINAL_VIEW_FIELDS: tuple[str, ...] = (
    "sip_inference_cost_usd",
    "query_embedding_incremental_cost_usd",
    "dense_incremental_cost_usd",
    "memory_lookup_incremental_cost_usd",
    "classifier_incremental_cost_usd",
    "total_marginal_usd",
    "note_no_double_counting",
)

RMCSS_SETUP_VIEW_FIELDS: tuple[str, ...] = (
    "embedding_corpus_index_build_usd",
    "repository_memory_index_build_usd",
    "setup_wall_seconds",
    "setup_compute_provenance",
    "amortized_at_n50_usd_per_task",
    "amortized_at_n300_usd_per_task",
)


@dataclass(frozen=True)
class ArmEfficiency:
    arm: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model_calls: int
    wall_seconds: float
    usd_cost: float

    @property
    def n_tasks(self) -> int:
        raise NotImplementedError

    def per_task(self, n_tasks: int) -> dict[str, float]:
        return {
            "mean_per_task_tokens": self.total_tokens / n_tasks if n_tasks else 0.0,
            "mean_per_task_calls": self.model_calls / n_tasks if n_tasks else 0.0,
            "mean_per_task_usd": self.usd_cost / n_tasks if n_tasks else 0.0,
            "mean_per_task_wall_seconds": self.wall_seconds / n_tasks if n_tasks else 0.0,
        }

    def record(self, n_tasks: int) -> dict[str, int | float | str]:
        return {
            "arm": self.arm,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "model_calls": self.model_calls,
            "wall_seconds": self.wall_seconds,
            "usd_cost": self.usd_cost,
            **self.per_task(n_tasks),
        }


def rmcss_marginal_view(
    *,
    sip_inference_cost_usd: float,
    query_embedding_incremental_cost_usd: float,
    dense_incremental_cost_usd: float,
    memory_lookup_incremental_cost_usd: float,
    classifier_incremental_cost_usd: float,
    n_tasks: int,
) -> dict[str, float | str]:
    total = (
        sip_inference_cost_usd
        + query_embedding_incremental_cost_usd
        + dense_incremental_cost_usd
        + memory_lookup_incremental_cost_usd
        + classifier_incremental_cost_usd
    )
    return {
        "sip_inference_cost_usd": sip_inference_cost_usd,
        "query_embedding_incremental_cost_usd": query_embedding_incremental_cost_usd,
        "dense_incremental_cost_usd": dense_incremental_cost_usd,
        "memory_lookup_incremental_cost_usd": memory_lookup_incremental_cost_usd,
        "classifier_incremental_cost_usd": classifier_incremental_cost_usd,
        "total_marginal_usd": total,
        "mean_marginal_usd_per_task": total / n_tasks if n_tasks else 0.0,
        "note_no_double_counting": (
            "already-built reusable indexes (embedding corpus cache, repository "
            "memory index) are NOT re-charged per task; only incremental "
            "per-change operations are charged."
        ),
    }


def rmcss_setup_view(
    *,
    embedding_corpus_index_build_usd: float,
    repository_memory_index_build_usd: float,
    setup_wall_seconds: float,
    setup_compute_provenance: str,
) -> dict[str, float | str]:
    setup_total = (
        embedding_corpus_index_build_usd + repository_memory_index_build_usd
    )
    return {
        "embedding_corpus_index_build_usd": embedding_corpus_index_build_usd,
        "repository_memory_index_build_usd": repository_memory_index_build_usd,
        "setup_total_usd": setup_total,
        "setup_wall_seconds": setup_wall_seconds,
        "setup_compute_provenance": setup_compute_provenance,
        "amortized_at_n50_usd_per_task": setup_total / 50 if setup_total else 0.0,
        "amortized_at_n300_usd_per_task": setup_total / 300 if setup_total else 0.0,
    }


LATENCY_PROVENANCE_RULE: str = (
    "Stored SIP/RM-CSS latency from an earlier endpoint/machine is NOT directly "
    "same-machine comparable with fresh repository-agent latency. Latency stays "
    "descriptive unless re-measured under a matched environment WITHOUT changing "
    "predictions."
)
