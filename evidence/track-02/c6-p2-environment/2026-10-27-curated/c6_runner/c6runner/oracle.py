# -*- coding: utf-8 -*-
"""Oracle validation: a behavioral oracle requires an actual test run.

A *valid* oracle is only established when the executed test command produced
a machine-readable junit-xml report containing AT LEAST ONE genuinely
executed, non-skipped test item (skipped, xfail, xpass-only and
zero-execution reports are tracked explicitly and fail closed). Anything else
(trivial success, "no tests ran", no report, zero collected) is vacuous and
can never yield PASS.
"""
import os
import re

SUMMARY_RE = re.compile(
    r"(?P<ran>\d+)\s+passed"
    r"(?:,\s*(?P<skipped>\d+)\s+skipped)?"
    r"(?:,\s*(?P<xfailed>\d+)\s+xfailed)?"
    r"(?:,\s*(?P<failed>\d+)\s+failed)?"
    r"(?:,\s*(?P<errors>\d+)\s+error[s]?)?"
    r"(?:,\s*(?P<xpassed>\d+)\s+xpassed)?",
    re.I)
# failure-only / error-only summaries ("1 failed in 0.4s", "2 errors in 1s")
FAIL_ONLY_RE = re.compile(r"(?P<failed>\d+)\s+failed", re.I)
ERROR_ONLY_RE = re.compile(r"(?P<errors>\d+)\s+error[s]?", re.I)

NO_TESTS_RAN_RE = re.compile(r"no tests ran", re.I)
COLLECTED_RE = re.compile(r"collected\s+(?P<n>\d+)\s+items?", re.I)

SUMMARY_LINE_RE = re.compile(r"in \d+\.\d+s", re.I)
TOKEN_RE = re.compile(r"(\d+)\s+(passed|failed|error|errors|skipped|xfailed|xpassed)", re.I)


def _summary_counts(text):
    """(passed, failed, errors, skipped, xfailed, xpassed) parsed from the
    pytest terminal summary token line, regardless of the order pytest prints
    the clauses (e.g. '1 failed, 1 passed in 0.18s'). None when no summary
    line is present."""
    for line in (text or "").splitlines():
        if not SUMMARY_LINE_RE.search(line):
            continue
        counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0,
                  "xfailed": 0, "xpassed": 0}
        for m in TOKEN_RE.finditer(line):
            key = m.group(2).lower()
            if key.startswith("error"):
                key = "errors"
            counts[key] = int(m.group(1))
        return (counts["passed"], counts["failed"], counts["errors"],
                counts["skipped"], counts["xfailed"], counts["xpassed"])
    return None

# ------------------------------------------------------------------------------
# Machine-readable oracle evidence: pytest --junitxml
#
# A behavioral oracle is only established by a real pytest process writing a
# junit-xml report inside the sandbox. The report must exist, be well-formed,
# contain >=1 executed testcase, every testcase must trace to the frozen test
# contract, the junit counts must agree with pytest's own terminal summary in
# the SAME process stdout, and failures/errors must agree with the exit status.
# ------------------------------------------------------------------------------


def is_pytest_command(command) -> bool:
    argv = [str(a) for a in command]
    if not argv:
        return False
    if os.path.basename(argv[0]).startswith("pytest"):
        return True
    py_tail = os.path.basename(argv[0]).lower()
    if py_tail in ("python", "python.exe", "python3", "python3.exe", "py") \
            and len(argv) >= 3 and argv[1] == "-m" and argv[2] == "pytest":
        return True
    if "pytest" in argv:
        return True
    return False


def inject_junitxml(command, path):
    """Return argv with `--junitxml=<path>` inserted after the pytest token.
    Non-pytest commands are returned unchanged (they can never produce a
    behavioral oracle)."""
    argv = [str(a) for a in command]
    if not is_pytest_command(argv):
        return argv
    if any(a.startswith("--junitxml") for a in argv):
        return argv
    idx = None
    if os.path.basename(argv[0]).startswith("pytest"):
        idx = 1
    else:
        for i in range(len(argv) - 1):
            if argv[i] == "-m" and argv[i + 1] == "pytest":
                idx = i + 2
                break
    if idx is None:
        return argv
    return argv[:idx] + [f"--junitxml={path}"] + argv[idx:]


def _contract_variants(path):
    """All textual forms of a repo-relative test path that pytest may emit in
    classname/nodeid: file path, stem, dotted module, dotted stem tail."""
    p = path.replace("\\", "/")
    stem = p[:-3] if p.endswith(".py") else p
    dotted = stem.replace("/", ".")
    tail = dotted.rsplit(".", 1)[-1]
    return {p, stem, dotted, tail}


def _testcase_maps_to_contract(classname, name, variants):
    if not classname:
        return False
    for chunk in str(classname).split("::")[0].split("."):
        if chunk in variants:
            return True
    return str(classname).split("::")[0] in variants


