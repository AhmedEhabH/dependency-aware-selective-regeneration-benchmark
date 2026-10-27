# -*- coding: utf-8 -*-
"""Isolated workspace for one task. The bare git store is READ-ONLY:
materialization uses `git archive` streamed to tarfile (never git worktree,
which would mutate the bare store). T-only test bytes go to a quarantined
`oracle/` directory, NEVER into the prospective source tree at P."""
import os
import subprocess
import tarfile
import uuid

from .errors import Blocked


class IsolatedWorkspace:
    def __init__(self, run_root: str, task_sha: str):
        self.root = os.path.join(run_root, task_sha[:12], uuid.uuid4().hex[:10])
        self.src = os.path.join(self.root, "src")
        self.oracle = os.path.join(self.root, "oracle")
        self.logs = os.path.join(self.root, "logs")
        self.scratch = os.path.join(self.root, "scratch")
        self.eval_dir = os.path.join(self.root, "oracle_evaluator")
        self.eval_work = os.path.join(self.root, "eval_work")
        self.eval_f2p = os.path.join(self.root, "eval_f2p")
        self.eval_scratch = os.path.join(self.root, "eval_scratch")
        self.eval_logs = os.path.join(self.root, "eval_logs")
        for d in (self.src, self.oracle, self.logs, self.scratch, self.eval_dir,
                  self.eval_work, self.eval_f2p, self.eval_scratch,
                  self.eval_logs):
            os.makedirs(d, exist_ok=True)

    def _stream_tree(self, git_dir: str, rev: str, dst: str):
        """Stream one tree from the READ-ONLY bare store into dst."""
        proc = subprocess.Popen(
            ["git", "archive", "--format=tar", rev],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"GIT_DIR": git_dir})
        try:
            with tarfile.open(fileobj=proc.stdout, mode="r|") as tf:
                tf.extractall(dst, filter="data")
        except Exception as e:  # tarfile read errors etc.
            err = proc.stderr.read().decode("utf-8", "replace") if proc.stderr else ""
            proc.kill()
            raise Blocked("tree materialization failed",
                          f"git archive: {err or e}") from e
        rc = proc.wait()
        if rc != 0:
            raise Blocked("tree materialization failed (rc=%d)" % rc,
                          proc.stderr.read().decode("utf-8", "replace"))
        if not os.path.isdir(dst):
            raise Blocked("tree materialization produced no tree", dst)
        return dst

    def materialize_parent(self, git_dir: str, parent: str):
        """Stream the P tree from the bare store into src/ (read-only-op)."""
        return self._stream_tree(git_dir, parent, self.src)

    def materialize_reference_tree(self, git_dir: str, code_rev: str,
                                   oracle_paths, dst=None):
        """Build an evaluation-only reference tree from `code_rev` bytes
        (code_rev = parent P for the F2P negative baseline; code_rev = T for
        the P2P positive reference), then overlay the T test bytes of the FULL
        M/A contract at their exact repo-relative paths. T bytes never enter
        src/; each reference tree exists only under its own eval dir
        (eval_f2p / eval_work)."""
        dst = dst or self.eval_work
        for f in os.listdir(dst):
            p = os.path.join(dst, f)
            if os.path.isdir(p):
                import shutil
                shutil.rmtree(p)
            else:
                os.remove(p)
        self._stream_tree(git_dir, code_rev, dst)
        for p in oracle_paths:
            src = os.path.join(self.oracle, p)
            if not os.path.exists(src):
                raise Blocked("reference oracle byte missing", p)
            out = os.path.join(dst, p)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(src, "rb") as f:
                data = f.read()
            with open(out, "wb") as f:
                f.write(data)
        return dst

    def materialize_t_only_files(self, git_dir: str, target: str, paths):
        """Quarantined oracle bytes: test paths AT T written under
        oracle/<path> (repo-relative). Never into src/."""
        return self.materialize_contract_files(git_dir, target, paths)

    def materialize_contract_files(self, git_dir: str, target: str, paths):
        """Quarantine the T bytes of the FULL M/A test contract: every path is
        materialized from T under oracle/<path>, mirrored repo layout. P-available
        paths therefore ALSO have their T bytes quarantined (they only ever run
        in the evaluation-only reference tree, never in the prospective input)."""
        written = []
        for p in paths:
            oid = subprocess.run(
                ["git", "rev-parse", f"{target}:{p}"],
                capture_output=True, text=True, env={"GIT_DIR": git_dir},
                check=False).stdout.strip()
            if not oid:
                raise Blocked("contract path unresolvable at T", p)
            data = subprocess.run(
                ["git", "cat-file", "blob", oid], capture_output=True,
                env={"GIT_DIR": git_dir}, check=False).stdout
            dst = os.path.join(self.oracle, p)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
            written.append((p, oid))
        return written

    def cwd(self):
        return self.src