# -*- coding: utf-8 -*-
"""C6Runner — fail-closed orchestrator.

Flow per task:
  1. GLOBAL STOP guards: authorization binding, frozen-input hashes, budget.
  2. R1: ledger row for T exists, C4_PASS, C5 TEST_CHANGE, M/A count > 0,
     single verified parent P; P byte-materializable from the bare store.
     Recompute C5_test_paths_hash from the SHA-verified H2 file-event source
     and require equality with the frozen ledger value.
  3. R2: issue body-as-of-work byte hash present in ledger; protected cache
     bytes re-verified equal; issue_createdAt < t_work (tz-aware).
  4. Build isolated workspace: P materialized read-only; T-only files to
     quarantined oracle dir (never into src).
  5. Compute 5-field identity + ENVIRONMENT_ID (bps from P manifests).
  6. Execute the THREE evaluation roles (issue 2):
        a. diagnostic  = P code + P tests        (ws/src, evidence only)
        b. F2P baseline = P code + T tests       (ws/eval_f2p, evaluation-only)
        c. P2P positive = T code + T tests       (ws/eval_work, evaluation-only)
     each under resource limits + offline gate (auth + freeze permitting
     execution) — or preflight-only -> BLOCKED. An expected F2P failure is
     the recorded negative-baseline outcome, never a broken environment; the
     verdict NEVER rests on the P/P diagnostic; oracle validity requires
     >=1 genuinely executed non-skipped test (issue 1).
  7. Verdict, receipt (write-then-hash). GLOBAL STOP cleans up and stops.
"""
import csv
import hashlib
import io
import json
import os

from . import RUNNER_VERSION
from .authorization import AuthorizationReceipt, FrozenProtocol
from .environment import EnvSnapshot, wheelhouse_dir_id
from .errors import (Blocked, BudgetExceeded, C6Stop, EnvDrift,
                     FrozenInputDrift, LeakageDetected, MissingApproval,
                     NotAuthorized)
from .hashes import json_blob, sha256_file
from .identity import (five_field, reference_patch_sha, test_contract_sha,
                       tree_scope_sha)
from .receipts import write_receipt
from .resources import ResourceLimits, read_log, run_limited
from .verdicts import Verdict, decide_from_reference, decide_from_run
from .workspace import IsolatedWorkspace
from .oracle import parse_junit_report, parse_pytest_summary
from .evaluator import expand_contract_in_command
from .taskplan import TaskPlan, TaskPlanError
from . import isolation as _iso

# F-role names carried by the frozen-input manifest (v2): the ACTUAL git
# store / ledger / H2 events / protected cache / manifest paths that the
# runner binds to. CLI overrides must equal these exactly (finding F6).
F_ROLE_KEYS = ("git_store", "ledger", "h2_events", "protected_cache",
               "frozen_manifest")

MANIFEST_NAMES = [
    "requirements.txt", "requirements.in", "requirements-dev.txt",
    "requirements-dev.in", "requirements-test.txt", "requirements_test.txt",
    "requirements-common.txt", "requirements-production.txt",
    "requirements-development.txt",
    "requirements/base.txt", "requirements/dev.txt", "requirements/production.txt",
    "requirements/test.txt", "requirements/base.in", "requirements/dev.in",
    "requirements/production.in", "requirements/test.in",
    "requirements/requirements.txt", "requirements/requirements-dev.txt",
    "poetry.lock", "pyproject.toml", "uv.lock", "Pipfile", "Pipfile.lock",
    "setup.py", "setup.cfg", "tox.ini", "pytest.ini", ".python-version",
    "runtime.txt", "environment.yml", "package.json",
]