class JunitReport:
    """Machine-readable oracle evidence derived from the junit-xml report that
    the executed pytest process wrote inside the sandbox.

    Testcase classification (real pytest 8.3.4 junit encoding):
      - a `testcase` WITHOUT a `<skipped/>` child genuinely EXECUTED;
      - pytest.skip AND pytest.xfail both render as `<skipped/>` children
        (xfail carries type="pytest.xfail") -> NOT genuinely executed;
      - pytest XPASS renders as a PLAIN passed testcase (no marker) so the
        xpassed count must come from the pytest terminal summary.
    `ran` therefore counts genuine, non-skipped executions only and a
    report is VALID only when at least one genuinely executed, non-skipped
    (and not all-xpass) test exists (issue 1: all-skipped / all-xfail /
    all-xpass / zero-execution must fail closed and can never yield PASS).
    """

    def __init__(self, junit_path=None, sha256=None, tests=0, failures=0,
                 errors=0, skipped=0, executed=0, xfailed=0, xpassed=0,
                 testcases=None, vacuous=True, reason="no report",
                 identity_ok=False, stdout_consistent=False,
                 exit_parity=False, exit_code=None):
        self.junit_path = junit_path
        self.sha256 = sha256
        self.tests = int(tests)
        self.failures = int(failures)
        self.errors = int(errors)
        self.skipped = int(skipped)
        self.executed = int(executed)   # testcases WITHOUT a <skipped> child
        self.xfailed = int(xfailed)     # <skipped type="pytest.xfail"> entries
        self.xpassed = int(xpassed)     # from the same-process terminal summary
        self.testcases = list(testcases or [])
        self.vacuous = vacuous
        self.reason = reason
        self.identity_ok = identity_ok
        self.stdout_consistent = stdout_consistent
        self.exit_parity = exit_parity
        self.exit_code = exit_code

    @property
    def ran(self):
        """Genuinely EXECUTED, non-skipped testcases only."""
        return self.executed

    @property
    def valid(self):
        """A usable oracle requires (a) the machine/identity/parity gates and
        (b) AT LEAST ONE genuinely executed non-skipped test; a report whose
        every executed test was an XPASS (nothing genuinely passed as
        expected) is also vacuous. Skipped/xfail/zero-execution reports are
        never valid."""
        if self.vacuous or not self.identity_ok \
                or not self.stdout_consistent or not self.exit_parity:
            return False
        if self.executed < 1:
            return False
        if self.xpassed and self.xpassed >= self.executed:
            return False       # every executed test was an xpass: fail closed
        return True

    @property
    def assertions_ok(self):
        if not self.valid:
            return None
        return self.failures == 0 and self.errors == 0

    def as_dict(self):
        return {"kind": "junit-xml", "path": self.junit_path,
                "sha256": self.sha256,
                "tests": self.tests, "failures": self.failures,
                "errors": self.errors, "skipped": self.skipped,
                "executed": self.executed, "xfailed": self.xfailed,
                "xpassed": self.xpassed,
                "ran": self.ran,
                "vacuous": self.vacuous, "reason": self.reason,
                "identity_ok": self.identity_ok,
                "stdout_consistent": self.stdout_consistent,
                "exit_parity": self.exit_parity,
                "exit_code": self.exit_code,
                "testcases": [{"classname": c, "name": n}
                               for c, n in self.testcases],
                "valid": self.valid, "assertions_ok": self.assertions_ok}


