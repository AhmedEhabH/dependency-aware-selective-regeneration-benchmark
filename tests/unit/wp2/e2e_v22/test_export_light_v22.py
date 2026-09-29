"""LIGHT export: priority order, caps, exclusions, secret scan, manifest, verification."""
from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]


def load():
    spec = importlib.util.spec_from_file_location("lx", PROJECT / "scripts" / "wp2_export_light.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_light_export_rules(tmp_path):
    mod = load()
    proj = tmp_path / "p"
    (proj / "a").mkdir(parents=True)
    (proj / "a" / "one.md").write_text("1" * 10)
    (proj / "a" / "big.bin").write_bytes(b"0" * 200)
    (proj / "a" / "cache").mkdir()
    (proj / "a" / "cache" / "x.json").write_text("{}")
    (proj / "a" / "leak.txt").write_text("key sk-or-v1-" + "ab" * 20)
    (proj / ".env").write_text("OPENROUTER_API_KEY=x")
    (proj / "b.md").write_text("2" * 60)
    (proj / "c.md").write_text("3" * 60)
    profile = {"include": ["a/**/*", "b.md", "c.md", ".env"], "exclude": ["*/cache/*"],
               "max_file_bytes": 100, "max_total_bytes": 100, "name_prefix": "project-LIGHT"}
    res = mod.build(proj, profile, tmp_path / "out", "STOP_E2E_PROVIDER_OUTAGE")
    assert res["testzip_ok"] and res["within_50mb"]
    assert res["name"].startswith("project-LIGHT-STOP_E2E_PROVIDER_OUTAGE-")
    with zipfile.ZipFile(res["path"]) as z:
        names = set(z.namelist())
        man = json.loads(z.read("LIGHT_MANIFEST.json"))
    assert names == {"a/one.md", "b.md", "LIGHT_MANIFEST.json"}
    reasons = {s["path"]: s["reason"] for s in man["skipped"]}
    assert reasons == {"a/big.bin": "file_over_cap", "a/leak.txt": "secret_like_content",
                       "c.md": "total_cap_reached"}
    assert ".env" not in names and "a/cache/x.json" not in names


def test_real_profile_is_valid_json_and_under_50mb_cap():
    prof = json.loads((PROJECT / "controller" / "light_profile_v22.json").read_text())
    assert prof["max_total_bytes"] <= 50 * 2**20
    assert "research/wp2/e2e_smoke_eng_v22/**/*" in prof["include"]
    assert "controller/*" in prof["include"]
