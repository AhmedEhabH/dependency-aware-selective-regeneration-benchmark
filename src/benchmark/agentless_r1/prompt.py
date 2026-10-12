"""Deterministic Agentless-style file-level localization prompt construction.

Implements the frozen repository-structure rendering and the official file-level
localization prompt from ``agentless/fl/FL.py`` at the frozen inspect commit.
The construction is a pure function of the frozen parent-commit inputs; it never
reads gold.
"""

# ruff: noqa: E501  (verbatim frozen official prompt template must not be reflowed)
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

# Official Agentless file-level localization prompt, transcribed verbatim from
# agentless/fl/FL.py (LLMFL.obtain_relevant_files_prompt) at the frozen commit.
OFFICIAL_FILE_LOCALIZATION_PROMPT = """Please look through the following GitHub problem description and Repository structure and provide a list of files that one would need to edit to fix the problem.

### GitHub Problem Description ###
{problem_statement}

###

### Repository Structure ###
{structure}

###

Please only provide the full path and return at most 5 files.
The returned files should be separated by new lines ordered by most to least important and wrapped with ```
For example:
```
file1.py
file2.py
```
"""

# Official context constant (agentless/fl/FL.py); diagnostic threshold only.
MAX_CONTEXT_LENGTH: int = 128000

# Frozen top-N for the file-level comparator (official --top_n default).
TOP_N: int = 3


def ls_tree_py_files(cache: Path, parent_commit: str) -> list[str]:
    """Enumerate all blob paths in the parent commit of the frozen cache repo.

    Uses ``git ls-tree -r -z`` (identical to the frozen R2 estimate and the
    frozen MAIN_297 materialization cache). Returns repository-relative paths
    with forward slashes, sorted as git emits them (deterministic).
    """
    lst = subprocess.run(
        ["git", "-C", str(cache), "ls-tree", "-r", "-z", parent_commit],
        capture_output=True,
        check=True,
    ).stdout
    files: list[str] = []
    for rec in lst.split(b"\x00"):
        if not rec:
            continue
        meta, path = rec.split(b"\t", 1)
        if meta.split(b" ")[1] == b"blob":
            files.append(path.decode("utf-8", "replace"))
    return files


def build_structure(files: list[str]) -> dict[str, object]:
    """Official ``create_structure`` + filters over a plain file list.

    Equivalent to the official create_structure tree restricted to *.py files
    (filter_none_python) with test keys removed (filter_out_test_files); only
    the path skeleton matters for the file-level prompt. Leaves for .py files
    carry the official {classes, functions, text} placeholder keys so that
    show_project_structure treats them as files.
    """
    structure: dict[str, object] = {}
    for f in files:
        if not f.endswith(".py"):
            continue
        parts = f.split("/")
        if any(p.startswith("test") for p in parts):
            continue  # official filter_out_test_files (key.startswith('test'))
        node = structure
        for part in parts[:-1]:
            sub = node.get(part)
            if not isinstance(sub, dict):
                sub = {}
                node[part] = sub
            node = sub
        if parts[-1] not in node:
            node[parts[-1]] = {"classes": [], "functions": [], "text": []}
    return structure


def show_project_structure(structure: dict[str, object], spacing: int = 0) -> str:
    """Official ``show_project_structure`` rendering (dirs + .py names only)."""
    pp = ""
    for key, value in structure.items():
        if "." in key and ".py" not in key:
            continue  # skip none python files (official)
        if "." in key:
            pp += " " * spacing + str(key) + "\n"
        else:
            pp += " " * spacing + str(key) + "/" + "\n"
        if isinstance(value, dict) and "classes" not in value:
            pp += show_project_structure(value, spacing + 4)
    return pp


def structure_file_paths(structure: dict[str, object], prefix: str = "") -> list[str]:
    """Full repository-relative paths of surviving .py files (forward slashes).

    This is the set used by the parser to validate/correct model-returned lines
    (official ``get_full_file_paths_and_classes_and_functions`` path set).
    """
    out: list[str] = []
    for key, value in structure.items():
        path = f"{prefix}/{key}" if prefix else str(key)
        if isinstance(value, dict) and "classes" in value:
            out.append(path)
        elif isinstance(value, dict):
            out.extend(structure_file_paths(value, path))
    return out


def build_agentless_prompt(problem_statement: str, structure_text: str) -> str:
    """Render the official file-level localization prompt (frozen construction).

    Mirrors ``LLMFL.localize``: ``template.format(...).strip()`` with the
    structure already stripped by the caller.
    """
    return OFFICIAL_FILE_LOCALIZATION_PROMPT.format(
        problem_statement=problem_statement,
        structure=structure_text,
    ).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
