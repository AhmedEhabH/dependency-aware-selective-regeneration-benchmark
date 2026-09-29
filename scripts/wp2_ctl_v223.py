#!/usr/bin/env python3
"""WP-2 deterministic mission controller v2.2.3 (brain-authored kit; hash-verified).

v2.2.3 changes vs v2.2 (scripts/wp2_ctl.py stays frozen for Smoke v2.2 provenance):
- tags are pushed by exact refspec only (never `git push --tags`);
- STOP reports embed the last 40 lines of the failing command log;
- the kit manifest path comes from the plan (settings.kit_manifest).

The controller, not an LLM, decides every transition. It reads a declarative plan
(controller/plan_*.json), keeps ONE state file, runs each phase's exact command,
maps exit codes to outcomes, checks artifacts, enforces allowed writes, verifies
the kit hashes, commits/tags/pushes, and on STOP writes the report and the exports.

Commands:
  python scripts/wp2_ctl_v223.py verify-kit --plan PLAN
  python scripts/wp2_ctl_v223.py status     --plan PLAN
  python scripts/wp2_ctl_v223.py dry-run    --plan PLAN
  python scripts/wp2_ctl_v223.py run        --plan PLAN [--max-seconds N]
  python scripts/wp2_ctl_v223.py ack-stop   --plan PLAN --token TOKEN --note "decision text"

Exit codes: 0 COMPLETE, 10 STOPPED, 20 YIELD (time budget used; run again),
2 KIT_TAMPERED, 11 NEEDS_ACK (a non-resumable stop is recorded).
"""
from __future__ import annotations

import argparse
import contextlib
import fnmatch
import glob as globmod
import hashlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
KIT_MANIFEST = PROJECT / "controller" / "KIT_MANIFEST.json"

EXIT_COMPLETE, EXIT_STOPPED, EXIT_YIELD, EXIT_TAMPER, EXIT_NEEDS_ACK = 0, 10, 20, 2, 11
ALWAYS_ALLOWED = ("logs/", "_workspace/tmp/", "controller/state/")
LARGE_FILE_BYTES = 32 * 1024 * 1024
IGNORED_PARTS = ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache")


# ---------------------------------------------------------------- utilities
def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def norm_sha256(path: Path) -> str:
    data = Path(path).read_bytes()
    if b"\x00" not in data[:8192]:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def file_fingerprint(p: Path) -> str:
    """Content hash for normal files; size+mtime for very large files (speed)."""
    if not p.is_file():
        return "<deleted>"
    st = p.stat()
    if st.st_size > LARGE_FILE_BYTES:
        return f"large:{st.st_size}:{st.st_mtime_ns}"
    return norm_sha256(p)


def json_sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode("utf-8")).hexdigest()


