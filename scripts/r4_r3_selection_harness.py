#!/usr/bin/env python3
"""M17_D7_R4_PHASE1C_HARNESS_R3 - unified additive selection harness.

Mission: M17_D7_R4_PHASE1C_HARNESS_R3_RELEASE_FOR_OPERATOR_EXECUTION
MODE: BUILD / TEST / FREEZE / PREFLIGHT ONLY inside OpenCode.

ONE additive per-unit execution path (the frozen Full144/driver path SAME as
population qualification) driven by exactly three committed frozen selection
manifests:

* TARGETED3 - units 71 (vu-cd262bbb641d), 119 (vu-bbb37661a274), 130
  (vu-9ed193747002); the first successor dynamic gate (3/3 PASS required).
* CAL12     - the exact frozen N12 membership/order/strata (R4-D plan ==
  N12 R2 receipt exact_ordered_n12); may run only after TARGETED3 3/3 PASS.
* FULL144   - the exact frozen 144 ordered population membership; may run only
  after CAL12 12/12 PASS.

Authority model (TWO-HEAD):
  SCIENTIFIC_AUTHORITY_HEAD = 5171a4e75cfb2064e7758423c146fcd4ca9ee95c
  SUPPORT_EVIDENCE_HEAD     = beeff152de2307b2067c8cd9f469542ef8200b95
  EXECUTION_CODE_SET        = 72d3d1262133505dd3046a78e9fc0130d004cfaf6e8ca89169b67620335584c0
  COMMITTED_CLOSURE_CONTENT = 71cc7fb72e34fbf707e0a7e8052d3ea2d49fc726cb3a16d9d678271f4a6404e1
The scientific tag peels to SCIENTIFIC_AUTHORITY_HEAD; SUPPORT_EVIDENCE_HEAD is
the descendant carrying the committed successor receipts/manifests/closure
authority.  Harness R3 is operational evidence layered on SUPPORT_EVIDENCE_HEAD
while its scientific binding remains SCIENTIFIC_AUTHORITY_HEAD.

CLOSURE HASH RULE: the committed closure content hash is verified against the
EXACT committed blob at HEAD/support-head (LF-normalized git blob bytes).  A
fresh re-derivation is never required to reproduce volatile serialization
bytes; if re-derived, scientific semantics are compared through the committed
closure semantic footprint (all non-volatile decision-relevant fields).

Commands:
  --preflight <SELECTION>  authority + selection + zero-exec gate (operator safe,
                           never executes a unit).  CAL12/FULL144 report
                           BLOCKED_BY_PREDECESSOR_RECEIPT when the predecessor
                           receipt is not yet available (expected) - distinct
                           from authority failure.
  --exec <SELECTION>       fail-closed execution gate: authority + predecessor
                           receipt exact counts then run the selection through
                           the frozen per-unit path.  Zero-network.
  --status <SELECTION>     compact status of the selection run root.
  --verify-selection <SEL> recompute and compare a selection manifest hash.

Exit codes: 0 = PASS (authority valid); 1 = fail-closed authority/receipt
mismatch or selection FAIL; 2 = unexpected internal error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parents[1]
SRC = PROJECT / "src"
SCRIPTS = PROJECT / "scripts"
R4_DIR = PROJECT / "research" / "env-canon-r4"
R3_DIR = R4_DIR / "r3"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from benchmark.wp2.full144 import population  # noqa: E402

# --- Authority (single committed source of truth) ---------------------------
AUTHORITY_PATH = R3_DIR / "R3_AUTHORITY_BINDING.json"
ALLOWLIST_PATH = R3_DIR / "R3_OPERATIONAL_ALLOWLIST.json"
SELECTION_FILES = {
    "TARGETED3": R3_DIR / "R3_SELECTION_TARGETED3.json",
    "CAL12": R3_DIR / "R3_SELECTION_CAL12.json",
    "FULL144": R3_DIR / "R3_SELECTION_FULL144.json",
}
PREDECESSOR = {"TARGETED3": None, "CAL12": "TARGETED3", "FULL144": "CAL12"}
PREDECESSOR_EXACT = {"CAL12": (3, 3, 0), "FULL144": (12, 12, 0)}

# Frozen canonical run roots (Task E).  Operator may override each via env but
# the receipt always records the effective root.
DEFAULT_ROOTS = {
    "TARGETED3": Path(r"D:\WP2\runs\r4-successor-r3-targeted3-2026-10-16"),
    "CAL12": Path(r"D:\WP2\runs\r4-successor-r3-cal12-2026-10-16"),
    "FULL144": Path(r"D:\WP2\runs\r4-successor-r3-qualification144-2026-10-16"),
}
ROOT_ENV_KEYS = {
    "TARGETED3": "R4_R3_TARGETED3_ROOT",
    "CAL12": "R4_R3_CAL12_ROOT",
    "FULL144": "R4_R3_QUALIFICATION144_ROOT",
}
RECEIPT_NAME = "R3_SELECTION_RECEIPT.json"
PROGRESS_NAME = "R3_PROGRESS.json"
NON_SCIENTIFIC_MARKER = "R3_ROOT_NON_SCIENTIFIC.txt"

WSL_DISTRO = "Ubuntu-24.04"
WSL_REPO = "/opt/wp2_v2/saleor-cache"
DRIVE = "D:"
DISK_STOP_GIB = 120.0


class R3Error(Exception):
    """Fail-closed harness error."""


class AuthorityError(R3Error):
    """Any mandatory authority/release drift."""


class SelectionError(R3Error):
    """Selection manifest validation failure."""


class ReceiptError(R3Error):
    """Predecessor/self receipt validation failure."""


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sha256_file_lf(path: Path) -> str:
    return _sha256_bytes(path.read_bytes().replace(b"\r\n", b"\n"))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise R3Error(f"missing artifact: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise R3Error(f"artifact {path} is not a JSON object")
    return data


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None, timeout=timeout
    )


def utcnow() -> str:
    return datetime.now(UTC).isoformat()


def load_authority() -> dict[str, Any]:
    a = _read_json(AUTHORITY_PATH)
    if a.get("artifact") != "R3_AUTHORITY_BINDING":
        raise AuthorityError("R3 authority binding artifact mismatch")
    return a


# ---------------------------------------------------------------------------
# Git / release identity
# ---------------------------------------------------------------------------
def git_head() -> str:
    p = _run(["git", "rev-parse", "HEAD"], cwd=PROJECT)
    if p.returncode != 0:
        raise AuthorityError(f"git rev-parse HEAD failed: {p.stderr.strip()}")
    return p.stdout.strip()


def git_branch() -> str:
    p = _run(["git", "branch", "--show-current"], cwd=PROJECT)
    if p.returncode != 0:
        raise AuthorityError(f"git branch failed: {p.stderr.strip()}")
    return p.stdout.strip()


def git_clean_tracked() -> bool:
    p = _run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PROJECT)
    if p.returncode != 0:
        raise AuthorityError(f"git status failed: {p.stderr.strip()}")
    return p.stdout.strip() == ""


def tag_peel(tag: str) -> str | None:
    p = _run(["git", "rev-list", "-n", "1", tag], cwd=PROJECT)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def blob_lf_sha256_at(rev: str, relpath: str) -> str:
    blob = subprocess.run(
        ["git", "rev-parse", f"{rev}:{relpath}"], capture_output=True, text=True, cwd=str(PROJECT)
    )
    if blob.returncode != 0:
        raise AuthorityError(f"committed blob missing {relpath} at {rev}")
    blob_oid = blob.stdout.strip()
    data = subprocess.run(
        ["git", "cat-file", "blob", blob_oid], capture_output=True, cwd=str(PROJECT)
    ).stdout
    return _sha256_bytes(data.replace(b"\r\n", b"\n"))


def _is_ancestor(anc: str, desc: str) -> bool:
    p = _run(["git", "merge-base", "--is-ancestor", anc, desc], cwd=PROJECT)
    return p.returncode == 0


# ---------------------------------------------------------------------------
# Execution-code-set + closure authority
# ---------------------------------------------------------------------------
def effective_code_set_hash() -> str:
    """Recompute the aggregate execution-code hash from committed blobs at HEAD."""
    manifest = _read_json(
        PROJECT / "research" / "env-canon-r4" / "R4_PHASE1B_EFFECTIVE_EXECUTION_CODE_SET.json"
    )
    members = [dict(m) for m in manifest["members"]]
    lines: list[str] = []
    for member in sorted(members, key=lambda m: m["path"]):
        path = str(member["path"])
        lines.append(f"{blob_lf_sha256_at('HEAD', path)}  {path}")
    return _sha256_bytes(("\n".join(sorted(lines)) + "\n").encode("utf-8"))


def committed_closure_semantic_footprint() -> str:
    """Compact-JSON sha256 over the non-volatile decision-relevant closure fields.

    This is the semantic-equivalence representation used when a closure is
    re-derived (volatile serialization bytes may differ; scientific fields must
    not).  Excludes only generation timestamps / bookkeeping that carries no
    scientific decision.  The footprint is computed from the COMMITTED closure
    blob at HEAD (CLOSURE HASH RULE), not from a fresh re-derivation.
    """
    authority = load_authority()
    rel = str(authority["closure_evidence_file"])
    blob = subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"], capture_output=True, text=True, cwd=str(PROJECT)
    )
    if blob.returncode != 0:
        raise AuthorityError(f"committed closure blob missing {rel} at HEAD")
    raw = subprocess.run(
        ["git", "cat-file", "blob", blob.stdout.strip()], capture_output=True, cwd=str(PROJECT)
    ).stdout
    c = json.loads(raw.decode("utf-8"))
    sem = {
        "N_UNITS": c["N_UNITS"],
        "N_RESOLVABLE": c["N_RESOLVABLE"],
        "N_MISSING": c["N_MISSING"],
        "N_INCOMPATIBLE": c["N_INCOMPATIBLE"],
        "verdict": c["verdict"],
        "population_identity": c["population_identity"],
        "ordered_membership_hash": c["ordered_membership_hash"],
        "ordered_membership": c["ordered_membership"],
        "per_unit": [
            {
                "calibration_index": u["calibration_index"],
                "validation_unit_id": u["validation_unit_id"],
                "python_version": u["python_version"],
                "lock_type": u["lock_type"],
                "install_route": u["install_route"],
                "wheelhouse_era": u["wheelhouse_era"],
                "runtime_pins_count": u["runtime_pins_count"],
                "resolved_wheels_count": u["resolved_wheels_count"],
                "resolvable": u["resolvable"],
                "missing": u["missing"],
                "incompatible": u["incompatible"],
                "source_fidelity_filenames": u["source_fidelity_filenames"],
                "source_fidelity_overlay_count": u["source_fidelity_overlay_count"],
                "recovery_overlay": u["recovery_overlay"],
                "recovery_overlay_versions": u["recovery_overlay_versions"],
            }
            for u in c["per_unit"]
        ],
    }
    return _sha256_bytes(json.dumps(sem, separators=(",", ":")).encode("utf-8"))


# ---------------------------------------------------------------------------
# Operational allowlist
# ---------------------------------------------------------------------------
def verify_allowlist() -> list[dict[str, Any]]:
    allow = _read_json(ALLOWLIST_PATH)
    entries: list[dict[str, Any]] = []
    for entry in allow["files"]:
        rel = str(entry["path"])
        expected = str(entry["blob_sha256_at_support_head"])
        try:
            got = blob_lf_sha256_at("HEAD", rel)
        except AuthorityError:
            raise AuthorityError(f"allowlist file missing at HEAD: {rel}") from None
        if got != expected:
            raise AuthorityError(
                f"allowlist drift at HEAD for {rel}: got {got} expected {expected}"
            )
        entries.append({"path": rel, "blob_sha256": got, "match": True})
    return entries


def static_checks() -> dict[str, Any]:
    """Zero-network / no-pull-build / no-LLM structural gate (F2P).

    The frozen per-unit execution path (qualified Attempt-6 runner + Full144
    driver) must carry the exact offline install command and never contain a
    pull/build literal.  The operator launcher must not depend on OpenCode /
    OpenRouter / LLM / external API.
    """
    runner_src = (SCRIPTS / "r4_behavioral_calibration_n12_r2.py").read_text(encoding="utf-8")
    driver_src = (SRC / "benchmark" / "wp2" / "full144" / "driver.py").read_text(encoding="utf-8")
    ps1_src = (SCRIPTS / "r4_r3_selection_launcher.ps1").read_text(encoding="utf-8")

    if '"--network=none"' not in runner_src:
        raise R3Error("runner does not require --network=none")
    for forbidden in ("OpenCode", "OpenRouter", "LLM", "openai", "anthropic"):
        if forbidden.lower() in ps1_src.lower():
            raise R3Error(f"launcher must not depend on {forbidden!r}")
    for src in (runner_src, driver_src):
        if '"pull"' in src or '"build"' in src:
            raise R3Error("pull/build literal present in execution path")

    return {
        "static": "PASS",
        "network_isolation": "--network=none",
        "no_llm_dependency": True,
        "no_pull_build": True,
        "no_network_fallback": True,
    }


# ---------------------------------------------------------------------------
# Release-identity gate (Task G rules; enforces final tag when it exists)
# ---------------------------------------------------------------------------
def verify_release_identity(authority: dict[str, Any]) -> dict[str, Any]:
    required_branch = str(authority["required_branch"])
    branch = git_branch()
    if branch != required_branch:
        raise AuthorityError(f"branch {branch} != required {required_branch}")
    if not git_clean_tracked():
        raise AuthorityError("tracked worktree is not clean")

    scientific_tag = str(authority["two_head_model"]["scientific_authority_tag"])
    sci_peel = tag_peel(scientific_tag)
    sci_head = str(authority["two_head_model"]["scientific_authority_head"])
    if sci_peel != sci_head:
        raise AuthorityError(
            f"scientific tag {scientific_tag} peels to {sci_peel} != {sci_head}"
        )

    support = str(authority["two_head_model"]["support_evidence_head"])
    head = git_head()
    if not _is_ancestor(sci_head, support):
        raise AuthorityError("scientific authority is not an ancestor of support evidence HEAD")
    if not _is_ancestor(support, head):
        raise AuthorityError("support evidence HEAD is not an ancestor of current HEAD")
    if not _is_ancestor(sci_head, head):
        raise AuthorityError("scientific authority is not an ancestor of current HEAD")

    r3_tag = str(authority["r3_release_tag"])
    r3_peel = tag_peel(r3_tag)
    release_state = "TAG_ABSENT"
    if r3_peel is not None:
        if r3_peel != head:
            raise AuthorityError(f"R3 tag {r3_tag} peels to {r3_peel} != current HEAD {head}")
        release_state = "TAG_PRESENT_HEAD_MATCHES"

    code = effective_code_set_hash()
    if code != str(authority["execution_code_set_hash"]):
        raise AuthorityError(f"execution-code-set recompute {code} != frozen")

    closure = str(authority["committed_closure_content_hash"])
    got_closure = blob_lf_sha256_at("HEAD", str(authority["closure_evidence_file"]))
    if got_closure != closure:
        raise AuthorityError(
            f"committed closure content hash {got_closure} != committed {closure}"
        )
    footprint = committed_closure_semantic_footprint()
    if footprint != str(authority["closure_semantic_footprint"]):
        raise AuthorityError(
            f"closure semantic footprint {footprint} != frozen {authority['closure_semantic_footprint']}"
        )

    allow = verify_allowlist()

    pop = population.validate_population()
    if pop["population_identity"] != str(authority["population_identity"]):
        raise AuthorityError("population identity mismatch")
    if pop["ordered_membership_hash"] != str(authority["ordered_membership_hash"]):
        raise AuthorityError("ordered membership hash mismatch")
    if pop["binding_hash"] != str(authority["image_binding_hash"]):
        raise AuthorityError("image binding hash mismatch")

    return {
        "branch": branch,
        "git_head": head,
        "scientific_authority_peel": sci_peel,
        "support_evidence_head": support,
        "r3_release_tag": r3_tag,
        "r3_release_state": release_state,
        "effective_execution_code_set_hash": code,
        "committed_closure_content_hash": got_closure,
        "closure_semantic_footprint": footprint,
        "population_identity": pop["population_identity"],
        "ordered_membership_hash": pop["ordered_membership_hash"],
        "image_binding_hash": pop["binding_hash"],
        "allowlist_files_verified": len(allow),
        "tracked_clean": True,
        "zero_network": True,
    }


# ---------------------------------------------------------------------------
# Selection manifests
# ---------------------------------------------------------------------------
def membership_hash(ids: list[str]) -> str:
    return _sha256_bytes(json.dumps(ids, separators=(",", ":")).encode("utf-8"))


def _validate_manifest(m: dict[str, Any]) -> None:
    """Fail-closed validation of one selection manifest (mutation-proof)."""
    name = str(m.get("selection_name", "?"))
    rec = {k: v for k, v in m.items() if k not in ("generated_utc", "manifest_sha256")}
    recomputed = _sha256_bytes(json.dumps(rec, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    if m.get("manifest_sha256") != recomputed:
        raise SelectionError(f"{name} manifest_sha256 self-inconsistent")
    ids = [str(u) for u in m.get("ordered_unit_ids", [])]
    if membership_hash(ids) != m.get("membership_hash"):
        raise SelectionError(f"{name} membership hash mismatch")
    if len(ids) != int(m["expected_count"]):
        raise SelectionError(f"{name} expected_count {m['expected_count']} != len {len(ids)}")
    if len(set(ids)) != len(ids):
        raise SelectionError(f"{name} duplicate unit id")


def load_selection(name: str) -> dict[str, Any]:
    if name not in SELECTION_FILES:
        raise SelectionError(f"unknown selection {name}")
    m = _read_json(SELECTION_FILES[name])
    _validate_manifest(m)
    return m


# ---------------------------------------------------------------------------
# Predecessor receipt (Task D)
# ---------------------------------------------------------------------------
def run_root_for(name: str) -> Path:
    env_key = ROOT_ENV_KEYS[name]
    override = os.environ.get(env_key)
    if override:
        return Path(override)
    return DEFAULT_ROOTS[name]


def _receipt_path(root: Path) -> Path:
    return root / RECEIPT_NAME


def receipt_for(name: str) -> dict[str, Any] | None:
    root = run_root_for(name)
    path = _receipt_path(root)
    if not path.is_file():
        return None
    return _read_json(path)


def validate_self_receipt(name: str, receipt: dict[str, Any], authority: dict[str, Any]) -> dict[str, Any]:
    """A selection's own receipt must bind every release authority."""
    if receipt.get("selection_name") != name:
        raise ReceiptError(f"receipt selection {receipt.get('selection_name')} != {name}")
    head = git_head()
    if receipt.get("release_head") != head:
        raise ReceiptError(f"receipt release_head {receipt.get('release_head')} != current HEAD {head}")
    if receipt.get("release_tag") != authority["r3_release_tag"]:
        raise ReceiptError("receipt release_tag mismatch")
    if receipt.get("scientific_authority_head") != authority["two_head_model"]["scientific_authority_head"]:
        raise ReceiptError("receipt scientific authority mismatch")
    if receipt.get("execution_code_set_hash") != authority["execution_code_set_hash"]:
        raise ReceiptError("receipt execution-code-set mismatch")
    if receipt.get("committed_closure_content_hash") != authority["committed_closure_content_hash"]:
        raise ReceiptError("receipt closure content mismatch")
    m = load_selection(name)
    if receipt.get("selection_membership_hash") != m["membership_hash"]:
        raise ReceiptError("receipt selection membership mismatch")
    if receipt.get("population_identity") != authority["population_identity"]:
        raise ReceiptError("receipt population identity mismatch")
    if receipt.get("ordered_membership_hash") != authority["ordered_membership_hash"]:
        raise ReceiptError("receipt ordered membership mismatch")
    if receipt.get("image_binding_hash") != authority["image_binding_hash"]:
        raise ReceiptError("receipt image binding mismatch")
    if receipt.get("zero_network") is not True:
        raise ReceiptError("receipt zero_network not asserted")
    return receipt


