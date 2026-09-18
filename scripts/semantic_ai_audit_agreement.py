#!/usr/bin/env python3
"""AI-assisted semantic-plausibility audit — ingest + agreement analysis (ZERO LLM).

Consumes the 10 frozen rater batch outputs (5 ChatGPT + 5 Claude, one JSON file
per batch per the strict output schema), validates them against the schema and
the expected neutral IDs, reassembles each rater's 25-case audit, maps neutral
IDs back privately via the sealed mapping, and computes:

- exact row-level agreement (4-category nominal, no collapsing);
- Cohen's kappa (nominal / unweighted);
- confusion matrix;
- agreement by label;
- abstention rate (per rater);
- agreement separately for historical_changed_file rows vs
  omitted_candidate_file rows;
- case-level agreement for proxy_quality / omitted_candidate_semantic_impact /
  mixed_tangled_commit;
- a disagreement list for later human spot-check;
- a deterministic random sample of 10 agreement rows for spot-check.

Integrity rules (fail-closed):
- exactly 10 input files (chatgpt_batch_01..05.json, claude_batch_01..05.json);
- every file conforms to AI_AUDIT_OUTPUT_SCHEMA.json;
- every rater's reassembled audit covers the expected 25 cases and 361 rows
  exactly once;
- no label fabrication, no category collapsing, no thesis results.

Inter-model agreement is NEVER called human agreement.

Usage:
    python scripts/semantic_ai_audit_agreement.py <outputs_dir> <sealed_mapping.json> [--out <analysis.json>]
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections.abc import Sequence
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
SCHEMA = PROJECT / "research" / "semantic_audit" / "ai_blinded_v1" / "AI_AUDIT_OUTPUT_SCHEMA.json"

LABELS = ["1_required", "2_related_optional", "3_incidental_tangled", "4_not_determinable"]
ROW_ID_RE = re.compile(r"^AI-ROW-\d{4}$")
CASE_ID_RE = re.compile(r"^AI-CASE-\d{3}$")
SPOTCHECK_SEED = 20260918
SPOTCHECK_N = 10


class AuditValidationError(ValueError):
    pass


def load_sealed(path: Path) -> dict:
    data: dict = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def expected_ids(sealed: dict) -> tuple[set[str], set[str], dict[str, str]]:
    """Return (row_ids, case_ids, row_id -> semantic_role) from the sealed mapping."""
    row_ids: set[str] = set()
    case_ids: set[str] = set()
    role_by_row: dict[str, str] = {}
    for ncid, cinfo in sealed["cases"].items():
        case_ids.add(ncid)
        for r in cinfo["rows"]:
            row_ids.add(r["neutral_row_id"])
            role_by_row[r["neutral_row_id"]] = r["semantic_role"]
    return row_ids, case_ids, role_by_row


def load_batch_outputs(outputs_dir: Path) -> dict[str, dict]:
    """Load and structurally validate the 10 batch output files."""
    expected_files = {
        f"{rater}_batch_{i:02d}.json" for rater in ("chatgpt", "claude") for i in range(1, 6)
    }
    present = {p.name for p in Path(outputs_dir).glob("*.json")}
    missing = expected_files - present
    extra = present - expected_files
    if missing:
        raise AuditValidationError(f"missing batch outputs: {sorted(missing)}")
    if extra:
        raise AuditValidationError(f"unexpected extra batch outputs: {sorted(extra)}")

    outputs: dict[str, dict] = {}
    for rater in ("chatgpt", "claude"):
        for i in range(1, 6):
            name = f"{rater}_batch_{i:02d}.json"
            path = Path(outputs_dir) / name
            raw = json.loads(path.read_text(encoding="utf-8"))
            _validate_batch_document(raw, name, rater)
            outputs[name] = raw
    return outputs


def _validate_batch_document(doc: dict, fname: str, rater: str) -> None:
    if not isinstance(doc, dict):
        raise AuditValidationError(f"{fname}: top-level must be an object")
    if doc.get("batch_id") != fname.replace(".json", ""):
        raise AuditValidationError(f"{fname}: batch_id mismatch ({doc.get('batch_id')})")
    if doc.get("rater_label") != rater:
        raise AuditValidationError(f"{fname}: rater_label mismatch ({doc.get('rater_label')})")
    if not isinstance(doc.get("rows"), list) or not doc["rows"]:
        raise AuditValidationError(f"{fname}: rows missing/empty")
    if not isinstance(doc.get("cases"), list) or not doc["cases"]:
        raise AuditValidationError(f"{fname}: cases missing/empty")

    seen_rows: set[str] = set()
    for row in doc["rows"]:
        if not isinstance(row, dict):
            raise AuditValidationError(f"{fname}: row not an object")
        nid = row.get("neutral_row_id")
        if not isinstance(nid, str) or not ROW_ID_RE.match(nid):
            raise AuditValidationError(f"{fname}: bad neutral_row_id {nid!r}")
        if nid in seen_rows:
            raise AuditValidationError(f"{fname}: duplicate neutral_row_id {nid}")
        seen_rows.add(nid)
        label = row.get("label")
        if label is None:
            if not (row.get("abstention_reason") or "").strip():
                raise AuditValidationError(f"{fname}: abstained row {nid} lacks abstention_reason")
            if row.get("confidence") is not None or (row.get("rationale") or "").strip():
                raise AuditValidationError(f"{fname}: abstained row {nid} has label fields")
        else:
            if label not in LABELS:
                raise AuditValidationError(f"{fname}: invalid label {label!r} for {nid}")
            if row.get("confidence") not in ("low", "medium", "high"):
                raise AuditValidationError(f"{fname}: invalid confidence for {nid}")
            if not (row.get("rationale") or "").strip():
                raise AuditValidationError(f"{fname}: missing rationale for {nid}")
            if not isinstance(row.get("evidence"), list):
                raise AuditValidationError(f"{fname}: evidence must be a list for {nid}")
            if (row.get("abstention_reason") or "").strip():
                raise AuditValidationError(f"{fname}: non-abstained row {nid} has abstention_reason")

    seen_cases: set[str] = set()
    for case in doc["cases"]:
        if not isinstance(case, dict):
            raise AuditValidationError(f"{fname}: case not an object")
        ncid = case.get("neutral_case_id")
        if not isinstance(ncid, str) or not CASE_ID_RE.match(ncid):
            raise AuditValidationError(f"{fname}: bad neutral_case_id {ncid!r}")
        if ncid in seen_cases:
            raise AuditValidationError(f"{fname}: duplicate neutral_case_id {ncid}")
        seen_cases.add(ncid)
        if case.get("proxy_quality") not in ("strong", "moderate", "weak", "indeterminate"):
            raise AuditValidationError(f"{fname}: invalid proxy_quality for {ncid}")
        if case.get("omitted_candidate_semantic_impact") not in ("yes", "no", "unclear"):
            raise AuditValidationError(f"{fname}: invalid omitted_candidate_semantic_impact for {ncid}")
        if case.get("mixed_tangled_commit") not in ("yes", "no", "unclear"):
            raise AuditValidationError(f"{fname}: invalid mixed_tangled_commit for {ncid}")


def reassemble_rater(outputs: dict[str, dict], rater: str) -> dict[str, dict]:
    """Merge a rater's 5 batch outputs into one rows + cases audit."""
    rows: dict[str, dict] = {}
    cases: dict[str, dict] = {}
    for i in range(1, 6):
        doc = outputs[f"{rater}_batch_{i:02d}.json"]
        for row in doc["rows"]:
            nid = row["neutral_row_id"]
            if nid in rows:
                raise AuditValidationError(f"{rater}: neutral_row_id {nid} appears in >1 batch")
            rows[nid] = row
        for case in doc["cases"]:
            ncid = case["neutral_case_id"]
            if ncid in cases:
                raise AuditValidationError(f"{rater}: neutral_case_id {ncid} appears in >1 batch")
            cases[ncid] = case
    return {"rows": rows, "cases": cases}


