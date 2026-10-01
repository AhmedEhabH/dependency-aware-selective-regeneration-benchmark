#!/usr/bin/env python3
"""Human-only M15-R authorization writer (brain-authored kit). ZERO model/API.

Writes research/wp2/m15r_v1/human_authorization.json bound to the frozen M15-R design hash,
the M15-R membership hash (produced by the zero-API S0 readiness), the generation route,
allow_fallbacks=false, the frozen protocol-v3 Agent and $2.00 <= max total spend <= $3.00
(Agent localization + S2 + S3 together; at least $2.00 so that the Agent worst case plus
the generation headroom fit). It then commits exactly that file and pushes main.
It refuses after any paid M15-R evidence exists.

  python scripts/wp2_m15r_authorize.py --approve "I_AUTHORIZE_WP2_M15R_V1=YES" --by "NAME" --max-usd 3.0
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parents[1]
R = P / "research/wp2/m15r_v1"
D = R / "m15r_design_freeze_v1.json"
M = R / "m15r_membership.json"
OUT = R / "human_authorization.json"
TOKEN = "I_AUTHORIZE_WP2_M15R_V1=YES"
MAX_USD, MIN_USD = 3.0, 2.0


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def sha_obj(x: object) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=P, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def build(by: str, max_usd: float, utc: str) -> dict:
    if not M.exists():
        raise SystemExit("AUTH_REFUSED membership missing (run the controller --until Q03_MEMBERSHIP)")
    m, d = load(M), load(D)
    if m.get("verdict") != "OK":
        raise SystemExit("AUTH_REFUSED membership verdict is not OK (M15R_POOL_INSUFFICIENT)")
    if not (MIN_USD <= max_usd <= MAX_USD):
        raise SystemExit(f"AUTH_REFUSED max-usd must be >= {MIN_USD} (Agent worst case + S2/S3 "
                         f"headroom) and <= {MAX_USD}")
    r = {"artifact": "m15r_human_authorization", "authorized": True, "authorized_by": by,
         "authorized_utc": utc, "approval_token": TOKEN,
         "design_artifact_sha256": d["artifact_sha256"],
         "membership_artifact_sha256": m["artifact_sha256"],
         "max_total_spend_usd": max_usd, "scope_of_spend":
         "Agent localization (protocol v3, 3 runs per member) + S2 GOLD G0 + S3 (only if S2 gate PASS)",
         "model": "qwen/qwen3-coder", "provider": "deepinfra/turbo", "allow_fallbacks": False,
         "agent_protocol": "wp1b_frozen_agent_protocol_v3", "artifact_sha256": ""}
    r["artifact_sha256"] = sha_obj(copy.deepcopy(r))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", required=True)
    ap.add_argument("--by", required=True)
    ap.add_argument("--max-usd", required=True, type=float)
    a = ap.parse_args()
    if a.approve != TOKEN:
        raise SystemExit("AUTH_REFUSED token mismatch")
    for sub in ("agent", "episodes", "ledger"):
        if (R / sub).exists():
            raise SystemExit(f"AUTH_REFUSED paid M15-R evidence already exists ({sub})")
    mrel = M.relative_to(P).as_posix()
    if git("ls-files", "--error-unmatch", mrel).returncode or \
            git("status", "--porcelain", "--", mrel).stdout.strip():
        raise SystemExit("AUTH_REFUSED membership is not committed cleanly")
    if git("diff", "--cached", "--name-only").stdout.strip():
        raise SystemExit("AUTH_REFUSED staged changes present")
    r = build(a.by, a.max_usd,
              dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    rel = OUT.relative_to(P).as_posix()
    for args in (("add", "--", rel), ("commit", "-q", "-m",
                                      "evidence(wp2): human authorization for M15-R V1")):
        q = git(*args)
        if q.returncode:
            raise SystemExit("AUTH_COMMIT_FAIL " + (q.stdout + q.stderr)[-1500:])
    pushed = git("push", "origin", "main").returncode == 0
    print("M15R_HUMAN_AUTH_COMPLETE")
    print(f"AUTHORIZED_BY={a.by}")
    print(f"MAX_TOTAL_SPEND_USD={a.max_usd}")
    print(f"PUSH_MAIN={'YES' if pushed else 'NO (the controller pushes later)'}")
    print("MODEL_API_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