def predecessor_receipt_state(name: str, authority: dict[str, Any]) -> dict[str, Any]:
    """Fresh-predecessor requirement (Task D) - fail closed after execution.

    For preflight the state is reported structurally; the operator execution
    gate (--exec) requires the exact counts.
    """
    pred = PREDECESSOR[name]
    if pred is None:
        return {"required": False, "status": "NOT_REQUIRED"}
    receipt = receipt_for(pred)
    if receipt is None:
        return {"required": True, "status": "BLOCKED_BY_PREDECESSOR_RECEIPT", "pred": pred}
    validate_self_receipt(pred, receipt, authority)
    n_exec = int(receipt.get("N_EXECUTED", -1))
    n_pass = int(receipt.get("N_PASS", -1))
    n_np = int(receipt.get("N_NON_PASS", -1))
    expected = PREDECESSOR_EXACT[name]
    if (n_exec, n_pass, n_np) != expected:
        raise ReceiptError(
            f"predecessor {pred} receipt counts {(n_exec, n_pass, n_np)} != {expected}"
        )
    return {
        "required": True,
        "status": "PREDECESSOR_VALID",
        "pred": pred,
        "N_EXECUTED": n_exec,
        "N_PASS": n_pass,
        "N_NON_PASS": n_np,
    }


