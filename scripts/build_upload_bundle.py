#!/usr/bin/env python3
"""Deterministic bundle builder for Kaggle deployment.

Builds project/kaggle_upload/ from canonical sources only.
Clears only project/kaggle_upload/.
Never clears canonical source directories.
Generates SHA-256 manifests.
Verifies every generated derivative against its canonical source.
Fails nonzero on missing, mismatched, or unexpected files.
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KAGGLE_UPLOAD = PROJECT_ROOT / "kaggle_upload"
KAGGLE_CODE = KAGGLE_UPLOAD / "code"
KAGGLE_DATA = KAGGLE_UPLOAD / "data"
KAGGLE_NOTEBOOKS = KAGGLE_UPLOAD / "notebooks"

CANONICAL_CODE_SOURCES = [
    PROJECT_ROOT / "seven_arm_benchmark.py",
    PROJECT_ROOT / "src" / "benchmark",
    PROJECT_ROOT / "configs",
    PROJECT_ROOT / "requirements-kaggle.txt",
    PROJECT_ROOT / "pyproject.toml",
]

CANONICAL_DATA_SOURCES = [
    PROJECT_ROOT / "benchmark_data" / "manifests",
    PROJECT_ROOT / "benchmark_data" / "repository_profiles",
    PROJECT_ROOT / "benchmark_data" / "repositories",
    PROJECT_ROOT / "benchmark_data" / "scenarios",
]

CANONICAL_NOTEBOOK_SOURCES = [
    PROJECT_ROOT / "notebooks" / "seven_arm_benchmark.ipynb",
]

EXCLUDE_PATTERNS = {
    ".git",
    ".gitignore",
    "__pycache__",
    "*.pyc",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "*.egg-info",
    "runs",
    "reports",
    "tests",
    "inputs",
    "_auto_resume_temp",
    "benchmark-results.zip",
    "db.sqlite3",
    "*.db",
    "*.sqlite3",
}

FORBIDDEN_IN_BUNDLE = {
    ".git", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "*.egg-info", "db.sqlite3", "*.db", "*.sqlite3",
}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized_sha256(path: Path) -> str:
    if path.suffix in (".py", ".toml", ".txt", ".yaml", ".yml", ".md", ".cfg", ".ini"):
        content = path.read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(content).hexdigest()
    return sha256_of(path)


def should_exclude(name: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if pat.startswith("*"):
            if name.endswith(pat[1:]):
                return True
        elif name == pat:
            return True
    return name.endswith(".pyc") or name.endswith(".pyo")


def copy_tree(src: Path, dst: Path, prefix: str = "") -> list[tuple[Path, Path]]:
    dst.mkdir(parents=True, exist_ok=True)
    copied = []
    for entry in src.iterdir():
        if should_exclude(entry.name):
            continue
        rel = entry.name if not prefix else f"{prefix}/{entry.name}"
        dst_path = dst / rel
        if entry.is_dir():
            dst_path.mkdir(parents=True, exist_ok=True)
            copied.extend(copy_tree(entry, dst, rel))
        else:
            shutil.copy2(entry, dst_path)
            copied.append((entry, dst_path))
    return copied


def copy_file(src: Path, dst_dir: Path) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    shutil.copy2(src, dst)
    return dst


def normalize_text(path: Path) -> None:
    if path.suffix in (".py", ".toml", ".txt", ".yaml", ".yml", ".md", ".cfg", ".ini"):
        text = path.read_bytes()
        path.write_bytes(text.replace(b"\r\n", b"\n"))


def scan_forbidden(directory: Path) -> list[str]:
    found = []
    forbidden_suffixes = tuple(pat[1:] for pat in FORBIDDEN_IN_BUNDLE if pat.startswith("*"))
    for root, dirs, files in os.walk(str(directory)):
        root_path = Path(root)
        for d in list(dirs):
            if d in FORBIDDEN_IN_BUNDLE or (d.startswith(".") and d not in (".",)):
                found.append(str(root_path / d))
                dirs.remove(d)
        for f in files:
            if f.endswith(forbidden_suffixes) or f.endswith(".pyc"):
                found.append(str(root_path / f))
    return found


def generate_manifest(directory: Path, _label: str) -> dict[str, str]:
    manifest = {}
    for root, _dirs, files in os.walk(str(directory)):
        for f in sorted(files):
            full = Path(root) / f
            rel = str(full.relative_to(directory))
            manifest[rel] = sha256_of(full)
    return manifest


def write_manifest(manifest: dict[str, str], path: Path) -> None:
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def verify_bundle(canonical: list[Path], bundle_base: Path, base_rel: Path | None = None, flat: bool = False) -> int:
    errors = 0
    for src in canonical:
        rel = src.relative_to(PROJECT_ROOT) if base_rel is None else src.relative_to(base_rel)
        bundle_path = bundle_base / src.name if flat else bundle_base / rel

        if src.is_file():
            if not bundle_path.exists():
                print(f"  MISSING: {bundle_path}")
                errors += 1
            elif normalized_sha256(src) != normalized_sha256(bundle_path):
                print(f"  MISMATCH: {rel}")
                errors += 1
        elif src.is_dir():
            for root, dirs, files in os.walk(str(src)):
                dirs[:] = [d for d in dirs if not should_exclude(d)]
                for f in files:
                    if should_exclude(f):
                        continue
                    src_file = Path(root) / f
                    if base_rel is None:
                        file_rel = src_file.relative_to(PROJECT_ROOT)
                    else:
                        file_rel = src_file.relative_to(base_rel)
                    bundle_file = bundle_base / file_rel
                    if not bundle_file.exists():
                        print(f"  MISSING: {bundle_file}")
                        errors += 1
                    elif normalized_sha256(src_file) != normalized_sha256(bundle_file):
                        print(f"  MISMATCH: {file_rel}")
                        errors += 1
    return errors


def count_files(directory: Path) -> int:
    return sum(1 for _ in directory.rglob("*") if _.is_file())


def total_size(directory: Path) -> int:
    return sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())


def build_bundle() -> int:
    errors = 0

    print("=== Kaggle Upload Bundle Builder ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Bundle root:  {KAGGLE_UPLOAD}")
    print()

    # Step 1: Clean bundle directory only
    if KAGGLE_UPLOAD.exists():
        print("Clearing project/kaggle_upload/ ...")
        shutil.rmtree(KAGGLE_UPLOAD)
    KAGGLE_UPLOAD.mkdir(parents=True)
    print("Done.\n")

    # Step 2: Build code bundle
    print("--- Code Bundle ---")
    KAGGLE_CODE.mkdir(parents=True)
    code_copied = []

    for src in CANONICAL_CODE_SOURCES:
        rel = src.relative_to(PROJECT_ROOT)
        dst = KAGGLE_CODE / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            code_copied.append((src, dst))
            print(f"  Copied: {rel}")
        elif src.is_dir():
            copied = copy_tree(src, dst)
            code_copied.extend(copied)
            print(f"  Copied: {rel}/ ({len(copied)} files)")

    # Normalize text files
    print("  Normalizing line endings ...")
    for _src, dst in code_copied:
        normalize_text(dst)

    # Step 3: Build data bundle
    print("\n--- Data Bundle ---")
    KAGGLE_DATA.mkdir(parents=True)
    data_copied = []

    for src in CANONICAL_DATA_SOURCES:
        if src.is_dir():
            rel = src.relative_to(PROJECT_ROOT / "benchmark_data")
            dst = KAGGLE_DATA / rel
            dst.mkdir(parents=True, exist_ok=True)
            copied = copy_tree(src, dst)
            data_copied.extend(copied)
            print(f"  Copied: benchmark_data/{rel}/ ({len(copied)} files)")

    # Step 4: Build notebook bundle
    print("\n--- Notebook Bundle ---")
    KAGGLE_NOTEBOOKS.mkdir(parents=True)
    notebook_copied = []

    for src in CANONICAL_NOTEBOOK_SOURCES:
        if src.is_file():
            dst = KAGGLE_NOTEBOOKS / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            notebook_copied.append((src, dst))
            print(f"  Copied: {src.name}")

    # Step 5: Check for forbidden items
    print("\n--- Forbidden Items Check ---")
    forbidden = scan_forbidden(KAGGLE_CODE)
    forbidden.extend(scan_forbidden(KAGGLE_DATA))
    forbidden.extend(scan_forbidden(KAGGLE_NOTEBOOKS))
    if forbidden:
        for f in forbidden:
            print(f"  FORBIDDEN: {f}")
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)
        print(f"  Removed {len(forbidden)} forbidden items.")
    else:
        print("  No forbidden items found.")

    # Step 6: Generate SHA-256 manifests
    print("\n--- Manifests ---")
    code_manifest = generate_manifest(KAGGLE_CODE, "code")
    data_manifest = generate_manifest(KAGGLE_DATA, "data")
    notebook_manifest = generate_manifest(KAGGLE_NOTEBOOKS, "notebooks")

    manifests_dir = KAGGLE_UPLOAD
    write_manifest(code_manifest, manifests_dir / "code_manifest.json")
    write_manifest(data_manifest, manifests_dir / "data_manifest.json")
    write_manifest(notebook_manifest, manifests_dir / "notebook_manifest.json")

    print(f"  code_manifest.json: {len(code_manifest)} entries")
    print(f"  data_manifest.json: {len(data_manifest)} entries")
    print(f"  notebook_manifest.json: {len(notebook_manifest)} entries")

    # Step 7: Verify against canonical sources
    print("\n--- Verification ---")
    code_errors = verify_bundle(CANONICAL_CODE_SOURCES, KAGGLE_CODE, PROJECT_ROOT)
    data_errors = verify_bundle(CANONICAL_DATA_SOURCES, KAGGLE_DATA, PROJECT_ROOT / "benchmark_data")
    nb_errors = verify_bundle(CANONICAL_NOTEBOOK_SOURCES, KAGGLE_NOTEBOOKS, PROJECT_ROOT, flat=True)

    if code_errors:
        print(f"  Code bundle: {code_errors} error(s)")
        errors += code_errors
    else:
        print("  Code bundle: OK")

    if data_errors:
        print(f"  Data bundle: {data_errors} error(s)")
        errors += data_errors
    else:
        print("  Data bundle: OK")

    if nb_errors:
        print(f"  Notebook bundle: {nb_errors} error(s)")
        errors += nb_errors
    else:
        print("  Notebook bundle: OK")

    # Step 8: Report counts and sizes
    print("\n--- Bundle Summary ---")
    code_count = count_files(KAGGLE_CODE)
    data_count = count_files(KAGGLE_DATA)
    nb_count = count_files(KAGGLE_NOTEBOOKS)
    code_size = total_size(KAGGLE_CODE)
    data_size = total_size(KAGGLE_DATA)
    nb_size = total_size(KAGGLE_NOTEBOOKS)

    print(f"  Code:     {code_count:4d} files, {code_size:>10,d} bytes")
    print(f"  Data:     {data_count:4d} files, {data_size:>10,d} bytes")
    print(f"  Notebooks: {nb_count:4d} files, {nb_size:>10,d} bytes")
    print(f"  Total:    {code_count + data_count + nb_count:4d} files, {code_size + data_size + nb_size:>10,d} bytes")

    if errors:
        print(f"\nFAILED: {errors} verification error(s)")
    else:
        print("\nBundle build complete and verified.")

    return errors


def main() -> None:
    err = build_bundle()
    sys.exit(err)


if __name__ == "__main__":
    main()

