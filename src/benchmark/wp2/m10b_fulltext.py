"""WP-2 Mission-10B full-text root-cause extraction (ZERO API).

Deterministic, zero-LLM extraction of the FULL <error>/<failure> element text
from C4/C2 (Linux V2) JUnit evidence and Mission-09 P2P-U ENG evidence, with
the Mission-10B V3 taxonomy (section 7.2) and exception-extraction precedence
(section 7.1). This fixes the Mission-10A limitation of truncated
``raw_error_text`` ([:1200] in ``ErrorRecord.to_dict`` and [:4000] in
``parse_junit_with_failures``) and the merged-repetition node->text map.

The module performs no model/API calls and never mutates frozen artifacts.
"""
from __future__ import annotations

import hashlib
import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# V3 taxonomy (Mission-10B section 7.2)
# ---------------------------------------------------------------------------
INFRA_EMFILE = "INFRA:EMFILE"
DB_WRONG_CONSTRAINTS = "DB:WRONG_CONSTRAINTS"
DB_SET_SESSION_IN_TXN = "DB:SET_SESSION_IN_TXN"
DB_OTHER = "DB:OTHER"
TIME_IMMATURE_SIGNATURE = "TIME:IMMATURE_SIGNATURE"
TIME_EXPIRED_SIGNATURE = "TIME:EXPIRED_SIGNATURE"
TIME_NBF = "TIME:NBF"
TIME_FREEZEGUN = "TIME:FREEZEGUN"
TIME_TIMEZONE = "TIME:TIMEZONE"
TIME_OTHER = "TIME:OTHER"
INSTALL = "INSTALL"
COLLECTION = "COLLECTION"
OTHER = "OTHER"

CAUSE_FAMILY: dict[str, str] = {
    "INFRA": "INFRA",
    "DB": "DB",
    "MISSING_FIXTURE": "MISSING_FIXTURE",
    "MODULE_NOT_FOUND": "MODULE_NOT_FOUND",
    "IMPORT_ERROR": "IMPORT_ERROR",
    "TIME": "TIME",
    "INSTALL": "INSTALL",
    "COLLECTION": "COLLECTION",
    "OTHER": "OTHER",
}

# Families that count toward the materiality numerator (14.3) ONLY when the
# cause is mechanically attributable and STABLE_CAUSE across the 3 target reps.
MATERIALITY_FAMILIES = frozenset({"INFRA", "DB", "MISSING_FIXTURE", "MODULE_NOT_FOUND"})

# ---------------------------------------------------------------------------
# Regexes (order matters: most specific first)
# ---------------------------------------------------------------------------
_RE_EMFILE = re.compile(r"(?:Too many open files|\[Errno 24\])", re.I)
_RE_WRONG_CONSTRAINTS = re.compile(
    r"Found wrong number\s*\(?\s*(\d+)\s*\)?\s*of constraints", re.I
)
_RE_SET_SESSION_TXN = re.compile(r"set_session cannot be used inside a transaction", re.I)
_RE_FIXTURE = re.compile(r"fixture ['\"]([^'\"]+)['\"] not found", re.I)
_RE_MODULE = re.compile(
    r"(?:ModuleNotFoundError|No module named)\s*['\"]?([A-Za-z_][\w.\-]*)['\"]?", re.I
)
_RE_IMPORT = re.compile(r"ImportError:\s*(.+)$", re.I | re.M)
_RE_IMMATURE = re.compile(
    r"(ImmatureSignatureError|immature signature|iat .*future|jwt\.exceptions\.ImmatureSignatureError)",
    re.I,
)
_RE_EXPIRED = re.compile(
    r"(ExpiredSignatureError|expired signature|expired.*token|jwt\.exceptions\.ExpiredSignatureError)",
    re.I,
)
_RE_NBF = re.compile(
    r"(NotBeforeError|not before|nbf .*not yet|jwt\.exceptions\.NotBeforeError)", re.I
)
_RE_FREEZEGUN = re.compile(r"(freezegun|FreezeGun|cannot use .*with freezegun|wrong_auto_tick)", re.I)
_RE_TIMEZONE = re.compile(
    r"(timezone|pytz|zoneinfo|tzinfo|UnknownTimeZoneError|non-naive|naive datetime|"
    r"Offset must be a timedelta|astimezone|utcfromtimestamp)", re.I
)
_RE_TIME_OTHER = re.compile(
    r"(ExpiredSignature|ImmatureSignature|JWT|jwt\.exceptions|\\biat\\b|\\bnbf\\b|\\bexp\\b|"
    r"timestamp.*(?:invalid|error|skew)|clock skew|datetime.*(?:error|skew))",
    re.I,
)
_RE_DB = re.compile(
    r"(OperationalError|ProgrammingError|psycopg|could not connect to server|"
    r"FATAL:\s+database|connection to server|django\.db\.utils\.|"
    r"django\.db\.migrations|DBError|database .* does not exist|"
    r"PermissionError.*postgres|relation .* does not exist|"
    r"set_session|transaction|cannot be used inside a transaction|"
    r"Too many connections|ConnectionRefusedError.*5432|psycopg2\.OperationalError)",
    re.I,
)
_RE_COLLECTION = re.compile(
    r"(ERROR at collection|error collecting|collection error|collecting .* failed|"
    r"attribute .* is not a file|failed to collect|import file mismatch|"
    r"error in pytest_plugins|Error while importing|no tests ran)",
    re.I,
)
_RE_INSTALL = re.compile(
    r"(error: |Could not find a version|No matching distribution|"
    r"Failed to build|Build failed|pip .* error|ResolutionImpossible|"
    r"package .* not found|ERROR: Invalid requirement|ResolverError|"
    r"Could not resolve dependencies)", re.I,
)

