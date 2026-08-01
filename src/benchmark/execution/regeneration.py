from __future__ import annotations

import asyncio
import ast
import contextlib
import hashlib
import json
import logging
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from benchmark.core.models import LLMResponse, RegenerationScenarioContext
from benchmark.core.protocols import LLMBackend
from benchmark.execution.budgets import resolve_completion_allowance
from benchmark.execution.isolation import IsolationContext
from benchmark.llm.output_normalization import normalize_single_payload
from benchmark.selection.planner import RegenerationPlan

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GeneratedArtifact:
    path: str
    content: str
    status: str  # "generated", "rejected", "skipped"


@dataclass(frozen=True)
class RegenerationExecutionResult:
    artifacts: tuple[GeneratedArtifact, ...] = ()
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model_calls: int = 0
    duration_seconds: float = 0.0
    failures: tuple[str, ...] = ()


BUILT_IN_PROMPT_TEMPLATE = """\
You are regenerating exactly one source artifact in an existing software project.

Requirement change:
{requirement_delta}

Artifact path: {artifact_path}

Current content:
```{language_hint}
{current_content}
```

Output contract:
- Make the smallest complete change needed in this artifact.
- Preserve every unrelated import, class, method, field, permission, route, and behavior.
- Do not add a new third-party dependency unless it is already imported by the current project.
- Do not move or duplicate models, serializers, views, permissions, or routes across modules.
- If this artifact does not require a change, return the current content byte-identically.
- Return only the complete replacement file content, without explanation or markdown fences.
"""

REPAIR_CONTEXT_PROMPT_TEMPLATE = """\

Previous attempt failed validation.

Failed stage: {stage}
Exit code: {exit_code}
Root cause: {root_cause}

Generation/scope failures from the previous attempt:
{generation_failures}

Validation stdout excerpt (head + tail):
{stdout}

Validation stderr excerpt (head + tail; root exception retained):
{stderr}

Correct the existing artifact using the evidence above. Do not repeat the same
invalid output. Return the complete replacement file content without explanation
or markdown fences.
"""

SCENARIO_CONTEXT_PROMPT_TEMPLATE = """\
Frozen scenario contract ({scenario_id}):
Acceptance criteria (must all hold in the final repository):
{acceptance_criteria}

Architecture constraints (must never be violated):
{architecture_constraints}

Scope contract for {artifact_path}:
- Expected action for this file: {expected_action}
- File-specific instruction: {artifact_instruction}
- If the expected action is "preserve", return the current file content byte-identically.
- Preserve unrelated behavior and unrelated files exactly as they are.
- Do not re-declare models, serializers, views, or classes that belong in other modules.
"""


def build_generation_prompt(
    requirement_delta: str,
    artifact_path: str,
    language_hint: str,
    current_content: str,
    scenario_context: RegenerationScenarioContext | None = None,
    expected_action: str | None = None,
    repair_context: str | None = None,
) -> str:
    """Build the full regeneration prompt for an artifact.

    When a frozen ``RegenerationScenarioContext`` is supplied, the prompt
    includes the repository-wide acceptance criteria, architecture
    constraints, the file-specific expected action, and the preserve-only /
    no-redeclare scope contract.
    """
    prompt = BUILT_IN_PROMPT_TEMPLATE.format(
        requirement_delta=requirement_delta or "Update the artifact to match the new requirements.",
        artifact_path=artifact_path,
        language_hint=language_hint,
        current_content=current_content,
    )
    prompt += (
        "\nArtifact responsibility:\n"
        + _artifact_role_guidance(artifact_path)
        + "\n"
    )
    if scenario_context is not None:
        ea = expected_action or scenario_context.expected_action_for(artifact_path)
        prompt += SCENARIO_CONTEXT_PROMPT_TEMPLATE.format(
            scenario_id=scenario_context.scenario_id,
            acceptance_criteria=(
                "\n".join(f"- {c}" for c in scenario_context.acceptance_criteria)
                or "- (none declared)"
            ),
            architecture_constraints=(
                "\n".join(f"- {c}" for c in scenario_context.architecture_constraints)
                or "- (none declared)"
            ),
            artifact_path=artifact_path,
            expected_action=ea,
            artifact_instruction=scenario_context.instruction_for(artifact_path),
        )
    if repair_context:
        prompt += repair_context
    return prompt


