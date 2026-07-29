"""Standalone evaluator for todo-smoke-003 (Project-owner authorization)."""
import json
import os
import sys


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "checks": [], "error": "expected exactly one workspace argument"}))
        sys.exit(1)

    workspace = sys.argv[1]
    if not os.path.isdir(workspace):
        print(json.dumps({"passed": False, "checks": [], "error": "workspace not found"}))
        sys.exit(1)

    sys.path.insert(0, workspace)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    from django.test.runner import DiscoverRunner
    from django.test.utils import setup_test_environment, teardown_test_environment

    checks = []
    errors = []
    passed = True

    django.setup()
    runner = DiscoverRunner()
    setup_test_environment()
    old_config = runner.setup_databases()

    try:
        from django.contrib.auth.models import User
        from rest_framework.test import APIClient
        from todo.models import Project, Task

        owner = User.objects.create_user(username="owner", password="pass")
        other = User.objects.create_user(username="other", password="pass")

        # create projects
        owner_client = APIClient()
        owner_client.force_authenticate(user=owner)
        other_client = APIClient()
        other_client.force_authenticate(user=other)

        proj_resp = owner_client.post("/api/projects/", {"name": "Owned"})
        assert proj_resp.status_code == 201, f"Project create failed: {proj_resp.status_code}"
        project_id = proj_resp.data["id"]

        # check 1: project_owner_field
        try:
            project = Project.objects.get(pk=project_id)
            assert hasattr(project, "owner"), "Project has no owner field"
            checks.append("project_owner_field")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 2: project_creator_becomes_owner
        try:
            project = Project.objects.get(pk=project_id)
            assert project.owner == owner, "Creator was not set as owner"
            checks.append("project_creator_becomes_owner")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 3: project_owner_read_only
        try:
            resp = owner_client.get(f"/api/projects/{project_id}/")
            assert resp.status_code == 200
            assert "owner" in resp.data, "owner not exposed"
            checks.append("project_owner_read_only")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 4: project_owner_can_write
        try:
            resp = owner_client.patch(f"/api/projects/{project_id}/", {"name": "Updated"})
            assert resp.status_code == 200, f"Owner update failed: {resp.status_code}"
            checks.append("project_owner_can_write")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 5: project_non_owner_forbidden
        try:
            resp = other_client.patch(f"/api/projects/{project_id}/", {"name": "Hacked"})
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
            checks.append("project_non_owner_forbidden")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 6: task_create_uses_project_owner
        try:
            resp = other_client.post("/api/tasks/", {"title": "Other Task", "project": project_id})
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
            checks.append("task_create_uses_project_owner")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 7: task_update_uses_project_owner
        try:
            task = Task.objects.create(title="Owner Task", project=Project.objects.get(pk=project_id))
            resp = other_client.patch(f"/api/tasks/{task.pk}/", {"title": "Hacked"})
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
            checks.append("task_update_uses_project_owner")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 8: task_delete_uses_project_owner
        try:
            task = Task.objects.create(title="Delete Me", project=Project.objects.get(pk=project_id))
            resp = other_client.delete(f"/api/tasks/{task.pk}/")
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
            checks.append("task_delete_uses_project_owner")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 9: authenticated_reads_unrestricted
        try:
            resp = other_client.get("/api/tasks/")
            assert resp.status_code == 200
            resp = other_client.get("/api/projects/")
            assert resp.status_code == 200
            checks.append("authenticated_reads_unrestricted")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 10: tag_permissions_unchanged
        try:
            tag_resp = other_client.post("/api/tags/", {"name": "newtag", "color": "#FFF"})
            assert tag_resp.status_code == 201, f"Tag create by non-owner failed: {tag_resp.status_code}"
            checks.append("tag_permissions_unchanged")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

    finally:
        runner.teardown_databases(old_config)
        teardown_test_environment()

    error_str = "; ".join(errors) if errors else ""
    result = {"passed": passed, "checks": checks, "error": error_str}
    print(json.dumps(result))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