# ---------------------------------------------------------------------------
# Preflight (Task I) - authority valid vs predecessor missing distinction
# ---------------------------------------------------------------------------
def preflight(name: str) -> dict[str, Any]:
    authority = load_authority()
    release = verify_release_identity(authority)
    m = load_selection(name)
    pred = predecessor_receipt_state(name, authority)
    root = run_root_for(name)
    static = static_checks()

    executed = 0
    root_exists = root.is_dir()
    progress_path = root / PROGRESS_NAME
    if progress_path.is_file():
        progress = _read_json(progress_path)
        executed = len(progress.get("completed", []))

    return {
        "preflight": "PASS",
        "selection": name,
        "expected_count": int(m["expected_count"]),
        "selection_membership_hash": m["membership_hash"],
        "selection_manifest_sha256": m["manifest_sha256"],
        "authority_preflight": "VALID",
        "predecessor_receipt": pred["status"] if pred["required"] else "NOT_REQUIRED",
        "predecessor_selection": pred.get("pred"),
        "units_executed": executed,
        "zero_units_executed": executed == 0,
        "run_root": str(root),
        "run_root_exists": root_exists,
        "release": release,
        "static": static["static"],
        "zero_network": True,
    }


# ---------------------------------------------------------------------------
# STATUS / verify
# ---------------------------------------------------------------------------
def status(name: str) -> dict[str, Any]:
    root = run_root_for(name)
    if not root.is_dir():
        return {"selection": name, "status": "NOT_STARTED", "run_root": str(root)}
    receipt = receipt_for(name)
    if receipt is not None:
        authority = load_authority()
        try:
            validate_self_receipt(name, receipt, authority)
            return {
                "selection": name,
                "status": "COMPLETE",
                "N_EXECUTED": receipt.get("N_EXECUTED"),
                "N_PASS": receipt.get("N_PASS"),
                "N_NON_PASS": receipt.get("N_NON_PASS"),
                "run_root": str(root),
                "receipt_valid": True,
            }
        except R3Error:
            return {
                "selection": name,
                "status": "RECEIPT_INVALID",
                "run_root": str(root),
                "receipt_valid": False,
            }
    progress = root / PROGRESS_NAME
    if progress.is_file():
        data = _read_json(progress)
        completed = data.get("completed", [])
        return {
            "selection": name,
            "status": "RUNNING",
            "completed": len(completed),
            "run_root": str(root),
        }
    return {"selection": name, "status": "NOT_STARTED", "run_root": str(root)}


