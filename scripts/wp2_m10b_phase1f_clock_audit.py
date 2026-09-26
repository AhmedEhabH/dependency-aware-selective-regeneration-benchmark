#!/usr/bin/env python3
"""WP-2 Mission-10B Phase 1F: clock/time audit + AT_RISK_F2P list (ZERO API).

1. Measures host Windows UTC vs WSL UTC skew with the midpoint method
   (>=3 samples, warm-up, reports median + max absolute skew).
2. Searches FULL C2/C4 parent-side evidence for every node currently
   classified BEHAVIORAL_F2P / SYMBOL_ABSENCE_F2P for TIME evidence
   (ImmatureSignatureError / ExpiredSignatureError / JWT iat/nbf/exp /
   freezegun / timezone clock exceptions) and writes the AT_RISK_F2P list.

Output: research/wp2/harness_v3_2026-09-26/phase1f_clock_audit.json
        research/wp2/harness_v3_2026-09-26/phase1f_at_risk_f2p.json

Usage:
    python scripts/wp2_m10b_phase1f_clock_audit.py [--out DIR]
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT_ROOT = PROJECT / "research" / "wp2" / "harness_v3_2026-09-26"
V2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_linux_v2_2026-09-23"
OLD_C2_ROOT = PROJECT / "research" / "wp2" / "oracle_confirmation_2026-09-22"

sys.path.insert(0, str(PROJECT))
sys.path.insert(0, str(PROJECT / "src"))
from benchmark.wp2.m10b_fulltext import merge_rep_junit  # noqa: E402

WSL_DISTRO = "Ubuntu-24.04"

_RE_TIME_EVIDENCE = re.compile(
    r"(ImmatureSignatureError|ExpiredSignatureError|NotBeforeError|"
    r"Signature has expired|token is not yet valid|"
    r"jwt\.exceptions\.(?:ImmatureSignatureError|ExpiredSignatureError|NotBeforeError)|"
    r"freezegun|FreezeGun|wrong_auto_tick|UnknownTimeZoneError|"
    r"non-naive datetime|naive datetime|clock skew|ClockSkew|"
    r"(?:pytz|zoneinfo).*(?:Error|exception|invalid|not found)|"
    r"\biat\b.{0,30}(?:future|valid|error)|"
    r"jwt\.exceptions\.(?:DecodeError|InvalidSignatureError|SignatureVerificationError)"
    r".{0,40}(?:iat|exp|nbf))", re.I)


def _now_utc() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


def wsl(script: str, timeout_s: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "--", "bash", "-lc", script],
        capture_output=True, text=True, encoding="utf-8", timeout=timeout_s, check=False,
    )


def measure_skew(n_samples: int = 6) -> dict:
    """Midpoint-method host<->WSL clock skew (12.1)."""
    def _wsl_ts() -> float:
        r = wsl("date +%s.%N")
        return float(r.stdout.strip())

    def _win_ts() -> float:
        return datetime.datetime.now().timestamp()

    _wsl_ts()  # warm-up WSL VM
    samples = []
    for _ in range(n_samples):
        t0 = _win_ts()
        w = _wsl_ts()
        t1 = _win_ts()
        samples.append({"windows_mid": (t0 + t1) / 2, "wsl": w,
                        "skew_s": w - (t0 + t1) / 2})
    skews = sorted(s["skew_s"] for s in samples)
    median = skews[len(skews) // 2]
    return {
        "n_samples": n_samples,
        "method": "midpoint (windows before/after wsl; median of >=3 samples)",
        "samples": samples,
        "median_skew_s": round(median, 6),
        "max_abs_skew_s": round(max(abs(s) for s in skews), 6),
        "verdict": "PASS" if abs(median) <= 0.5 else "WARN_GT_0.5s",
    }


def search_f2p_time_evidence() -> dict:
    """Search C2/C4 parent-side evidence for TIME anomalies in F2P nodes."""
    import xml.etree.ElementTree as ET

    at_risk: list[dict] = []
    counts = Counter()

    # C4 DEV: per_test_dev_v2.jsonl has parent_outcomes + classification, and
    # junit holds full parent error text.
    per_test = V2_ROOT / "per_test_dev_v2.jsonl"
    junit_dir = V2_ROOT / "junit"

    f2p_classes = {"BEHAVIORAL_F2P", "SYMBOL_ABSENCE_F2P"}
    rows = [json.loads(ln) for ln in per_test.read_text(encoding="utf-8").splitlines()]

    for r in rows:
        if r["classification"] not in f2p_classes:
            continue
        task_id = r["task_id"]
        node_id = r["node_id"]
        t12 = task_id.split("-")[-1]
        parent_outcomes = r.get("parent_outcomes", [])
        # collect parent rep error text for this node
        time_evidence: list[str] = []
        for rep, out in enumerate(parent_outcomes):
            if out not in ("error", "failed", "failure"):
                continue
            tdir = junit_dir / task_id
            if not tdir.exists():
                continue
            files = [f for f in tdir.glob(f"{t12}_p_r{rep}_f*.xml")]
            if not files:
                continue
            merged = merge_rep_junit(task_id=task_id, side="p", repetition=rep,
                                     xml_files=[(f.name, f.read_text(encoding="utf-8")) for f in files])
            ev = merged.get(node_id)
            if ev is None:
                continue
            hay = (ev.message or "") + "\n" + (ev.full_text or "")
            for m in _RE_TIME_EVIDENCE.finditer(hay):
                snippet = hay[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
                time_evidence.append(f"r{rep}:{m.group(0)}::{snippet[:140]}")
        if time_evidence:
            at_risk.append({
                "node_id": node_id,
                "task_id": task_id,
                "split": r.get("split", "DEV_TRAIN"),
                "era_key": r.get("era_key", "UNKNOWN"),
                "v2_class": r["classification"],
                "parent_outcomes": parent_outcomes,
                "time_evidence": time_evidence,
                "n_affected_reps": len({s.split(":")[0] for s in time_evidence}),
            })
            counts[r["classification"]] += 1

    # C2 rescue: search archive F2P nodes similarly (scoped to rescue coverage)
    c2_tar = V2_ROOT / "c2_junit_rescue_2026-09-23.tar.gz"
    c2_at_risk: list[dict] = []
    c2_f2p = set()
    if c2_tar.exists():
        import tarfile
        task_meta = {}
        for ln in (V2_ROOT / "per_task_v2.jsonl").read_text(encoding="utf-8").splitlines():
            m = json.loads(ln)
            task_meta[m["task_id"]] = m
        with tarfile.open(c2_tar, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.endswith(".xml"):
                    continue
                base = member.name.rsplit("/", 1)[-1]
                m2 = re.match(r"^([a-f0-9]{12})_([pt])_r(\d+)_f(\d+)\.xml$", base)
                if not m2 or m2.group(2) != "p":
                    continue
                content = tar.extractfile(member).read().decode("utf-8", errors="replace")
                try:
                    root = ET.fromstring(content)
                except Exception:
                    continue
                for tc in root.iter("testcase"):
                    e = tc.find("error") or tc.find("failure")
                    if e is None:
                        continue
                    hay = (e.get("message", "") or "") + "\n" + (e.text or "")
                    if not _RE_TIME_EVIDENCE.search(hay):
                        continue
                    nid = ((tc.get("classname") or "").replace(".", "/") + ".py::"
                           + (tc.get("name") or "?"))
                    # resolve task_id
                    tid = next((x for x in task_meta
                                if x.split("-")[-1].startswith(m2.group(1))),
                               f"saleor-rc-{m2.group(1)}")
                    c2_f2p.add((tid, nid, m2.group(3), hay))
    for tid, nid, rep, hay in sorted(c2_f2p):
        mm = _RE_TIME_EVIDENCE.search(hay)
        snippet = hay[max(0, mm.start() - 60):mm.end() + 60].replace("\n", " ")
        c2_at_risk.append({
            "node_id": nid,
            "task_id": tid,
            "split": "MAIN",
            "era_key": task_meta.get(tid, {}).get("era_key", "UNKNOWN"),
            "v2_class": "C2_PARENT_TIME_EVIDENCE",
            "parent_outcomes": [None, None, None],
            "time_evidence": [f"r{rep}:{mm.group(0)}::{snippet[:140]}"],
            "n_affected_reps": 1,
        })

    result = {
        "artifact": "m10b_phase1f_at_risk_f2p",
        "created_utc": _now_utc(),
        "method": "full parent-side error/failure text searched for the TIME "
                  "taxonomy patterns (12.2). V2 classes are NOT modified.",
        "c4_at_risk": at_risk,
        "c4_at_risk_count": len(at_risk),
        "c4_by_v2_class": dict(counts),
        "c2_at_risk": c2_at_risk,
        "c2_at_risk_count": len(c2_at_risk),
        "note": "AT_RISK_F2P is informational (12.2): V2 historical "
                "classifications are not deleted/reclassified.",
    }
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--no-time-search", action="store_true",
                    help="skip the F2P time-evidence search (slow)")
    args = ap.parse_args()
    out_root = Path(args.out) if args.out else OUT_ROOT
    out_root.mkdir(parents=True, exist_ok=True)

    skew = measure_skew()
    (out_root / "phase1f_clock_audit.json").write_text(
        json.dumps({"artifact": "m10b_phase1f_clock_audit", "created_utc": _now_utc(),
                    **skew}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[1F] skew median={skew['median_skew_s']:+}s max_abs={skew['max_abs_skew_s']:+}s "
          f"verdict={skew['verdict']}")

    if not args.no_time_search:
        at_risk = search_f2p_time_evidence()
        (out_root / "phase1f_at_risk_f2p.json").write_text(
            json.dumps(at_risk, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[1F] AT_RISK_F2P C4={at_risk['c4_at_risk_count']} "
              f"C2={at_risk['c2_at_risk_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
