"""WP-2 Mission-10A environment test-dependency audit - shared logic (ZERO API).

Deterministic, zero-LLM classification of error-bearing oracle evidence from
C2/C4 (Linux V2) and Mission-09 P2P-U ENG runs, plus the preregistered
materiality rule, mechanical test-category definitions, and plugin-state layer
model used by the optional ENG-only scratch probe.

This module performs no model/API calls and never mutates frozen artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Error taxonomy (Mission-10A section 6)
# ---------------------------------------------------------------------------
TAXONOMY = (
    "MISSING_FIXTURE",
    "MODULE_NOT_FOUND",
    "IMPORT_ERROR",
    "DB_ERROR",
    "PLUGIN_LOAD_ERROR",
    "COLLECTION_OTHER",
    "SETUP_OTHER",
    "EXECUTION_OTHER",
    "OTHER",
)

PHASE_COLLECTION = "collection"
PHASE_SETUP = "setup"
PHASE_CALL = "call"
PHASE_TEARDOWN = "teardown"
PHASE_IMPORT = "import/bootstrap"
PHASE_UNKNOWN = "unknown"

_RE_FIXTURE = re.compile(r"fixture '([^']+)' not found")
_RE_MODULE = re.compile(r"(?:ModuleNotFoundError|No module named)\s*['\"]?([A-Za-z_][\w.\-]*)['\"]?", re.I)
_RE_IMPORT = re.compile(r"ImportError:\s*(.+)$", re.I | re.M)
_RE_DB = re.compile(
    r"(OperationalError|ProgrammingError|psycopg|could not connect to server|"
    r"FATAL:\s+database|connection to server|django\.db\.utils\.|"
    r"DBError|database .* does not exist)",
    re.I,
)
_RE_PLUGIN = re.compile(
    r"(unknown error: pytest_plugins|pytest_plugins|plugin.*(?:not found|failed to load)|"
    r"Error loading plugin|cannot load plugin)",
    re.I,
)
_RE_COLLECTION = re.compile(
    r"(ERROR at collection|error collecting|collection error|collecting .* failed|"
    r"attribute .* is not a file|failed to collect|import file mismatch)",
    re.I,
)
_RE_SETUP = re.compile(
    r"(ERROR at setup|failed on setup|error during setup|setup error|SetupError|"
    r"ERROR at setup of|fixture .* not found)",
    re.I,
)
_RE_TEARDOWN = re.compile(r"(ERROR at teardown|failed at teardown|teardown error)", re.I)
_RE_IMPORT_PHASE = re.compile(
    r"(ImportError while loading|error in main|pytest_plugins|"
    r"During handling of the above exception)", re.I,
)

# Volatile path normalization: strip /workspace/<wt>/ prefix and temp dirs.
_RE_WORKSPACE = re.compile(r"/workspace/[A-Za-z0-9_\-]+/")
_RE_TMP = re.compile(r"/tmp/[A-Za-z0-9_\-\./]+")
_RE_ABS_PATH = re.compile(r"(/[A-Za-z0-9_\-]+)+(/[A-Za-z0-9_\-\.]+\.py)")


def detect_phase(full_text: str) -> str:
    """Detect the pytest phase from JUnit error/failure text (Mission-10A §6)."""
    if not full_text:
        return PHASE_UNKNOWN
    head = full_text[:4000]
    if _RE_COLLECTION.search(head):
        return PHASE_COLLECTION
    if _RE_SETUP.search(head):
        return PHASE_SETUP
    if _RE_TEARDOWN.search(head):
        return PHASE_TEARDOWN
    if _RE_IMPORT_PHASE.search(head):
        return PHASE_IMPORT
    return PHASE_CALL


def classify_error(full_text: str) -> tuple[str, str]:
    """Classify an error-bearing JUnit record into the deterministic taxonomy.

    Returns (taxonomy_label, detail). ``detail`` is the fixture/module name for
    the specific classes, else a normalized root-cause fragment.
    """
    text = full_text or ""
    head = text[:4000]
    m = _RE_FIXTURE.search(head)
    if m:
        return f"MISSING_FIXTURE:{m.group(1)}", m.group(1)
    m = _RE_MODULE.search(head)
    if m:
        return f"MODULE_NOT_FOUND:{m.group(1)}", m.group(1)
    m = _RE_IMPORT.search(head)
    if m:
        return f"IMPORT_ERROR:{normalize(m.group(1))[:120]}", normalize(m.group(1))[:120]
    if _RE_DB.search(head):
        return "DB_ERROR", normalize(first_useful_line(text))[:160]
    if _RE_PLUGIN.search(head):
        return "PLUGIN_LOAD_ERROR", normalize(first_useful_line(text))[:160]
    phase = detect_phase(text)
    if phase == PHASE_COLLECTION:
        return "COLLECTION_OTHER", normalize(first_useful_line(text))[:160]
    if phase == PHASE_SETUP:
        return "SETUP_OTHER", normalize(first_useful_line(text))[:160]
    if phase in (PHASE_CALL, PHASE_TEARDOWN):
        return "EXECUTION_OTHER", normalize(first_useful_line(text))[:160]
    return "OTHER", normalize(first_useful_line(text))[:160]


def first_useful_line(text: str) -> str:
    """First non-empty, non-punctuation line of the error text (root cause)."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith(("file ", ">", "request", "django_", "self", "return")):
            continue
        if line.startswith("Traceback"):
            continue
        return line
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def normalize(text: str) -> str:
    """Normalize volatile paths/temp IDs so identical root causes aggregate."""
    if not text:
        return ""
    out = _RE_WORKSPACE.sub("WS/", text)
    out = _RE_TMP.sub("TMP/", out)
    out = _RE_ABS_PATH.sub("PATH", out)
    out = re.sub(r"0x[0-9a-fA-F]+", "HEX", out)
    out = re.sub(r"\s+", " ", out)
    return out.strip()


