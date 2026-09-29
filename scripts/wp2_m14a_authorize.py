#!/usr/bin/env python3
"""Human-only Pilot-A authorization writer (brain-authored corrected kit). ZERO model/API.

The M13B template research/wp2/pilot_v1_design/PILOT_A_HUMAN_AUTH_TEMPLATE.json is part of
the M13 freeze (hash-verified by M13 verify and by the M14A guard), so it is never edited.
This writes research/wp2/pilot_a_v1/human_authorization.json, bound to:
  the M13B template hash, the design hash, the final-membership hash, model, provider,
  allow_fallbacks=false and 0 < max spend <= $1.00 (the frozen Pilot-A ceiling),
then commits exactly that file and pushes main. It refuses after any paid evidence exists.

  python scripts/wp2_m14a_authorize.py --approve "I_AUTHORIZE_WP2_PILOT_A_V1=YES" --by "NAME" --max-usd 1.0
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
R = P / "research/wp2/pilot_a_v1"
D = P / "research/wp2/pilot_v1_design/pilot_design_freeze_v1.json"
T = P / "research/wp2/pilot_v1_design/PILOT_A_HUMAN_AUTH_TEMPLATE.json"
M = R / "pilot_final_membership.json"
OUT = R / "human_authorization.json"
TOKEN = "I_AUTHORIZE_WP2_PILOT_A_V1=YES"


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
        raise SystemExit("AUTH_REFUSED final membership missing (run the controller to P03)")
    m, d, t = load(M), load(D), load(T)
    if m.get("verdict") == "POOL_INSUFFICIENT" or len(m.get("A", [])) < 10:
        raise SystemExit("AUTH_REFUSED pool insufficient")
    if t.get("approval_token_required") != TOKEN or t.get("design_artifact_sha256") != \
            d["artifact_sha256"]:
        raise SystemExit("AUTH_REFUSED M13B template/design mismatch")
    if not (0 < max_usd <= float(t.get("max_generation_spend_usd", 1.0)) <= 1.0):
        raise SystemExit("AUTH_REFUSED max-usd must be > 0 and <= 1.00")
    r = {"artifact": "pilot_a_human_authorization", "authorized": True, "authorized_by": by,
         "authorized_utc": utc, "approval_token": TOKEN,
         "m13_auth_template_sha256": t["artifact_sha256"],
         "design_artifact_sha256": d["artifact_sha256"],
         "membership_artifact_sha256": m["artifact_sha256"],
         "max_generation_spend_usd": max_usd, "model": t["model"], "provider": t["provider"],
         "allow_fallbacks": False, "artifact_sha256": ""}
    q = copy.deepcopy(r)
    r["artifact_sha256"] = sha_obj(q)
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
        raise SystemExit("AUTH_REFUSED paid evidence already exists")
    mrel = M.relative_to(P).as_posix()
    if git("ls-files", "--error-unmatch", mrel).returncode or \
            git("status", "--porcelain", "--", mrel).stdout.strip():
        raise SystemExit("AUTH_REFUSED final membership is not committed cleanly")
    if git("diff", "--cached", "--name-only").stdout.strip():
        raise SystemExit("AUTH_REFUSED staged changes present")
    r = build(a.by, a.max_usd,
              dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    rel = OUT.relative_to(P).as_posix()
    for args in (("add", "--", rel), ("commit", "-q", "-m",
                                      "evidence(wp2): human authorization for Pilot-A V1")):
        q = git(*args)
        if q.returncode:
            raise SystemExit("AUTH_COMMIT_FAIL " + (q.stdout + q.stderr)[-1500:])
    pushed = git("push", "origin", "main").returncode == 0
    print("PILOT_A_HUMAN_AUTH_COMPLETE")
    print(f"AUTHORIZED_BY={a.by}")
    print(f"MAX_GENERATION_SPEND_USD={a.max_usd}")
    print(f"PUSH_MAIN={'YES' if pushed else 'NO (the controller pushes later)'}")
    print("MODEL_API_CALLS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
