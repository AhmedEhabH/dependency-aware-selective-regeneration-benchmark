from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass
from pathlib import Path

from benchmark.core.models import LLMResponse
from benchmark.core.protocols import LLMBackend
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
    ) -> RegenerationExecutionResult:
        old_loop: asyncio.AbstractEventLoop | None = None
        with contextlib.suppress(RuntimeError):
            old_loop = asyncio.get_event_loop()
        try:
            return asyncio.run(
                self._execute_async(plan, isolation, requirement_delta)
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
    ) -> RegenerationExecutionResult:
        workspace_root = str(isolation.workspace.root)
        start_time = time.monotonic()

        generated: list[GeneratedArtifact] = []
        total_prompt = 0
        total_completion = 0
        calls = 0
        failures: list[str] = []

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

            # Reject path traversal before any file operation
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

            # Read current content from isolated workspace
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

            try:
                response: LLMResponse = await self._backend.generate(prompt=prompt)
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
            total_prompt += response.token_usage.prompt_tokens
            total_completion += response.token_usage.completion_tokens

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

            # Reject Markdown-fenced output — contract requires raw file content
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

            # Write generated content inside isolated workspace only
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