def _artifact_role_guidance(path: str) -> str:
    """Return generic module-role guidance without scenario-specific inference."""
    name = Path(path).name
    role_map = {
        "models.py": (
            "Define or edit data models and model-local enums only. Do not define "
            "serializers, API views, permissions, or URL routes here. For string "
            "choices, size max_length to hold the longest stored value."
        ),
        "serializers.py": (
            "Define or edit serializers only. Reuse model classes from the models "
            "module and expose model-defined choices; do not re-declare model enums "
            "or define models, viewsets, permissions, or routes here."
        ),
        "views.py": (
            "Define or edit views/viewsets only. Reuse imported models and serializers; "
            "do not define database models or serializers here. Preserve existing "
            "authentication, permissions, and unrelated view behavior unless the "
            "requirement explicitly changes them."
        ),
        "permissions.py": (
            "Define or edit permission classes only. Do not define models, serializers, "
            "views, or routes here."
        ),
        "urls.py": (
            "Define or edit URL/router registration only. Do not define models, "
            "serializers, views, or permissions here."
        ),
    }
    return role_map.get(
        name,
        "Keep the artifact's existing responsibility and module boundaries unchanged.",
    )


def _output_evidence(text: str, *, excerpt_limit: int = 6000) -> str:
    """Persist reproducible rejected-output evidence without unbounded records."""
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    if len(text) <= excerpt_limit:
        excerpt = text
        truncated = False
    else:
        half = excerpt_limit // 2
        omitted = len(text) - excerpt_limit
        excerpt = (
            text[:half]
            + f"\n... [{omitted} chars omitted from rejected output] ...\n"
            + text[-half:]
        )
        truncated = True
    return (
        f"response_sha256={digest} response_chars={len(text)} "
        f"response_truncated={str(truncated).lower()} "
        f"response_excerpt_json={json.dumps(excerpt, ensure_ascii=False)}"
    )


_DISTRIBUTION_IMPORT_ROOTS = {
    "django": "django",
    "djangorestframework": "rest_framework",
    "pytest": "pytest",
    "pytestdjango": "pytest_django",
}


def _dotted_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def _import_roots(tree: ast.AST) -> set[str]:
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _declared_import_roots(workspace_root: str | Path) -> set[str]:
    root = Path(workspace_root)
    allowed = set(sys.stdlib_module_names)
    for child in root.iterdir() if root.is_dir() else ():
        if child.is_dir() and (child / "__init__.py").is_file():
            allowed.add(child.name)
        elif child.is_file() and child.suffix == ".py":
            allowed.add(child.stem)
    requirements = root / "requirements.txt"
    if requirements.is_file():
        for raw in requirements.read_text(encoding="utf-8", errors="replace").splitlines():
            item = raw.split("#", 1)[0].split(";", 1)[0].strip()
            if not item:
                continue
            distribution = re.split(r"[<>=!~\[\s]", item, maxsplit=1)[0]
            normalized = distribution.lower().replace("-", "").replace("_", "")
            allowed.add(
                _DISTRIBUTION_IMPORT_ROOTS.get(
                    normalized,
                    distribution.replace("-", "_"),
                )
            )
    return allowed