def validate_reassembly(audit: dict[str, dict], exp_rows: set[str], exp_cases: set[str], rater: str) -> None:
    got_rows = set(audit["rows"])
    got_cases = set(audit["cases"])
    if got_rows != exp_rows:
        raise AuditValidationError(
            f"{rater}: row coverage mismatch (missing {len(exp_rows - got_rows)}, "
            f"extra {len(got_rows - exp_rows)})"
        )
    if got_cases != exp_cases:
        raise AuditValidationError(
            f"{rater}: case coverage mismatch (missing {len(exp_cases - got_cases)}, "
            f"extra {len(got_cases - exp_cases)})"
        )


def _pair_labels(a_audit: dict[str, dict], b_audit: dict[str, dict]) -> list[tuple[str, str | None, str | None]]:
    rows = sorted(set(a_audit["rows"]) & set(b_audit["rows"]))
    pairs = []
    for nid in rows:
        la = a_audit["rows"][nid].get("label")
        lb = b_audit["rows"][nid].get("label")
        pairs.append((nid, la, lb))
    return pairs


def _cohen_kappa(a: list, b: list) -> float | None:
    if not a or len(a) != len(b):
        return None
    if len(set(a)) < 2 or len(set(b)) < 2:
        return None
    try:
        from sklearn.metrics import cohen_kappa_score
    except Exception:
        return None
    return float(cohen_kappa_score(a, b, weights=None))