# Exception-shaped line: pytest renders as ``E   <Exc>: <msg>`` or plain
# ``<Exc>: <msg>`` / ``<Exc>`` at end of a traceback.
_RE_EXC_LINE = re.compile(
    r"^\s*(?:E\s+)?"
    r"([A-Za-z_][\w.]*(?:Error|Exception)|OSError|OperationalError|ProgrammingError|"
    r"ImmatureSignatureError|ExpiredSignatureError|NotBeforeError|ImproperlyConfigured|"
    r"ImportError|ModuleNotFoundError|TypeError|ValueError|AttributeError|KeyError|"
    r"IndexError|django\.db\.utils\.[A-Za-z_]+|psycopg2\.[A-Za-z_]+|"
    r"django\.core\.exceptions\.[A-Za-z_]+)\s*:?\s*(.*)$"
)
_RE_SETUP_WITH = re.compile(r'failed on setup with\s+"([^"]+)"')
_RE_SETUP_SUMMARY = re.compile(r"(failed on setup with|ERROR at setup|error during setup|SetupError)", re.I)

# Volatile normalization (7.1) - preserve errno/constraint counts/fixtures/classes
_RE_WORKSPACE = re.compile(r"/workspace/[A-Za-z0-9_\-]+/")
_RE_TMP = re.compile(r"/tmp/[A-Za-z0-9_\-\./]+")
_RE_HEX = re.compile(r"0x[0-9a-fA-F]{4,}")
_RE_DBNAME = re.compile(r"\b(?:test_)?[a-z0-9]{12,}\b")
_RE_TS = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b")
_RE_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_RE_CONTAINER = re.compile(r"\bwp2-t3-[a-f0-9]{12}-[pt]-[0-9]\b")
_RE_PID = re.compile(r"\bpid\s+[0-9]+\b", re.I)
_RE_FD = re.compile(r"\bfd\s+[0-9]+\b", re.I)
_RE_TASK12 = re.compile(r"\b[a-f0-9]{12}(?:_[a-z0-9_]+)?\b")


def normalize(text: str) -> str:
    """Normalize volatile values without deleting semantically meaningful ones."""
    if not text:
        return ""
    out = _RE_UUID.sub("UUID", text)
    out = _RE_CONTAINER.sub("CTR", out)
    out = _RE_WORKSPACE.sub("WS/", out)
    out = _RE_TMP.sub("TMP/", out)
    out = _RE_HEX.sub("HEX", out)
    out = _RE_TS.sub("TS", out)
    out = _RE_PID.sub("pid PID", out)
    out = _RE_FD.sub("fd FD", out)
    out = re.sub(r"\s+", " ", out)
    return out.strip()


