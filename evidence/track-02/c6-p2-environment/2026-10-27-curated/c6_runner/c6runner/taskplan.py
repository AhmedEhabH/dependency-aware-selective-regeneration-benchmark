# -*- coding: utf-8 -*-
"""Task plan: the immutable, authorization-bound specification for one C6 task.

The operator freezes one TaskPlan per task (command bytes, test identities,
oracle mode, isolation backend, interpreter, resource ceilings). The plan's
canonical SHA-256 is bound inside the operator authorization receipt
(`task_bindings`); the CLI loads a plan file, recomputes its canonical hash and
requires equality with the bound value. The runner executes ONLY the plan:
no free-form command/test-path/resource/network overrides are accepted.
"""
import json

from . import TASK_PLAN_SCHEMA_V1
from .hashes import sha256_hex


class TaskPlanError(ValueError):
    pass


DEFAULT_RESOURCES = {
    "timeout_s": 1800.0,
    "ram_mb": 16384.0,
    "disk_mb": 5120.0,         # scratch delta cap
    "scratch_mb": 5120.0,
    "global_floor_gb": 20.0,   # host free-disk floor, checked pre-task
    "network_bytes": 0,        # allowed network budget (0 for C6)
    "pids_limit": 512,
    "cpu_quota": 1.0,          # host CPUs ceiling (docker --cpus)
}

VALID_ORACLE_MODES = ("POSITIVE_REFERENCE", "NEG_TESTS_EXPECTED_FAIL", "NONE")
VALID_BACKENDS = ("docker", "job-object", "python-process")

# junitxml evidence lives in the container-writable scratch bind
DOCKER_JUNIT_DEFAULT = "/scratch-dir/c6-junit.xml"
DOCKER_JUNIT_PREFIX = "/scratch-dir/"
DIGEST_PREFIX = "sha256:"


class TaskPlan:
    def __init__(self, task, command, test_paths, t_only_paths,
                 oracle_mode="POSITIVE_REFERENCE",
                 isolation_backend="docker", image=None,
                 image_digest=None, interpreter="python",
                 interpreter_version=None, wheelhouse=None,
                 wheelhouse_id=None, junitxml_path=None,
                 resources=None, notes="", harness=False):
        self.task = task
        self.command = [str(a) for a in command] if not isinstance(command, str) \
            else command.split()
        if not self.command:
            raise TaskPlanError("command empty")
        self.test_paths = list(test_paths or [])
        self.t_only_paths = list(t_only_paths or [])
        self.oracle_mode = oracle_mode
        if oracle_mode not in VALID_ORACLE_MODES:
            raise TaskPlanError(f"oracle_mode must be one of {VALID_ORACLE_MODES}")
        self.isolation_backend = isolation_backend
        if isolation_backend not in VALID_BACKENDS:
            raise TaskPlanError(f"isolation_backend must be one of {VALID_BACKENDS}")
        self.image = image
        self.image_digest = image_digest
        self.interpreter = interpreter or "python"
        self.interpreter_version = interpreter_version
        self.wheelhouse = wheelhouse
        self.wheelhouse_id = wheelhouse_id
        self.junitxml_path = junitxml_path or DOCKER_JUNIT_DEFAULT
        if self.isolation_backend == "docker":
            if not self.image:
                raise TaskPlanError(
                    "docker plan requires a pinned image ref (plan.image)")
            if not (self.image_digest or "").strip():
                raise TaskPlanError(
                    "docker plan requires an immutable image_digest "
                    "(never a bare mutable tag as publication identity)")
            if not self.junitxml_path.startswith(DOCKER_JUNIT_PREFIX):
                raise TaskPlanError(
                    "docker junitxml_path must live under " + DOCKER_JUNIT_PREFIX)
        self.resources = dict(DEFAULT_RESOURCES)
        if resources:
            self.resources.update({k: v for k, v in resources.items()
                                   if v is not None})
        for k, v in self.resources.items():
            if isinstance(v, (int, float)) and v < 0:
                raise TaskPlanError(f"resource {k}= {v} must be >= 0")
        self.notes = notes or ""
        self.harness = bool(harness)

    # ------------------------------------------------------------------
    def canonical(self) -> str:
        """Deterministic canonical bytes (the authorization binding unit)."""
        doc = {
            "schema": TASK_PLAN_SCHEMA_V1,
            "task": self.task,
            "command": self.command,
            "test_paths": sorted(self.test_paths),
            "t_only_paths": sorted(self.t_only_paths),
            "oracle_mode": self.oracle_mode,
            "isolation_backend": self.isolation_backend,
            "image": self.image,
            "image_digest": self.image_digest,
            "interpreter": self.interpreter,
            "interpreter_version": self.interpreter_version,
            "wheelhouse": self.wheelhouse,
            "wheelhouse_id": self.wheelhouse_id,
            "junitxml_path": self.junitxml_path,
            "resources": {k: self.resources[k] for k in sorted(self.resources)},
            "harness": self.harness,
        }
        return (json.dumps(doc, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True) + "\n")

    def canonical_sha256(self) -> str:
        return sha256_hex(self.canonical().encode("utf-8"))

    def to_dict(self):
        doc = json.loads(self.canonical())
        doc["notes"] = self.notes
        return doc

    @classmethod
    def from_dict(cls, doc):
        return cls(
            task=str(doc["task"]),
            command=list(doc["command"]),
            test_paths=list(doc.get("test_paths", [])),
            t_only_paths=list(doc.get("t_only_paths", [])),
            oracle_mode=doc.get("oracle_mode", "POSITIVE_REFERENCE"),
            isolation_backend=doc.get("isolation_backend", "docker"),
            image=doc.get("image"),
            image_digest=doc.get("image_digest"),
            interpreter=doc.get("interpreter", "python"),
            interpreter_version=doc.get("interpreter_version"),
            wheelhouse=doc.get("wheelhouse"),
            wheelhouse_id=doc.get("wheelhouse_id"),
            junitxml_path=doc.get("junitxml_path"),
            resources=doc.get("resources"),
            notes=doc.get("notes", ""),
            harness=bool(doc.get("harness", False)),
        )