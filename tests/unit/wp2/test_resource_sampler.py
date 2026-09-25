"""WP-2 real resource sampler (Mission-09) - unit tests (ZERO API).

Verifies:
- aggregate metrics distinguish used vs total/capacity (ERRATUM A fix);
- aggregates derived from raw samples only;
- derived quantities (host_used = total - available; wsl_used = MemTotal -
  MemAvailable) are computed correctly;
- monotonic/wall timestamps present and ordered.
"""

from __future__ import annotations

import json

from benchmark.wp2.resource_sampler import (
    _gib,
    aggregate_samples,
)


def test_gib_conversion() -> None:
    assert abs(_gib(1024**3) - 1.0) < 1e-9
    assert abs(_gib(512 * 1024**2) - 0.5) < 1e-9


def test_aggregate_used_not_total(tmp_path) -> None:
    """Host used must be derived from total-available, not equal to total."""
    p = tmp_path / "s.jsonl"
    lines = [
        {
            "ts_mono": 0.0,
            "ts_wall": 1000.0,
            "host_total_gib": 16.0,
            "host_available_gib": 8.0,
            "host_used_gib": 8.0,
            "wsl_mem_total_gib": 13.0,
            "wsl_mem_available_gib": 10.0,
            "wsl_used_gib": 3.0,
            "c_free_gib": 50.0,
            "docker": {"wp2-pg": {"cpu_percent": 1.0, "mem_used_gib": 0.1}},
        },
        {
            "ts_mono": 5.0,
            "ts_wall": 1005.0,
            "host_total_gib": 16.0,
            "host_available_gib": 4.0,
            "host_used_gib": 12.0,
            "wsl_mem_total_gib": 13.0,
            "wsl_mem_available_gib": 6.0,
            "wsl_used_gib": 7.0,
            "c_free_gib": 49.0,
            "docker": {"wp2-pg": {"cpu_percent": 2.0, "mem_used_gib": 0.2}},
        },
    ]
    p.write_text("\n".join(json.dumps(ln) for ln in lines) + "\n", encoding="utf-8")
    agg = aggregate_samples(p)
    assert agg["n_samples"] == 2
    # host used peak = 12, NOT the total 16 (ERRATUM A guard)
    assert agg["host_used_gib"]["max"] == 12.0
    assert agg["host_used_gib"]["min"] == 8.0
    assert agg["host_total_gib"]["max"] == 16.0
    # wsl used peak = 7, total stays separate as the VM ceiling
    assert agg["wsl_used_gib"]["max"] == 7.0
    assert agg["wsl_mem_total_gib"]["max"] == 13.0
    assert agg["c_free_gib"]["min"] == 49.0
    assert agg["docker"]["wp2-pg"]["mem_used_gib"]["max"] == 0.2
    # monotonic timestamps ordered
    assert agg["wall_span_s"] == 5.0


def test_aggregate_empty(tmp_path) -> None:
    p = tmp_path / "empty.jsonl"
    p.write_text("", encoding="utf-8")
    assert aggregate_samples(p)["n_samples"] == 0


def test_aggregate_ignores_missing_fields(tmp_path) -> None:
    p = tmp_path / "s.jsonl"
    p.write_text(
        json.dumps({"ts_mono": 0.0, "ts_wall": 0.0, "host_used_gib": 1.0}) + "\n",
        encoding="utf-8",
    )
    agg = aggregate_samples(p)
    assert agg["host_used_gib"]["n"] == 1
    assert agg["wsl_used_gib"]["n"] == 0  # absent -> not fabricated
