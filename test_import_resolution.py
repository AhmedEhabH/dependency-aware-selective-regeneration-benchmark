"""Focused tests for relative import resolution in source_graph module."""

import ast
from pathlib import Path
from src.benchmark.external_validity.source_graph import (
    _import_edges_from_file,
    _make_resolver,
    _build_module_map,
)


def test_relative_import_resolution() -> None:
    """Test that relative imports resolve correctly without self-edges."""
    
    # Create mock module map
    records = [
        {
            "path": "cms/pkg/a.py",
            "module": "cms.pkg.a",
            "sha256": "test",
            "loc": 10,
            "classes": [],
            "functions": [],
            "import_count": 0,
        },
        {
            "path": "cms/pkg/b.py",
            "module": "cms.pkg.b",
            "sha256": "test",
            "loc": 10,
            "classes": [],
            "functions": [],
            "import_count": 0,
        },
        {
            "path": "cms/pkg/__init__.py",
            "module": "cms.pkg",
            "sha256": "test",
            "loc": 10,
            "classes": [],
            "functions": [],
            "import_count": 0,
        },
        {
            "path": "cms/other/c.py",
            "module": "cms.other.c",
            "sha256": "test",
            "loc": 10,
            "classes": [],
            "functions": [],
            "import_count": 0,
        },
    ]
    
    module_map = _build_module_map(records)
    resolve = _make_resolver(module_map)
    
    # Test 1: from . import b
    content1 = "from . import b"
    targets1 = _import_edges_from_file(content1, "cms.pkg.a", resolve)
    assert "cms/pkg/b.py" in targets1, f"Expected cms/pkg/b.py, got {targets1}"
    assert "cms/pkg/a.py" not in targets1, f"Self-edge found: {targets1}"
    
    # Test 2: from .b import X
    content2 = "from .b import MyClass"
    targets2 = _import_edges_from_file(content2, "cms.pkg.a", resolve)
    assert "cms/pkg/b.py" in targets2, f"Expected cms/pkg/b.py, got {targets2}"
    
    # Test 3: from ..other import c
    content3 = "from ..other import c"
    targets3 = _import_edges_from_file(content3, "cms.pkg.a", resolve)
    assert "cms/other/c.py" in targets3, f"Expected cms/other/c.py, got {targets3}"
    
    # Test 4: absolute local import
    content4 = "import cms.other.c"
    targets4 = _import_edges_from_file(content4, "cms.pkg.a", resolve)
    assert "cms/other/c.py" in targets4, f"Expected cms/other/c.py, got {targets4}"
    
    # Test 5: external import ignored
    content5 = "import django.db.models"
    targets5 = _import_edges_from_file(content5, "cms.pkg.a", resolve)
    assert len(targets5) == 0, f"Expected no targets for external import, got {targets5}"
    
    # Test 6: no false self-edge for from . import (empty)
    content6 = "from . import something_not_in_universe"
    targets6 = _import_edges_from_file(content6, "cms.pkg.a", resolve)
    assert "cms/pkg/a.py" not in targets6, f"Self-edge found: {targets6}"
    
    print("All relative import tests passed")


def test_module_name_conversion() -> None:
    """Test _module_name function for package __init__.py vs normal modules."""
    from src.benchmark.external_validity.source_graph import _module_name
    
    # Normal module
    assert _module_name(Path("cms/pkg/a.py")) == "cms.pkg.a"
    
    # __init__.py in package
    assert _module_name(Path("cms/pkg/__init__.py")) == "cms.pkg"
    
    # Root __init__.py
    assert _module_name(Path("cms/__init__.py")) == "cms"
    
    print("Module name conversion tests passed")


if __name__ == "__main__":
    test_module_name_conversion()
    test_relative_import_resolution()
    print("\nDONE All focused import resolution tests passed")