# ---------------------------------------------------------------------------
# Exception extraction (7.1 precedence)
# ---------------------------------------------------------------------------
def final_exception_line(full_text: str, message: str = "") -> str:
    """Extract the final normalized exception using the 7.1 precedence.

    1. explicit <error>/<failure> message attribute (or "failed on setup with
       ..." wrapped message);
    2. last exception-shaped line in the full element text;
    3. pytest setup-failure summary;
    4. normalized traceback tail;
    5. OTHER if unresolved.
    """
    msg = (message or "").strip()
    m = _RE_SETUP_WITH.search(msg)
    if m:
        inner = m.group(1).strip()
        if inner and not inner.lower().startswith(("traceback", "during handling")):
            return normalize(inner)
    if msg and ("Error" in msg or "Exception" in msg):
        return normalize(msg[:300])
    # last exception-shaped line across the whole text
    lines = (full_text or "").splitlines()
    exc_lines = [ln for ln in lines if _RE_EXC_LINE.match(ln)]
    if exc_lines:
        m = _RE_EXC_LINE.match(exc_lines[-1])
        if m:
            exc = m.group(1).strip()
            rest = (m.group(2) or "").strip()
            return normalize((exc + (": " + rest if rest else ""))[:300])
    m = _RE_SETUP_SUMMARY.search(full_text or "")
    if m:
        start = max(0, m.start())
        return normalize((full_text or "")[start:start + 300])
    tail = (full_text or "").strip().splitlines()
    if tail:
        return normalize(tail[-1][:300])
    return "OTHER"


# ---------------------------------------------------------------------------
# V3 classification
# ---------------------------------------------------------------------------
def classify_error_v3(full_text: str, message: str = "") -> tuple[str, str]:
    """Classify full error text into the Mission-10B V3 taxonomy.

    Returns (taxonomy, detail). Detail keeps the semantically meaningful value
    (errno, constraint count, fixture name, module, exception class).
    """
    text = full_text or ""
    hay = text + "\n" + (message or "")
    # INFRA:EMFILE
    if _RE_EMFILE.search(hay):
        return INFRA_EMFILE, "OSError: [Errno 24] Too many open files"
    # DB:WRONG_CONSTRAINTS
    m = _RE_WRONG_CONSTRAINTS.search(hay)
    if m:
        return DB_WRONG_CONSTRAINTS, f"Found wrong number ({m.group(1)}) of constraints"
    # DB:SET_SESSION_IN_TXN
    if _RE_SET_SESSION_TXN.search(hay):
        return DB_SET_SESSION_IN_TXN, "set_session cannot be used inside a transaction"
    # MISSING_FIXTURE
    m = _RE_FIXTURE.search(hay)
    if m:
        return f"MISSING_FIXTURE:{m.group(1)}", m.group(1)
    # MODULE_NOT_FOUND
    m = _RE_MODULE.search(hay)
    if m:
        return f"MODULE_NOT_FOUND:{m.group(1)}", m.group(1)
    # IMPORT_ERROR (kept distinct; a parent-side import of a target-only symbol
    # is a legitimate semantic condition, not automatically infra)
    m = _RE_IMPORT.search(hay)
    if m:
        return f"IMPORT_ERROR:{normalize(m.group(1))[:120]}", normalize(m.group(1))[:120]
    # TIME taxonomy (specific before generic)
    if _RE_IMMATURE.search(hay):
        return TIME_IMMATURE_SIGNATURE, "ImmatureSignatureError (JWT iat in future)"
    if _RE_EXPIRED.search(hay):
        return TIME_EXPIRED_SIGNATURE, "ExpiredSignatureError (JWT exp/iat)"
    if _RE_NBF.search(hay):
        return TIME_NBF, "JWT not-before (nbf)"
    if _RE_FREEZEGUN.search(hay):
        return TIME_FREEZEGUN, "freezegun time-freeze error"
    if _RE_TIMEZONE.search(hay):
        return TIME_TIMEZONE, final_exception_line(text, message)[:160]
    if _RE_TIME_OTHER.search(hay):
        return TIME_OTHER, final_exception_line(text, message)[:160]
    # DB:OTHER (before INSTALL/COLLECTION/OTHER)
    if _RE_DB.search(hay):
        return DB_OTHER, final_exception_line(text, message)[:160]
    # INSTALL
    if _RE_INSTALL.search(hay):
        return INSTALL, final_exception_line(text, message)[:160]
    # COLLECTION
    if _RE_COLLECTION.search(hay):
        return COLLECTION, final_exception_line(text, message)[:160]
    # OTHER
    return OTHER, final_exception_line(text, message)[:160]


def cause_family(taxonomy: str) -> str:
    head = taxonomy.split(":", 1)[0]
    return CAUSE_FAMILY.get(head, OTHER)


