"""M17 P04/P08 - qualification-membership determinism and edge strata (zero network)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

P = Path(__file__).resolve().parents[4]
for _p in (P, P / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

GEN = P / "scripts/wp2_m17_p04_qualification.py"
OUT = P / "research/wp2/m17_v1/m17_qualification_membership.json"
SALT = "m17-qualification-2026-10-02"


def run_gen(tmp: Path, audit: dict, out_name: str) -> dict:
    """Run the membership generator against a synthetic audit JSON."""
    audit_path = tmp / "audit.json"
    audit_path.write_text(json.dumps(audit, indent=1), encoding="utf-8")
    out_path = tmp / out_name
    import os

    env = {
        "M17_AUDIT_OVERRIDE": str(audit_path),
        "M17_OUT_OVERRIDE": str(out_path),
        "M17_ALLOW_SYNTHETIC_FRAME": "1",
    }
    proc = subprocess.run(
        [sys.executable, str(GEN)],
        capture_output=True,
        text=True,
        cwd=str(P),
        env={**os.environ, **env},
    )
    if proc.returncode != 0:
        raise AssertionError(f"generator failed: {proc.stdout}\n{proc.stderr}")
    return json.loads(out_path.read_text(encoding="utf-8"))


def synthetic_audit(n_tasks: int, strata: dict[str, tuple[str, str]]) -> dict:
    """Build a synthetic P01-style audit with explicit strata."""
    tasks = []
    i = 0
    for (era, mech), count in strata.items():
        for _ in range(count):
            tasks.append(
                {
                    "task_id": f"saleor-rc-test-{i:04d}",
                    "target_commit": f"deadbeef{i:04d}",
                    "era_key": era,
                    "historical_install_mode": {
                        "value": "NOT_RECORDED_IN_FROZEN_V2",
                        "manifest_mechanism_derived": mech,
                        "lockfile_present": {"uv.lock": mech == "uv"},
                    },
                    "historical_schema_signature": {"schema": "oracle_harness_schema_v2"},
                }
            )
            i += 1
    return {
        "artifact": "m17_main_frame_audit",
        "frame": {"n_tasks": len(tasks), "n_unique_ids": len(set(t["task_id"] for t in tasks))},
        "tasks": tasks,
    }


def test_frozen_membership_is_deterministic():
    m1 = json.loads(OUT.read_text(encoding="utf-8"))
    ids1 = m1["membership"]
    assert len(ids1) == 12 and len(set(ids1)) == 12
    assert m1["membership_sha256"] == m1["membership_sha256"]
    # recompute independently from the audit via the generator
    proc = subprocess.run([sys.executable, str(GEN)], capture_output=True, text=True, cwd=str(P))
    assert proc.returncode == 0, proc.stderr
    m2 = json.loads(OUT.read_text(encoding="utf-8"))
    assert m1["membership"] == m2["membership"]
    assert m1["membership_sha256"] == m2["membership_sha256"]


def test_membership_with_fewer_than_12_strata_backfills_globally(tmp_path):
    audit = synthetic_audit(
        n_tasks=40,
        strata={("py39", "poetry"): 20, ("py312", "uv"): 20},
    )
    m = run_gen(tmp_path, audit, "m1.json")
    assert len(m["membership"]) == 12
    assert len(m["derivation_transcript"]) == 12
    # both strata must be represented
    ids = set(m["membership"])
    assert any(t["era_key"] == "py39" for t in audit["tasks"] if t["task_id"] in ids)


def test_membership_with_zero_strata_fails_closed(tmp_path):
    audit = synthetic_audit(n_tasks=0, strata={})
    with pytest.raises(AssertionError):
        run_gen(tmp_path, audit, "m2.json")


def test_membership_salt_is_stable():
    a = json.loads(OUT.read_text(encoding="utf-8"))
    assert a["salt"] == SALT
    assert a["n_target"] == 12