def dig(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in dotted.split(".") if dotted else []:
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


# ---------------------------------------------------------------- kit integrity
def verify_kit(project: Path = PROJECT, manifest: Path | None = None) -> list[str]:
    manifest = manifest or project / "controller" / "KIT_MANIFEST.json"
    if not manifest.exists():
        return [f"kit manifest missing: {manifest}"]
    data = json.loads(manifest.read_text(encoding="utf-8"))
    bad = []
    for rel, digest in sorted(data["files"].items()):
        p = project / rel
        if not p.exists():
            bad.append(f"missing {rel}")
        elif norm_sha256(p) != digest:
            bad.append(f"modified {rel}")
    return bad


# ---------------------------------------------------------------- git helpers
class Git:
    def __init__(self, root: Path, enabled: bool = True, push: bool = True,
                 remote: str = "origin", branch: str = "main") -> None:
        self.root, self.enabled, self.push_enabled = root, enabled, push
        self.remote, self.branch = remote, branch

    def _run(self, *args: str, check: bool = False) -> subprocess.CompletedProcess:
        r = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr[-500:]}")
        return r

    def dirty_snapshot(self) -> dict[str, str]:
        r = self._run("status", "--porcelain=v1", "-z", "-uall")
        out: dict[str, str] = {}
        entries = r.stdout.split("\0")
        i = 0
        while i < len(entries):
            e = entries[i]
            i += 1
            if len(e) < 4:
                continue
            code, path = e[:2], e[3:]
            if code[0] in "RC":
                i += 1  # skip the rename source
            p = self.root / path
            if any(part in IGNORED_PARTS for part in Path(path).parts):
                continue
            out[path.replace("\\", "/")] = file_fingerprint(p)
        return out

    def commit(self, prefixes: list[str], message: str) -> str | None:
        if not self.enabled:
            return None
        existing = [p for p in prefixes if (self.root / p).exists()]
        if existing:
            self._run("add", "-A", "--", *existing, check=True)
        staged = self._run("diff", "--cached", "--name-only").stdout.strip()
        if not staged:
            return None
        self._run("commit", "-q", "-m", message, check=True)
        return self._run("rev-parse", "HEAD").stdout.strip()

    def push(self) -> bool:
        if not (self.enabled and self.push_enabled):
            return True
        for attempt in range(3):
            if self._run("push", self.remote, self.branch).returncode == 0:
                return True
            time.sleep(20 * (attempt + 1))
        return False

    def push_tag(self, name: str) -> bool:
        """Push exactly one tag ref. Unrelated local tags can never fail this push."""
        if not (self.enabled and self.push_enabled):
            return True
        ref = f"refs/tags/{name}:refs/tags/{name}"
        for attempt in range(3):
            if self._run("push", self.remote, ref).returncode == 0:
                return True
            time.sleep(20 * (attempt + 1))
        return False

    def tag(self, name: str, message: str) -> str:
        head = self._run("rev-parse", "HEAD").stdout.strip()
        existing = self._run("rev-parse", "-q", "--verify", f"refs/tags/{name}^{{commit}}")
        if existing.returncode == 0:
            if existing.stdout.strip() != head:
                raise RuntimeError(f"tag {name} exists on another commit; tags never move")
            return head
        self._run("tag", "-a", name, "-m", message, check=True)
        return head


# ---------------------------------------------------------------- checks
def run_check(spec: dict[str, Any], root: Path, runcmd: Callable[..., int]) -> tuple[bool, str]:
    kind = spec["type"]
    if kind == "file_exists":
        p = root / spec["path"]
        return p.exists(), f"file_exists {spec['path']}"
    if kind == "file_absent":
        p = root / spec["path"]
        return not p.exists(), f"file_absent {spec['path']}"
    if kind in ("json_equals", "json_ge", "json_le"):
        p = root / spec["path"]
        if not p.exists():
            return False, f"{kind}: missing {spec['path']}"
        val = dig(json.loads(p.read_text(encoding="utf-8")), spec["key"])
        target = spec["value"]
        ok = (val == target if kind == "json_equals"
              else (val is not None and (val >= target if kind == "json_ge" else val <= target)))
        return ok, f"{kind} {spec['path']}:{spec['key']}={val!r} vs {target!r}"
    if kind == "count_files":
        n = count_files(root, spec)
        op, v = spec.get("op", "=="), spec["value"]
        ok = {"==": n == v, ">=": n >= v, "<=": n <= v}[op]
        return ok, f"count_files {spec['glob']} = {n} {op} {v}"
    if kind == "command_ok":
        code = runcmd(spec["command"], spec.get("timeout_s", 1800), "check")
        return code == 0, f"command_ok {' '.join(spec['command'])} -> {code}"
    raise ValueError(f"unknown check type {kind}")


def count_files(root: Path, spec: dict[str, Any]) -> int:
    n = 0
    for f in globmod.glob(str(root / spec["glob"]), recursive=True):
        if "where" in spec:
            try:
                rec = json.loads(Path(f).read_text(encoding="utf-8"))
            except (ValueError, OSError):
                continue
            if all(dig(rec, k) in (v if isinstance(v, list) else [v])
                   for k, v in spec["where"].items()):
                n += 1
        else:
            n += 1
    return n