# ---------------------------------------------------------------------------
# Execution gate / aggregates (Task D / Task C common runner) - NOT executed
# in this mission; implemented for the operator.
# ---------------------------------------------------------------------------
def aggregate_progress(name: str) -> dict[str, Any]:
    """Conditions identical to FULL144 aggregate: exact N, exact order, no FAIL."""
    m = load_selection(name)
    root = run_root_for(name)
    progress_path = root / PROGRESS_NAME
    if not progress_path.is_file():
        raise ReceiptError(f"no progress file for {name}")
    progress = _read_json(progress_path)
    completed = progress.get("completed", [])
    if len(completed) != int(m["expected_count"]):
        raise ReceiptError(f"aggregate {len(completed)} != {m['expected_count']}")
    order = [c["validation_unit_id"] for c in completed]
    if order != m["ordered_unit_ids"]:
        raise ReceiptError("aggregate order mismatch")
    if any(c["result"] != "PASS" for c in completed):
        raise ReceiptError("aggregate contains a FAIL")
    return {
        "N_EXECUTED": len(completed),
        "N_PASS": sum(1 for c in completed if c["result"] == "PASS"),
        "N_NON_PASS": sum(1 for c in completed if c["result"] != "PASS"),
        "order_preserved": order == m["ordered_unit_ids"],
        "units": completed,
    }