def _confusion_matrix(a: list, b: list, labels: list[str]) -> list[list[int]]:
    try:
        from sklearn.metrics import confusion_matrix
    except Exception:
        return []
    cm = confusion_matrix(a, b, labels=labels)
    return [[int(v) for v in row] for row in cm.tolist()]


def _row_agreement_stats(pairs: list[tuple[str, str | None, str | None]]) -> dict:
    rated = [(nid, la, lb) for nid, la, lb in pairs if la is not None and lb is not None]
    n_rated = len(rated)
    n_agree = sum(1 for _, la, lb in rated if la == lb)
    exact = round(n_agree / n_rated, 4) if n_rated else None
    kappa = _cohen_kappa([la for _, la, _ in rated], [lb for _, _, lb in rated])
    cm = _confusion_matrix([la for _, la, _ in rated], [lb for _, _, lb in rated], LABELS)
    return {
        "n_total_rows": len(pairs),
        "n_rated_both": n_rated,
        "n_agreements": n_agree,
        "exact_row_agreement": exact,
        "cohen_kappa": kappa,
        "confusion_matrix": cm,
        "confusion_labels": LABELS,
    }


def _agreement_by_label(pairs: list[tuple[str, str | None, str | None]]) -> dict[str, dict]:
    out = {}
    for label in LABELS:
        both = sum(1 for _, la, lb in pairs if la == label and lb == label)
        either = sum(1 for _, la, lb in pairs if la == label or lb == label)
        out[label] = {
            "both": both,
            "either": either,
            "pct_both_of_either": round(both / either, 4) if either else None,
        }
    return out


def _abstention_stats(pairs: list[tuple[str, str | None, str | None]]) -> dict[str, dict]:
    out = {}
    for name, idx in (("chatgpt", 1), ("claude", 2)):
        n = sum(1 for p in pairs if p[idx] is None)
        out[name] = {"n_abstained": n, "rate": round(n / len(pairs), 4) if pairs else None}
    return out


def _role_split(pairs: list[tuple[str, str | None, str | None]], role_by_row: dict[str, str]) -> dict[str, dict]:
    out = {}
    for role in ("historical_changed_file", "omitted_candidate_file"):
        sub = [(nid, la, lb) for nid, la, lb in pairs if role_by_row.get(nid) == role]
        out[role] = _row_agreement_stats(sub)
        out[role]["n_rows"] = len(sub)
    return out


