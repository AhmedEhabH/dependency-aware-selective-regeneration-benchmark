import io
import json
import os
import sys
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


def _workspace_from_argv() -> Path:
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "checks": [], "error": "expected exactly one workspace argument"}))
        sys.exit(1)
    ws = Path(sys.argv[1])
    if not ws.is_dir():
        print(json.dumps({"passed": False, "checks": [], "error": "workspace not found"}))
        sys.exit(1)
    if not (ws / "manage.py").exists():
        print(json.dumps({"passed": False, "checks": [], "error": "manage.py not found in workspace"}))
        sys.exit(1)
    if not (ws / "config" / "settings.py").exists():
        print(json.dumps({"passed": False, "checks": [], "error": "config/settings.py not found"}))
        sys.exit(1)
    if not (ws / "todo").is_dir():
        print(json.dumps({"passed": False, "checks": [], "error": "todo/ directory not found"}))
        sys.exit(1)
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

            from django.conf import settings
            from django.contrib.auth.models import User
            from rest_framework.test import APIClient
            from todo.models import Project, Task
            from todo.serializers import ProjectSerializer

            owner = User.objects.create_user(username="owner", password="pass")
            other = User.objects.create_user(username="other", password="pass")
            staff_user = User.objects.create_user(username="staff", password="pass", is_staff=True)

            owner_client = APIClient()
            owner_client.force_authenticate(user=owner)
            other_client = APIClient()
            other_client.force_authenticate(user=other)
            staff_client = APIClient()
            staff_client.force_authenticate(user=staff_user)

            proj_resp = owner_client.post("/api/projects/", {"name": "OwnedProject"})
            assert proj_resp.status_code == 201, f"Project create failed: {proj_resp.status_code}"
            project = Project.objects.get(pk=proj_resp.data["id"])

            checks: list[str] = []
            errors: list[str] = []

            def _project_owner_field() -> None:
                field = Project._meta.get_field("owner")
                assert field is not None, "Project has no owner field"
                assert field.remote_field, "owner is not a ForeignKey"
                expected = settings.AUTH_USER_MODEL
                actual = field.remote_field.model._meta.label
                assert actual.lower() == expected.lower(), f"Expected FK to {expected}, got {actual}"

            def _project_creator_becomes_owner() -> None:
                fresh = Project.objects.get(pk=project.pk)
                assert fresh.owner == owner, "Creator was not set as owner"
                override_resp = owner_client.post("/api/projects/", {"name": "OverrideTest", "owner": other.pk})
                assert override_resp.status_code == 201, f"Override create failed: {override_resp.status_code}"
                override_project = Project.objects.get(pk=override_resp.data["id"])
                assert override_project.owner == owner, "Owner was overridden by provided owner ID"

            def _project_owner_read_only() -> None:
                s = ProjectSerializer()
                assert "owner" in s.fields, "owner not in serializer fields"
                assert s.fields["owner"].read_only is True, "owner field is not read-only"

            def _project_owner_can_write() -> None:
                patch_resp = owner_client.patch(f"/api/projects/{project.pk}/", {"name": "UpdatedByOwner"})
                assert patch_resp.status_code == 200, f"Owner PATCH returned {patch_resp.status_code}"
                del_resp = owner_client.post("/api/projects/", {"name": "ToDeleteByOwner"})
                assert del_resp.status_code == 201
                del_pk = del_resp.data["id"]
                delete_resp = owner_client.delete(f"/api/projects/{del_pk}/")
                assert delete_resp.status_code == 204, f"Owner DELETE returned {delete_resp.status_code}"

            def _project_non_owner_forbidden() -> None:
                patch_resp = other_client.patch(f"/api/projects/{project.pk}/", {"name": "Hacked"})
                assert patch_resp.status_code == 403, f"Non-owner PATCH expected 403, got {patch_resp.status_code}"
                delete_resp = other_client.delete(f"/api/projects/{project.pk}/")
                assert delete_resp.status_code == 403, f"Non-owner DELETE expected 403, got {delete_resp.status_code}"
                create_resp = other_client.post("/api/projects/", {"name": "OtherOwnProject"})
                assert create_resp.status_code == 201, f"Other create project returned {create_resp.status_code}"

            def _task_create_uses_project_owner() -> None:
                ok_resp = owner_client.post("/api/tasks/", {"title": "OwnerTask", "project": project.pk})
                assert ok_resp.status_code == 201, f"Owner task create returned {ok_resp.status_code}"
                fail_resp = other_client.post("/api/tasks/", {"title": "OtherTask", "project": project.pk})
                assert fail_resp.status_code == 403, f"Other task create expected 403, got {fail_resp.status_code}"

            def _task_update_uses_project_owner() -> None:
                task = Task.objects.create(title="UpdateConflict", project=project, owner=other)
                owner_patch = owner_client.patch(f"/api/tasks/{task.pk}/", {"title": "OwnerUpdated"})
                assert owner_patch.status_code == 200, f"Project owner PATCH returned {owner_patch.status_code}"
                other_patch = other_client.patch(f"/api/tasks/{task.pk}/", {"title": "OtherUpdated"})
                assert other_patch.status_code == 403, f"Legacy owner PATCH expected 403, got {other_patch.status_code}"

            def _task_delete_uses_project_owner() -> None:
                task1 = Task.objects.create(title="DeleteConflict1", project=project, owner=other)
                owner_del = owner_client.delete(f"/api/tasks/{task1.pk}/")
                assert owner_del.status_code == 204, f"Project owner DELETE returned {owner_del.status_code}"
                task2 = Task.objects.create(title="DeleteConflict2", project=project, owner=other)
                other_del = other_client.delete(f"/api/tasks/{task2.pk}/")
                assert other_del.status_code == 403, f"Legacy owner DELETE expected 403, got {other_del.status_code}"

            def _authenticated_reads_unrestricted() -> None:
                p_resp = other_client.get("/api/projects/")
                assert p_resp.status_code == 200, f"Projects list returned {p_resp.status_code}"
                t_resp = other_client.get("/api/tasks/")
                assert t_resp.status_code == 200, f"Tasks list returned {t_resp.status_code}"
                tr_resp = other_client.get("/api/tags/")
                assert tr_resp.status_code == 200, f"Tags list returned {tr_resp.status_code}"

            def _tag_permissions_unchanged() -> None:
                create_resp = other_client.post("/api/tags/", {"name": "newtag", "color": "#FFF"})
                assert create_resp.status_code == 201, f"Non-staff tag create returned {create_resp.status_code}"
                tag_pk = create_resp.data["id"]
                patch_resp = other_client.patch(f"/api/tags/{tag_pk}/", {"color": "#000"})
                assert patch_resp.status_code == 403, f"Non-staff tag PATCH expected 403, got {patch_resp.status_code}"
                delete_resp = other_client.delete(f"/api/tags/{tag_pk}/")
                assert delete_resp.status_code == 403, (
                    f"Non-staff tag DELETE expected 403, got {delete_resp.status_code}"
                )
                staff_patch = staff_client.patch(f"/api/tags/{tag_pk}/", {"color": "#123"})
                assert staff_patch.status_code == 200, f"Staff tag PATCH returned {staff_patch.status_code}"

            _record_check("project_owner_field", checks, errors, _project_owner_field)
            _record_check("project_creator_becomes_owner", checks, errors, _project_creator_becomes_owner)
            _record_check("project_owner_read_only", checks, errors, _project_owner_read_only)
            _record_check("project_owner_can_write", checks, errors, _project_owner_can_write)
            _record_check("project_non_owner_forbidden", checks, errors, _project_non_owner_forbidden)
            _record_check("task_create_uses_project_owner", checks, errors, _task_create_uses_project_owner)
            _record_check("task_update_uses_project_owner", checks, errors, _task_update_uses_project_owner)
            _record_check("task_delete_uses_project_owner", checks, errors, _task_delete_uses_project_owner)
            _record_check("authenticated_reads_unrestricted", checks, errors, _authenticated_reads_unrestricted)
            _record_check("tag_permissions_unchanged", checks, errors, _tag_permissions_unchanged)

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
                if old_config is not None:
                    runner.teardown_databases(old_config)
                if environment_ready:
                    runner.teardown_test_environment()

    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
