from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any


class ResultsPackager:
    def __init__(self, runs_dir: Path) -> None:
        self._runs_dir = runs_dir

    def create_zip(self, output_path: Path) -> Path:
        files_to_include: list[Path] = []
        for name in [
            "run_records.jsonl",
            "checkpoint.json",
            "progress.json",
            "benchmark_summary.json",
            "benchmark_summary.partial.json",
        ]:
            p = self._runs_dir / name
            if p.is_file():
                files_to_include.append(p)

        failure_records = self._collect_failure_records()
        if failure_records:
            failures_path = self._runs_dir / "failure_records.json"
            failures_path.write_text(json.dumps(failure_records, indent=2), encoding="utf-8")
            files_to_include.append(failures_path)

        env_meta = self._collect_env_metadata()
        env_path = self._runs_dir / "environment_metadata.json"
        env_path.write_text(json.dumps(env_meta, indent=2), encoding="utf-8")
        files_to_include.append(env_path)

        manifest = self._build_manifest(files_to_include)
        manifest_path = self._runs_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        files_to_include.append(manifest_path)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in files_to_include:
                arcname = fp.name
                zf.write(str(fp), arcname)

        return output_path

    def _collect_failure_records(self) -> list[dict[str, Any]]:
        records_path = self._runs_dir / "run_records.jsonl"
        if not records_path.is_file():
            return []
        failures: list[dict[str, Any]] = []
        with open(records_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("status") in ("failed", "timed_out", "cancelled"):
                        failures.append(record)
                except json.JSONDecodeError:
                    pass
        return failures

    def _collect_env_metadata(self) -> dict[str, Any]:
        import platform
        import sys

        meta: dict[str, Any] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
        }
        try:
            import torch
            meta["torch_version"] = torch.__version__
            meta["cuda_available"] = torch.cuda.is_available()
            if torch.cuda.is_available():
                meta["cuda_version"] = torch.version.cuda
                meta["gpu_name"] = torch.cuda.get_device_name(0)
        except ImportError:
            meta["torch"] = "not available"
        return meta

    def _build_manifest(self, files: list[Path]) -> dict[str, Any]:
        manifest: dict[str, Any] = {}
        for fp in sorted(files):
            if fp.is_file():
                content = fp.read_bytes()
                manifest[fp.name] = {
                    "size_bytes": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
        return manifest
