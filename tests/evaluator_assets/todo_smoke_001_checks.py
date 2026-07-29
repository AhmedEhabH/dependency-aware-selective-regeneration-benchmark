"""Standalone evaluator for todo-smoke-001 (Priority field)."""
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

        # check 1: task_priority_enum
        try:
            assert hasattr(Task, "Priority"), "Priority enum missing on Task"
            checks.append("task_priority_enum")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 2: task_priority_field
        try:
            assert hasattr(Task, "priority"), "priority field missing"
            checks.append("task_priority_field")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 3: task_priority_default (must be MEDIUM)
        try:
            task = Task.objects.create(title="Default Priority", project=project)
            assert task.priority == "MEDIUM", f"Expected MEDIUM, got {task.priority}"
            checks.append("task_priority_default")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 4: task_priority_valid_values
        try:
            for val in ["HIGH", "MEDIUM", "LOW"]:
                t = Task.objects.create(title=f"Priority {val}", project=project, priority=val)
                assert t.priority == val, f"Expected {val}"
            checks.append("task_priority_valid_values")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 5: task_serializer_priority
        try:
            from todo.serializers import TaskSerializer
            s = TaskSerializer()
            assert "priority" in s.fields, "priority not in serializer fields"
            checks.append("task_serializer_priority")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 6: task_priority_invalid_rejected (URGENT must fail)
        try:
            resp = client.post("/api/tasks/", {"title": "Bad", "project": project.pk, "priority": "URGENT"})
            assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
            checks.append("task_priority_invalid_rejected")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 7: task_priority_filter
        try:
            resp = client.get("/api/tasks/?priority=HIGH")
            assert resp.status_code == 200
            checks.append("task_priority_filter")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 8: task_unfiltered_list (returns all)
        try:
            resp = client.get("/api/tasks/")
            assert resp.status_code == 200
            assert "results" in resp.data, "pagination results missing"
            checks.append("task_unfiltered_list")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 9: baseline_task_fields
        try:
            task = Task.objects.create(title="Baseline", project=project)
            assert task.title == "Baseline"
            assert task.status == Task.Status.PENDING
            checks.append("baseline_task_fields")
        except AssertionError as e:
            errors.append(str(e))
            passed = False

        # check 10: project_and_tag_regression
        try:
            from todo.models import Tag
            tag = Tag.objects.create(name="regression", color="#FFF")
            task = Task.objects.create(title="With Tag", project=project)
            task.tags.add(tag)
            assert tag in task.tags.all()
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
