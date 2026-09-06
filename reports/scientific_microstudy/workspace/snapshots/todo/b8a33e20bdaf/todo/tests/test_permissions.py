from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from todo.models import Project, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember


class IsOwnerOrReadOnlyTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(username="owner", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        self.project = Project.objects.create(name="Test")
        self.task = Task.objects.create(title="Test Task", project=self.project, owner=self.owner)

    def test_owner_can_write(self):
        request = self.factory.patch("/api/tasks/1/")
        request.user = self.owner
        permission = IsOwnerOrReadOnly()
        result = permission.has_object_permission(request, None, self.task)
        self.assertTrue(result)

    def test_other_cannot_write(self):
        request = self.factory.patch("/api/tasks/1/")
        request.user = self.other
        permission = IsOwnerOrReadOnly()
        result = permission.has_object_permission(request, None, self.task)
        self.assertFalse(result)

    def test_authenticated_can_read(self):
        request = self.factory.get("/api/tasks/1/")
        request.user = self.owner
        permission = IsOwnerOrReadOnly()
        result = permission.has_object_permission(request, None, self.task)
        self.assertTrue(result)

    def test_authenticated_has_permission(self):
        request = self.factory.get("/api/tasks/")
        request.user = self.owner
        permission = IsOwnerOrReadOnly()
        self.assertTrue(permission.has_permission(request, None))

    def test_unauthenticated_no_permission(self):
        request = self.factory.get("/api/tasks/")
        request.user = AnonymousUser()
        permission = IsOwnerOrReadOnly()
        self.assertFalse(permission.has_permission(request, None))


class IsProjectMemberTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.staff = User.objects.create_user(username="staff", password="pass", is_staff=True)
        self.member = User.objects.create_user(username="member", password="pass")

    def test_authenticated_has_permission(self):
        request = self.factory.get("/api/projects/")
        request.user = self.member
        permission = IsProjectMember()
        self.assertTrue(permission.has_permission(request, None))

    def test_unauthenticated_no_permission(self):
        request = self.factory.get("/api/projects/")
        request.user = AnonymousUser()
        permission = IsProjectMember()
        self.assertFalse(permission.has_permission(request, None))

    def test_staff_can_write(self):
        request = self.factory.patch("/api/projects/1/")
        request.user = self.staff
        permission = IsProjectMember()
        self.assertTrue(permission.has_object_permission(request, None, None))

    def test_non_staff_read_only(self):
        request = self.factory.patch("/api/projects/1/")
        request.user = self.member
        permission = IsProjectMember()
        self.assertFalse(permission.has_object_permission(request, None, None))