# ---------------------------------------------------------------------------
# Full-text JUnit parsing (per file)
# ---------------------------------------------------------------------------
@dataclass
class JunitTestcase:
    node_id: str
    file: str | None
    classname: str
    name: str
    outcome: str  # error | failure | passed | skipped
    message: str = ""
    full_text: str = ""
    phase: str = ""

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "node_id": self.node_id,
            "file": self.file,
            "classname": self.classname,
            "name": self.name,
            "outcome": self.outcome,
            "message": self.message[:800],
            "phase": self.phase,
            "full_text_len": len(self.full_text),
        }


def node_id_from_tc(tc: ET.Element) -> str:
    fname = tc.get("file")
    cname = tc.get("classname")
    name = tc.get("name") or "?"
    if fname:
        return f"{fname}::{name}"
    if cname:
        return f"{cname.replace('.', '/')}.py::{name}"
    return f"{name.replace('.', '/')}.py::{name}"


def detect_phase_v3(full_text: str, message: str = "") -> str:
    if not full_text and not message:
        return "unknown"
    hay = (full_text or "")[:4000] + "\n" + (message or "")
    if _RE_COLLECTION.search(hay):
        return "collection"
    if _RE_SETUP_SUMMARY.search(hay) or _RE_SETUP_WITH.search(hay):
        return "setup"
    if re.search(r"(ERROR at teardown|failed at teardown|teardown error)", hay, re.I):
        return "teardown"
    if re.search(r"(ImportError while loading|error in main|pytest_plugins)", hay, re.I):
        return "import/bootstrap"
    return "call"


def parse_junit_fulltext(xml_text: str) -> list[JunitTestcase]:
    """Parse a JUnit XML blob into per-testcase records with FULL error text."""
    root = ET.fromstring(xml_text)
    out: list[JunitTestcase] = []
    for tc in root.iter("testcase"):
        nid = node_id_from_tc(tc)
        file_attr = tc.get("file")
        cname = tc.get("classname") or ""
        name = tc.get("name") or "?"
        err = tc.find("error")
        fail = tc.find("failure")
        skp = tc.find("skipped")
        if err is not None:
            message = html.unescape(err.get("message") or "")
            body = html.unescape(err.text or "")
            out.append(JunitTestcase(
                node_id=nid, file=file_attr, classname=cname, name=name,
                outcome="error", message=message, full_text=body,
                phase=detect_phase_v3(body, message),
            ))
        elif fail is not None:
            message = html.unescape(fail.get("message") or "")
            body = html.unescape(fail.text or "")
            out.append(JunitTestcase(
                node_id=nid, file=file_attr, classname=cname, name=name,
                outcome="failure", message=message, full_text=body,
                phase=detect_phase_v3(body, message),
            ))
        elif skp is not None:
            out.append(JunitTestcase(
                node_id=nid, file=file_attr, classname=cname, name=name,
                outcome="skipped", message="", full_text="", phase="skipped",
            ))
        else:
            out.append(JunitTestcase(
                node_id=nid, file=file_attr, classname=cname, name=name,
                outcome="passed", message="", full_text="", phase="passed",
            ))
    return out


# ---------------------------------------------------------------------------
# Per-(task, side, rep) node->text merging
# ---------------------------------------------------------------------------
@dataclass
class RepEvidence:
    task_id: str
    side: str  # p | t
    repetition: int
    node_id: str
    outcome: str
    message: str
    full_text: str
    phase: str
    evidence_files: list[str] = field(default_factory=list)

    @property
    def evidence_path(self) -> str:
        return ";".join(self.evidence_files)


