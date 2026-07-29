"""Standalone evaluator for todo-smoke-002 (Soft Delete)."""
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

        user = User.objects.create_user(username="tester", password="pass")
        project = Project.objects.create(name="Test")
        client = APIClient()
        client.force_authenticate(user=user)

        # check 1: soft_delete_retains_row
        try:
            task = Task.all_objects.create(owner=user, title="To Delete", project=project)
            task_id = task.pk
            client.delete(f"/api/tasks/{task.pk}/")
            still_exists = Task.all_objects.filter(pk=task_id).exists()
            assert still_exists, "Row was removed from database"
            checks.append("soft_delete_retains_row")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 2: soft_delete_sets_timestamp
        try:
            task = Task.all_objects.create(owner=user, title="Timestamp Check", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            task.refresh_from_db()
            assert task.deleted_at is not None, "deleted_at not set"
            checks.append("soft_delete_sets_timestamp")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 3: default_manager_excludes_deleted
        try:
            task = Task.all_objects.create(owner=user, title="Hidden", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            qs = Task.objects.all()
            assert task not in qs, "Default manager returned deleted task"
            checks.append("default_manager_excludes_deleted")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 4: normal_list_excludes_deleted
        try:
            task = Task.all_objects.create(owner=user, title="Hidden From List", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            resp = client.get("/api/tasks/")
            ids = [item["id"] for item in resp.data.get("results", [])]
            assert task.pk not in ids, "Normal list includes deleted task"
            checks.append("normal_list_excludes_deleted")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 5: deleted_detail_is_404
        try:
            task = Task.all_objects.create(owner=user, title="Gone", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            resp = client.get(f"/api/tasks/{task.pk}/")
            assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
            checks.append("deleted_detail_is_404")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 6: deleted_action_lists_deleted
        try:
            task = Task.all_objects.create(owner=user, title="Only In Deleted", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            resp = client.get("/api/tasks/deleted/")
            ids = [item["id"] for item in resp.data.get("results", [])]
            assert task.pk in ids, "Deleted action did not list the task"
            checks.append("deleted_action_lists_deleted")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 7: restore_action_restores
        try:
            task = Task.all_objects.create(owner=user, title="Restore Me", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            resp = client.post(f"/api/tasks/{task.pk}/restore/")
            assert resp.status_code == 200, f"Restore failed: {resp.status_code}"
            task.refresh_from_db()
            assert task.deleted_at is None, "deleted_at not cleared after restore"
            checks.append("restore_action_restores")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 8: soft_deleted_data_preserved
        try:
            task = Task.all_objects.create(owner=user, title="Preserved", project=project)
            client.delete(f"/api/tasks/{task.pk}/")
            task.refresh_from_db()
            assert task.title == "Preserved", "Title was modified"
            assert task.project == project, "Project reference lost"
            checks.append("soft_deleted_data_preserved")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 9: project_and_tag_regression
        try:
            from todo.models import Tag
            Tag.objects.create(name="regression", color="#FFF")
            assert Tag.objects.count() >= 1
            assert Project.objects.count() >= 1
            checks.append("project_and_tag_regression")
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