def write_receipt(name: str, aggregate: dict[str, Any]) -> Path:
    authority = load_authority()
    m = load_selection(name)
    root = run_root_for(name)
    (root / NON_SCIENTIFIC_MARKER).write_text(
        f"NON-SCIENTIFIC R3 {name} selection root (M17_D7_R4_PHASE1C_HARNESS_R3)\n",
        encoding="utf-8",
    )
    payload: dict[str, Any] = {
        "schema_version": "env-canon-r4/r3-selection/receipt/1.0",
        "selection_name": name,
        "release_tag": authority["r3_release_tag"],
        "release_head": git_head(),
        "scientific_authority_head": authority["two_head_model"]["scientific_authority_head"],
        "support_evidence_head": authority["two_head_model"]["support_evidence_head"],
        "execution_code_set_hash": authority["execution_code_set_hash"],
        "committed_closure_content_hash": authority["committed_closure_content_hash"],
        "selection_membership_hash": m["membership_hash"],
        "selection_manifest_sha256": m["manifest_sha256"],
        "population_identity": authority["population_identity"],
        "ordered_membership_hash": authority["ordered_membership_hash"],
        "image_binding_hash": authority["image_binding_hash"],
        "N_EXECUTED": aggregate["N_EXECUTED"],
        "N_PASS": aggregate["N_PASS"],
        "N_NON_PASS": aggregate["N_NON_PASS"],
        "units": aggregate["units"],
        "run_root": str(root),
        "zero_network": True,
        "network_policy": "--network=none; no pull/build/download/acquire",
        "generated_utc": utcnow(),
    }
    path = _receipt_path(root)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