class C6Runner:
    def __init__(self, freeze_path, auth_path, git_dir, ledger_path, h2_events_path,
                 protected_cache_dir, out_root, frozen_inputs,
                 limits=None, offline=True, input_roles=None):
        self.freeze = FrozenProtocol(freeze_path)
        self.auth = AuthorizationReceipt(auth_path)
        self.git_dir = git_dir
        self.ledger_path = ledger_path
        self.h2_events_path = h2_events_path
        self.protected_cache_dir = protected_cache_dir
        self.out_root = out_root
        self.frozen_inputs = frozen_inputs  # {path: sha256} (one per file)
        # F6 binding map: role -> frozen manifest path. When supplied (the CLI
        # always supplies it), the ACTUAL bound paths must equal these exactly.
        self.input_roles = dict(input_roles or {})
        self.limits = limits or ResourceLimits()
        self.offline = offline
        self.inputs_verified = False
        self.global_stop = None

    # ------------------------------------------------------------------- F6
    def verify_input_binding(self):
        """Fail-closed F6 gate: every frozen-role path the operator wired must
        equal the manifest-declared canonical path for that role (normalized
        absolute, case-insensitive). Any substitution -> C6Stop
        INPUT_BINDING_MISMATCH before any input is trusted."""
        if not self.input_roles:
            return True
        bound = {
            "git_store": getattr(self, "git_dir", None),
            "ledger": getattr(self, "ledger_path", None),
            "h2_events": getattr(self, "h2_events_path", None),
            "protected_cache": getattr(self, "protected_cache_dir", None),
        }
        bad = []
        for role in F_ROLE_KEYS:
            want = self.input_roles.get(role)
            if not want:
                continue
            got = bound.get(role)
            if not got:
                bad.append((role, None, want))
                continue
            if os.path.normcase(os.path.abspath(got)) != \
                    os.path.normcase(os.path.abspath(want)):
                bad.append((role, got, want))
        if bad:
            raise C6Stop(
                "INPUT_BINDING_MISMATCH",
                "the supplied execution input does not equal the frozen "
                "manifest path for role(s): " + json.dumps(bad))
        return True

    # ------------------------------------------------------------------ setup
    def verify_frozen_inputs(self):
        """Fail-closed: every declared frozen input must exist with a byte-exact
        SHA-256. Any drift raises FrozenInputDrift (GLOBAL STOP)."""
        failures = []
        for path, want in self.frozen_inputs.items():
            if not os.path.exists(path):
                failures.append((path, "MISSING", None, want))
                continue
            got = sha256_file(path)
            if got != want.upper():
                failures.append((path, "HASH_DRIFT", got, want))
        if failures:
            raise FrozenInputDrift("frozen input verification failed",
                                   json.dumps(failures))
        self.inputs_verified = True
        return True

    def _check_stop(self):
        if self.global_stop is not None:
            raise self.global_stop

    def _authorize(self, task_sha):
        self.verify_input_binding()      # F6: bind actual inputs to the contract
        if not self.inputs_verified:
            self.verify_frozen_inputs()
        return self.auth.authorize(self.freeze, task_sha)

    # ------------------------------------------------------------- eligibility
    def _load_ledger_row(self, task_sha):
        with open(self.ledger_path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["sha"] == task_sha:
                    return r
        raise Blocked("candidate not in frozen ledger", task_sha)

    def _recompute_c5_hash(self, task_sha):
        """Recompute the frozen C5 test-path hash from the SHA-verified H2
        source (streaming, uppercase json_blob). Raises on source drift."""
        seen = {}
        with open(self.h2_events_path, encoding="utf-8") as f:
            for line in f:
                e = json.loads(line)
                if e["commit"] != task_sha:
                    continue
                status = str(e.get("status") or "").upper()
                p = e.get("new_path") or e.get("old_path")
                if p and status in ("A", "M", "D", "R", "C", "T"):
                    if _is_test_path(p):
                        seen[(p, status)] = True
        return json_blob(list(seen.keys()))

    def _check_eligibility(self, task_sha):
        r = self._load_ledger_row(task_sha)
        issues = []
        # R1: frozen ledger uses C4=C4_PASS (exact value, e.g. 222 rows)
        if r.get("C4") != "C4_PASS":
            issues.append("C4!=C4_PASS")
        if r.get("C5") != "TEST_CHANGE":
            issues.append("C5!=TEST_CHANGE")
        if not r.get("C5_test_paths_hash"):
            issues.append("C5_test_paths_hash missing")
        if not (r.get("C5_test_events_count") or 0) > 0:
            issues.append("C5_test_events_count==0")
        if not (r.get("C5_ma_count") or 0) > 0:
            issues.append("C5_ma_count==0")
        parent = r.get("P")
        if not parent:
            issues.append("no parent P")
        if r.get("commit_kind") != "SINGLE_PARENT":
            issues.append(f"commit_kind={r.get('commit_kind')}")
        if issues:
            raise Blocked("eligibility R1/R3 failed", ";".join(issues))
        # recompute C5 hash from the verified source
        got = self._recompute_c5_hash(task_sha)
        if got != r["C5_test_paths_hash"]:
            raise FrozenInputDrift(
                "C5_test_paths_hash recompute drift",
                f"got={got} frozen={r['C5_test_paths_hash']}")
        # R2 (fail-closed): every field must be present, parseable and ordered.
        body_sha = r.get("issue_body_as_of_work_sha256")
        issue = r.get("ISSUE_NUMBER")
        t_work = r.get("t_work")
        created = r.get("issue_createdAt")
        if not body_sha:
            raise Blocked("eligibility R2 failed",
                          "issue_body_as_of_work_sha256 missing")
        if issue is None:
            raise Blocked("eligibility R2 failed", "ISSUE_NUMBER missing")
        if not created or not t_work:
            raise Blocked("eligibility R2 failed",
                          f"chronology incomplete: createdAt={created!r} "
                          f"t_work={t_work!r}")
        from datetime import datetime

        def _tzaware(v):
            v = v.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(v)
            except ValueError:
                return None

        c, t = _tzaware(created), _tzaware(t_work)
        if c is None or t is None:
            raise Blocked("eligibility R2 failed",
                          f"chronology unparsable: createdAt={created!r} "
                          f"t_work={t_work!r}")
        if not (c < t):
            raise LeakageDetected(
                "chronology violated (issue_createdAt >= t_work)", task_sha)
        # protected body bytes re-verified equal
        cache = os.path.join(self.protected_cache_dir,
                             f"issue_{issue}_body_at_t_work.bin")
        if not os.path.exists(cache):
            raise Blocked("protected body cache missing", cache)
        if sha256_file(cache) != body_sha.upper():
            raise FrozenInputDrift("protected body bytes drift", task_sha)
        return r, parent

    # ------------------------------------------------------------------ env
    def _env_snapshot(self, parent):
        """Manifest snapshot at P only (legacy/compat form). The runner uses
        _resolve_environment (which binds the ACTUAL interpreter, wheelhouse
        and image digest) for the identity."""
        import subprocess
        manifests = {}
        for name in MANIFEST_NAMES:
            out = subprocess.run(
                ["git", "rev-parse", f"{parent}:{name}"],
                capture_output=True, text=True, env={"GIT_DIR": self.git_dir},
                check=False)
            oid = out.stdout.strip() if out.returncode == 0 else ""
            if not oid:
                continue
            data = subprocess.run(["git", "cat-file", "blob", oid],
                                  capture_output=True,
                                  env={"GIT_DIR": self.git_dir}, check=False).stdout
            manifests[name] = {"content_sha256": hashlib.sha256(data).hexdigest().upper(),
                               "bytes": len(data)}
        return EnvSnapshot(manifests)

    def _verify_environment(self, parent, plan):
        """F4: bind the ACTUAL resolved runtime to the frozen plan pins.
        - docker: resolve the immutable local image digest; digest drift or an
          unresolvable mutable tag is refused (never ':latest' identity); the
          interpreter is probed INSIDE the pinned image (cached); wheelhouse
          identity binds the declared dir.
        - drift of any FROZEN pin is GLOBAL STOP ENV_DRIFT; unavailability is
          BLOCKED (infra)."""
        manifests = self._env_snapshot(parent).manifests
        interp = (plan.interpreter or "python").strip()
        if plan.isolation_backend != "docker":
            # harness: the ACTUAL interpreter of the run is the parent python
            import sys as _sys
            ver = _sys.version.split()[0]
            resolved = f"{interp}@{ver}"
            if plan.interpreter_version and \
                    plan.interpreter_version != ver:
                raise EnvDrift(
                    "interpreter version drift",
                    f"plan={plan.interpreter_version} resolved={ver}")
            return EnvSnapshot(manifests, interpreter=resolved,
                               wheelhouse_id=wheelhouse_dir_id(plan.wheelhouse)
                               if plan.wheelhouse else "NONE",
                               image_ref="NONE",
                               extra={"backend": "python-process"}), resolved, None

        # ---- docker: pin the runtime identity ---------------------------
        image = plan.image
        digest = plan.image_digest
        if not image or not digest:
            raise Blocked("docker_image_not_pinned",
                          "plan.image + plan.image_digest required")
        resolved_digest = _iso.resolve_image_digest(image)
        if resolved_digest is None:
            raise Blocked(
                "docker_image_not_pinned",
                f"image ref {image!r} not resolvable locally "
                "(no pull policy; immutable digest required)")
        if resolved_digest.upper() != digest.upper():
            raise EnvDrift(
                "image digest drift",
                f"image={image} resolved={resolved_digest} frozen={digest}")
        interp_ver = _iso.probe_interpreter_version(
            _iso.immutable_ref(resolved_digest), interp)
        if interp_ver is None:
            raise Blocked("interpreter_probe_failed",
                          f"could not resolve {interp!r} inside the image")
        if plan.interpreter_version and plan.interpreter_version != interp_ver:
            raise EnvDrift("interpreter version drift",
                           f"plan={plan.interpreter_version} resolved={interp_ver}")
        wheel_id = wheelhouse_dir_id(plan.wheelhouse) if plan.wheelhouse else "NONE"
        if plan.wheelhouse_id and wheel_id != plan.wheelhouse_id:
            raise EnvDrift("wheelhouse identity drift",
                           f"plan={plan.wheelhouse_id} resolved={wheel_id}")
        env = EnvSnapshot(manifests,
                          interpreter=f"{interp}@{interp_ver}",
                          wheelhouse_id=wheel_id, image_ref=resolved_digest,
                          extra={"backend": "docker",
                                 "image_digest": resolved_digest,
                                 "interpreter_version": interp_ver})
        return env, f"{interp}@{interp_ver}", resolved_digest

    def _resolve_environment(self, parent, plan):
        env, interp, digest = self._verify_environment(parent, plan)
        return env

    # ------------------------------------------------------------------ task
    def run_task(self, task_sha, command=None, preflight_only=False,
                 test_paths=None, t_only_paths=None, dry_run=False,
                 oracle_mode="POSITIVE_REFERENCE", plan=None, floor_gb=20.0) -> dict:
        """Per-task runner. Blocked conditions return a BLOCKED receipt result;
        global STOP classes propagate to halt the batch.

        `plan` (TaskPlan) is the frozen specification (command, test paths,
        oracle mode, isolation backend, resource caps). When omitted (unit
        harness) a python-process harness plan is derived from the legacy
        command/test_paths arguments and `harness=True`.
        """
        self._check_stop()
        binding = self._authorize(task_sha)
        if plan is None:
            if isinstance(binding, dict):
                raise C6Stop("PLAN_UNBOUND",
                             "authorization is task-bound; a plan is required")
            plan = self._harness_plan(task_sha, command, test_paths,
                                      t_only_paths, oracle_mode)
        else:
            if not isinstance(plan, TaskPlan):
                raise TaskPlanError("plan must be a TaskPlan")
            if plan.task != task_sha:
                raise C6Stop("PLAN_TASK_MISMATCH",
                             f"plan.task={plan.task} requested={task_sha}")
            if isinstance(binding, dict):
                self._verify_plan_bound(plan, binding, task_sha)
            else:
                raise C6Stop("PLAN_UNBOUND",
                             "authorization has no task binding; a plan cannot run")
        try:
            return self._run_task_inner(task_sha, preflight_only, dry_run, plan)
        except Blocked as b:
            payload = {
                "runner_version": RUNNER_VERSION,
                "utc": None,
                "task": {"T": task_sha},
                "verdict": Verdict.BLOCKED.value,
                "blocked_classification": b.classification,
                "blocked_detail": b.detail,
                "preflight_only": preflight_only,
                "inputs_verified": self.inputs_verified,
            }
            ws_dir = os.path.join(self.out_root, task_sha[:12])
            os.makedirs(ws_dir, exist_ok=True)
            rp = os.path.join(ws_dir, "receipt_blocked.json")
            write_receipt(rp, payload)
            return {"verdict": Verdict.BLOCKED, "receipt_path": rp,
                    "workspace": ws_dir, "payload": payload}

    def _harness_plan(self, task_sha, command, test_paths, t_only_paths,
                      oracle_mode):
        """Synthetic-harness plan (no OS enforcement, never claim otherwise).
        Used only when unit tests drive run_task without an operator plan.
        Resource ceilings for harness runs come from the runner's limits."""
        res = {"timeout_s": self.limits.timeout_s,
               "ram_mb": self.limits.ram_mb, "disk_mb": self.limits.disk_mb}
        if command is None:
            return TaskPlan(task_sha, ["true"], test_paths or [],
                            t_only_paths or [], oracle_mode=oracle_mode,
                            isolation_backend="python-process", harness=True,
                            image=None, resources=res)
        return TaskPlan(task_sha, command, test_paths or [], t_only_paths or [],
                        oracle_mode=oracle_mode,
                        isolation_backend="python-process", harness=True,
                        image=None, resources=res)

    def _verify_plan_bound(self, plan, binding, task_sha):
        """The operator-frozen per-task binding must match the CLI plan bytes
        exactly (canonical SHA-256). Any mismatch is GLOBAL STOP."""
        bound = binding.get("plan_sha256")
        if not bound:
            raise C6Stop("PLAN_UNBOUND", f"binding for {task_sha} has no plan_sha256")
        got = plan.canonical_sha256()
        if got.upper() != str(bound).upper():
            raise C6Stop("PLAN_MISMATCHED",
                         f"plan sha mismatch: file={got} bound={bound}")

    def _run_task_inner(self, task_sha, preflight_only, dry_run, plan):
        # GLOBAL budget floor before ANY experiment (every path)
        self.check_budget(_Budget(plan.resources.get("global_floor_gb", 20.0)))
        r, parent = self._check_eligibility(task_sha)
        test_paths = list(plan.test_paths)
        if not test_paths:
            raise Blocked("test_paths empty in task plan", task_sha)
        t_only_paths = list(plan.t_only_paths)
        oracle_mode = plan.oracle_mode

        ws = IsolatedWorkspace(self.out_root, task_sha)
        materialized = ws.materialize_parent(self.git_dir, parent)
        # FULL M/A contract bytes AT T are quarantined under oracle/ (never src)
        contract_paths = sorted(set(list(test_paths) + list(t_only_paths)))
        contract_files = ws.materialize_contract_files(
            self.git_dir, task_sha, contract_paths)
        oracle_files = [(p, o) for (p, o) in contract_files if p in t_only_paths]
        existing_at_p = sorted(
            p for p in contract_paths
            if os.path.exists(os.path.join(ws.src, p)))

        # 5-field identity over the FULL M/A contract
        scope_hash = tree_scope_sha(self.git_dir, parent)
        ref_patch_hash = reference_patch_sha(self.git_dir, parent, task_sha,
                                             contract_paths)
        t_blobs = []
        import subprocess
        for p in contract_paths:
            oid = subprocess.run(
                ["git", "rev-parse", f"{task_sha}:{p}"],
                capture_output=True, text=True, env={"GIT_DIR": self.git_dir},
                check=False).stdout.strip()
            t_blobs.append((p, oid))
        contract_hash = test_contract_sha(t_blobs)
        env = self._resolve_environment(parent, plan)   # F4: bound runtime
        env_id = env.environment_id()
        ident = five_field(task_sha, scope_hash, ref_patch_hash,
                           contract_hash, env_id)

        # isolation: resolve an OS-level backend that satisfies the plan
        backend = _iso.resolve_backend(plan)
        if plan.isolation_backend == "python-process" and not plan.harness:
            raise Blocked("no_os_isolation",
                          "harness backend is not OS-isolated; refuse to run")
        if not plan.harness and backend.backend == "python-process":
            raise Blocked("no_os_isolation",
                          "no OS-level isolation backend satisfies the plan")
        limits = ResourceLimits(
            timeout_s=float(plan.resources["timeout_s"]),
            ram_mb=float(plan.resources["ram_mb"]),
            disk_mb=float(plan.resources["disk_mb"]))

        run = None
        exec_ok = (not preflight_only) and plan.command is not None
        oracle_report = None     # machine-readable oracle evidence (junit-xml)
        reference = None
        input_junit = None
        if exec_ok and not dry_run:
            # INPUT run (prospective input): P tree + P-available tests only.
            # T-only tokens are dropped; this run NEVER produces PASS by itself.
            input_cmd = expand_contract_in_command(
                plan.command, contract_paths, subset=existing_at_p)
            run = run_limited(input_cmd, materialized, limits, ws.logs,
                              offline_gate=True, backend=backend,
                              scratch_dir=ws.scratch, plan=plan)
            stdout_txt = read_log(run.stdout_path)
            if run.junit_path is not None:
                input_junit = parse_junit_report(
                    run.junit_path, stdout_txt, run.exit_code, existing_at_p)
            run.assertions_ok = (input_junit.assertions_ok
                                 if (input_junit is not None
                                     and input_junit.valid) else None)
            if (input_junit is None or not input_junit.valid
                    or input_junit.ran <= 0):
                run.vacuous_oracle = True
                run.blocked_reason = "vacuous_oracle"

        if (exec_ok and not dry_run and oracle_mode != "NONE"
                and run is not None
                and not (run.timeout or run.resource_overflow
                         or run.blocked_reason)):
            # Evaluation-only reference roles (issue 2), EACH in a SEPARATE
            # evaluator directory/container:
            #   F2P negative baseline  = P code + T test bytes (eval_f2p)
            #   P2P positive reference = T code + T test bytes (eval_work)
            # The frozen plan is passed through (F1); infra failure of either
            # blocks the task (F2). T code / T tests never enter src/.
            negative_baseline = None      # F2P (P code + T tests)
            reference = None              # P2P (T code + T tests)
            oracle_evaluation = None
            oracle_report = None
            f2p_outcome = None
            try:
                from .evaluator import evaluate_t_only
                ws.materialize_reference_tree(self.git_dir, parent,
                                              contract_paths, dst=ws.eval_f2p)
                negative_baseline = evaluate_t_only(
                    ws, t_only_paths, plan, backend, git_dir=self.git_dir,
                    parent=parent, code_rev=parent, role="f2p",
                    dst=ws.eval_f2p)
                ws.materialize_reference_tree(self.git_dir, task_sha,
                                              contract_paths, dst=ws.eval_work)
                reference = evaluate_t_only(
                    ws, t_only_paths, plan, backend, git_dir=self.git_dir,
                    parent=parent, code_rev=task_sha, role="p2p",
                    dst=ws.eval_work)
                if reference is not None \
                        and reference.junit_report is not None:
                    oracle_report = reference.junit_report
                oracle_evaluation = reference.evidence \
                    if reference is not None else None
            except Blocked:
                raise
            except Exception as e:  # noqa: BLE001
                oracle_evaluation = oracle_evaluation or {
                    "evaluator_error": f"{type(e).__name__}: {e}"}
        else:
            negative_baseline = None
            reference = None
            oracle_evaluation = None
            oracle_report = None
            f2p_outcome = None

        # Verdict: infra failures first, then the reference ROLE semantics
        # (issue 2). The candidate verdict NEVER rests on the P/P diagnostic;
        # an EXPECTED F2P failure is the negative-baseline outcome (recorded),
        # never a broken environment and never a PASS source.
        verdict = Verdict.BLOCKED
        if not exec_ok or run is None:
            verdict = Verdict.BLOCKED   # preflight / missing command
        elif run.timeout or run.resource_overflow or run.blocked_reason:
            verdict = Verdict.BLOCKED   # infra: timeout/overflow/vacuous input
        elif oracle_mode == "NONE":
            verdict = Verdict.BLOCKED   # diagnostic-only: no reference contract
        else:
            p2p_ok = (reference is not None and reference.error is None
                      and reference.junit_report is not None
                      and reference.junit_report.valid)
            f2p_ok = (negative_baseline is not None
                      and negative_baseline.error is None
                      and negative_baseline.junit_report is not None
                      and negative_baseline.junit_report.valid)
            if not p2p_ok or not f2p_ok:
                verdict = Verdict.BLOCKED  # either control unestablished (F2)
            else:
                fr = negative_baseline.junit_report
                if fr.failures > 0 or fr.errors > 0:
                    f2p_outcome = "expected_failure"
                else:
                    f2p_outcome = "unexpected_green"
                if oracle_mode == "NEG_TESTS_EXPECTED_FAIL":
                    verdict = decide_from_reference(negative_baseline.run, fr,
                                                    "NEG_TESTS_EXPECTED_FAIL")
                else:
                    verdict = decide_from_reference(reference.run,
                                                    reference.junit_report,
                                                    "POSITIVE_REFERENCE")
        f2p_evidence = None
        if negative_baseline is not None:
            f2p_evidence = dict(negative_baseline.evidence)
            f2p_evidence["role"] = "f2p"
            f2p_evidence["outcome"] = f2p_outcome

        payload = {
            "runner_version": RUNNER_VERSION,
            "utc": None,
            "task": {
                "T": task_sha,
                "P": parent,
                "issue": r.get("ISSUE_NUMBER"),
                "pr": r.get("PR_NUMBER"),
                "year": r.get("year"),
            },
            "identity": ident,
            "verdict": verdict.value,
            "preflight_only": preflight_only,
            "scope": "C6",
            "task_plan": {
                "schema": "c6-task-plan-v1",
                "sha256": plan.canonical_sha256(),
                "command": plan.command,
                "oracle_mode": plan.oracle_mode,
                "isolation_backend": plan.isolation_backend,
                "harness": plan.harness,
                "image": plan.image,
                "image_digest": plan.image_digest,
                "interpreter": plan.interpreter,
                "interpreter_version": plan.interpreter_version,
                "wheelhouse": plan.wheelhouse,
                "wheelhouse_id": plan.wheelhouse_id,
                "junitxml_path": plan.junitxml_path,
            },
            "environment": {
                "interpreter": env.interpreter,
                "wheelhouse_id": env.wheelhouse_id,
                "image_ref": env.image_ref,
                "extra": env.extra,
            },
            "budget_preflight": {
                "floor_gb": plan.resources.get("global_floor_gb"),
                "checked": True,
            },
            "isolation": backend.as_dict() if backend else None,
            "oracle_quarantine": {
                "t_only_files": [{"path": p, "blob": o} for p, o in oracle_files],
                "contract_files": [{"path": p, "blob": o}
                                    for p, o in contract_files],
            },
            "reference_definition": {
                "parent": parent,
                "contract": contract_paths,
                "principle": "evaluation-only reference roles; the candidate "
                             "verdict never rests on P tests alone; an "
                             "expected F2P failure is the negative-baseline "
                             "outcome, never a broken environment",
                "roles": {
                    "diagnostic": {
                        "content": "P code + P tests",
                        "tree": ws.src,
                        "scope": "starting-environment diagnostic, evidence "
                                 "only; never a PASS source"},
                    "f2p": {
                        "content": "P code + T tests",
                        "tree": ws.eval_f2p,
                        "scope": "negative baseline F2P, evaluation-only"},
                    "p2p": {
                        "content": "T code + T tests",
                        "tree": ws.eval_work,
                        "scope": "positive reference P2P, evaluation-only"},
                },
                "generated_code_e2e": "not implemented (separate future gate)",
                "evaluator_separate": True,
            },
            "oracle_evaluation": oracle_evaluation,
            "negative_baseline_f2p": f2p_evidence,
            "oracle_report": oracle_report.as_dict() if oracle_report else None,
            "input_evidence": (input_junit.as_dict() if input_junit else None),
            "eligibility": {
                "C4": r.get("C4"), "C5": r.get("C5"),
                "C5_test_paths_hash": r.get("C5_test_paths_hash"),
                "recomputed_c5_hash_matches": True,
                "body_bytes_verified": True,
                "chronology_ok": True,
            },
            "execution": None,
            "inputs_verified": self.inputs_verified,
            "authorization": {
                "freeze_sha256": self.freeze.protocol_sha256,
                "authorization_sha256": self.auth.authorization_sha256,
                "bound": True,
            },
        }
        if run is not None:
            payload["execution"] = {
                "exit_code": run.exit_code,
                "wall_s": round(run.wall_s, 3) if run.wall_s is not None else None,
                "peak_rss_mb": run.peak_rss_mb,
                "disk_mb_before": round(run.disk_mb_before, 3) if run.disk_mb_before is not None else None,
                "disk_mb_after": round(run.disk_mb_after, 3) if run.disk_mb_after is not None else None,
                "timeout": run.timeout,
                "resource_overflow": run.resource_overflow,
                "blocked_reason": run.blocked_reason,
                "network_enforced": run.network_enforced,
                "os_isolation_active": run.os_isolation_active,
                "memory_enforced": run.memory_enforced,
                "python_gate_active": run.python_gate_active,
                "backend": run.backend,
                "assertions_ok": run.assertions_ok,
                "vacuous_oracle": run.vacuous_oracle,
                "effective_command": run.effective_command,
                "junit_path": run.junit_path,
                "junit_sha256": run.junit_sha256,
                "cleanup": run.cleanup_evidence,
                "stdout_sha256": _log_sha(run.stdout_path),
                "stderr_sha256": _log_sha(run.stderr_path),
                "stdout_tail": read_log(run.stdout_path)[-4000:],
                "stderr_tail": read_log(run.stderr_path)[-4000:],
            }
        result = {
            "receipt_path": os.path.join(ws.root, "receipt.json"),
            "workspace": ws.root,
            "payload": payload,
            "verdict": verdict,
        }
        write_receipt(result["receipt_path"], payload)
        return result

    # ------------------------------------------------------------- batch/budget
    def check_budget(self, budget):
        """GLOBAL disk floor, verified IMMEDIATELY before every experiment."""
        import shutil
        os.makedirs(self.out_root, exist_ok=True)
        t, u, f = shutil.disk_usage(self.out_root)
        free_gb = f / (1024 ** 3)
        if free_gb < budget.min_free_gb:
            raise BudgetExceeded("free disk below budget",
                                 f"free={free_gb:.1f}GiB "
                                 f"min={budget.min_free_gb}GiB")


class _Budget:
    def __init__(self, min_free_gb=20.0):
        self.min_free_gb = float(min_free_gb)


def _is_test_path(path):
    p = path.encode("utf-8", "surrogateescape")
    segs = p.split(b"/")
    for s in segs:
        if s in (b"tests", b"test"):
            return True
    base = segs[-1]
    if base.endswith(b".py"):
        if base.startswith(b"test_") or base.endswith(b"_test.py") or base == b"conftest.py":
            return True
    return False


def _log_sha(path):
    if not path or not os.path.exists(path):
        return None
    return sha256_file(path)