# ---------------------------------------------------------------------------
# Fixture -> candidate package (Mission-10A section 9)
# ---------------------------------------------------------------------------
# Mechanical-only: a fixture/module maps to its well-known pytest plugin
# provider. Confidence is assigned from dependency-declaration evidence later;
# the mapping table itself is a deterministic lookup used for the hypothesis.
FIXTURE_TO_PACKAGE: dict[str, str] = {
    "count_queries": "pytest-django-queries",
    "mocker": "pytest-mock",
    "mock": "pytest-mock",
    "recording": "pytest-recording",
    "celery_worker": "pytest-celery",
    "celery_app": "pytest-celery",
    "asyncio": "pytest-asyncio",
    "memray": "pytest-memray",
}

PACKAGE_TO_ENTRYPOINT: dict[str, str] = {
    "pytest-mock": "pytest_mock",
    "pytest-django-queries": "pytest_django_queries",
    "pytest-recording": "pytest_recording",
    "pytest-celery": "pytest_celery",
    "pytest-asyncio": "pytest_asyncio",
    "pytest-memray": "pytest_memray",
}


@dataclass
class ErrorRecord:
    """One error-bearing node record extracted from oracle evidence."""

    dataset: str  # C2 | C4 | P2P_U_ENG
    task_id: str
    split: str
    era_key: str
    test_file: str
    node_id: str
    oracle_class: str
    side: str
    repetition: int
    evidence_path: str
    phase: str
    error_type: str
    taxonomy: str
    root_cause_line: str
    fixture_missing: str | None = None
    module_missing: str | None = None
    raw_error_text: str = ""

    def to_dict(self) -> dict:
        return {
            "dataset": self.dataset,
            "task_id": self.task_id,
            "split": self.split,
            "era_key": self.era_key,
            "test_file": self.test_file,
            "node_id": self.node_id,
            "oracle_class": self.oracle_class,
            "side": self.side,
            "repetition": self.repetition,
            "evidence_path": self.evidence_path,
            "phase": self.phase,
            "error_type": self.error_type,
            "taxonomy": self.taxonomy,
            "root_cause_line": self.root_cause_line,
            "fixture_missing": self.fixture_missing,
            "module_missing": self.module_missing,
            "raw_error_text": self.raw_error_text[:1200],
        }


# ---------------------------------------------------------------------------
# Dependency declaration resolution (Mission-10A sections 10-11)
# ---------------------------------------------------------------------------
# Requirement-file name priority per mechanism. A "declared" package is one
# whose name appears in any of these manifests at the target commit.
DECLARATION_FILES = (
    "pyproject.toml",
    "poetry.lock",
    "uv.lock",
    "requirements.txt",
    "requirements-dev.txt",
    "requirements_dev.txt",
    "requirements-test.txt",
    "requirements_test.txt",
    "setup.py",
    "setup.cfg",
    "tox.ini",
    "Pipfile",
    "Pipfile.lock",
)