def _class_base_names(tree: ast.Module) -> list[tuple[str, tuple[str, ...]]]:
    values: list[tuple[str, tuple[str, ...]]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            values.append((node.name, tuple(_dotted_name(base) for base in node.bases)))
    return values


def _choice_max_length_failures(tree: ast.Module) -> list[str]:
    failures: list[str] = []
    for owner in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        enum_values: dict[str, list[str]] = {}
        for nested in (node for node in owner.body if isinstance(node, ast.ClassDef)):
            values: list[str] = []
            for statement in nested.body:
                if not isinstance(statement, ast.Assign) or not isinstance(
                    statement.value, ast.Tuple
                ):
                    continue
                if not statement.value.elts or not isinstance(
                    statement.value.elts[0], ast.Constant
                ):
                    continue
                stored = statement.value.elts[0].value
                if isinstance(stored, str):
                    values.append(stored)
            if values:
                enum_values[nested.name] = values

        for statement in owner.body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            value = statement.value
            if not isinstance(value, ast.Call) or not _dotted_name(value.func).endswith(
                ".CharField"
            ):
                continue
            keywords = {item.arg: item.value for item in value.keywords if item.arg}
            choices = keywords.get("choices")
            max_length = keywords.get("max_length")
            if not isinstance(choices, ast.Attribute) or choices.attr != "choices":
                continue
            enum_name = _dotted_name(choices.value)
            values = enum_values.get(enum_name)
            if not values or not isinstance(max_length, ast.Constant) or not isinstance(
                max_length.value, int
            ):
                continue
            required = max(len(item) for item in values)
            if max_length.value < required:
                failures.append(
                    "choice_max_length_too_small: "
                    f"{owner.name}.{enum_name} needs >= {required}, got {max_length.value}"
                )
    return failures


def _python_artifact_contract_failures(
    *,
    artifact_path: str,
    output_text: str,
    current_content: str,
    workspace_root: str | Path,
) -> tuple[str, ...]:
    """Apply small generic guards for real model outputs before writing them."""
    try:
        output_tree = ast.parse(output_text, filename=artifact_path)
    except SyntaxError as exc:
        return (
            f"python_syntax_error: line={exc.lineno} offset={exc.offset} msg={exc.msg}",
        )
    try:
        current_tree = ast.parse(current_content, filename=artifact_path)
    except SyntaxError:
        current_tree = ast.parse("")

    failures: list[str] = []
    new_imports = _import_roots(output_tree) - _import_roots(current_tree)
    undeclared = sorted(new_imports - _declared_import_roots(workspace_root))
    if undeclared:
        failures.append("undeclared_dependency: " + ", ".join(undeclared))

    role = Path(artifact_path).name
    class_bases = _class_base_names(output_tree)
    forbidden_prefixes: dict[str, tuple[str, ...]] = {
        "models.py": ("serializers.", "viewsets.", "permissions.", "APIView"),
        "serializers.py": ("models.Model", "models.TextChoices", "viewsets.", "APIView"),
        "views.py": ("models.Model", "models.TextChoices", "serializers."),
        "permissions.py": ("models.", "serializers.", "viewsets.", "APIView"),
        "urls.py": ("models.", "serializers.", "viewsets.", "APIView"),
    }
    prefixes = forbidden_prefixes.get(role, ())
    for class_name, bases in class_bases:
        for base in bases:
            if any(base == prefix or base.startswith(prefix) for prefix in prefixes):
                failures.append(
                    f"module_role_violation: {class_name} cannot inherit {base} in {role}"
                )
    if role == "serializers.py":
        for class_name, _bases in class_bases:
            if class_name.endswith("ViewSet"):
                failures.append(
                    f"module_role_violation: viewset {class_name} belongs in views.py"
                )

    if role == "models.py":
        failures.extend(_choice_max_length_failures(output_tree))
    return tuple(dict.fromkeys(failures))


def _language_hint(path: str) -> str:
    suffix = Path(path).suffix
    hint_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".rs": "rust",
        ".go": "go",
    }
    return hint_map.get(suffix, "text")


def _is_path_traversal(target: str, workspace_root: str) -> bool:
    resolved = Path(workspace_root).resolve()
    target_path = (resolved / target).resolve()
    try:
        target_path.relative_to(resolved)
    except ValueError:
        return True
    return ".." in Path(target).parts


