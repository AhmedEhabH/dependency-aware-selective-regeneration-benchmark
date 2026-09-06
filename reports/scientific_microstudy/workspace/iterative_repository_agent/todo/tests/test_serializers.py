from django.test import TestCase

from todo.models import Project, Tag, Task
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TagSerializerTest(TestCase):
    def test_tag_serializer_fields(self):
        serializer = TagSerializer()
        expected = {"id", "name", "color"}
        self.assertEqual(set(serializer.fields.keys()), expected)

    def test_tag_serialization(self):
        tag = Tag.objects.create(name="urgent", color="#FF0000")
        serializer = TagSerializer(tag)
        self.assertEqual(serializer.data["name"], "urgent")
        self.assertEqual(serializer.data["color"], "#FF0000")

    def test_tag_deserialization_valid(self):
        serializer = TagSerializer(data={"name": "new-tag", "color": "#FFFFFF"})
        self.assertTrue(serializer.is_valid())

    def test_tag_deserialization_invalid(self):
        serializer = TagSerializer(data={"name": "", "color": "not-a-color"})
        self.assertFalse(serializer.is_valid())


class ProjectSerializerTest(TestCase):
    def test_project_serializer_fields(self):
        serializer = ProjectSerializer()
        required = {"id", "name", "description"}
        self.assertTrue(
            required <= set(serializer.fields.keys()),
            f"Baseline fields missing from ProjectSerializer: {sorted(required - set(serializer.fields.keys()))}",
        )

    def test_project_serialization(self):
        project = Project.objects.create(name="Test", description="Desc")
        serializer = ProjectSerializer(project)
        self.assertEqual(serializer.data["name"], "Test")
        self.assertEqual(serializer.data["description"], "Desc")

    def test_project_deserialization(self):
        serializer = ProjectSerializer(data={"name": "New Project"})
        self.assertTrue(serializer.is_valid())
        project = serializer.save()
        self.assertEqual(project.name, "New Project")


class TaskSerializerTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project A")

    def test_task_serializer_fields(self):
        serializer = TaskSerializer()
        required = {"id", "title", "description", "status", "project", "tags", "created_at", "updated_at"}
        self.assertTrue(
            required <= set(serializer.fields.keys()),
            f"Baseline fields missing from TaskSerializer: {sorted(required - set(serializer.fields.keys()))}",
        )

    def test_task_serialization(self):
        task = Task.objects.create(title="Test", project=self.project)
        serializer = TaskSerializer(task)
        self.assertEqual(serializer.data["title"], "Test")
        self.assertEqual(serializer.data["status"], "PENDING")

    def test_task_deserialization_valid(self):
        serializer = TaskSerializer(data={
            "title": "New Task",
            "project": self.project.pk,
        })
        self.assertTrue(serializer.is_valid())

    def test_task_deserialization_with_tags(self):
        tag = Tag.objects.create(name="bug", color="#FF0000")
        serializer = TaskSerializer(data={
            "title": "Bug Fix",
            "project": self.project.pk,
            "tags": [tag.pk],
        })
        self.assertTrue(serializer.is_valid())

    def test_task_deserialization_invalid_no_title(self):
        serializer = TaskSerializer(data={
            "project": self.project.pk,
        })
        self.assertFalse(serializer.is_valid())