def package_declared_in_text(package: str, text: str) -> bool:
    """Mechanical detection: normalized package name appears in manifest text."""
    norm = package.lower().replace("_", "-")
    pat = re.compile(rf"^\s*{re.escape(norm)}\s*[=<>~!\[^\]]", re.M | re.I)
    pat2 = re.compile(rf"[\"']{re.escape(norm)}[\"']", re.I)
    return bool(pat.search(text) or pat2.search(text))


@dataclass
class DeclaredPackage:
    package: str
    mechanism: str  # poetry/pyproject | pip-requirements | pipenv | setup | tox | lockfile
    declared: bool
    version_spec: str | None = None
    locked_version: str | None = None
    group: str | None = None
    markers: str | None = None
    file: str | None = None


def resolve_declared_version(package: str, manifest_texts: dict[str, str]) -> DeclaredPackage:
    """Resolve a package's declaration across all target-commit manifests.

    ``manifest_texts`` maps relpath -> text content at the target commit.
    Returns the strongest evidence. pyproject.toml is checked FIRST because it
    carries the dev/test group membership (the strongest "required by test/dev
    config" evidence); lockfiles are checked next for the exact pinned version;
    then requirements pins.
    """
    result = DeclaredPackage(package=package, mechanism="none", declared=False)
    order = sorted(
        manifest_texts,
        key=lambda p: (0 if p.rsplit("/", 1)[-1] == "pyproject.toml" else 1, p),
    )
    for path in order:
        text = manifest_texts[path]
        if not text:
            continue
        base = path.rsplit("/", 1)[-1]
        if base == "poetry.lock":
            # Poetry lock: [[package]] name = "pytest-mock" ... version = "3.10.0"
            m = re.search(
                rf"\[\[package\]\]\s*\n(?:.*?\n)*?name\s*=\s*[\"']{re.escape(package)}[\"']\s*\n"
                rf"(?:.*?\n)*?version\s*=\s*[\"']([^\"']+)[\"']",
                text,
            )
            if m:
                result.declared = True
                result.mechanism = "poetry.lock"
                result.locked_version = m.group(1)
                result.file = path
                return result
        elif base == "uv.lock":
            m = re.search(
                rf"name\s*=\s*[\"']{re.escape(package)}[\"']\s*\n"
                rf"(?:.*?\n)*?version\s*=\s*[\"']([^\"']+)[\"']",
                text,
            )
            if m:
                result.declared = True
                result.mechanism = "uv.lock"
                result.locked_version = m.group(1)
                result.file = path
                return result
        elif base == "pyproject.toml":
            # Poetry sections: modern [tool.poetry.group.<grp>.dependencies],
            # legacy [tool.poetry.dev-dependencies], and runtime
            # [tool.poetry.dependencies]. Split on section headers so the
            # target line belongs to the right group.
            section_hits: list[re.Match[str]] = list(
                re.finditer(
                    r"\[(tool\.poetry\.group\.([\w\-]+)\.dependencies|"
                    r"tool\.poetry\.dev-dependencies|tool\.poetry\.dependencies)\]",
                    text,
                )
            )
            for idx, sec in enumerate(section_hits):
                end = section_hits[idx + 1].start() if idx + 1 < len(section_hits) else len(text)
                body = text[sec.end():end]
                m = re.search(rf"^\s*{re.escape(package)}\s*=\s*([^\n]+)", body, re.M | re.I)
                if m:
                    result.declared = True
                    header = sec.group(1)
                    if header == "tool.poetry.dependencies":
                        result.group = "main"
                    elif header == "tool.poetry.dev-dependencies":
                        result.group = "dev"
                    else:
                        result.group = sec.group(2)
                    result.mechanism = "pyproject-poetry"
                    result.version_spec = m.group(1).strip()
                    result.file = path
                    return result
            # PEP 735 [dependency-groups] (uv/pip modern projects)
            dg = re.search(r"\[dependency-groups\]\s*\n(.*?)(?=\n\[|\Z)", text, re.S)
            if dg:
                dg_body = dg.group(1)
                # find group name owning the package: the last ``name = [``
                # block start before the package occurrence
                occ = dg_body.find(package)
                if occ != -1:
                    head = dg_body[:occ]
                    grp = re.findall(r"^\s*([\w\-]+)\s*=\s*\[", head, re.M)
                    if grp:
                        # capture version spec inside the quoted string
                        tail = dg_body[occ + len(package):]
                        mm = re.match(r'([^"\']*)["\']', tail.lstrip())
                        result.declared = True
                        result.mechanism = "pyproject-dependency-groups"
                        result.group = grp[-1]
                        result.version_spec = (mm.group(1).strip() if mm else "")
                        result.file = path
                        return result
        elif base.startswith("requirements"):
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            for ln in lines:
                if ln.startswith("#") or ln.startswith("-"):
                    continue
                m = re.match(rf"^{re.escape(package)}([<>=~!].*?)?(?:\s*;\s*(.*))?$", ln, re.I)
                if m:
                    result.declared = True
                    result.mechanism = "pip-requirements"
                    result.version_spec = m.group(1) or ""
                    result.markers = m.group(2)
                    result.file = path
                    return result
    # bare mention fallback
    for path, text in manifest_texts.items():
        if text and package_declared_in_text(package, text):
            result.declared = True
            if result.mechanism == "none":
                result.mechanism = "mention"
                result.file = path
    return result


