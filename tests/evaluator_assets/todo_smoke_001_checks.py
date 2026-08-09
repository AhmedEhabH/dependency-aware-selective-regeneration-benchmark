import io
import json
import os
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def _workspace_from_argv() -> Path:
    if len(sys.argv) != 2:
        raise ValueError("expected exactly one workspace argument")
    ws = Path(sys.argv[1])
    if not ws.is_dir():
        raise ValueError("workspace not found")
    if not (ws / "manage.py").exists():
        raise ValueError("manage.py not found in workspace")
    if not (ws / "config" / "settings.py").exists():
        raise ValueError("config/settings.py not found")
    if not (ws / "todo").is_dir():
        raise ValueError("todo/ directory not found")
    return ws


def _record_check(name: str, checks: list[str], errors: list[str], function: Callable[[], None]) -> None:
    try:
        function()
    except Exception as exc:
        errors.append(f"{name}: {type(exc).__name__}: {exc}")
    else:
        checks.append(name)


def main() -> int:
    payload = {"passed": False, "checks": [], "error": ""}
    captured = io.StringIO()
    runner = None
    old_config = None
    environment_ready = False
    teardown_errors: list[str] = []

    try:
        workspace = _workspace_from_argv()
        sys.path.insert(0, str(workspace))
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

        with redirect_stdout(captured), redirect_stderr(captured):
            import django
            django.setup()

            from django.test.runner import DiscoverRunner
            runner = DiscoverRunner(verbosity=0, interactive=False)
            runner.setup_test_environment()
            environment_ready = True
            old_config = runner.setup_databases()

            from django.contrib.auth.models import User
            from django.db import models as db_models
            from rest_framework.test import APIClient
            from todo.models import Project, Task
            from todo.serializers import TaskSerializer

            user = User.objects.create_user(username="tester", password="pass")
            project = Project.objects.create(name="Smoke001Project")
            client = APIClient()
            client.force_authenticate(user=user)

            checks: list[str] = []
            errors: list[str] = []

            def _task_priority_enum() -> None:
                assert hasattr(Task, "Priority"), "Priority enum missing on Task"
                assert issubclass(Task.Priority, db_models.TextChoices), "Priority is not TextChoices"
                values = [v.value for v in Task.Priority]
                assert values == ["HIGH", "MEDIUM", "LOW"], f"Expected HIGH/MEDIUM/LOW, got {values}"
                assert len(Task.Priority) == 3, f"Expected 3 choices, got {len(Task.Priority)}"

            def _task_priority_field() -> None:
                field = Task._meta.get_field("priority")
                assert field is not None, "priority field not found"
                choice_values = {c[0] for c in field.choices}
                assert choice_values == {"HIGH", "MEDIUM", "LOW"}, f"Unexpected choices: {choice_values}"
                default = field.default() if callable(field.default) else field.default
                assert default == "MEDIUM", f"Expected default MEDIUM, got {default}"

            def _task_priority_default() -> None:
                task = Task.objects.create(title="No Priority Given", project=project)
                task.refresh_from_db()
                assert task.priority == "MEDIUM", f"Expected MEDIUM, got {task.priority}"

            def _task_priority_valid_values() -> None:
                for val in ("HIGH", "MEDIUM", "LOW"):
                    data = {"title": f"Priority {val}", "project": project.pk, "priority": val}
                    resp = client.post("/api/tasks/", data)
                    assert resp.status_code == 201, f"POST {val} returned {resp.status_code}: {resp.data}"
                    assert resp.data["priority"] == val, f"Expected {val}, got {resp.data['priority']}"
                    pk = resp.data["id"]
                    fetch = client.get(f"/api/tasks/{pk}/")
                    assert fetch.data["priority"] == val, f"Fetched priority mismatch for {val}"

            def _task_serializer_priority() -> None:
                s = TaskSerializer()
                assert "priority" in s.fields, "priority not in serializer fields"
                assert not s.fields["priority"].read_only, "priority field is read-only"
                choices = s.fields["priority"].choices
                assert set(choices.keys()) == {"HIGH", "MEDIUM", "LOW"}, (
                    f"Unexpected serializer choices: {list(choices.keys())}"
                )

            def _task_priority_invalid_rejected() -> None:
                resp = client.post("/api/tasks/", {"title": "Bad", "project": project.pk, "priority": "URGENT"})
                assert resp.status_code == 400, f"Expected 400 for URGENT, got {resp.status_code}"

            def _task_priority_filter() -> None:
                Task.objects.create(title="HighTask", project=project, priority="HIGH")
                Task.objects.create(title="MedTask", project=project, priority="MEDIUM")
                Task.objects.create(title="LowTask", project=project, priority="LOW")
                resp = client.get("/api/tasks/?priority=HIGH")
                assert resp.status_code == 200, f"Filter list returned {resp.status_code}"
                results = resp.data.get("results", [])
                ids = [r["id"] for r in results]
                high = Task.objects.get(title="HighTask")
                med = Task.objects.get(title="MedTask")
                low = Task.objects.get(title="LowTask")
                assert high.pk in ids, "HIGH task missing from filtered list"
                assert med.pk not in ids, "MEDIUM task present in HIGH filtered list"
                assert low.pk not in ids, "LOW task present in HIGH filtered list"

            def _task_unfiltered_list() -> None:
                t1 = Task.objects.create(title="UnfA", project=project)
                t2 = Task.objects.create(title="UnfB", project=project)
                t3 = Task.objects.create(title="UnfC", project=project)
                resp = client.get("/api/tasks/")
                assert resp.status_code == 200, f"List returned {resp.status_code}"
                results = resp.data.get("results", [])
                ids = [r["id"] for r in results]
                assert t1.pk in ids, "First unfiltered task missing"
                assert t2.pk in ids, "Second unfiltered task missing"
                assert t3.pk in ids, "Third unfiltered task missing"

            def _baseline_task_fields() -> None:
                from todo.models import Tag
                tag = Tag.objects.create(name="base-tag", color="#abc")
                task = Task.objects.create(
                    title="Baseline Task",
                    description="Desc",
                    status=Task.Status.IN_PROGRESS,
                    owner=user,
                    project=project,
                )
                task.tags.add(tag)
                task.refresh_from_db()
                assert task.title == "Baseline Task"
                assert task.description == "Desc"
                assert task.status == "IN_PROGRESS"
                assert task.owner == user
                assert task.project == project
                assert tag in task.tags.all()
                assert task.created_at is not None
                assert task.updated_at is not None

            def _project_and_tag_regression() -> None:
                from todo.models import Tag, Project
                resp = client.post("/api/projects/", {"name": "RegrProject"})
                assert resp.status_code == 201, f"Project create failed: {resp.status_code}"
                tag = Tag.objects.create(name="regr-tag", color="#fff")
                assert client.get(f"/api/tags/{tag.pk}/").status_code == 200
                assert client.get(f"/api/projects/{resp.data['id']}/").status_code == 200
                dup = client.post("/api/tags/", {"name": "regr-tag", "color": "#000"})
                assert dup.status_code == 400, f"Duplicate tag returned {dup.status_code}"
                proj = Project.objects.get(pk=resp.data["id"])
                assert proj.name == "RegrProject"
                assert Project._meta.get_field("name").max_length == 200
                assert Project._meta.get_field("description").blank is True
                assert Tag._meta.get_field("name").max_length == 100 and Tag._meta.get_field("name").unique is True
                assert Tag._meta.get_field("color").max_length == 7
                from todo.serializers import ProjectSerializer, TagSerializer
                ps = ProjectSerializer()
                assert set(ps.fields.keys()) == {"id", "name", "description"}
                ts = TagSerializer()
                assert set(ts.fields.keys()) == {"id", "name", "color"}

            _record_check("task_priority_enum", checks, errors, _task_priority_enum)
            _record_check("task_priority_field", checks, errors, _task_priority_field)
            _record_check("task_priority_default", checks, errors, _task_priority_default)
            _record_check("task_priority_valid_values", checks, errors, _task_priority_valid_values)
            _record_check("task_serializer_priority", checks, errors, _task_serializer_priority)
            _record_check("task_priority_invalid_rejected", checks, errors, _task_priority_invalid_rejected)
            _record_check("task_priority_filter", checks, errors, _task_priority_filter)
            _record_check("task_unfiltered_list", checks, errors, _task_unfiltered_list)
            _record_check("baseline_task_fields", checks, errors, _baseline_task_fields)
            _record_check("project_and_tag_regression", checks, errors, _project_and_tag_regression)

        payload = {
            "passed": not errors,
            "checks": checks,
            "error": "; ".join(errors),
        }
    except Exception as exc:
        captured_text = captured.getvalue()[-1000:]
        detail = f"{type(exc).__name__}: {exc}"
        if captured_text:
            detail += f" | captured: {captured_text}"
        payload = {
            "passed": False,
            "checks": payload.get("checks", []),
            "error": detail,
        }
    finally:
        if runner is not None:
            with redirect_stdout(captured), redirect_stderr(captured):
                try:
                    if old_config is not None:
                        runner.teardown_databases(old_config)
                except Exception as exc:
                    teardown_errors.append(f"teardown_databases: {type(exc).__name__}: {exc}")
                try:
                    if environment_ready:
                        runner.teardown_test_environment()
                except Exception as exc:
                    teardown_errors.append(f"teardown_test_environment: {type(exc).__name__}: {exc}")

        if teardown_errors:
            payload["passed"] = False
            if payload["error"]:
                payload["error"] += "; " + "; ".join(teardown_errors)
            else:
                payload["error"] = "; ".join(teardown_errors)

    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