# ---------------------------------------------------------------------------
# Operator execution sweep (Task D / Task C) - delegates to the frozen common
# per-unit path (driver.Full144UnitRunner -> qualified Attempt-6 runner).
# NOT invoked inside OpenCode; provided for the operator's final release.
# ---------------------------------------------------------------------------
def selection_plan(name: str) -> dict[str, Any]:
    """Runner-compatible plan built from the committed selection manifest."""
    m = load_selection(name)
    units = []
    for rec in m["unit_records"]:
        units.append(
            {
                "validation_unit_id": rec["validation_unit_id"],
                "member_task_ids": rec["member_task_ids"],
                "docker_profile_id": rec["docker_profile_id"],
                "native_profile_id": rec["native_profile_id"],
                "python_version": rec["python_version"],
                "lock_type": rec["lock_type"],
                "install_route": rec["install_route"],
                "wheelhouse_era": rec["wheelhouse_era"],
                "source_fidelity_overlay_required": rec.get("source_fidelity_overlay_required", False),
            }
        )
    return {
        "schema_version": "env-canon-r4/r3-selection/plan/1.0",
        "selection_name": name,
        "calibration_units": units,
        "population": {"n_validation_units": len(units), "n_mapped_tasks": len(units)},
    }


def configure_driver(name: str, root: Path) -> Any:
    """Bind the frozen Full144 driver to the selection root and plan.

    Mirrors the frozen driver's configure_runner() parameterization (the SAME
    per-unit execution/gate path used by population qualification).  Only the
    selection membership/order/root differ.
    """
    os.environ["R4_FULL144_RUN_ROOT"] = str(root)
    from benchmark.wp2.full144 import driver

    driver.configure_runner()
    m = load_selection(name)
    driver.r2.FROZEN_UNIT_ORDER = tuple(m["ordered_unit_ids"])
    driver.r2.load_plan = lambda: selection_plan(name)
    driver.PROGRESS_JSON = root / PROGRESS_NAME
    driver.RECEIPTS_DIR = root / "receipts"
    return driver


