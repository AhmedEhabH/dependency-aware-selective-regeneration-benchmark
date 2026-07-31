from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass
from pathlib import Path

from benchmark.core.models import LLMResponse
from benchmark.core.protocols import LLMBackend
from benchmark.execution.budgets import resolve_completion_allowance
from benchmark.execution.isolation import IsolationContext
from benchmark.selection.planner import RegenerationPlan


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
You are regenerating a source file for a software project.

Requirement change:
{requirement_delta}

Artifact path: {artifact_path}

Current content:
```{language_hint}
{current_content}
```

Generate the complete replacement file content. \
Return only the file content, without any explanation or markdown fences.
"""

REPAIR_CONTEXT_PROMPT_TEMPLATE = """\

Previous functional validation attempt failed.

Exit code: {exit_code}

Validation stdout:
{stdout}

Validation stderr:
{stderr}

Fix the issues above so that the functional validation passes. \
Return the complete replacement file content without explanation or markdown fences.
"""


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
                current_content = src_path.read_text(encoding="utf-8")
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

            prompt = BUILT_IN_PROMPT_TEMPLATE.format(
                requirement_delta=requirement_delta or "Update the artifact to match the new requirements.",
                artifact_path=artifact.path,
                language_hint=_language_hint(artifact.path),
                current_content=current_content,
            )
            if repair_context:
                prompt += repair_context

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
                    break
                local_remaining = max(0, local_remaining - usage.total_tokens)

            output_text = response.text

            stripped = output_text.strip()
            if not stripped:
                failures.append(f"Empty generation for {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            if stripped.startswith("```") or stripped.endswith("```"):
                failures.append(f"Markdown-fenced output rejected for {artifact.path}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content=output_text,
                        status="rejected",
                    )
                )
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

            target_path = Path(workspace_root) / artifact.path.lstrip("/")
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(output_text, encoding="utf-8")
            except (OSError, PermissionError) as e:
                failures.append(f"Cannot write {artifact.path}: {e}")
                generated.append(
                    GeneratedArtifact(
                        path=artifact.path,
                        content="",
                        status="rejected",
                    )
                )
                continue

            generated.append(
                GeneratedArtifact(
                    path=artifact.path,
                    content=output_text,
                    status="generated",
                )
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