def _case_agreement(a_audit: dict[str, dict], b_audit: dict[str, dict]) -> dict[str, dict]:
    fields = ["proxy_quality", "omitted_candidate_semantic_impact", "mixed_tangled_commit"]
    out = {}
    ncases = sorted(set(a_audit["cases"]) & set(b_audit["cases"]))
    for field in fields:
        a = [a_audit["cases"][cid][field] for cid in ncases]
        b = [b_audit["cases"][cid][field] for cid in ncases]
        n_agree = sum(1 for x, y in zip(a, b, strict=True) if x == y)
        out[field] = {
            "n_cases": len(ncases),
            "exact_agreement": round(n_agree / len(ncases), 4) if ncases else None,
            "cohen_kappa": _cohen_kappa(a, b),
        }
    return out


def _disagreements(pairs: list[tuple[str, str | None, str | None]], role_by_row: dict[str, str]) -> list[dict]:
    out = []
    for nid, la, lb in pairs:
        if la is None or lb is None or la != lb:
            out.append(
                {
                    "neutral_row_id": nid,
                    "semantic_role": role_by_row.get(nid),
                    "chatgpt_label": la,
                    "claude_label": lb,
                }
            )
    return out


def _agreement_sample(agreed_pairs: Sequence[tuple[str, str | None, str | None]]) -> list[str]:
    agreed = sorted(nid for nid, la, lb in agreed_pairs if la is not None and lb is not None and la == lb)
    rng = random.Random(SPOTCHECK_SEED)
    sample = rng.sample(agreed, min(SPOTCHECK_N, len(agreed)))
    return sample


def analyze(outputs_dir: Path, sealed_path: Path) -> dict:
    sealed = load_sealed(sealed_path)
    exp_rows, exp_cases, role_by_row = expected_ids(sealed)
    outputs = load_batch_outputs(outputs_dir)
    chatgpt = reassemble_rater(outputs, "chatgpt")
    claude = reassemble_rater(outputs, "claude")
    validate_reassembly(chatgpt, exp_rows, exp_cases, "chatgpt")
    validate_reassembly(claude, exp_rows, exp_cases, "claude")

    pairs = _pair_labels(chatgpt, claude)
    agreed_pairs = [(nid, la, lb) for nid, la, lb in pairs if la is not None and lb is not None and la == lb]
    disagreements = _disagreements(pairs, role_by_row)
    sample = _agreement_sample(agreed_pairs)

    return {
        "analysis_date": "2026-09-18",
        "package": "ai_blinded_v1",
        "n_cases": len(exp_cases),
        "n_rows": len(exp_rows),
        "row_level": _row_agreement_stats(pairs),
        "agreement_by_label": _agreement_by_label(pairs),
        "abstention": _abstention_stats(pairs),
        "role_split": _role_split(pairs, role_by_row),
        "case_level": _case_agreement(chatgpt, claude),
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
        "agreement_spotcheck_sample": sample,
        "spotcheck_seed": SPOTCHECK_SEED,
        "spotcheck_n": SPOTCHECK_N,
        "note": "Inter-model agreement is NOT human agreement. No labels altered; no categories collapsed.",
        "sealed_mapping_used": str(sealed_path),
        "outputs_dir_used": str(outputs_dir),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("outputs_dir", type=Path, help="dir with the 10 batch output JSON files")
    parser.add_argument("sealed_mapping", type=Path, help="path to sealed_mapping.json")
    parser.add_argument("--out", type=Path, default=Path("reports/ai_semantic_audit_agreement_result.json"))
    args = parser.parse_args(argv)

    try:
        result = analyze(args.outputs_dir, args.sealed_mapping)
    except AuditValidationError as exc:
        print("VALIDATION_FAILED:", exc)
        return 1

    args.out = Path(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["row_level"], indent=2))
    print("n_disagreements:", result["n_disagreements"])
    print("spotcheck_sample:", result["agreement_spotcheck_sample"])
    print("output:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
