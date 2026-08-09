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
            from rest_framework.test import APIClient
            from todo.models import Project, Task

            user = User.objects.create_user(username="tester", password="pass")
            project = Project.objects.create(name="Smoke002Project")
            client = APIClient()
            client.force_authenticate(user=user)

            checks: list[str] = []
            errors: list[str] = []

            def _soft_delete_retains_row() -> None:
                task = Task._base_manager.create(owner=user, title="RetainRow", project=project)
                pk = task.pk
                resp = client.delete(f"/api/tasks/{pk}/")
                assert resp.status_code in (200, 204), f"Delete returned {resp.status_code}"
                exists = Task._base_manager.filter(pk=pk).exists()
                assert exists, "Row was hard-deleted from database"

            def _soft_delete_sets_timestamp() -> None:
                task = Task._base_manager.create(owner=user, title="TimestampCheck", project=project)
                pk = task.pk
                client.delete(f"/api/tasks/{pk}/")
                deleted = Task._base_manager.get(pk=pk)
                assert deleted.deleted_at is not None, "deleted_at was not set"

            def _default_manager_excludes_deleted() -> None:
                task = Task._base_manager.create(owner=user, title="DefaultExclude", project=project)
                pk = task.pk
                client.delete(f"/api/tasks/{pk}/")
                qs = Task.objects.filter(pk=pk)
                assert qs.count() == 0, "Default manager returned the deleted task"

            def _normal_list_excludes_deleted() -> None:
                target = Task._base_manager.create(owner=user, title="NormalExclude", project=project)
                active = Task.objects.create(owner=user, title="ActiveControl", project=project)
                client.delete(f"/api/tasks/{target.pk}/")
                resp = client.get("/api/tasks/")
                assert resp.status_code == 200
                ids = [r["id"] for r in resp.data.get("results", [])]
                assert target.pk not in ids, "Deleted task appears in normal list"
                assert active.pk in ids, "Active task missing from normal list"

            def _deleted_detail_is_404() -> None:
                task = Task._base_manager.create(owner=user, title="Detail404", project=project)
                client.delete(f"/api/tasks/{task.pk}/")
                resp = client.get(f"/api/tasks/{task.pk}/")
                assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

            def _deleted_action_lists_deleted() -> None:
                target = Task._base_manager.create(owner=user, title="DeletedActionTarget", project=project)
                active = Task.objects.create(owner=user, title="DeletedActionControl", project=project)
                client.delete(f"/api/tasks/{target.pk}/")
                resp = client.get("/api/tasks/deleted/")
                assert resp.status_code == 200
                ids = [r["id"] for r in resp.data.get("results", [])]
                assert target.pk in ids, "Deleted task missing from /deleted/ endpoint"
                assert active.pk not in ids, "Active task present in /deleted/ endpoint"

            def _restore_action_restores() -> None:
                task = Task._base_manager.create(owner=user, title="RestoreTest", project=project)
                pk = task.pk
                client.delete(f"/api/tasks/{pk}/")
                restore_resp = client.post(f"/api/tasks/{pk}/restore/")
                assert restore_resp.status_code == 200, f"Restore returned {restore_resp.status_code}"
                restored = Task._base_manager.get(pk=pk)
                assert restored.deleted_at is None, "deleted_at not cleared after restore"
                normal_resp = client.get("/api/tasks/")
                normal_ids = [r["id"] for r in normal_resp.data.get("results", [])]
                assert pk in normal_ids, "Restored task missing from normal list"
                detail_resp = client.get(f"/api/tasks/{pk}/")
                assert detail_resp.status_code == 200, f"Detail after restore returned {detail_resp.status_code}"

            def _soft_deleted_data_preserved() -> None:
                from todo.models import Tag
                tag = Tag.objects.create(name="preserved-tag", color="#abc")
                task = Task._base_manager.create(
                    owner=user,
                    title="PreservedTitle",
                    description="PreservedDesc",
                    status="IN_PROGRESS",
                    project=project,
                )
                task.tags.add(tag)
                pk = task.pk
                client.delete(f"/api/tasks/{pk}/")
                restore_resp = client.post(f"/api/tasks/{pk}/restore/")
                assert restore_resp.status_code == 200
                restored = Task._base_manager.get(pk=pk)
                assert restored.title == "PreservedTitle", f"Expected PreservedTitle, got {restored.title}"
                assert restored.description == "PreservedDesc", f"Expected PreservedDesc, got {restored.description}"
                assert restored.status == "IN_PROGRESS", f"Expected IN_PROGRESS, got {restored.status}"
                assert restored.project == project, "Project reference lost"
                assert tag in restored.tags.all(), "Tags not preserved after restore"

            def _project_and_tag_regression() -> None:
                from todo.models import Project, Tag
                proj_resp = client.post("/api/projects/", {"name": "Smoke002Proj"})
                assert proj_resp.status_code == 201, f"Project create returned {proj_resp.status_code}"
                proj = Project.objects.get(pk=proj_resp.data["id"])
                proj_detail = client.get(f"/api/projects/{proj.pk}/")
                assert proj_detail.status_code == 200
                assert proj_detail.data["name"] == "Smoke002Proj"
                tag_resp = client.post("/api/tags/", {"name": "smoke002-tag", "color": "#fff"})
                assert tag_resp.status_code == 201, f"Tag create returned {tag_resp.status_code}"
                tag_detail = client.get(f"/api/tags/{tag_resp.data['id']}/")
                assert tag_detail.status_code == 200
                assert tag_detail.data["name"] == "smoke002-tag"
                dup_resp = client.post("/api/tags/", {"name": "smoke002-tag", "color": "#000"})
                assert dup_resp.status_code == 400, f"Duplicate tag returned {dup_resp.status_code}"
                assert Project._meta.get_field("name").max_length == 200
                assert Project._meta.get_field("description").blank is True
                assert Tag._meta.get_field("name").max_length == 100 and Tag._meta.get_field("name").unique is True
                assert Tag._meta.get_field("color").max_length == 7
                from todo.serializers import ProjectSerializer, TagSerializer
                assert set(ProjectSerializer().fields.keys()) == {"id", "name", "description"}
                assert set(TagSerializer().fields.keys()) == {"id", "name", "color"}

            _record_check("soft_delete_retains_row", checks, errors, _soft_delete_retains_row)
            _record_check("soft_delete_sets_timestamp", checks, errors, _soft_delete_sets_timestamp)
            _record_check("default_manager_excludes_deleted", checks, errors, _default_manager_excludes_deleted)
            _record_check("normal_list_excludes_deleted", checks, errors, _normal_list_excludes_deleted)
            _record_check("deleted_detail_is_404", checks, errors, _deleted_detail_is_404)
            _record_check("deleted_action_lists_deleted", checks, errors, _deleted_action_lists_deleted)
            _record_check("restore_action_restores", checks, errors, _restore_action_restores)
            _record_check("soft_deleted_data_preserved", checks, errors, _soft_deleted_data_preserved)
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
