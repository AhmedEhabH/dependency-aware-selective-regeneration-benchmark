# Controlled Django Todo Application

A small, purpose-built synthetic Django REST Framework application
implementing a layered REST architecture for task management.

**Part of:** Dependency-Aware Selective Regeneration Benchmark
**Protocol Version:** 1.0 (FROZEN)

## Domain

- **Task** — title, description, status, project, timestamps
- **Project** — name, description
- **Tag** — name, color

## Architecture

Layered REST: urls.py → views.py → serializers.py → models.py
Permissions are a cross-cutting concern.

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python -m pytest
```