# ---------------------------------------------------------------- controller
class Controller:
    def __init__(self, plan_path: Path, root: Path = PROJECT, git: Git | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 kit_check: Callable[[], list[str]] | None = None) -> None:
        self.root = root
        self.plan_path = plan_path
        self.plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.plan_sha = norm_sha256(plan_path)
        s = self.plan["settings"]
        self.state_path = root / s["state_file"]
        self.git = git or Git(root, s.get("git_commit", True), s.get("git_push", True),
                              s.get("remote", "origin"), s.get("branch", "main"))
        self.clock = clock
        manifest = root / s.get("kit_manifest", "controller/KIT_MANIFEST.json")
        self.kit_check = kit_check or (lambda: verify_kit(root, manifest))
        self.last_log: Path | None = None
        self.state = self._load_state()
        self.log_dir = root / "logs" / "controller"

    # ------------------------------------------------------------ state
    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"plan": self.plan["id"], "plan_sha256": self.plan_sha, "phases": {},
                "stop": None, "history": [], "acks": []}

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.state, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def event(self, phase: str, kind: str, detail: str = "") -> None:
        self.state["history"].append({"utc": utc(), "phase": phase, "event": kind,
                                      "detail": detail[:1500]})
        self.save()
        print(f"[ctl] {utc()} {phase} {kind} {detail[:300]}", flush=True)

    # ------------------------------------------------------------ commands
    def runcmd(self, command: list[str], timeout: int, tag: str) -> int:
        cmd = [sys.executable if c == "{python}" else c for c in command]
        self.log_dir.mkdir(parents=True, exist_ok=True)
        log = self.log_dir / f"{time.strftime('%Y%m%dT%H%M%S')}_{tag}.log"
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([str(self.root / "src"), str(self.root),
                                             env.get("PYTHONPATH", "")])
        env["PYTHONIOENCODING"] = "utf-8"
        with log.open("w", encoding="utf-8") as fh:
            fh.write(f"$ {' '.join(cmd)}\n")
            fh.flush()
            try:
                r = subprocess.run(cmd, cwd=self.root, stdout=fh, stderr=subprocess.STDOUT,
                                   env=env, timeout=timeout)
                code = r.returncode
            except subprocess.TimeoutExpired:
                fh.write("\n[ctl] TIMEOUT\n")
                code = 124
        self.last_log = log
        tail = log.read_text(encoding="utf-8", errors="replace").splitlines()[-6:]
        print(f"[ctl]   exit={code} log={log.relative_to(self.root)} :: {' | '.join(tail)[-400:]}",
              flush=True)
        return code

    # ------------------------------------------------------------ writes
    def allowed(self, path: str, prefixes: list[str]) -> bool:
        allowed = list(ALWAYS_ALLOWED) + list(prefixes) + [
            self.plan["settings"]["state_file"]]
        return any(path == p or path.startswith(p) or fnmatch.fnmatch(path, p) for p in allowed)

    def unexpected_writes(self, before: dict[str, str], prefixes: list[str]) -> list[str]:
        after = self.git.dirty_snapshot()
        changed = [p for p, h in after.items() if before.get(p) != h]
        changed += [p for p in before if p not in after and before[p] != "<deleted>"]
        return sorted(p for p in set(changed) if not self.allowed(p, prefixes))

    # ------------------------------------------------------------ stop
    def stop(self, phase: str, token: str, detail: str) -> int:
        resumable = token in set(self.plan["settings"].get("resumable_tokens", []))
        if self.last_log is not None and self.last_log.exists():
            tail = self.last_log.read_text(encoding="utf-8", errors="replace").splitlines()[-40:]
            detail = (f"{detail}\n--- last log: {self.last_log.relative_to(self.root).as_posix()}"
                      f" ---\n" + "\n".join(tail))
        self.state["stop"] = {"token": token, "phase": phase, "utc": utc(),
                              "detail": detail[-6000:], "resumable": resumable}
        self.event(phase, "STOP", f"{token}: {detail}")
        report = self.write_stop_report()
        exports = self.run_exports(f"STOP_{token}")
        self.state["stop"]["exports"] = exports
        self.save()
        if self.git.enabled:
            self.git.commit(self.plan["settings"]["stop_commit_prefixes"],
                            f"evidence(wp2): controller STOP {token} at {phase}")
            self.git.push()
        self.print_block("STOPPED", report)
        return EXIT_STOPPED

    def write_stop_report(self) -> Path:
        st = self.state["stop"]
        lines = [f"# Controller STOP — {st['token']}", "",
                 f"- plan: {self.plan['id']} (sha {self.plan_sha[:12]})",
                 f"- phase: {st['phase']}", f"- utc: {st['utc']}",
                 f"- resumable: {st['resumable']}", "", "## Detail", "", "```",
                 st["detail"], "```", "", "## Phase status", ""]
        for ph in self.plan["phases"]:
            lines.append(f"- {ph['id']}: {self.state['phases'].get(ph['id'], {}).get('status', 'PENDING')}")
        lines += ["", "## Next", "",
                  ("Resumable: fix the external cause, then run the controller again."
                   if st["resumable"] else
                   "Not resumable automatically: a human decision is required, recorded with "
                   "`python scripts/wp2_ctl.py ack-stop --token <TOKEN> --note ...`."), ""]
        d = self.root / self.plan["settings"]["report_dir"]
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"STOP_{st['token']}_{time.strftime('%Y%m%dT%H%M%S')}.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def run_exports(self, label: str) -> dict[str, Any]:
        res: dict[str, Any] = {}
        for name, command in self.plan["settings"].get("exports", {}).items():
            cmd = [c.replace("{label}", label) for c in command]
            res[name] = self.runcmd(cmd, 3600, f"export_{name}")
        return res

    def print_block(self, head: str, report: Path | None = None) -> None:
        print("=" * 72)
        print(f"WP2_CONTROLLER_{head}")
        print(f"PLAN={self.plan['id']}")
        for ph in self.plan["phases"]:
            print(f"  {ph['id']}={self.state['phases'].get(ph['id'], {}).get('status', 'PENDING')}")
        if self.state.get("stop"):
            print(f"STOP_TOKEN={self.state['stop']['token']}")
            print(f"STOP_PHASE={self.state['stop']['phase']}")
            print(f"RESUMABLE={self.state['stop']['resumable']}")
            print(f"EXPORTS={json.dumps(self.state['stop'].get('exports', {}))}")
        if report:
            print(f"REPORT={report.relative_to(self.root)}")
        print("=" * 72)

    # ------------------------------------------------------------ phases
    def run(self, max_seconds: float | None = None, until: str | None = None) -> int:
        t0 = self.clock()
        bad = self.kit_check()
        if bad:
            print("KIT_TAMPERED " + "; ".join(bad[:20]))
            return EXIT_TAMPER
        if self.state["plan_sha256"] != self.plan_sha:
            return self.stop("PLAN", "PLAN_CHANGED", "plan file differs from the state's plan hash")
        if self.state.get("stop"):
            st = self.state["stop"]
            if not st["resumable"]:
                print(f"NEEDS_ACK {st['token']} at {st['phase']}")
                self.print_block("NEEDS_ACK")
                return EXIT_NEEDS_ACK
            self.event(st["phase"], "RESUME", f"after {st['token']}")
            self.state["stop"] = None
            self.save()
        for ph in self.plan["phases"]:
            pid = ph["id"]
            pst = self.state["phases"].setdefault(pid, {"status": "PENDING", "attempts": 0,
                                                        "iterations": 0})
            if pst["status"] == "PASS":
                continue
            for req in ph.get("requires", []):
                if self.state["phases"].get(req, {}).get("status") != "PASS":
                    return self.stop(pid, "REQUIREMENT_NOT_MET", f"{req} is not PASS")
            flag = self.plan["settings"].get("stop_flag")
            if flag and (self.root / flag).exists():
                return self.stop(pid, "USER_STOP_FLAG", f"{flag} present")
            code = self.run_phase(ph, pst, t0, max_seconds)
            if code is not None:
                return code
            if until and pid == until:
                self.print_block("PAUSED_AT_" + pid)
                return EXIT_YIELD
        self.print_block("COMPLETE")
        return EXIT_COMPLETE

    def run_phase(self, ph: dict[str, Any], pst: dict[str, Any], t0: float,
                  max_seconds: float | None) -> int | None:
        pid = ph["id"]
        prefixes = ph.get("allowed_write_prefixes", [])
        self.last_log = None
        pst["status"] = "RUNNING"
        pst["runs"] = pst.get("runs", 0) + 1
        pst["attempts"], pst["failures"] = 0, 0  # retries are per controller run
        self.event(pid, "START", ph.get("title", ""))
        loop = ph.get("kind") == "loop"
        stalled = 0
        while True:
            if not loop:
                pst["attempts"] += 1
            for pre in ph.get("pre_checks", []):
                ok, msg = run_check(pre, self.root, self.runcmd)
                if not ok:
                    return self.stop(pid, pre.get("fail_token", ph["fail_token"]), msg)
            if loop:
                done = all(run_check(c, self.root, self.runcmd)[0] for c in ph["done_checks"])
                if done:
                    break
                if max_seconds is not None and self.clock() - t0 >= max_seconds:
                    pst["status"] = "PENDING"
                    self.event(pid, "YIELD", "time budget used")
                    self.print_block("YIELD")
                    return EXIT_YIELD
                progress_before = count_files(self.root, ph["progress"])
            before = self.git.dirty_snapshot()
            outcome = self.execute(ph)
            unexpected = self.unexpected_writes(before, prefixes)
            if unexpected:
                return self.stop(pid, "UNEXPECTED_WRITE", "; ".join(unexpected[:20]))
            if outcome.startswith("STOP:"):
                return self.stop(pid, outcome[5:], f"exit mapped to {outcome}")
            if outcome == "FAIL":
                if loop:
                    pst["iterations"] += 1
                    pst["failures"] = pst.get("failures", 0) + 1
                    if pst["failures"] > ph.get("max_retries", 1):
                        return self.stop(pid, ph["fail_token"], "command failed")
                    continue
                if pst["attempts"] <= ph.get("max_retries", 0):
                    self.event(pid, "RETRY", f"attempt {pst['attempts']}")
                    continue
                return self.stop(pid, ph["fail_token"], "command failed")
            if loop:
                pst["iterations"] += 1
                pst["failures"] = 0
                self.save()
                progress_after = count_files(self.root, ph["progress"])
                if progress_after <= progress_before:
                    stalled += 1
                    if stalled >= 2:
                        return self.stop(pid, "NO_PROGRESS",
                                         f"two iterations without progress ({progress_after})")
                else:
                    stalled = 0
                if ph.get("commit_each_iteration", True):
                    self.git.commit(prefixes, f"{ph['commit_message']} ({progress_after})")
                    self.git.push()
                if pst["iterations"] >= ph.get("max_iterations", 50):
                    return self.stop(pid, "MAX_ITERATIONS", str(pst["iterations"]))
                continue
            break
        for chk in ph.get("pass_checks", []):
            ok, msg = run_check(chk, self.root, self.runcmd)
            if not ok:
                return self.stop(pid, chk.get("fail_token", ph["fail_token"]), msg)
        for act in ph.get("post_actions", []):
            try:
                self.post_action(act)
            except Exception as exc:
                return self.stop(pid, "POST_ACTION_FAILED", f"{act}: {exc}")
        if ph.get("commit_message"):
            self.git.commit(prefixes, ph["commit_message"])
            if not self.git.push():
                self.event(pid, "PUSH_PENDING", "push failed after 3 attempts")
        pst["status"] = "PASS"
        pst["passed_utc"] = utc()
        self.event(pid, "PASS")
        return None

    def execute(self, ph: dict[str, Any]) -> str:
        if ph.get("builtin") == "verify_kit":
            bad = self.kit_check()
            return "PASS" if not bad else "STOP:KIT_TAMPERED"
        if ph.get("builtin") == "noop":
            return "PASS"
        code = self.runcmd(ph["command"], ph.get("timeout_s", 10800), ph["id"])
        mapping = {int(k): v for k, v in ph.get("exit_codes", {}).items()}
        if code in mapping:
            return mapping[code]
        return "PASS" if code == 0 else "FAIL"

    def post_action(self, act: dict[str, Any]) -> None:
        if act["type"] == "commit":
            self.git.commit(act["prefixes"], act["message"])
        elif act["type"] == "tag":
            name = act["name"].replace("{date}", time.strftime("%Y-%m-%d"))
            try:
                self.git.tag(name, act.get("message", name))
            except RuntimeError:
                if not self.tag_only_behind_by_controller_files(name):
                    raise
            if not self.git.push_tag(name):
                raise RuntimeError(f"exact push of tag {name} failed")
        elif act["type"] == "push":
            if not self.git.push():
                raise RuntimeError("push failed")
        elif act["type"] == "exports":
            res = self.run_exports(act.get("label", "CLOSURE"))
            if any(v != 0 for k, v in res.items() if k in act.get("required", ["light"])):
                raise RuntimeError(f"required export failed: {res}")
        else:
            raise ValueError(f"unknown post action {act['type']}")

    def tag_only_behind_by_controller_files(self, name: str) -> bool:
        """A resumed phase may find its tag one STOP-commit behind HEAD. Accept it only if
        every file changed since the tagged commit is controller bookkeeping."""
        tagged = self.git._run("rev-parse", f"refs/tags/{name}^{{commit}}").stdout.strip()
        if not tagged or self.git._run("merge-base", "--is-ancestor", tagged, "HEAD").returncode:
            return False
        changed = self.git._run("diff", "--name-only", tagged, "HEAD").stdout.split()
        s = self.plan["settings"]
        return all(c == s["state_file"] or c.startswith(s["report_dir"].rstrip("/") + "/")
                   for c in changed)

    def ack(self, token: str, note: str) -> int:
        st = self.state.get("stop")
        if not st or st["token"] != token:
            print(f"ACK_REFUSED current stop is {st['token'] if st else None}")
            return 1
        self.state["acks"].append({"utc": utc(), "token": token, "phase": st["phase"],
                                   "note": note})
        st["resumable"] = True
        self.event(st["phase"], "ACK", f"{token}: {note}")
        return 0

    def dry_run(self) -> int:
        for ph in self.plan["phases"]:
            cmd = " ".join(ph.get("command", [ph.get("builtin", "")]))
            print(f"{ph['id']:<22} {ph.get('kind', 'once'):<5} requires={ph.get('requires', [])} "
                  f"fail={ph['fail_token']} :: {cmd}")
        return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("verify-kit", "status", "dry-run", "run", "ack-stop"))
    ap.add_argument("--plan", required=True)
    ap.add_argument("--max-seconds", type=float, default=None)
    ap.add_argument("--until", default=None)
    ap.add_argument("--token", default=None)
    ap.add_argument("--note", default="")
    a = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(errors="replace")  # Windows consoles: never crash on printing
    if a.command == "verify-kit":
        plan = json.loads((PROJECT / a.plan).read_text(encoding="utf-8"))
        bad = verify_kit(PROJECT, PROJECT / plan["settings"].get("kit_manifest",
                                                               "controller/KIT_MANIFEST.json"))
        print("KIT_OK" if not bad else "KIT_TAMPERED " + "; ".join(bad))
        return 0 if not bad else EXIT_TAMPER
    ctl = Controller(PROJECT / a.plan)
    if a.command == "status":
        ctl.print_block("STATUS")
        return 0
    if a.command == "dry-run":
        return ctl.dry_run()
    if a.command == "ack-stop":
        if not a.token or not a.note:
            print("ack-stop needs --token and --note")
            return 1
        return ctl.ack(a.token, a.note)
    return ctl.run(a.max_seconds, a.until)


if __name__ == "__main__":
    raise SystemExit(main())