# ---------------------------------------------------------------------------
# Test-category definitions (Mission-10A section 13) - mechanical, static
# ---------------------------------------------------------------------------
def test_path_category(node_id: str) -> str:
    """Mechanical top-level test path category (Mission-10A §8.5)."""
    file_part = node_id.split("::", 1)[0]
    norm = file_part.replace("\\", "/")
    parts = [p for p in norm.split("/") if p]
    for i, p in enumerate(parts):
        if p == "tests" and i + 1 < len(parts):
            sub = parts[i + 1]
            if sub == "benchmark":
                return "tests/benchmark"
            return f"tests/{sub}"
    return "other"


def file_requests_fixture(text: str, fixture: str) -> bool:
    """Static file-level evidence: fixture appears as a function arg, in
    ``@pytest.mark.usefixtures``, or in a ``@pytest.fixture``-style reference."""
    if not text:
        return False
    if fixture not in text:
        return False
    return bool(
        re.search(rf"\bdef \w+\([^)]*\b{re.escape(fixture)}\b[^)]*\)", text)
        or re.search(rf"usefixtures\([^)]*\b{re.escape(fixture)}\b[^)]*\)", text)
    )


def node_requests_fixture(test_text: str, test_name: str, fixture: str) -> bool:
    """Node-level static evidence: the SPECIFIC test function (or its decorators)
    requests the fixture (function argument or usefixtures/pytestmark).

    Mission-10A section 13: category definitions must use static/mechanical
    evidence such as fixture argument in test signature, pytestmark /
    usefixtures, path category, import/reference — never probe outcomes.
    """
    if not test_text or not test_name:
        return False
    idx = test_text.find(f"def {test_name}")
    if idx == -1:
        bare = test_name.split("[", 1)[0]
        idx = test_text.find(f"def {bare}")
    if idx == -1:
        return False
    start = test_text.rfind("@", 0, idx)
    if start == -1:
        start = idx
    block = test_text[start:idx + 600]
    return bool(
        re.search(rf"\bdef \w+\([^)]*\b{re.escape(fixture)}\b[^)]*\)", test_text[idx:idx + 400])
        or re.search(rf"usefixtures\([^)]*\b{re.escape(fixture)}\b[^)]*\)", block)
    )


def category_key(node_id: str, fixture: str) -> str:
    return f"{test_path_category(node_id)}::{fixture}"


# ---------------------------------------------------------------------------
# Preregistered materiality rule (Mission-10A section 14)
# ---------------------------------------------------------------------------
@dataclass
class MaterialityRule:
    version: str
    preregistered_before_probe: bool
    rule_text: str
    conditions: dict = field(default_factory=dict)


