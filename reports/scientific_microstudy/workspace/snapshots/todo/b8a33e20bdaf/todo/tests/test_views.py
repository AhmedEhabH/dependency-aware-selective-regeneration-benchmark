from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from todo.models import Project, Tag, Task


class TaskViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/projects/", {"name": "Test Project"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.project = Project.objects.get(pk=response.data["id"])

    def test_list_tasks(self):
        Task.objects.create(title="Task 1", project=self.project)
        Task.objects.create(title="Task 2", project=self.project)
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_task(self):
        response = self.client.post("/api/tasks/", {
            "title": "New Task",
            "project": self.project.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)

    def test_retrieve_task(self):
        task = Task.objects.create(title="Detail Task", project=self.project, owner=self.user)
        response = self.client.get(f"/api/tasks/{task.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Detail Task")

    def test_update_owned_task(self):
        task = Task.objects.create(title="Original", project=self.project, owner=self.user)
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"title": "Updated"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, "Updated")

    def test_delete_owned_task(self):
        task = Task.objects.create(title="Delete Me", project=self.project, owner=self.user)
        response = self.client.delete(f"/api/tasks/{task.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_update_unowned_task_forbidden(self):
        other_user = User.objects.create_user(username="other", password="pass")
        other_client = APIClient()
        other_client.force_authenticate(user=other_user)
        other_project_response = other_client.post("/api/projects/", {"name": "Other Project"})
        self.assertEqual(other_project_response.status_code, status.HTTP_201_CREATED)
        other_project = Project.objects.get(pk=other_project_response.data["id"])
        task = Task.objects.create(title="Others Task", project=other_project, owner=other_user)
        response = self.client.patch(f"/api/tasks/{task.pk}/", {"title": "Hacked"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ProjectViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        Project.objects.create(name="Project A")
        Project.objects.create(name="Project B")
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_project(self):
        response = self.client.post("/api/projects/", {"name": "New Project"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_retrieve_project(self):
        project = Project.objects.create(name="Test")
        response = self.client.get(f"/api/projects/{project.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test")


class TagViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_tags(self):
        Tag.objects.create(name="bug", color="#FF0000")
        Tag.objects.create(name="feature", color="#00FF00")
        response = self.client.get("/api/tags/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_tag(self):
        response = self.client.post("/api/tags/", {"name": "docs", "color": "#0000FF"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unique_tag_name(self):
        Tag.objects.create(name="duplicate", color="#FF0000")
        response = self.client.post("/api/tags/", {"name": "duplicate", "color": "#00FF00"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