def parse_junit_report(junit_path, stdout_text, exit_code, contract_paths):
    """Bind machine-readable pytest evidence to the frozen contract.

    Returns a JunitReport. A report is valid ONLY when the junit file exists
    (written by the executed pytest inside the sandbox), is well-formed, has
    >=1 genuinely executed, non-skipped testcase (skipped / xfail / xpass-only /
    zero-execution reports fail closed and can NEVER yield PASS), every
    testcase traces to the frozen M/A contract, the junit counts agree with the
    same-process pytest terminal summary and the failures/errors agree with the
    exit status."""
    import xml.etree.ElementTree as ET
    from .hashes import sha256_file

    if not junit_path or not os.path.exists(junit_path):
        return JunitReport(junit_path=junit_path, vacuous=True,
                           reason="missing", exit_code=exit_code)
    try:
        tree = ET.parse(junit_path)
    except ET.ParseError:
        return JunitReport(junit_path=junit_path, vacuous=True,
                           reason="malformed", exit_code=exit_code)
    tests = failures = errors = skipped = 0
    testcases = []
    for suite in tree.iter("testsuite"):
        tests += int(suite.attrib.get("tests", 0))
        failures += int(suite.attrib.get("failures", 0))
        errors += int(suite.attrib.get("errors", 0))
        skipped += int(suite.attrib.get("skipped", 0))
    executed = 0      # testcases WITHOUT a <skipped> child (genuine runs)
    xfailed = 0       # <skipped type="pytest.xfail"> entries (explicit)
    for tc in tree.iter("testcase"):
        testcases.append((tc.attrib.get("classname") or "",
                          tc.attrib.get("name") or ""))
        skip_el = next((c for c in tc if c.tag == "skipped"), None)
        if skip_el is None:
            executed += 1
        elif skip_el.attrib.get("type") == "pytest.xfail":
            xfailed += 1
    hexsha = sha256_file(junit_path)

    variants = set()
    for c in contract_paths:
        variants |= _contract_variants(c)
    ran = executed
    identity_ok = bool(ran) and all(
        _testcase_maps_to_contract(cn, nm, variants) for cn, nm in testcases)

    counts = _summary_counts(stdout_text or "")
    stdout_consistent = False
    xpassed = 0
    if counts is not None:
        passed, failed, errors_s, skipped_s, xfailed_s, xpassed_s = counts
        xpassed = xpassed_s
        total = (passed + failed + errors_s + skipped_s
                 + xfailed_s + xpassed_s)
        stdout_consistent = (total == tests and failed == failures
                             and errors_s == errors)
    exit_parity = ((failures + errors) == 0) == (exit_code == 0)

    # Fail-closed classification (issue 1): only a genuinely executed,
    # non-skipped test can establish the oracle. Skipped / xfail / xpass /
    # zero-execution are tracked explicitly and can never be valid alone.
    vacuous, reason = (tests == 0 or executed == 0), "no_tests"
    if tests == 0:
        reason = "no_tests"
    elif executed == 0:
        if xfailed and xfailed == tests:
            reason = "only_xfail"
        elif skipped > 0:
            reason = "all_skipped"
        else:
            reason = "no_tests"
    elif executed > 0 and xpassed and xpassed >= executed:
        vacuous, reason = True, "only_xpass"
    else:
        reason = "okay"
    return JunitReport(junit_path=junit_path, sha256=hexsha, tests=tests,
                       failures=failures, errors=errors, skipped=skipped,
                       executed=executed, xfailed=xfailed, xpassed=xpassed,
                       testcases=testcases, vacuous=vacuous, reason=reason,
                       identity_ok=identity_ok,
                       stdout_consistent=stdout_consistent,
                       exit_parity=exit_parity, exit_code=exit_code)


class OracleReport:
    def __init__(self, collected, ran, failed, errors,
                 skipped=0, xfailed=0, xpassed=0, vacuous=False):
        self.collected = collected
        self.ran = ran
        self.failed = failed
        self.errors = errors
        self.skipped = skipped
        self.xfailed = xfailed
        self.xpassed = xpassed
        self.vacuous = vacuous  # no report / no tests executed -> invalid oracle

    @property
    def valid(self):
        """A usable oracle: tests actually ran and none infra-failed to run."""
        if self.vacuous or self.ran <= 0:
            return False
        return True

    @property
    def assertions_ok(self):
        """Semantic green: everything that ran passed and nothing errored."""
        if not self.valid:
            return None
        return self.failed == 0 and self.errors == 0

    def as_dict(self):
        return {"collected": self.collected, "ran": self.ran,
                "failed": self.failed, "errors": self.errors,
                "skipped": self.skipped, "xfailed": self.xfailed,
                "xpassed": self.xpassed, "vacuous": self.vacuous,
                "valid": self.valid, "assertions_ok": self.assertions_ok}


def parse_pytest_summary(text, exit_code=None):
    """Parse the pytest terminal summary from combined stdout.

    Returns an OracleReport (vacuous=True) when no summary can be found or when
    the run did not actually execute tests. `exit_code` is a hint only: a
    report-less process (trivial command) is always vacuous.
    """
    if not text:
        return OracleReport(0, 0, 0, 0, vacuous=True)
    m = SUMMARY_RE.search(text)
    if not m and FAIL_ONLY_RE.search(text):
        failed = int(FAIL_ONLY_RE.search(text).group("failed") or 0)
        errors = int(ERROR_ONLY_RE.search(text).group("errors")
                     if ERROR_ONLY_RE.search(text) else 0)
        # "1 failed" / "2 errors" means those tests RAN and failed
        ran = failed + errors
        return OracleReport(ran, ran, failed, errors)
    if not m and ERROR_ONLY_RE.search(text):
        errors = int(ERROR_ONLY_RE.search(text).group("errors") or 0)
        return OracleReport(errors, 0, 0, errors)
    if not m:
        if NO_TESTS_RAN_RE.search(text):
            return OracleReport(0, 0, 0, 0, vacuous=True)
        return OracleReport(0, 0, 0, 0, vacuous=True)
    ran = int(m.group("ran"))
    failed = int(m.group("failed") or 0)
    errors = int(m.group("errors") or 0)
    skipped = int(m.group("skipped") or 0)
    xfailed = int(m.group("xfailed") or 0)
    xpassed = int(m.group("xpassed") or 0)
    collected = ran + failed + errors + skipped + xfailed + xpassed
    cm = COLLECTED_RE.search(text)
    if cm:
        collected = int(cm.group("n"))
    return OracleReport(collected, ran, failed, errors,
                        skipped=skipped, xfailed=xfailed, xpassed=xpassed)