#!/usr/bin/env python3
"""Semantic-proxy audit — packet integrity check + synthetic dry-run (Block G).

Part 1 — packet integrity:
- every manifest case has a packet dir;
- every packet has the required JSON evidence;
- every packet dir is listed in audit_file_manifest.json;
- forms are parseable and have exactly the manifest items;
- blinded ordering SHA matches the persisted blinded_ordering.json;
- rater forms are BLANK (no fabricated judgments).

Part 2 — synthetic dry-run (clearly marked NOT REAL):
- fills a COPY of Rater A/B with synthetic/mock labels (NOT real judgments);
- runs the kappa script on the mock copies to prove the pipeline end-to-end;
- writes mock result to a separate file marked NOT_REAL.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "research" / "semantic_audit"

REQUIRED_EVIDENCE = {
    "intent.json": "public",
    "candidate_universe.json": "public",
    "dependency_graph.json": "public",
    "observed_change_set_proxy.json": "hidden",
}


def _packet_proxy_present(p: Path) -> bool:
    """Proxy present in either layout: new two-rater layout (hidden/*.json) or
    original prepare_semantic_audit_packets layout (evidence_packet.json proxy_paths)."""
    if (p / "hidden" / "observed_change_set_proxy.json").is_file():
        return True
    ep = p / "evidence_packet.json"
    if ep.is_file():
        try:
            payload = json.loads(ep.read_text(encoding="utf-8"))
            return isinstance(payload.get("proxy_paths"), list) and len(payload["proxy_paths"]) > 0
        except Exception:
            return False
    return False


def part1_integrity() -> bool:
    ok = True
    manifest = json.loads((OUT / "sample_manifest.json").read_text(encoding="utf-8"))
    case_ids = manifest["case_ids"]
    audit_manifest = json.loads((OUT / "audit_file_manifest.json").read_text(encoding="utf-8"))
    packets = set(p.name for p in OUT.iterdir() if p.is_dir())

    for cid in case_ids:
        p = OUT / cid
        if not p.is_dir():
            print("MISSING_PACKET", cid)
            ok = False
            continue
        # new two-rater layout: intent/universe/graph under public/
        has_new = all((p / sub / fname).is_file() for fname, sub in REQUIRED_EVIDENCE.items())
        # original layout: evidence_packet.json with the same evidence
        ep = p / "evidence_packet.json"
        has_old = ep.is_file() and _packet_proxy_present(p)
        if not (has_new or has_old):
            print("MISSING_EVIDENCE", cid)
            ok = False
        if not _packet_proxy_present(p):
            print("MISSING_PROXY", cid)
            ok = False

    extra_packets = packets - set(case_ids)
    if extra_packets:
        print("EXTRA_PACKETS", sorted(extra_packets))
        ok = False
    if set(audit_manifest["files"]) != (packets & set(case_ids)):
        print("AUDIT_MANIFEST_MISMATCH")
        ok = False

    # blinded ordering integrity
    blinded = json.loads((OUT / "blinded_ordering.json").read_text(encoding="utf-8"))
    recomputed = hashlib.sha256(json.dumps(blinded["order"], separators=(",", ":")).encode()).hexdigest()
    if recomputed != blinded["sha256"]:
        print("BLINDED_SHA_MISMATCH", recomputed, blinded["sha256"])
        ok = False

    # forms blank
    for fname in ("rater_form_A.csv", "rater_form_B.csv"):
        with open(OUT / fname, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        filled = [r for r in rows if (r.get("rater_category") or "").strip()]
        if filled:
            print("FABRICATED_RATINGS", fname, len(filled))
            ok = False
        if len(rows) != 150:
            print("FORM_ROW_COUNT", fname, len(rows))
            ok = False

    print("integrity_all_ok", ok)
    return ok


def part2_synthetic_dryrun() -> bool:
    """Fill mock copies of rater forms with synthetic labels and run kappa.

    The mock forms and result are clearly marked NOT_REAL. No real judgments.
    """
    with open(OUT / "rater_form_A.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cats = ["1_required", "2_related_optional", "3_incidental_tangled", "4_not_determinable"]
    mock_a = []
    mock_b = []
    for i, r in enumerate(rows):
        a = dict(r)
        b = dict(r)
        # deterministic pseudo-labels: A = category by item index mod 4; B = A
        # for even index, shifted by one for odd index (creates realistic
        # disagreement while remaining fully synthetic).
        ca = cats[i % 4]
        cb = cats[(i + (1 if i % 2 else 0)) % 4]
        a["rater_category"] = ca
        a["confidence"] = "0.9"
        b["rater_category"] = cb
        b["confidence"] = "0.8"
        mock_a.append(a)
        mock_b.append(b)

    mock_a_path = OUT / "MOCK_NOT_REAL_rater_form_A.csv"
    mock_b_path = OUT / "MOCK_NOT_REAL_rater_form_B.csv"
    with open(mock_a_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(mock_a)
    with open(mock_b_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(mock_b)

    result = subprocess.run(
        [sys.executable, str(PROJECT / "scripts" / "semantic_audit_kappa.py"), str(mock_a_path), str(mock_b_path)],
        capture_output=True, text=True, cwd=PROJECT,
    )
    if result.returncode != 0:
        print("MOCK_KAPPA_RUN_FAILED", result.stderr[:300])
        return False
    # rename the output to mark it NOT REAL
    kappa_out = OUT / "kappa_result.json"
    not_real_out = OUT / "MOCK_NOT_REAL_kappa_result.json"
    if kappa_out.is_file():
        if not_real_out.is_file():
            not_real_out.unlink()
        kappa_out.rename(not_real_out)
    print("mock_kappa_pipeline_ok", True)
    print("mock output:", not_real_out.name, "MARKED NOT_REAL")
    return True


def main() -> int:
    ok1 = part1_integrity()
    ok2 = part2_synthetic_dryrun()
    print("PACKET_INTEGRITY", "PASS" if ok1 else "FAIL")
    print("SYNTHETIC_DRYRUN", "PASS" if ok2 else "FAIL")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
