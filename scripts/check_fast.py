"""Dependency-free fast check script for changed-file diagnostics.

Usage:
    python scripts/check_fast.py

Environment: Windows PowerShell, Python 3.11, standard library only.
"""

import os
import subprocess
import sys
from pathlib import Path


def get_git_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print("::error:: Not in a git repository.")
        sys.exit(1)
    return Path(result.stdout.strip())


def get_changed_files(root: Path) -> set[Path]:
    raw = set()
    # staged
    r1 = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=False, cwd=root,
    )
    if r1.returncode == 0 and r1.stdout.strip():
        raw.update(r1.stdout.strip().splitlines())
    # unstaged
    r2 = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, check=False, cwd=root,
    )
    if r2.returncode == 0 and r2.stdout.strip():
        raw.update(r2.stdout.strip().splitlines())
    # untracked
    r3 = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, check=False, cwd=root,
    )
    if r3.returncode == 0 and r3.stdout.strip():
        raw.update(r3.stdout.strip().splitlines())
    return {root / p for p in raw}


def is_ignored(p: Path, root: Path) -> bool:
    rel = p.relative_to(root).as_posix()
    ignored_prefixes = (
        ".git/",
        "__pycache__/",
        ".mypy_cache/",
        ".pytest_cache/",
        ".ruff_cache/",
        "kaggle_upload/code/",
        "benchmark_data/",
        "notebooks/",
        ".gitattributes",
        ".gitignore",
    )
    return any(
        rel.startswith(prefix) or rel == prefix.rstrip("/")
        for prefix in ignored_prefixes
    )


def run_command(cmd: list[str], cwd: Path | None = None,
                label: str | None = None) -> int:
    desc = label or " ".join(cmd)
    print(f"\n:: Running: {desc}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode == 0:
        if result.stdout.strip():
            print(result.stdout.strip()[-2000:])
        print(f"  [OK] {desc}")
    else:
        out = result.stdout.strip() if result.stdout.strip() else ""
        err = result.stderr.strip() if result.stderr.strip() else ""
        tail = (out + "\n" + err).strip()[-2000:]
        print(tail)
        print(f"  [FAIL] {desc} (exit code {result.returncode})")
    return result.returncode


def select_tests(changed_python: list[Path],
                 root: Path) -> list[str]:
    tests: set[str] = set()
    src_dir = root / "src" / "benchmark"
    for fp in changed_python:
        try:
            rel = fp.relative_to(src_dir).as_posix()
        except ValueError:
            rel = ""
        if not rel:
            fn = fp.name
            if fn == "seven_arm_benchmark.py":
                tests.add(str(root / "tests" / "unit" / "test_cli.py"))
                tests.add(str(root / "tests" / "unit" / "execution"
                              / "test_pipeline.py"))
                tests.add(str(root / "tests" / "unit" / "execution"
                              / "test_runner.py"))
                tests.add(str(root / "tests" / "integration"
                              / "test_su0010a_regeneration.py"))
                tests.add(str(root / "tests" / "integration"
                              / "test_su0011_iterative_agent.py"))
            continue
        parts = rel.split("/")
        if not parts:
            continue
        top = parts[0]
        if top == "execution":
            tests.add(str(root / "tests" / "unit" / "execution"))
            tests.add(str(root / "tests" / "integration"
                          / "test_su0010a_regeneration.py"))
            tests.add(str(root / "tests" / "integration"
                          / "test_su0011_iterative_agent.py"))
        elif top == "strategies":
            tests.add(str(root / "tests" / "unit" / "strategies"))
            tests.add(str(root / "tests" / "integration"
                          / "test_su0011_iterative_agent.py"))
        elif top == "checkpoint":
            tests.add(str(root / "tests" / "unit" / "test_checkpoint.py"))
            tests.add(str(root / "tests" / "unit"
                          / "test_su0008_cross_session_reporting.py"))
            tests.add(str(root / "tests" / "unit"
                          / "test_su0006_recovery_activation.py"))
            tests.add(str(root / "tests" / "unit"
                          / "test_su0007_continuous_execution.py"))
        elif top == "statistics":
            tests.add(str(root / "tests" / "unit" / "statistics"))
        elif top == "graph":
            tests.add(str(root / "tests" / "unit" / "graph"))
            tests.add(str(root / "tests" / "unit" / "strategies"))
    # Also add any directly changed test files
    for fp in changed_python:
        if "tests" in fp.parts:
            tests.add(str(fp))
    # Filter to only existing paths; fail clearly on missing configured paths
    result: list[str] = []
    for p in sorted(tests):
        pp = Path(p)
        if pp.exists():
            result.append(p)
        else:
            print(f"::error:: Configured test path does not exist: {p}")
            sys.exit(1)
    return result


def main() -> None:
    root = get_git_root()
    os.chdir(root)
    changed = get_changed_files(root)
    changed = {p for p in changed if not is_ignored(p, root)}

    print(f"Repository root: {root}")
    print(f"Changed files: {len(changed)}")

    # git diff --check (unstaged)
    rc = run_command(["git", "diff", "--check"], cwd=root)
    if rc != 0:
        sys.exit(rc)
    # git diff --cached --check (staged)
    rc = run_command(["git", "diff", "--cached", "--check"], cwd=root)
    if rc != 0:
        sys.exit(rc)

    changed_py = sorted(p for p in changed if p.suffix == ".py")

    if not changed_py:
        print("\nNo Python files changed. Skipping Python checks.")
        return

    prod_py = sorted(
        p for p in changed_py
        if "tests" not in p.parts and "test_" not in p.stem
    )

    # Ruff on changed Python files
    rc = run_command(
        ["ruff", "check"] + [str(p) for p in changed_py],
        label="ruff check <changed-python-files>",
    )
    if rc != 0:
        sys.exit(rc)

    # Mypy on changed production Python files
    if prod_py:
        rc = run_command(
            ["mypy", "--strict"] + [str(p) for p in prod_py],
            label="mypy --strict <changed-production-python-files>",
        )
        if rc != 0:
            sys.exit(rc)
    else:
        print("  [SKIP] No changed production Python files for mypy.")

    # Python compile check
    for fp in changed_py:
        rc = run_command(
            ["python", "-m", "py_compile", str(fp)],
            label=f"python -m py_compile {fp.name}",
        )
        if rc != 0:
            sys.exit(rc)

    # Targeted tests
    test_paths = select_tests(changed_py, root)
    if test_paths:
        rc = run_command(
            ["python", "-m", "pytest", "-q"] + test_paths,
            label="pytest <targeted-tests>",
        )
        if rc != 0:
            sys.exit(rc)
    else:
        print("  [SKIP] No targeted tests matched.")

    print("\nAll fast checks passed.")


if __name__ == "__main__":
    main()
