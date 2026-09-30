#!/usr/bin/env python3
"""Human-only M14R authorization writer (brain-authored kit). ZERO model/API.

Writes research/wp2/m14r_v1/human_authorization.json bound to the frozen M14R design hash,
the M14R membership hash (produced by the zero-API readiness), the model route,
allow_fallbacks=false and 0 < max spend <= $3.00, then commits exactly that file and pushes
main. It refuses after any paid M14R evidence exists.

  python scripts/wp2_m14r_authorize.py --approve "I_AUTHORIZE_WP2_M14R_V1=YES" --by "NAME" --max-usd 3.0
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
R = P / "research/wp2/m14r_v1"
D = R / "m14r_design_freeze_v1.json"
M = R / "m14r_membership.json"
OUT = R / "human_authorization.json"
TOKEN = "I_AUTHORIZE_WP2_M14R_V1=YES"
MAX_USD = 3.0


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
        raise SystemExit("AUTH_REFUSED membership missing (run the controller --until R04_MEMBERSHIP)")
    m, d = load(M), load(D)
    if m.get("verdict") != "OK":
        raise SystemExit("AUTH_REFUSED membership verdict is not OK")
    if not (0 < max_usd <= MAX_USD):
        raise SystemExit(f"AUTH_REFUSED max-usd must be > 0 and <= {MAX_USD}")
    r = {"artifact": "m14r_human_authorization", "authorized": True, "authorized_by": by,
         "authorized_utc": utc, "approval_token": TOKEN,
         "design_artifact_sha256": d["artifact_sha256"],
         "membership_artifact_sha256": m["artifact_sha256"],
         "max_generation_spend_usd": max_usd, "model": "qwen/qwen3-coder",
         "provider": "deepinfra/turbo", "allow_fallbacks": False, "artifact_sha256": ""}
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
    if (R / "episodes").exists() or (R / "ledger").exists():
        raise SystemExit("AUTH_REFUSED paid M14R evidence already exists")
    mrel = M.relative_to(P).as_posix()
    if git("ls-files", "--error-unmatch", mrel).returncode or \
            git("status", "--porcelain", "--", mrel).stdout.strip():
        raise SystemExit("AUTH_REFUSED membership is not committed cleanly")
    if git("diff", "--cached", "--name-only").stdout.strip():
        raise SystemExit("AUTH_REFUSED staged changes present")
    r = build(a.by, a.max_usd,
              dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    rel = OUT.relative_to(P).as_posix()
    for args in (("add", "--", rel), ("commit", "-q", "-m",
                                      "evidence(wp2): human authorization for M14R V1")):
        q = git(*args)
        if q.returncode:
            raise SystemExit("AUTH_COMMIT_FAIL " + (q.stdout + q.stderr)[-1500:])
    pushed = git("push", "origin", "main").returncode == 0
    print("M14R_HUMAN_AUTH_COMPLETE")
    print(f"AUTHORIZED_BY={a.by}")
    print(f"MAX_GENERATION_SPEND_USD={a.max_usd}")
    print(f"PUSH_MAIN={'YES' if pushed else 'NO (the controller pushes later)'}")
    print("MODEL_API_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
