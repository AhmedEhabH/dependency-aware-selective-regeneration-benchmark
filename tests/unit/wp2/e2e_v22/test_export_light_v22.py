"""LIGHT export: priority order, caps, exclusions, secret scan, manifest, verification,
and the naming convention (project-light-YYYY-MM-DD-HHMM.zip; timezone-aware local time,
minute precision; same-minute collision fails closed)."""
from __future__ import annotations

import importlib.util
import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[4]
NAME_RE = re.compile(r"^project-light-\d{4}-\d{2}-\d{2}-\d{4}\.zip$")

FROZEN = datetime(2026, 10, 2, 18, 55, 0, tzinfo=timezone(timedelta(hours=2)))
FROZEN_UTC = "2026-10-02T16:55:00Z"
FROZEN_LOCAL = "2026-10-02T18:55:00+02:00"
FROZEN_OFFSET = "+0200"


def load():
    spec = importlib.util.spec_from_file_location("lx", PROJECT / "scripts" / "wp2_export_light.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_future_name_matches_new_convention():
    mod = load()
    name = mod.future_name(FROZEN)
    assert NAME_RE.match(name), name
    assert name == "project-light-2026-10-02-1855.zip"
    assert name.startswith("project-light-")


def test_future_name_is_deterministic_under_frozen_clock():
    mod = load()
    same_minute = FROZEN + timedelta(seconds=30)
    assert mod.future_name(FROZEN) == mod.future_name(same_minute)
    assert mod.future_name(FROZEN) == mod.future_name(FROZEN)
    # local timezone-aware datetime is formatted at minute precision
    assert re.match(r"^project-light-\d{4}-\d{2}-\d{2}-\d{4}\.zip$", mod.future_name(FROZEN))


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
               "max_file_bytes": 100, "max_total_bytes": 100, "name_prefix": "project-LIGHT",
               "plan_id": "T2_FINALIZE", "phase": "baseline-finalization"}
    res = mod.build(proj, profile, tmp_path / "out", "STOP_E2E_PROVIDER_OUTAGE", now=FROZEN)
    assert res["testzip_ok"] and res["within_50mb"]
    assert res["name"] == mod.future_name(FROZEN)
    assert NAME_RE.match(res["name"]), res["name"]
    assert res["name"].startswith("project-light-")
    with zipfile.ZipFile(res["path"]) as z:
        names = set(z.namelist())
        man = json.loads(z.read("LIGHT_MANIFEST.json"))
    assert names == {"a/one.md", "b.md", "LIGHT_MANIFEST.json"}
    reasons = {s["path"]: s["reason"] for s in man["skipped"]}
    assert reasons == {"a/big.bin": "file_over_cap", "a/leak.txt": "secret_like_content",
                       "c.md": "total_cap_reached"}
    assert ".env" not in names and "a/cache/x.json" not in names
    # include/exclude/cap semantics unchanged (cap byte totals identical to previous run)
    assert man["naming_convention"] == "project-light-YYYY-MM-DD-HHMM"
    assert man["label"] == "STOP_E2E_PROVIDER_OUTAGE"
    assert man["stop_or_completion_token"] == "STOP_E2E_PROVIDER_OUTAGE"
    assert man["created_utc"] == man["export_timestamp_utc"]
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", man["created_utc"])


def test_manifest_identity_fields_still_exist(tmp_path):
    mod = load()
    proj = tmp_path / "p"
    (proj / "a").mkdir(parents=True)
    (proj / "a" / "one.md").write_text("1" * 10)
    profile = {"include": ["a/**/*"], "max_file_bytes": 10**6, "max_total_bytes": 10**6,
               "plan_id": "PLAN_7", "phase": "phase-7",
               "source_run_identifiers": ["run-1", "run-2"]}
    res = mod.build(proj, profile, tmp_path / "out", "COMPLETED", now=FROZEN)
    with zipfile.ZipFile(res["path"]) as z:
        man = json.loads(z.read("LIGHT_MANIFEST.json"))
    for field in ("plan_id", "phase", "label", "stop_or_completion_token",
                  "git_commit", "git_tag", "created_utc", "export_timestamp_utc",
                  "created_local", "local_offset", "naming_convention",
                  "source_run_identifiers", "files", "skipped"):
        assert field in man, f"manifest missing identity field {field}"
    assert man["plan_id"] == "PLAN_7"
    assert man["phase"] == "phase-7"
    assert man["source_run_identifiers"] == ["run-1", "run-2"]
    assert man["created_local"] == FROZEN_LOCAL
    assert man["local_offset"] == FROZEN_OFFSET
    assert man["created_utc"] == FROZEN_UTC
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$", man["created_local"])


def test_collision_fails_closed(tmp_path):
    mod = load()
    proj = tmp_path / "p"
    (proj / "a").mkdir(parents=True)
    (proj / "a" / "one.md").write_text("1" * 10)
    profile = {"include": ["a/**/*"], "max_file_bytes": 10**6, "max_total_bytes": 10**6}
    out = tmp_path / "out"
    out.mkdir()
    # Pre-seed the exact target file that future_name() will produce, so the
    # test is immune to a clock-boundary race between two build() calls.
    name = mod.future_name(FROZEN)
    (out / name).write_bytes(b"tampered")
    res = mod.build(proj, profile, out, "SECOND", now=FROZEN)
    assert res["collision"] is True
    assert res["testzip_ok"] is False
    assert res["bytes"] == 0
    # the exporter must not have overwritten the existing file
    assert (out / name).read_bytes() == b"tampered"


def test_same_minute_collision_fails_closed(tmp_path):
    mod = load()
    proj = tmp_path / "p"
    (proj / "a").mkdir(parents=True)
    (proj / "a" / "one.md").write_text("1" * 10)
    profile = {"include": ["a/**/*"], "max_file_bytes": 10**6, "max_total_bytes": 10**6}
    out = tmp_path / "out"
    out.mkdir()
    # Two exports inside the same minute (different seconds) collide because the
    # filename has minute precision only: no suffix, no overwrite.
    res1 = mod.build(proj, profile, out, "FIRST", now=FROZEN)
    assert res1["collision"] is False
    later_same_minute = FROZEN + timedelta(seconds=45)
    assert mod.future_name(later_same_minute) == mod.future_name(FROZEN)
    res2 = mod.build(proj, profile, out, "SECOND", now=later_same_minute)
    assert res2["collision"] is True
    assert res2["bytes"] == 0
    assert (out / mod.future_name(FROZEN)).read_bytes() != b""


def test_historical_exports_untouched(tmp_path):
    mod = load()
    proj = tmp_path / "p"
    (proj / "a").mkdir(parents=True)
    (proj / "a" / "one.md").write_text("1" * 10)
    profile = {"include": ["a/**/*"], "max_file_bytes": 10**6, "max_total_bytes": 10**6}
    out = tmp_path / "out"
    out.mkdir()
    hist = out / "project-LIGHT-STOP_M16_ADAPTER_FAIL-2026-10-02-1606.zip"
    hist.write_bytes(b"historical")
    mod.build(proj, profile, out, "CLOSURE", now=FROZEN)
    # the historical LIGHT filename/hash is never renamed or modified
    assert hist.read_bytes() == b"historical"
    # and it does not match the new future convention
    assert not NAME_RE.match(hist.name)


def test_real_profile_is_valid_json_and_under_50mb_cap():
    prof = json.loads((PROJECT / "controller" / "light_profile_v22.json").read_text())
    assert prof["max_total_bytes"] <= 50 * 2**20
    assert "research/wp2/e2e_smoke_eng_v22/**/*" in prof["include"]
    assert "controller/*" in prof["include"]
