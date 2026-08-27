"""PILOT-EXEC-01 v0.9.21 — per-cell validation runtime parity (B1/B2/B3).

The pristine preflight proven by v0.9.20 uses per-repository provisioned
interpreters, the frozen repository env, and completes Saleor in ~776s. The
scientific generated-workspace path (seven_arm_benchmark → PipelineConfig →
BenchmarkRunner Stage 3 → FunctionalValidator) must have runtime parity:

- B1: validation commands start with the explicit per-repository interpreter
  (never a silent sys.executable fallback);
- B2: the frozen per-repository validation env reaches the subprocess
  (parent env preserved, os.environ never mutated);
- B3: the validation subprocess budget is an explicit bounded positive value
  (Pilot launches pass 1800; the model ``--timeout 600`` stays separate).
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[2]
FROZEN_MANIFEST = PROJECT_DIR / "benchmark_data" / "manifests" / "pilot_validation_commands.yaml"
SCRIPT = PROJECT_DIR / "seven_arm_benchmark.py"


def _assigned_list_elements(source: str, target: str) -> list[ast.expr]:
    tree = ast.parse(source)
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(name, ast.Name) and name.id == target for name in node.targets)
    ]
    assert len(assignments) == 1, f"expected one assignment to {target}"
    value = assignments[0].value
    assert isinstance(value, ast.List), f"{target} must be a list"
    return list(value.elts)


def _assert_string(node: ast.expr, expected: str) -> None:
    assert isinstance(node, ast.Constant) and node.value == expected


def _assert_prefixed_name(node: ast.expr, prefix: str, name: str) -> None:
    assert isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)
    _assert_string(node.left, prefix)
    assert isinstance(node.right, ast.Name) and node.right.id == name


def _load_script() -> Any:
    spec = importlib.util.spec_from_file_location(
        "seven_arm_benchmark_v0921_under_test", str(SCRIPT)
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _frozen_commands() -> dict[str, Any]:
    from benchmark.repositories.validation_commands import load_validation_commands

    mapping = load_validation_commands(FROZEN_MANIFEST)
    return {repo: mapping.require(repo) for repo in ("todo", "djangocms", "saleor")}


@pytest.fixture()
def fake_interpreters(tmp_path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for repo in ("todo", "djangocms", "saleor"):
        interp = tmp_path / "envs" / repo / "bin" / ("python.exe" if os.name == "nt" else "python")
        interp.parent.mkdir(parents=True, exist_ok=True)
        interp.write_text("# interpreter placeholder\n", encoding="utf-8")
        out[repo] = str(interp)
    return out


# ---------------------------------------------------------------------------
# B1 — explicit per-repository interpreter mapping
# ---------------------------------------------------------------------------


class TestValidationPythonMapping:
    def test_parse_rejects_duplicates(self) -> None:
        sab = _load_script()
        with pytest.raises(ValueError, match="duplicate"):
            sab.parse_validation_python_args(["saleor=/a", "saleor=/b"])

    @pytest.mark.parametrize("bad", ["saleor", "=/path", "saleor=", " "])
    def test_parse_rejects_malformed(self, bad: str) -> None:
        sab = _load_script()
        with pytest.raises(ValueError, match="invalid --validation-python"):
            sab.parse_validation_python_args([bad])

    def test_parse_accepts_repeatable_values(self) -> None:
        sab = _load_script()
        mapping = sab.parse_validation_python_args(
            ["todo=/t", " djangocms=/d ", "saleor=/s"]
        )
        assert mapping == {"todo": "/t", "djangocms": "/d", "saleor": "/s"}

    def test_saleor_command_starts_with_provided_interpreter_and_carries_frozen_env(
        self, fake_interpreters: dict[str, str]
    ) -> None:
        """Gate 3 contract around the actual resolution helper."""
        sab = _load_script()
        frozen = _frozen_commands()["saleor"]
        argv, env = sab.resolve_frozen_validation_runtime(
            "saleor", frozen, fake_interpreters["saleor"]
        )
        assert argv[0] == fake_interpreters["saleor"]
        assert argv[1:3] == ["-m", "pytest"]
        # The frozen PRIMARY command legitimately contains a second -m marker
        # token ("-m not e2e"); the single-`-m` invariant belongs to the
        # v0.9.20 fast capability gate, not to this runtime contract.
        assert argv[3] == "-m" and argv[4] == "not e2e"
        assert env == {
            "DATABASE_URL": "postgres://saleor:saleor@127.0.0.1:5433/saleor",
            "CACHE_URL": "redis://127.0.0.1:6379/0",
            "SECRET_KEY": "ci-test",
            "TZ": "UTC",
        }

    def test_djangocms_and_todo_runtime(self, fake_interpreters: dict[str, str]) -> None:
        sab = _load_script()
        cmds = _frozen_commands()
        dj_argv, dj_env = sab.resolve_frozen_validation_runtime(
            "djangocms", cmds["djangocms"], fake_interpreters["djangocms"]
        )
        assert dj_argv[0] == fake_interpreters["djangocms"]
        assert dj_argv[1:3] == ["manage.py", "test"]
        assert dj_env == {"DATABASE_URL": "sqlite://localhost/testdb.sqlite"}
        todo_argv, todo_env = sab.resolve_frozen_validation_runtime(
            "todo", cmds["todo"], fake_interpreters["todo"]
        )
        assert todo_argv[0] == fake_interpreters["todo"]
        assert todo_argv[1:] == ["-m", "pytest"]
        assert todo_env == {}

    def test_missing_mapping_fails_closed_no_sys_executable_fallback(
        self, fake_interpreters: dict[str, str]
    ) -> None:
        sab = _load_script()
        frozen = _frozen_commands()["saleor"]
        old_behavior = list(frozen.resolve_interpreter(sys.executable))
        assert old_behavior[0] == sys.executable, (
            "precondition: the v0.9.20 path silently routed to sys.executable"
        )
        with pytest.raises(RuntimeError, match="missing --validation-python mapping"):
            sab.resolve_frozen_validation_runtime("saleor", frozen, "")

    def test_nonexistent_interpreter_fails_closed(
        self, fake_interpreters: dict[str, str], tmp_path: Path
    ) -> None:
        sab = _load_script()
        frozen = _frozen_commands()["saleor"]
        missing = str(tmp_path / "does-not-exist" / "python")
        with pytest.raises(RuntimeError, match="does not exist"):
            sab.resolve_frozen_validation_runtime("saleor", frozen, missing)

    def test_resolution_gate_precedes_execution_plan_in_main(self) -> None:
        """Structural fail-closed proof: main() resolves/validates the runtime
        before creating the scientific execution plan."""
        source = SCRIPT.read_text(encoding="utf-8")
        main_start = source.index("def main() -> int:")
        main_src = source[main_start:]
        resolution_idx = main_src.index("resolve_frozen_validation_runtime(")
        plan_idx = main_src.index("_build_execution_plan(")
        assert resolution_idx < plan_idx

    def test_cli_nonexistent_interpreter_fails_before_any_run_output(
        self, tmp_path: Path
    ) -> None:
        """End-to-end CLI gate (B1/Task E): a non-dry-run Pilot invocation with
        a non-existent mapped interpreter is an environment/harness failure —
        exit 1 with zero run records and no model initialization."""
        out_dir = tmp_path / "runs"
        model_dir = tmp_path / "model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        (model_dir / "model.safetensors").write_bytes(b"\x00" * 16)
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--profile", "pilot",
                "--backend", "kaggle-qwen",
                "--model-path", str(model_dir),
                "--validation-python", "todo=missing/python",
                "--validation-python", "djangocms=/djangocms/envs/bin/python",
                "--validation-python", "saleor=/saleor/envs/.venv/bin/python",
                "--validation-timeout", "1800",
                "--output-dir", str(out_dir),
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=600,
        )
        assert proc.returncode == 1
        combined = proc.stdout + proc.stderr
        assert "does not exist" in combined
        assert "todo" in combined
        assert not (out_dir / "run_records.jsonl").exists()
        assert list(out_dir.glob("**/run_records.jsonl")) == []

    def test_cli_dry_run_tolerates_absent_external_interpreters(
        self, tmp_path: Path
    ) -> None:
        """Rule 6: dry run performs no validation/model execution, so it does
        not require the external repository interpreters."""
        out_dir = tmp_path / "runs"
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--profile", "pilot",
                "--validation-python", "todo=missing/python",
                "--validation-timeout", "1800",
                "--output-dir", str(out_dir),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=900,
        )
        assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]

    def test_cli_nonpositive_validation_timeout_fails_closed(
        self, tmp_path: Path
    ) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--profile", "pilot",
                "--validation-timeout", "0",
                "--output-dir", str(tmp_path / "runs"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_DIR,
            timeout=300,
        )
        assert proc.returncode == 1
        combined = proc.stdout + proc.stderr
        assert "--validation-timeout must be a positive integer" in combined


# ---------------------------------------------------------------------------
# B2 — frozen env propagation into FunctionalValidator subprocesses
# ---------------------------------------------------------------------------


class TestFunctionalValidatorEnv:
    @staticmethod
    def _env_dump_command() -> list[str]:
        return [sys.executable, "-c", "import json,os;print(json.dumps(dict(os.environ)))"]

    def test_parent_env_preserved_and_overrides_present(self, tmp_path: Path) -> None:
        from benchmark.execution.validation import FunctionalValidator

        sentinel_parent = "V0921_PARENT_SENTINEL_VALUE"
        os.environ["V0921_PARENT_SENTINEL"] = sentinel_parent
        try:
            result = FunctionalValidator().validate(
                workspace_root=tmp_path,
                command=self._env_dump_command(),
                timeout=60,
                env={"V0921_FROZEN_MARKER": "frozen-value"},
            )
        finally:
            del os.environ["V0921_PARENT_SENTINEL"]
        assert result.passed, result.stderr
        child_env = json.loads(result.stdout.strip().splitlines()[-1])
        assert child_env["V0921_PARENT_SENTINEL"] == sentinel_parent
        assert child_env["V0921_FROZEN_MARKER"] == "frozen-value"

    def test_saleor_exact_frozen_env_reaches_subprocess(self, tmp_path: Path) -> None:
        from benchmark.execution.validation import FunctionalValidator

        saleor_env = {
            "DATABASE_URL": "postgres://saleor:saleor@127.0.0.1:5433/saleor",
            "CACHE_URL": "redis://127.0.0.1:6379/0",
            "SECRET_KEY": "ci-test",
            "TZ": "UTC",
        }
        result = FunctionalValidator().validate(
            workspace_root=tmp_path,
            command=self._env_dump_command(),
            timeout=60,
            env=saleor_env,
        )
        assert result.passed, result.stderr
        child_env = json.loads(result.stdout.strip().splitlines()[-1])
        for key, value in saleor_env.items():
            assert child_env[key] == value, key

    def test_empty_env_invents_nothing_and_never_mutates_global_environ(
        self, tmp_path: Path
    ) -> None:
        from benchmark.execution.validation import FunctionalValidator

        before = dict(os.environ)
        result = FunctionalValidator().validate(
            workspace_root=tmp_path,
            command=self._env_dump_command(),
            timeout=60,
            env={},
        )
        after = dict(os.environ)
        assert result.passed, result.stderr
        assert before == after, "FunctionalValidator must not mutate os.environ"
        child_env = json.loads(result.stdout.strip().splitlines()[-1])
        assert "V0921_FROZEN_MARKER" not in child_env

    def test_old_signature_without_env_param_is_gone(self) -> None:
        import inspect

        from benchmark.execution.validation import FunctionalValidator

        params = inspect.signature(FunctionalValidator.validate).parameters
        assert "env" in params, (
            "B2 regression: validate() lost the frozen-env parameter "
            "(the v0.9.20 signature discarded the frozen repository env)"
        )


# ---------------------------------------------------------------------------
# B3 — explicit bounded validation timeout (model --timeout 600 untouched)
# ---------------------------------------------------------------------------


class TestValidationTimeoutContract:
    def test_pipeline_config_accepts_1800(self) -> None:
        from benchmark.execution.pipeline import PipelineConfig

        config = PipelineConfig(
            protocol_version="1.0",
            validation_timeout=1800,
        )
        assert config.validation_timeout == 1800

    @pytest.mark.parametrize("bad", [0, -1])
    def test_pipeline_config_rejects_non_positive(self, bad: int) -> None:
        from benchmark.execution.pipeline import PipelineConfig

        with pytest.raises(ValueError, match="validation_timeout"):
            PipelineConfig(protocol_version="1.0", validation_timeout=bad)

    def test_runner_config_rejects_non_positive(self) -> None:
        from benchmark.execution.runner import RunnerConfig

        with pytest.raises(ValueError, match="validation_timeout"):
            RunnerConfig(
                strategy_name="selective",
                backend_name="backend",
                protocol_version="1.0",
                validation_timeout=-5,
            )

    def test_runner_passes_exact_timeout_and_env_to_validator(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        from benchmark.core.enums import ArtifactType, RunStatus
        from benchmark.core.models import ArtifactRef, Scenario, TokenUsage
        from benchmark.execution import runner as runner_mod
        from benchmark.execution.isolation import IsolationContext
        from benchmark.execution.runner import BenchmarkRunner, RunnerConfig
        from benchmark.execution.validation import FunctionalValidationResult
        from benchmark.repositories.workspace import WorkspacePath
        from benchmark.strategies import MonolithicRegenerationStrategy

        class _FixedTokenBackend:
            token_accounting_mode = "fixture_or_approximate"

            def __init__(self) -> None:
                self._tokens = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                self.call_count = 0

            def count_prompt_tokens(self, prompt: str) -> int:
                return self._tokens.prompt_tokens

            async def generate(self, prompt: str = "", temperature: float = 0.0, max_tokens: int = 4096):
                self.call_count += 1
                from benchmark.core.models import LLMResponse

                return LLMResponse(text=f"value = {self.call_count}", token_usage=self._tokens, finish_reason="stop")

        captured: dict[str, Any] = {}

        class _SpyValidator:
            def validate(self, workspace_root, command, timeout=30, env=None):
                captured["timeout"] = timeout
                captured["env"] = dict(env or {})
                captured["command"] = list(command)
                return FunctionalValidationResult(
                    passed=True, exit_code=0, stdout="", stderr="", duration_seconds=0.01
                )

        monkeypatch.setattr(runner_mod, "FunctionalValidator", _SpyValidator)

        artifact = ArtifactRef(path="src/a.py", artifact_type=ArtifactType.source)
        scenario = Scenario(
            scenario_id="v0921-timeout-probe",
            repository="todo",
            blast_radius="localized",
            requirement_before="before",
            requirement_after="after",
            change_type="modify",
            rationale="test",
            expected_affected_artifacts=(artifact,),
            evaluator_asset=None,
        )

        ws_root = tmp_path / "workspace"
        ws_root.mkdir(parents=True, exist_ok=True)
        snap_base = tmp_path / "snapshots"
        snap_base.mkdir(exist_ok=True)
        active_root = snap_base / "todo" / "rev"
        active_root.mkdir(parents=True, exist_ok=True)
        (ws_root / "src").mkdir()
        (ws_root / "src" / "a.py").write_text("original", encoding="utf-8")
        (active_root / "src").mkdir()
        (active_root / "src" / "a.py").write_text("original", encoding="utf-8")
        iso = IsolationContext(
            workspace=WorkspacePath(root=str(ws_root)),
            snapshot_base=snap_base,
            active_snapshot_root=active_root,
        )
        cfg = RunnerConfig(
            strategy_name="monolithic",
            backend_name="mock",
            protocol_version="1.0",
            timeout_seconds=0,
            enable_regeneration=True,
            validation_command=[sys.executable, "-c", "exit(0)"],
            validation_timeout=1800,
            validation_env={"TZ": "UTC"},
            editable_artifact_paths=("src/a.py",),
            python_executable=sys.executable,
        )
        runner = BenchmarkRunner(
            strategy=MonolithicRegenerationStrategy(),
            backend=_FixedTokenBackend(),  # type: ignore[arg-type]
            isolation=iso,
            config=cfg,
        )
        record = runner.run(scenario)
        assert record.status == RunStatus.succeeded
        assert captured["timeout"] == 1800
        assert captured["env"] == {"TZ": "UTC"}
        assert captured["command"] == [sys.executable, "-c", "exit(0)"]

    def test_notebook_launch_and_resume_pin_exact_flags(self) -> None:
        nb = json.loads((PROJECT_DIR / "notebooks" / "pilot_exec_01.ipynb").read_text(encoding="utf-8"))
        checked = 0
        for cell in nb["cells"]:
            cid = str(cell.get("id", ""))
            if cid not in ("pilot-launch-cell", "pilot-resume-cell"):
                continue
            src = "".join(cell["source"])
            target = "exec_cmd" if cid == "pilot-launch-cell" else "resume_cmd"
            elements = _assigned_list_elements(src, target)
            validation_indices = [
                index
                for index, value in enumerate(elements)
                if isinstance(value, ast.Constant) and value.value == "--validation-python"
            ]
            assert len(validation_indices) == 3, cid
            for index, expected in zip(
                validation_indices,
                (
                    ("todo=", "TODO_PYTHON"),
                    ("djangocms=", "DJANGO_PYTHON"),
                    ("saleor=", "SALEOR_PYTHON"),
                ),
                strict=True,
            ):
                _assert_prefixed_name(elements[index + 1], *expected)

            validation_timeout_indices = [
                index
                for index, value in enumerate(elements)
                if isinstance(value, ast.Constant) and value.value == "--validation-timeout"
            ]
            assert len(validation_timeout_indices) == 1, cid
            _assert_string(elements[validation_timeout_indices[0] + 1], "1800")
            hf_indices = [
                index
                for index, value in enumerate(elements)
                if isinstance(value, ast.Constant) and value.value == "--hf-repo-id"
            ]
            assert len(hf_indices) == 1, cid
            assert validation_timeout_indices[0] < hf_indices[0], cid
            scientific_timeout_indices = [
                index
                for index, value in enumerate(elements)
                if isinstance(value, ast.Constant) and value.value == "--timeout"
            ]
            assert len(scientific_timeout_indices) == 1, cid
            _assert_string(elements[scientific_timeout_indices[0] + 1], "600")
            checked += 1
        assert checked == 2
        dryrun = "".join(next(c for c in nb["cells"] if c.get("id") == "dryrun-cell")["source"])
        assert '"--validation-python"' not in dryrun
        assert '"--validation-timeout"' not in dryrun
