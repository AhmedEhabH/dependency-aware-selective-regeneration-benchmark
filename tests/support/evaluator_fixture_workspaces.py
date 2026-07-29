from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_BASELINE_REPO = Path(__file__).resolve().parent.parent.parent / "benchmark_data" / "repositories" / "todo"


def _copy_baseline(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(str(_BASELINE_REPO), str(destination), symlinks=False)


def _run_makemigrations(workspace: Path) -> None:
    mig_dir = workspace / "todo" / "migrations"
    if mig_dir.exists():
        for f in list(mig_dir.iterdir()):
            if f.suffix == ".py" and f.name != "__init__.py":
                f.unlink()
    result = subprocess.run(
        [sys.executable, "manage.py", "makemigrations", "todo", "--noinput"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"makemigrations failed: {result.stderr or result.stdout}")


def _overwrite(workspace: Path, relative_path: str, content: str) -> None:
    target = workspace / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def build_todo_smoke_001_workspace(destination: Path, variant: str = "correct") -> Path:
    _copy_baseline(destination)

    models_content: str
    serializers_content: str
    views_content: str

    if variant == "correct":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "wrong_default":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        HIGH = "HIGH", "High"
        MEDIUM = "MEDIUM", "Medium"
        LOW = "LOW", "Low"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.HIGH,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "missing_filter":
        models_content = '''from django.conf import settings
from django.db import models


class Priority(models.TextChoices):
    HIGH = "HIGH", "High"
    MEDIUM = "MEDIUM", "Medium"
    LOW = "LOW", "Low"


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "invalid_serializer_choice":
        models_content = '''from django.conf import settings
from django.db import models


class Priority(models.TextChoices):
    HIGH = "HIGH", "High"
    MEDIUM = "MEDIUM", "Medium"
    LOW = "LOW", "Low"


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["id", "name", "description"]


class TaskSerializer(serializers.ModelSerializer):
    priority = serializers.IntegerField()

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        priority = self.request.query_params.get("priority")
        if priority:
            qs = qs.filter(priority=priority)
        return qs

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    else:
        raise ValueError(f"Unknown variant for smoke-001: {variant}")

    _overwrite(destination, "todo/models.py", models_content)
    _overwrite(destination, "todo/serializers.py", serializers_content)
    _overwrite(destination, "todo/views.py", views_content)
    _run_makemigrations(destination)
    return destination


def build_todo_smoke_002_workspace(destination: Path, variant: str = "correct") -> Path:
    _copy_baseline(destination)

    models_content: str
    views_content: str

    if variant == "correct":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    all_objects = models.Manager()
    objects = TaskManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        views_content = '''from rest_framework import decorators, response, status, viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])

    @decorators.action(detail=False)
    def deleted(self, request):
        qs = Task.all_objects.filter(deleted_at__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        task = Task.all_objects.get(pk=pk)
        self.check_object_permissions(request, task)
        task.deleted_at = None
        task.save(update_fields=["deleted_at"])
        return response.Response(self.get_serializer(task).data)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "hard_delete":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        views_content = '''from rest_framework import decorators, response, status, viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.all_objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "deleted_visible_in_normal_list":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        views_content = '''from rest_framework import decorators, response, status, viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.all_objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])

    @decorators.action(detail=False)
    def deleted(self, request):
        qs = Task.all_objects.filter(deleted_at__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        task = self.get_object()
        task.deleted_at = None
        task.save(update_fields=["deleted_at"])
        return response.Response(self.get_serializer(task).data)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "restore_keeps_timestamp":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, default=None)

    objects = TaskManager()
    all_objects = models.Manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        views_content = '''from rest_framework import decorators, response, status, viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.all_objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save(update_fields=["deleted_at"])

    @decorators.action(detail=False)
    def deleted(self, request):
        qs = Task.all_objects.filter(deleted_at__isnull=False)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        task = self.get_object()
        task.deleted_at = None
        task.save(update_fields=["deleted_at"])
        return response.Response(self.get_serializer(task).data)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    else:
        raise ValueError(f"Unknown variant for smoke-002: {variant}")

    _overwrite(destination, "todo/models.py", models_content)
    _overwrite(destination, "todo/views.py", views_content)
    _run_makemigrations(destination)
    return destination


def build_todo_smoke_003_workspace(destination: Path, variant: str = "correct") -> Path:
    _copy_baseline(destination)

    models_content: str
    serializers_content: str
    permissions_content: str
    views_content: str

    if variant == "correct":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        permissions_content = '''from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsProjectMember(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, _obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsProjectOwner(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        project = getattr(obj, "project", None)
        if project is not None:
            return project.owner == request.user
        return getattr(obj, "owner", None) == request.user
'''
        views_content = '''from rest_framework import exceptions, viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember, IsProjectOwner
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        project = serializer.validated_data.get("project")
        if project is not None and project.owner != self.request.user:
            raise exceptions.PermissionDenied("You do not own this project")
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        user = self.request.user
        if isinstance(user, User):
            serializer.save(owner=user)
        else:
            serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "task_owner_authority":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        permissions_content = '''from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsProjectMember(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, _obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsProjectOwner(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        task_owner = getattr(obj, "owner", None)
        if task_owner is not None:
            return task_owner == request.user
        project = getattr(obj, "project", None)
        if project is not None:
            return project.owner == request.user
        return getattr(obj, "owner", None) == request.user
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember, IsProjectOwner
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        user = self.request.user
        if isinstance(user, User):
            serializer.save(owner=user)
        else:
            serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "project_non_owner_write_allowed":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        permissions_content = '''from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsProjectMember(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, _obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsProjectOwner(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        project = getattr(obj, "project", None)
        if project is not None:
            return project.owner == request.user
        return getattr(obj, "owner", None) == request.user
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember, IsProjectOwner
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectMember]

    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        user = self.request.user
        if isinstance(user, User):
            serializer.save(owner=user)
        else:
            serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    elif variant == "project_owner_writable":
        models_content = '''from django.conf import settings
from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=7)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
'''
        serializers_content = '''from rest_framework import serializers

from todo.models import Project, Tag, Task


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")

    class Meta:
        model = Project
        fields = ["id", "name", "description", "owner"]


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "project",
            "tags",
            "created_at",
            "updated_at",
        ]
'''
        permissions_content = '''from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "owner", None) == request.user


class IsProjectMember(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, _obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff


class IsProjectOwner(BasePermission):
    def has_permission(self, request, _view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, _view, obj):
        if request.method in SAFE_METHODS:
            return True
        project = getattr(obj, "project", None)
        if project is not None:
            return project.owner == request.user
        return getattr(obj, "owner", None) == request.user
'''
        views_content = '''from rest_framework import viewsets

from todo.models import Project, Tag, Task
from todo.permissions import IsOwnerOrReadOnly, IsProjectMember, IsProjectOwner
from todo.serializers import ProjectSerializer, TagSerializer, TaskSerializer


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        serializer.save()


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsProjectOwner]

    def perform_create(self, serializer):
        from django.contrib.auth.models import User
        user = self.request.user
        if isinstance(user, User):
            serializer.save(owner=user)
        else:
            serializer.save()


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsProjectMember]
'''

    else:
        raise ValueError(f"Unknown variant for smoke-003: {variant}")

    _overwrite(destination, "todo/models.py", models_content)
    _overwrite(destination, "todo/serializers.py", serializers_content)
    _overwrite(destination, "todo/permissions.py", permissions_content)
    _overwrite(destination, "todo/views.py", views_content)
    _run_makemigrations(destination)
    return destination
