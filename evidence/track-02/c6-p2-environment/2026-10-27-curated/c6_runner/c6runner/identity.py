# -*- coding: utf-8 -*-
"""Task/test identity: the 5-field dedup record for every C6 task.

TASK_ID            = T (exact SHA from the frozen ledger)
SCOPE_HASH         = identity of the parent tree mounted read-only at P
REFERENCE_PATCH_HASH = identity of the test-only diff P->T over the M/A test paths
TEST_CONTRACT_HASH = identity of the M/A test-file bytes AT T (quarantined oracle)
ENVIRONMENT_ID     = versioned environment identity (environment.environment_id)
"""
import subprocess

from . import IDENTITY_SCHEMA_V1
from .hashes import sha256_hex


def git_run(git_dir, args, check=True):
    out = subprocess.run(["git"] + args, capture_output=True,
                         env={"GIT_DIR": git_dir}, text=True, check=False)
    if check and out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr[:500]}")
    return out


def tree_scope_sha(git_dir, rev: str) -> str:
    """Identity of the complete tree at rev: canonical path->oid listing."""
    out = git_run(git_dir, ["ls-tree", "-r", rev], check=True).stdout
    return sha256_hex(out.encode("utf-8"))


def reference_patch_sha(git_dir, parent: str, target: str, paths) -> str:
    """SHA-256 of `git diff P T -- <test paths>` raw bytes (test-only reference
    patch). Empty diff hashes to the digest of the empty string (documented)."""
    args = ["diff", "--no-ext-diff", parent, target, "--"] + list(paths)
    out = git_run(git_dir, args, check=True)
    return sha256_hex(out.stdout.encode("utf-8"))


def test_contract_sha(test_files_t: list) -> str:
    """Identity of oracle test-file bytes at T. test_files_t: sorted
    (path, blob_oid) for the M/A test paths resolved at T."""
    records = [(p, oid) for p, oid in sorted(test_files_t)]
    import json
    data = json.dumps({"schema": IDENTITY_SCHEMA_V1, "files": records},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    return sha256_hex(data.encode("utf-8"))


def five_field(task_sha, scope_hash, reference_patch_hash, test_contract_hash,
               environment_id):
    return {
        "TASK_ID": task_sha,
        "SCOPE_HASH": scope_hash,
        "REFERENCE_PATCH_HASH": reference_patch_hash,
        "TEST_CONTRACT_HASH": test_contract_hash,
        "ENVIRONMENT_ID": environment_id,
    }