class SharedRegenerationExecutor:
    def __init__(self, backend: LLMBackend) -> None:
        self._backend = backend

    def execute(
        self,
        plan: RegenerationPlan,
        isolation: IsolationContext,
        requirement_delta: str = "",
        repair_context: str | None = None,
        *,
        scenario_context: RegenerationScenarioContext | None = None,
        max_completion_tokens_per_call: int = 4096,
        remaining_total_workflow_tokens: int | None = None,
    ) -> RegenerationExecutionResult:
        old_loop: asyncio.AbstractEventLoop | None = None
        with contextlib.suppress(RuntimeError):
            old_loop = asyncio.get_event_loop()
        try:
            return asyncio.run(
                self._execute_async(
                    plan, isolation, requirement_delta, repair_context,
                    scenario_context=scenario_context,
                    max_completion_tokens_per_call=max_completion_tokens_per_call,
                    remaining_total_workflow_tokens=remaining_total_workflow_tokens,
                )
            )
        finally:
            if old_loop is not None and not old_loop.is_closed():
                asyncio.set_event_loop(old_loop)
            elif old_loop is None:
                with contextlib.suppress(RuntimeError):
                    asyncio.set_event_loop(asyncio.new_event_loop())

    async def _execute_async(
        self,
        plan: RegenerationPlan,
        isolation: IsolationContext,
        requirement_delta: str,
        repair_context: str | None = None,
        *,
        scenario_context: RegenerationScenarioContext | None = None,
        max_completion_tokens_per_call: int = 4096,
        remaining_total_workflow_tokens: int | None = None,
    ) -> RegenerationExecutionResult:
        workspace_root = str(isolation.workspace.root)
        start_time = time.monotonic()

        generated: list[GeneratedArtifact] = []
        total_prompt = 0
        total_completion = 0
        calls = 0
        failures: list[str] = []
        local_remaining = remaining_total_workflow_tokens
        has_limit = remaining_total_workflow_tokens is not None

        for artifact in plan.ordered_artifacts:
            action = plan.actions.get(artifact.path)
            if action is None:
                continue
            action_str = str(action)

            if action_str == "human_review":
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="skipped",
                    )
                )
                continue

            if action_str == "preserve" or action_str == "validate_only":
                continue

            if _is_path_traversal(artifact.path, workspace_root):
                failures.append(f"Path traversal rejected: {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            src_path = Path(workspace_root) / artifact.path.lstrip("/")
            try:
                current_bytes = src_path.read_bytes()
                current_content = current_bytes.decode("utf-8")
            except FileNotFoundError:
                failures.append(f"Source file not found in workspace: {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue
            except (OSError, UnicodeDecodeError) as e:
                failures.append(f"Cannot read {artifact.path}: {e}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            prompt = build_generation_prompt(
                requirement_delta=requirement_delta,
                artifact_path=artifact.path,
                language_hint=_language_hint(artifact.path),
                current_content=current_content,
                scenario_context=scenario_context,
                repair_context=repair_context,
            )

            prompt_estimate = getattr(
                self._backend, "count_prompt_tokens", lambda p: max(1, len(p) // 4)
            )(prompt)

            allowance = resolve_completion_allowance(
                max_completion_tokens_per_call=max_completion_tokens_per_call,
                remaining_total_workflow_tokens=local_remaining,
                prompt_tokens=prompt_estimate,
            )
            if allowance <= 0:
                failures.append(f"Token budget exhausted before {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            artifact_start = time.monotonic()
            logger.info("REGEN_ARTIFACT_START path=%s", artifact.path)
            try:
                response: LLMResponse = await self._backend.generate(prompt=prompt, max_tokens=allowance)
            except Exception as e:
                failures.append(f"LLM backend error for {artifact.path}: {e}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            calls += 1
            usage = response.token_usage
            total_prompt += usage.prompt_tokens
            total_completion += usage.completion_tokens

            if has_limit and local_remaining is not None:
                if usage.completion_tokens > allowance:
                    failures.append(
                        f"Backend overrun for {artifact.path}: "
                        f"completion_tokens {usage.completion_tokens} > allowance {allowance}"
                    )
                    generated.append(
                        GeneratedArtifact(
                            path=artifact.path,
                            content="",
                            status="rejected",
                        )
                    )
                    logger.info(
                        "REGEN_ARTIFACT_END path=%s status=rejected elapsed=%.3f",
                        artifact.path, time.monotonic() - artifact_start,
                    )
                    break
                if local_remaining > 0 and usage.total_tokens > local_remaining:
                    failures.append(
                        f"Backend total overrun for {artifact.path}: "
                        f"total_tokens {usage.total_tokens} > remaining {local_remaining}"
                    )
                    generated.append(
                        GeneratedArtifact(
                            path=artifact.path,
                            content="",
                            status="rejected",
                        )
                    )
                    logger.info(
                        "REGEN_ARTIFACT_END path=%s status=rejected elapsed=%.3f",
                        artifact.path, time.monotonic() - artifact_start,
                    )
                    break
                local_remaining = max(0, local_remaining - usage.total_tokens)

            output_text = response.text

            normalized_body, normalization_mode = normalize_single_payload(output_text)
            if normalized_body is None:
                if normalization_mode == "empty":
                    message = f"Empty generation for {artifact.path}"
                else:
                    message = f"Output rejected for {artifact.path}: {normalization_mode}"
                failures.append(message)
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content=output_text,
                        status="rejected",
                    )
                )
                logger.info(
                    "REGEN_ARTIFACT_END path=%s status=rejected elapsed=%.3f",
                    artifact.path, time.monotonic() - artifact_start,
                )
                continue
            output_text = normalized_body
            if normalization_mode == "single_fence_stripped":
                logger.info("MODEL_OUTPUT_NORMALIZED path=%s mode=single_fence_stripped", artifact.path)

            if _is_path_traversal(artifact.path, workspace_root):
                failures.append(f"Path traversal rejected: {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                logger.info(
                    "REGEN_ARTIFACT_END path=%s status=rejected elapsed=%.3f",
                    artifact.path, time.monotonic() - artifact_start,
                )
                continue

            if scenario_context is not None and scenario_context.expected_actions:
                expected = scenario_context.expected_action_for(artifact.path)
                if expected == "preserve" and output_text.encode("utf-8") != current_bytes:
                    failures.append(
                        f"out_of_scope_change: {artifact.path} expected action 'preserve' "
                        "but generated output differs from the current file; "
                        f"{_output_evidence(output_text)}"
                    )
                    generated.append(
                        GeneratedArtifact(
                            path=artifact.path,
                            content=output_text,
                            status="rejected",
                        )
                    )
                    logger.info(
                        "REGEN_ARTIFACT_END path=%s status=rejected reason=out_of_scope_change elapsed=%.3f",
                        artifact.path, time.monotonic() - artifact_start,
                    )
                    continue

            if (
                scenario_context is not None
                and scenario_context.expected_actions
                and artifact.path.endswith(".py")
            ):
                contract_failures = _python_artifact_contract_failures(
                    artifact_path=artifact.path,
                    output_text=output_text,
                    current_content=current_content,
                    workspace_root=workspace_root,
                )
                if contract_failures:
                    for contract_failure in contract_failures:
                        failures.append(
                            f"artifact_contract_violation: {artifact.path}: "
                            f"{contract_failure}; {_output_evidence(output_text)}"
                        )
                    generated.append(
                        GeneratedArtifact(
                            path=artifact.path,
                            content=output_text,
                            status="rejected",
                        )
                    )
                    logger.info(
                        "REGEN_ARTIFACT_END path=%s status=rejected "
                        "reason=artifact_contract_violation elapsed=%.3f",
                        artifact.path,
                        time.monotonic() - artifact_start,
                    )
                    continue

            target_path = Path(workspace_root) / artifact.path.lstrip("/")
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(output_text, encoding="utf-8", newline="")
            except (OSError, PermissionError) as e:
                failures.append(f"Cannot write {artifact.path}: {e}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                logger.info(
                    "REGEN_ARTIFACT_END path=%s status=rejected elapsed=%.3f",
                    artifact.path, time.monotonic() - artifact_start,
                )
                continue

            generated.append(
                GeneratedArtifact(
                    path=artifact.path,
                    content=output_text,
                    status="generated",
                )
            )
            logger.info(
                "REGEN_ARTIFACT_END path=%s status=generated elapsed=%.3f",
                artifact.path, time.monotonic() - artifact_start,
            )

        duration = time.monotonic() - start_time
        return RegenerationExecutionResult(
            artifacts=tuple(generated),
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            model_calls=calls,
            duration_seconds=duration,
            failures=tuple(failures),
        )
