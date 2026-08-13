from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"

PINNED_SHAS = {
    "todo": "b8a33e20bdaf5b329114273063fbe8d5aa66e9cf",
    "djangocms": "0f633fc9fa213357f4202482aab2b0edad680f95",
    "saleor": "e11a5557eff29fbb2eed36e6ff3cd0af08ab9e10",
}


def _load_module(module_name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_pilot_snapshot_module() -> Any:
    return _load_module(
        "pilot_repo_snapshot_test_helper",
        SCRIPTS_DIR / "pilot_repo_snapshot.py",
    )


def load_pilot_builder_module() -> Any:
    return _load_module(
        "build_pilot_upload_bundle_test_helper",
        SCRIPTS_DIR / "build_pilot_upload_bundle.py",
    )


@pytest.fixture
def hermetic_pilot_repo_materialize(monkeypatch: Any) -> Any:
    """Replace git-checkout materialization with a deterministic local stub.

    The default suite must never touch developer-local caches, network, or the
    real django CMS/Saleor checkouts; real acquisition is the explicit Gate 8
    step outside the default suite. The stub targets the exact module object the
    Pilot bundle builder loads (and caches), so every bundle built under this
    fixture is hermetic and byte-deterministic.
    """
    snapshot_mod = load_pilot_builder_module()._load_pilot_repo_snapshot()

    # Upstream-style Kaggle-unsafe filenames exercised in every hermetic bundle
    # build so the transport encoding is always under test (brackets, at-sign,
    # ampersand, equals-sign, square brackets).
    unsafe_filenames: dict[str, tuple[str, ...]] = {
        "djangocms": (
            "cms/locale/sr@latin/LC_MESSAGES/django.po",
            "cms/static/cms/img/loader@2x.gif",
        ),
        "saleor": (
            "saleor/core/tests/cassettes/test_http_client/test_http_client_disallows_private_ip_ranges[http].yaml",
            "saleor/graphql/core/tests/cassettes/test_core/test_get_oembed_data[https---www.youtube.com-watch-v=dQw4w9WgXcQ-VIDEO].yaml",
            "saleor/plugins/avatax/tests/cassettes/test_avatax/test_calculate_checkout_total[24.39-30.00-True].yaml",
        ),
    }

    def _stub(
        data_repositories_dir: Path,
        repo_cache: Path | None,
        *,
        allow_acquire: bool = False,
        pins: Any = None,
        **_kwargs: Any,
    ) -> dict[str, dict[str, Any]]:
        data_repositories_dir.mkdir(parents=True, exist_ok=True)
        evidence: dict[str, dict[str, Any]] = {}
        for repo_id in ("todo", "djangocms", "saleor"):
            root = data_repositories_dir / repo_id
            root.mkdir(parents=True, exist_ok=True)
            payload = f"pilot-hermetic-marker-{repo_id}\n".encode()
            marker = root / "pilot_hermetic_marker.txt"
            marker.write_bytes(payload)
            for rel in unsafe_filenames.get(repo_id, ()):
                unsafe_path = root / rel
                unsafe_path.parent.mkdir(parents=True, exist_ok=True)
                unsafe_path.write_bytes(
                    f"pilot-hermetic-unsafe-{repo_id}\n".encode()
                )
            staged_files = [p for p in root.rglob("*") if p.is_file()]
            digest = hashlib.sha256()
            for staged in sorted(staged_files, key=lambda p: p.relative_to(root).as_posix()):
                digest.update(staged.relative_to(root).as_posix().encode("utf-8"))
                digest.update(b"\0")
                digest.update(staged.read_bytes())
                digest.update(b"\0")
            evidence[repo_id] = {
                "repo_id": repo_id,
                "mode": "hermetic-stub",
                "requested_sha": PINNED_SHAS[repo_id],
                "resolved_head": "hermetic",
                "file_count": len(staged_files),
                "content_hash": digest.hexdigest(),
                "size_bytes": sum(p.stat().st_size for p in staged_files),
            }
        return evidence

    monkeypatch.setattr(snapshot_mod, "materialize_repositories", _stub)
    return snapshot_mod