def preregister_materiality_rule(created_utc: str) -> MaterialityRule:
    """Exact preregistered ENV_V3_RECOMMENDED rule (Mission-10A §14)."""
    _ = created_utc  # recorded by the caller in the artifact
    rule_text = (
        "ENV_V3_RECOMMENDED iff "
        "PRECONDITION: a dependency is project-declared for the historical TARGET "
        "commit AND required by the relevant project test/dev configuration AND not "
        "available correctly in frozen V2 (not installed OR plugin not loaded / "
        "fixture unavailable); "
        "AND at least one materiality condition M1/M2/M3; "
        "AND all safety conditions S1/S2."
    )
    return MaterialityRule(
        version="mission10a-materiality-v1-2026-09-26",
        preregistered_before_probe=True,
        rule_text=rule_text,
        conditions={
            "precondition": [
                "dependency project-declared at target commit",
                "required by test/dev config",
                "not correctly available in V2",
            ],
            "materiality": {
                "M1": ">=1 tested ENG task newly oracle-valid in probe",
                "M2": "ENG task BEHAVIORAL_F2P node set changed by recovering valid "
                "behavioral F2P nodes V2 excluded",
                "M3": "V2 omission systematically excludes a mechanically defined "
                "whole test category",
            },
            "safety": {
                "S1": "zero new infrastructure failure categories introduced",
                "S2": "non-regression: every V2 BEHAVIORAL_F2P and P2P_ONLY node in "
                "probe tasks keeps SAME classification",
            },
            "decision": {
                "ENV_V3_RECOMMENDED": "precondition + (M1|M2|M3) + S1 + S2",
                "ENV_V2_ADEQUATE": "no material omission under M1/M2/M3 and no other "
                "validity defect",
                "ENV_AUDIT_INCONCLUSIVE": "mixed evidence / ambiguous dependency "
                "history / probe class changes / safety fails",
            },
        },
    )


def evaluate_materiality(
    *,
    declared_but_not_installed_causes: int,
    declared_installed_plugin_not_loaded_causes: int,
    m1_newly_oracle_valid_tasks: int,
    m2_recovered_behavioral_f2p_nodes: int,
    m3_systematic_category_exclusion: bool,
    s1_new_infrastructure_failure_categories: int,
    s2_non_regression_holds: bool,
) -> str:
    """Deterministic materiality evaluation. Returns one decision token."""
    precondition = declared_but_not_installed_causes + declared_installed_plugin_not_loaded_causes > 0
    materiality = (
        m1_newly_oracle_valid_tasks >= 1
        or m2_recovered_behavioral_f2p_nodes >= 1
        or m3_systematic_category_exclusion
    )
    safety = s1_new_infrastructure_failure_categories == 0 and s2_non_regression_holds
    if precondition and materiality and safety:
        return "ENV_V3_RECOMMENDED"
    if not materiality and s2_non_regression_holds:
        return "ENV_V2_ADEQUATE"
    return "ENV_AUDIT_INCONCLUSIVE"


# ---------------------------------------------------------------------------
# Probe node-set reconciliation (Mission-10A section 19)
# ---------------------------------------------------------------------------
def reconcile_probe_sets(
    set_a_ids: list[str],
    set_b_v2_ids: list[str],
    v2_classes: dict[str, str],
    probe_classes: dict[str, str],
) -> dict:
    """Verify zero missing/duplicate/orphan and report class transitions."""
    set_a = sorted(set(set_a_ids))
    set_b = sorted(set(set_b_v2_ids))
    missing_a = [n for n in set_a_ids if n not in probe_classes]
    dup_a = [n for n in set_a_ids if set_a_ids.count(n) > 1]
    missing_b = [n for n in set_b if n not in probe_classes]
    dup_b = [n for n in set_b_v2_ids if set_b_v2_ids.count(n) > 1]
    orphan = [n for n in probe_classes if n not in set_a_ids and n not in set_b]
    transitions = {}
    for n in set_b:
        v2 = v2_classes.get(n)
        probe = probe_classes.get(n)
        if v2 != probe:
            transitions[n] = {"v2": v2, "probe": probe}
    return {
        "set_a_n": len(set_a),
        "set_b_n": len(set_b),
        "set_a_missing": missing_a,
        "set_a_duplicates": dup_a,
        "set_b_missing": missing_b,
        "set_b_duplicates": dup_b,
        "orphan_records": orphan,
        "class_transitions": transitions,
        "ok": not (missing_a or dup_a or missing_b or dup_b or orphan or transitions),
    }


def sha256_json(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
