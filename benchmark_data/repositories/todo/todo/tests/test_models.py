from django.test import TestCase

from todo.models import Project, Tag, Task


class ProjectModelTest(TestCase):
    def test_create_project(self):
        project = Project.objects.create(name="Test Project", description="A test project")
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.description, "A test project")

    def test_project_str(self):
        project = Project.objects.create(name="My Project")
        self.assertEqual(str(project), "My Project")


class TagModelTest(TestCase):
    def test_create_tag(self):
        tag = Tag.objects.create(name="urgent", color="#FF0000")
        self.assertEqual(tag.name, "urgent")
        self.assertEqual(tag.color, "#FF0000")

    def test_tag_unique_name(self):
        Tag.objects.create(name="unique", color="#000000")
        with self.assertRaises(Exception):
            Tag.objects.create(name="unique", color="#FFFFFF")

    def test_tag_str(self):
        tag = Tag.objects.create(name="bug", color="#00FF00")
        self.assertEqual(str(tag), "bug")


class TaskModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="Project A")

    def test_create_task(self):
        task = Task.objects.create(
            title="Test Task",
            description="A description",
            project=self.project,
        )
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "A description")
        self.assertEqual(task.status, Task.Status.PENDING)
        self.assertEqual(task.project, self.project)

    def test_task_default_status(self):
        task = Task.objects.create(title="Default Status", project=self.project)
        self.assertEqual(task.status, Task.Status.PENDING)

    def test_task_status_choices(self):
        task = Task.objects.create(title="In Progress Task", project=self.project, status=Task.Status.IN_PROGRESS)
        self.assertEqual(task.status, Task.Status.IN_PROGRESS)

        task.status = Task.Status.COMPLETED
        task.save()
        self.assertEqual(task.status, Task.Status.COMPLETED)

    def test_task_str(self):
        task = Task.objects.create(title="My Task", project=self.project)
        self.assertEqual(str(task), "My Task")

    def test_task_project_relationship(self):
        task = Task.objects.create(title="Related Task", project=self.project)
        self.assertIn(task, self.project.tasks.all())

    def test_task_tags(self):
        tag1 = Tag.objects.create(name="critical", color="#FF0000")
        tag2 = Tag.objects.create(name="minor", color="#0000FF")
        task = Task.objects.create(title="Tagged Task", project=self.project)
        task.tags.add(tag1, tag2)
        self.assertEqual(task.tags.count(), 2)
        self.assertIn(tag1, task.tags.all())
        self.assertIn(tag2, task.tags.all())

    def test_task_created_at_auto(self):
        task = Task.objects.create(title="Timed Task", project=self.project)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)

    def test_task_project_delete_cascade(self):
        Task.objects.create(title="Cascade Task", project=self.project)
        self.project.delete()
        self.assertEqual(Task.objects.count(), 0)