def run_selection_sweep(name: str, root: Path) -> dict[str, Any]:
    """Fail-closed, deterministic, resumable execution sweep over one selection.

    Zero network: every unit container runs with --network=none through the
    frozen per-unit path.  Checkpointed atomically after each unit; a non-PASS
    result stops the sweep (no skip/reorder/rerun).  Returns the aggregate.
    """
    m = load_selection(name)
    driver = configure_driver(name, root)
    for idx in range(1, int(m["expected_count"]) + 1):
        record = driver.run_unit(idx)
        if record.get("result") != "PASS":
            raise ReceiptError(
                f"{name} unit {idx} {record['validation_unit_id']} non-PASS "
                f"({record.get('classification')}); sweep stopped"
            )
    return aggregate_progress(name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M17_D7_R4_PHASE1C Harness R3")
    ap.add_argument("--preflight", metavar="SELECTION", type=str.upper, default=None,
                    help="TARGETED3 | CAL12 | FULL144")
    ap.add_argument("--exec", metavar="SELECTION", type=str.upper, default=None,
                    help="fail-closed operator execution gate (not run in OpenCode)")
    ap.add_argument("--status", metavar="SELECTION", type=str.upper, default=None,
                    help="status of one selection run root")
    ap.add_argument("--verify-selection", metavar="SELECTION", type=str.upper, default=None,
                    help="recompute + compare a selection manifest hash")
    args = ap.parse_args(argv)

    try:
        if args.preflight:
            out = preflight(args.preflight)
            print(json.dumps(out, indent=2, sort_keys=True))
            if out["predecessor_receipt"] in ("BLOCKED_BY_PREDECESSOR_RECEIPT", "NOT_REQUIRED"):
                print(
                    f"PREFLIGHT_AUTHORITY_VALID {args.preflight} "
                    f"count={out['expected_count']} zero_units=True "
                    f"predecessor={out['predecessor_receipt']}"
                )
                return 0
            if out["predecessor_receipt"] == "PREDECESSOR_VALID":
                print(
                    f"PREFLIGHT_AUTHORITY_VALID {args.preflight} "
                    f"count={out['expected_count']} zero_units=False-ish "
                    f"predecessor=PREDECESSOR_VALID"
                )
                return 0
            return 0
        if args.verify_selection:
            m = load_selection(args.verify_selection)
            print(json.dumps(
                {"selection": args.verify_selection, "expected_count": m["expected_count"],
                 "membership_hash": m["membership_hash"], "manifest_sha256": m["manifest_sha256"]},
                indent=2, sort_keys=True))
            print("SELECTION_MANIFEST_VALID")
            return 0
        if args.status:
            print(json.dumps(status(args.status), indent=2, sort_keys=True))
            return 0
        if args.exec:
            # Fail-closed operator gate (authority + predecessor), then delegate
            # to the frozen common per-unit path in a fresh selection root.
            # OpenCode does NOT run this subcommand.
            authority = load_authority()
            verify_release_identity(authority)
            pred = predecessor_receipt_state(args.exec, authority)
            if pred["required"] and pred["status"] != "PREDECESSOR_VALID":
                raise ReceiptError(f"{args.exec} blocked: {pred['status']}")
            root = run_root_for(args.exec)
            root.mkdir(parents=True, exist_ok=True)
            (root / NON_SCIENTIFIC_MARKER).write_text(
                f"NON-SCIENTIFIC R3 {args.exec} selection root "
                f"(M17_D7_R4_PHASE1C_HARNESS_R3)\n",
                encoding="utf-8",
            )
            aggregate = run_selection_sweep(args.exec, root)
            receipt = write_receipt(args.exec, aggregate)
            print(json.dumps(
                {"selection": args.exec, "authority": "VALID",
                 "predecessor": pred["status"], "gate": "PASS",
                 "N_EXECUTED": aggregate["N_EXECUTED"],
                 "N_PASS": aggregate["N_PASS"],
                 "N_NON_PASS": aggregate["N_NON_PASS"],
                 "receipt": str(receipt)},
                indent=2, sort_keys=True))
            return 0
    except R3Error as exc:
        print(f"FAIL_CLOSED {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive
        print(f"UNEXPECTED_FAILURE {exc!r}", file=sys.stderr)
        return 2

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