def merge_rep_junit(
    *,
    task_id: str,
    side: str,
    repetition: int,
    xml_files: list[tuple[str, str]],
) -> dict[str, RepEvidence]:
    """Merge multiple JUnit files for one (task, side, rep) into node->evidence.

    ``xml_files`` is a list of (path_or_label, xml_text). When a node has
    multiple rows across files, an error/failure row is preferred over a passed
    row and the fullest text wins.
    """
    merged: dict[str, RepEvidence] = {}
    for label, xml_text in xml_files:
        try:
            records = parse_junit_fulltext(xml_text)
        except ET.ParseError:
            continue
        for rec in records:
            if rec.outcome not in ("error", "failure", "passed"):
                continue
            prev = merged.get(rec.node_id)
            if prev is None:
                merged[rec.node_id] = RepEvidence(
                    task_id=task_id, side=side, repetition=repetition,
                    node_id=rec.node_id, outcome=rec.outcome,
                    message=rec.message, full_text=rec.full_text,
                    phase=rec.phase, evidence_files=[label],
                )
                continue
            rank = {"passed": 0, "failure": 1, "error": 2}
            if rank[rec.outcome] > rank[prev.outcome]:
                prev.outcome = rec.outcome
                prev.message = rec.message
                prev.full_text = rec.full_text
                prev.phase = rec.phase
            elif rank[rec.outcome] == rank[prev.outcome]:
                if len(rec.full_text) > len(prev.full_text):
                    prev.full_text = rec.full_text
                    prev.message = rec.message
                    prev.phase = rec.phase
            if label not in prev.evidence_files:
                prev.evidence_files.append(label)
    return merged


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Node-level attribution (7.3)
# ---------------------------------------------------------------------------
def attribute_node_target_reps(rep_evidences: list[RepEvidence | None]) -> dict[str, object]:
    """Attribute a node across its 3 TARGET repetitions.

    ``rep_evidences`` is a length-3 list (r0, r1, r2); None = missing evidence.
    Returns dict with per-rep taxonomy/family, stability classification and
    materiality membership.
    """
    per_rep: list[dict[str, str] | None] = []
    families: list[str] = []
    for ev in rep_evidences:
        if ev is None or not ev.full_text:
            per_rep.append(None)
            continue
        tax, detail = classify_error_v3(ev.full_text, ev.message)
        fam = cause_family(tax)
        per_rep.append({"taxonomy": tax, "detail": detail, "family": fam,
                        "phase": ev.phase})
        families.append(fam)
    present = [p for p in per_rep if p is not None]
    if not present:
        stability = "MISSING_EVIDENCE"
    elif len(present) < 3:
        stability = "MISSING_EVIDENCE" if any(p is None for p in per_rep) else "MIXED_CAUSE"
    else:
        fam_set = set(families)
        stability = "STABLE_CAUSE" if len(fam_set) == 1 else "MIXED_CAUSE"
    # Majority (>2/3 = 2 of 3) families, descriptive only (never the gate).
    majority = sorted({f for f in families if families.count(f) >= 2})
    materiality = (
        stability == "STABLE_CAUSE"
        and bool(present)
        and all(p["family"] in MATERIALITY_FAMILIES for p in present)
    )
    return {
        "per_rep": per_rep,
        "stability": stability,
        "stable_family": families[0] if stability == "STABLE_CAUSE" and families else None,
        "majority_families": majority,
        "materiality": materiality,
    }


def majority_cause_share(attribution: dict[str, object]) -> str | None:
    """Descriptive >=2/3 majority cause family (secondary table only)."""
    per_rep = attribution["per_rep"]
    assert isinstance(per_rep, list)
    fams = [p["family"] for p in per_rep if p is not None]
    if not fams:
        return None
    for f in sorted(set(fams)):
        if fams.count(f) >= 2:
            return str(f)
    return None


# ---------------------------------------------------------------------------
# Reconciliation helpers
# ---------------------------------------------------------------------------
def reconcile_counts(
    *,
    authoritative_total: int,
    authoritative_error: int,
    authoritative_failed: int,
    attributed: dict[str, dict[str, str]],
) -> dict[str, object]:
    n_stable = sum(1 for v in attributed.values() if v["stability"] == "STABLE_CAUSE")
    n_mixed = sum(1 for v in attributed.values() if v["stability"] == "MIXED_CAUSE")
    n_missing = sum(1 for v in attributed.values() if v["stability"] == "MISSING_EVIDENCE")
    n_failed_only = sum(1 for v in attributed.values() if v["stability"] == "FAILED_ONLY")
    total = n_stable + n_mixed + n_missing + n_failed_only
    return {
        "authoritative_total": authoritative_total,
        "authoritative_error_bearing": authoritative_error,
        "authoritative_failed_only": authoritative_failed,
        "STABLE_CAUSE": n_stable,
        "MIXED_CAUSE": n_mixed,
        "MISSING_EVIDENCE": n_missing,
        "FAILED_ONLY": n_failed_only,
        "reconciled_total": total,
        "mismatch": authoritative_total - total,
        "ok": total == authoritative_total,
    }
