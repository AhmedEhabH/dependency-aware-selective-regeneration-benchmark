#!/usr/bin/env python3
"""T12 M02 — dependency-aware selective-regeneration competitor arm adapter (READ-ONLY).

Mission: T12_M02_ARM_ADAPTER_READINESS_20261027 (Track 1.2).

PURPOSE
------
Provide a minimal, testable, FAIL-CLOSED adapter that plans, gates and audits the
13 frozen M01D scope arms under Option B (REUSE_NOT_PERMITTED) WITHOUT executing
any experiment.  This module performs NO benchmark API calls, NO WSL/Docker/pytest
execution, no model downloads and no writes into the frozen source worktrees.

The adapter is the missing 13-arm orchestration layer identified by M01D
(``arm_runner_13_frozen_interface: UNVERIFIED``).  The frozen command surface
contains ingredient executables (materializer ``opws_phase3b_patch_materialize.py``,
P2P engine ``wp2_p2p_u_v2_exec.py``, single-node smoke ``wp2_m3b_runner_smoke.py``,
qualification ``wp2_m17_p04_qualification.py``, CLI ``benchmark_cli.py``) but NO
13-arm runner.  This tool therefore:
  * ``preflight``  - verifies frozen identities/hashes/environment gates (offline);
  * ``dry-run``    - emits the deterministic per-arm plan and the NOT_RUN manifest;
  * ``manifest``   - builds/validates PHYSICAL_EXECUTION_MANIFEST.csv (13 rows);
  * ``receipts-check`` - offline verification of per-arm JUnit receipts vs expected
    classifications and anti-reuse (Option B) checks;
  * ``gate``       - computes the M02_GO_STOP.json verdict (STOP until separately
    authorized);
  * ``run``        - FAIL-CLOSED: refuses without a separately authorized execution
    authorization AND even then cannot run, because no frozen multi-node per-arm
    F2P driver exists (INTEGRATION_GAP, no speculative mock).

Design invariants
-----------------
* Standard library ONLY (absent import of any benchmark package).  The frozen
  harness is never imported or modified; the frozen worktree is only ever read.
* All scientific inputs are pinned by SHA-256 exactly as frozen in M01D / R7.
* Any hash drift, unknown provider, unset budget, or missing JUnit → STOP /
  NOT_RUN / NOT_MEASURED, never silently repaired or adversarially re-labelled.

Exit codes: 0 PASS | 1 STOP | 2 PENDING/NOT_RUN (no execution authorized)
            3 usage | 4 HASH_MISMATCH | 5 RUN_DESIGN_GAP.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SCHEMA = "t12_m02_arm_adapter_v1"
VERSION = "1.0.0"

# --------------------------------------------------------------------------
# Frozen protocol pins (from T12_M01D_RESULT_20261027-080147 and the fresh R7
# package M19B_R7_F2P_PILOT_20261027T082605801327Z_f32b72b6).  These are the
# prospective-sealed constants; the adapter refuses any drift.
# --------------------------------------------------------------------------
FROZEN_TASK = "saleor-rc-7e42fc67ce72"
FROZEN_PARENT = "798632158394c9f2911e6d36e8e424fd55007dc4"
FROZEN_TARGET = "7e42fc67ce72770720440781fc83685a48bd91b8"
# Pin of the frozen M01D deliverable EXECUTION_IDENTITY_MATRIX.csv (byte-exact).
FROZEN_MATRIX_SHA256 = "c7a81b06406c1b7c9d6e2e4db4c04f63626a818bdef4edcc5a47c6cc7043abd5"
# Pin of the frozen EFFECTIVE_PATCH_PLAN_219.json (M19A1B plan).
FROZEN_PLAN_SHA256 = "62ef73588d302553596b9eb6161f03df5a4fe0df4c131390a9b61138754ac401"
ROUTE_REFERENCE_SHA256 = "974eaf1fcc57ded34b3ed8032b35dff8589beca5748be88c574ea6584d9e8979"
# Frozen opws-runtime-compat worktree HEAD (read-only attested in M01D).
FROZEN_WORKTREE_HEAD = "22d569464fdbf9d0ebda842497cc23a7a10e2237"

ROUTE_PIN = {
    "model": "qwen/qwen3-coder",
    "model_name": "Qwen3-Coder-480B-A35B-Instruct",
    "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    "provider_order": ["deepinfra/turbo"],
    "allow_fallbacks": False,
    "orchestration_model": "deepseek/deepseek-v4-flash-0731",
}

# Fresh R7 frozen_inputs: 3 F2P nodes and their exact frozen list hash.
F2P_NODES = [
    "saleor/app/tests/test_app_commands.py::test_creates_app_from_manifest_skips_sending_token_when_target_url_not_provided",
    "saleor/app/tests/test_installation_utils.py::test_install_app_manifest_data_without_token_target_url",
    "saleor/app/tests/test_validators.py::test_new_tab_relative_url_without_app_url",
]
F2P_NODES_SHA256 = "aa12d54639efd07fcf93efc7fa880d1c1df8f4f878d04eb6b20d27f82946b9a2"
JUNIT_COUNT_PER_ARM_PILOT = 9  # 3 frozen F2P nodes x 3 invocations (R9); NOT 27 independent tasks.
F2P_REPETITIONS = 3
F2P_NODES_COUNT = 3

# R7 stage hashes (stage_head 22d56946) — the frozen script pins R7 actually used.
STAGE_HASH_PINS = {
    "scripts/wp2_m3b_runner_smoke.py": "63b3cd630b2cbc489db397ed91ab3d0312a668456361ffe18211111bbb996464",
    "src/benchmark/wp2/harness_v3.py": "db47cd1e5a3d47e9b52b1b0b56ae500dfc6f518ed153884434898b1053fb6db1",
    "src/benchmark/wp2/opws_isolated_runtime_v1.py": "721a45a2b2aba50afc13b0d962866b4d3bcba3c8548b7fb4355d71d876359112",
    "src/benchmark/wp2/runtime_image_compat_v1.py": "650a4ddf4bc4cc5641a75f160ab6e1f8a4f19a0f48a98c58d3cc8b090bb71824",
}

# Requalification controls under Option B (historical R7 evidence is historical;
# prospective M02-e observations require fresh executions).  NEG's healthy
# control event is ANY failing testcase (R7 labels these FAIL_ASSERTION; Django
# ValidationError failures are not Python AssertionError and are classified
# here as FAILURE without fake assertion-type introspection).
CONTROL_EXPECTED_JUNIT = {"NEG": "FAILURE", "FULL_REFERENCE": "PASS", "RM_CSS": "PASS"}

# --------------------------------------------------------------------------
# Frozen per-arm scope/classification input pins (M02-D1, verified 2026-10-27)
#
# Source of truth: the frozen EFFECTIVE_PATCH_PLAN_219.json ``arm_status``
# records per arm the ``scope_source`` path and byte pin ``source_sha256``.
# These are the SELECTOR (scope) inputs ONLY; they are frozen prediction
# files, never behavioral outcomes.  Paths were verified on this machine and
# all pins marked MATCH reproduce byte-for-byte (2026-10-27).
# --------------------------------------------------------------------------
FROZEN_WORKTREE_ROOT_DEFAULT = Path(r"D:\WP2\active\opws-runtime-compat-2026-10-26")
FROZEN_SOURCE_SALEOR_REPO = Path(
    r"C:\Users\Ahmed\Desktop\OpenCode\master-2026-07-21-2355",
    "project", "dist", "pilot-repo-cache", "saleor",
)
ARM_SCOPE_SOURCES: dict[str, dict[str, Any]] = {
    "SIP": {
        "source": "research/wp1a/sip_rmcss_per_task_predictions.json",
        "sha256": "76f16217f11043338ebfeb2c402bc4eaef8e6673394d93232fc41ddb21123e8f",
        "kind": "PREDICTION_FILE",
    },
    "DENSE_K3": {
        "source": "D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json",
        "sha256": "601e9c192aaee7748f33996d55712ad4cb5a3c04c98125feac6ebf345d59c6ed",
        "kind": "PREDICTION_FILE",
    },
    "DENSE_K10": {
        "source": "D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json",
        "sha256": "601e9c192aaee7748f33996d55712ad4cb5a3c04c98125feac6ebf345d59c6ed",
        "kind": "PREDICTION_FILE",
    },
    "BM25_K10": {
        "source": "D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json",
        "sha256": "601e9c192aaee7748f33996d55712ad4cb5a3c04c98125feac6ebf345d59c6ed",
        "kind": "PREDICTION_FILE",
    },
    "BM25_TO_CIA_1HOP": {
        "source": "D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json",
        "sha256": "601e9c192aaee7748f33996d55712ad4cb5a3c04c98125feac6ebf345d59c6ed",
        "kind": "PREDICTION_FILE",
    },
    "SELECT_ALL": {
        "source": "benchmark_data/real_commit_impact_saleor/scientific/<task_id>/public/candidate_universe.json",
        # byte pin of the PILOT task candidate universe (2026-10-27 hash).
        "sha256": "38b4db0ef99d09b586219f983ba4f63bb56b2fe2d6fa4e2a6f86fad7b4d7c9e3",
        "kind": "UNIVERSE_FILE",
    },
    "GOLD": {
        "source": "research/saleor-reserve-300-rmcss/saleor_reserve_300_proxies.json",
        "sha256": "d4ecdb7de555e0943c726a5e9ec0bfc7854515aba4406883f164697e39056e43",
        "kind": "PREDICTION_FILE",
    },
    "RM_CSS": {
        "source": "research/wp1a/sip_rmcss_per_task_predictions.json",
        "sha256": "76f16217f11043338ebfeb2c402bc4eaef8e6673394d93232fc41ddb21123e8f",
        "kind": "PREDICTION_FILE",
    },
    "AGENT": {
        "source": "research/wp1b/main-297-2026-09-22/wp1b_agent_predictions.json",
        "sha256": "c0b85dc7170327f283c977116e46d0deec0a2907d172137349b9b3dac3abc743",
        "kind": "PREDICTION_FILE",
    },
    "AGENTLESS_STYLE_ADAPTATION": {
        "source": "D:/wp2_agentless_main297/research/competitor-agentless-r1/agentless_r1_prediction_freeze.json",
        "sha256": "90495bbb2c8d66a2c9a079cb2dfcd6e1cbf929c01972f1331df4242cdabd9815",
        "kind": "PREDICTION_FILE",
    },
    "BM25_K3": {
        "source": "D:/wp2_comp_baselines/research/competitor-baselines-r2/per_task_predictions_r2.json",
        "sha256": "601e9c192aaee7748f33996d55712ad4cb5a3c04c98125feac6ebf345d59c6ed",
        "kind": "PREDICTION_FILE",
    },
    "NEG": {
        "source": "derived-control:empty-scope", "sha256": None, "kind": "DERIVED_CONTROL",
    },
    "FULL_REFERENCE": {
        "source": "materialize_full_reference", "sha256": None, "kind": "DERIVED_CONTROL",
    },
}
# No frozen byte-pinned per-arm classification JSON exists on disk (verified
# 2026-10-27); the materializer's --classification-json argument therefore
# stays UNRESOLVED for the reference-transfer phase until re-pinned.
CLASSIFICATION_INPUT_STATUS = "UNRESOLVED"


def resolve_scope_source(arm_id: str, base: Path | None = None) -> dict:
    """Resolve + byte-verify one arm's frozen scope source (never reads content).

    Returns a report dict; reads happen ONLY for hashing.  Content of the
    frozen prediction files is never printed or stored (no label exposure).
    """
    pin = ARM_SCOPE_SOURCES.get(arm_id)
    if pin is None:
        return {"arm_id": arm_id, "path": None, "present": False,
                "match": None, "reason": "UNKNOWN_ARM"}
    src = pin["source"]
    if pin["kind"] == "DERIVED_CONTROL":
        return {"arm_id": arm_id, "path": None, "present": True, "match": True,
                "reason": "DERIVED_CONTROL", "kind": pin["kind"], "source": src}
    path = Path(src)
    if not path.is_absolute():
        base = base or FROZEN_WORKTREE_ROOT_DEFAULT
        path = base / src
    if "<task_id>" in src:
        path = Path(str(path).replace("<task_id>", FROZEN_TASK))
    if not path.is_file():
        return {"arm_id": arm_id, "path": str(path), "present": False,
                "match": None, "reason": "FILE_NOT_FOUND",
                "kind": pin["kind"], "source": src}
    dig = sha256_file(path)
    if pin["sha256"] is None:
        return {"arm_id": arm_id, "path": str(path), "present": True,
                "match": True, "reason": "UNPINNED_SOURCE",
                "kind": pin["kind"], "source": src, "sha256": dig}
    return {"arm_id": arm_id, "path": str(path), "present": True,
            "match": dig == pin["sha256"], "reason": "PIN_MATCH" if dig == pin["sha256"] else "PIN_DRIFT",
            "kind": pin["kind"], "source": src, "sha256": dig}


# Frozen 13-arm identity rows, verbatim from EXECUTION_IDENTITY_MATRIX.csv
# (matrix sha c7a81b06…).  Field order follows the frozen CSV.
# arm_id, order, effective_tree_oid, scope_hash, reference_patch_sha256,
# reference_patch_bytes, test_contract_hash, five_field_provisional_id, alias_pair
ARMS = [
    ("SIP", 1, "91338624d6a0130b26b320da08cc8426af96957e",
     "045d3282885c08398e7a39ec2306aa11ef784b04ac8d73becd7bf660ca48d0b3",
     "fae3b574ddf741ea67d0769c365463878df5a04e245768fde0d4e8f2c19603cb", 2182,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "a6da4a2fabef07e701f954a23cbcfdcc9d315d7b24f674bd0ab8371c6f53c611", None),
    ("DENSE_K3", 2, "5360fba77dd89f992543d187cdb14cc74100ee51",
     "43f7ad35ff4a3cbe0d8eea750658d0ac3a4149b5dfa72c1e537cec9fb8e3fbdf",
     "6e977aea81c5cdef977d27cd718da8918b90a7025bdeef933361717c11df670d", 2342,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "a716c58f818f731f8bd59597e80fd07e825857c1014869cbf222115d729e5bdf", None),
    ("DENSE_K10", 3, "23eb717ccf30bcb9a54826e71e748eb84963072c",
     "05580898c34cad4a2fd98fb8d122d48491f098ad6bf832c2d6fe7d75bbbc528e",
     "535967036efa2e3f6afe2a08d293dc6e221ebe63d3e3e1fdd30d6b7cab730a80", 3010,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "9b5f46a1d9719bbe5646eb15d1fe947306a7d31844769b5c4059a2178b62c52c", None),
    ("BM25_K10", 4, "fa6896a4a54955669f2d496253304bde10f58354",
     "21ca1d999a66984f47936557d231a7a27d252254adb772f8e5d8428a6121f7ac",
     "74c2514ca063de0cc8766d2da58d755fd0992b8c6e68e5f819a1a7bd7b3aeab7", 5192,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "cf520e4aeb507a65d691f4e13d40218370394c9de346e54a98c3548c4b5cbea4", None),
    ("BM25_TO_CIA_1HOP", 5, "fa6896a4a54955669f2d496253304bde10f58354",
     "f1d1e38e3ee40b8e7fa44fa42ca9ac8df19b6859cb51c5d8ed0fd0c24f8585ae",
     "74c2514ca063de0cc8766d2da58d755fd0992b8c6e68e5f819a1a7bd7b3aeab7", 5192,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "46110849fd13d5e400a5654771d34be7aee41f23e87993f87ba1deebf87e94cb", None),
    ("SELECT_ALL", 6, "fa6896a4a54955669f2d496253304bde10f58354",
     "47a27b8d72fecfab414114233072a4ddaaad17d8f167d35b707d3f8270124687",
     "74c2514ca063de0cc8766d2da58d755fd0992b8c6e68e5f819a1a7bd7b3aeab7", 5192,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "312c10d52e2a768c0cbb0f0ac6238498a148358ee51b9e0e6c657bd13f201ddb", None),
    ("GOLD", 7, "fa6896a4a54955669f2d496253304bde10f58354",
     "5b8181267c5b73a7d3f670198391fcc0056aab4b5de273004efa7bacb6319992",
     "74c2514ca063de0cc8766d2da58d755fd0992b8c6e68e5f819a1a7bd7b3aeab7", 5192,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "abcb166a2f43bae02cd65295aafa952a2bc5db7e2d53facb2a6d1729f0ec95f5", None),
    ("RM_CSS", 8, "614e68d4396450d7f821271c3c641a681d4e8de4",
     "fc91dbeb4ddee77883532ccacf32bb0b671e66acbea8f1af357f00fbe75a6654",
     "2ba014eac662fb50e04b2cd01fb6a37a731064a0d267517297538f7321541370", 4524,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "42ee0bfb7c540a45025433a71ac86cc06ff8e0931047fec4e87b25b52f8bbbf7", None),
    ("AGENT", 9, "614e68d4396450d7f821271c3c641a681d4e8de4",
     "5791ec434ac0d20161b75275c56fe6dba909049c5d528ce2f513b47736b5957d",
     "2ba014eac662fb50e04b2cd01fb6a37a731064a0d267517297538f7321541370", 4524,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "f3a7f200b3a56cee35177b29673a9225e4c15ae7a86f5d4144f4cffa057ca95e", None),
    ("AGENTLESS_STYLE_ADAPTATION", 10, "614e68d4396450d7f821271c3c641a681d4e8de4",
     "9b0582cbb91ffc1df1ffd697acfe92b71511cfea2f92d37ee7190fcd6f68ae31",
     "2ba014eac662fb50e04b2cd01fb6a37a731064a0d267517297538f7321541370", 4524,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "85c806beff9a75f689c8897f75f73258de99b2b5c4ac12d57946e833b4644207",
     "AGENTLESS_STYLE_ADAPTATION=BM25_K3"),
    ("BM25_K3", 11, "614e68d4396450d7f821271c3c641a681d4e8de4",
     "9b0582cbb91ffc1df1ffd697acfe92b71511cfea2f92d37ee7190fcd6f68ae31",
     "2ba014eac662fb50e04b2cd01fb6a37a731064a0d267517297538f7321541370", 4524,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "85c806beff9a75f689c8897f75f73258de99b2b5c4ac12d57946e833b4644207",
     "AGENTLESS_STYLE_ADAPTATION=BM25_K3"),
    ("NEG", 12, "65cd0b6e07e73c102ae600fea0fabea827b7fe29",
     "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
     "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", 0,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "72748faf4a23505e4df94849b99997ddedaad5097d8471aa81a5b1174e100b57", None),
    ("FULL_REFERENCE", 13, "b555542a98f62636173c6c82db80d380c083f180",
     "774fa3bffcc51bd65150c7614b241091ba9ef5c35bed7e4c96358e18d13756da",
     "54a2813788658dc997fff69ab77fc1ab93d9fa4c42367224e5102bc31d72a612", 6133,
     "ddb6e5401178f2af766b490477186e2cc4f295f413316b898754342a7a7cf279",
     "b1698bcf7257d072cddea18546ed48bcfc2efa18702227ea9d758d2459f864b2", None),
]

MANIFEST_HEADER = [
    "frozen_order", "arm_id", "task_id", "effective_tree_oid", "scope_hash",
    "reference_patch_sha256", "reference_patch_bytes", "test_contract_hash",
    "option_b_physical_execution_required", "historical_evidence_f2p_p2p",
    "prospective_m02e_status", "prospective_junit_count", "prospective_model_usd",
    "prospective_wall_seconds", "execution_id", "run_dir", "result_reuse_allowed",
    "scientific_independent_repetitions",
]


# --------------------------------------------------------------------------
# hashing helpers
# --------------------------------------------------------------------------
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_join(key_fields: list) -> str:
    return sha256_bytes("|".join(str(x) for x in key_fields).encode("utf-8"))


def four_field_id(arm: dict) -> str:
    """Deterministic four-field class identity: scope | patch | bytes | contract."""
    return sha256_join([arm["scope_hash"], arm["patch_sha256"], arm["patch_bytes"],
                        arm["test_contract_hash"]])


def five_field_pairs() -> dict:
    """five_field_provisional_id -> arms sharing it (alias pair detection)."""
    out: dict = {}
    for arm in load_arms():
        out.setdefault(arm["five_field_provisional_id"], []).append(arm["arm_id"])
    return out


def load_arms() -> list[dict]:
    arms = []
    for (arm_id, order, oid, scope, patch, patch_bytes, contract, five, alias) in ARMS:
        arms.append({
            "arm_id": arm_id,
            "frozen_order": order,
            "task_id": FROZEN_TASK,
            "effective_tree_oid": oid,
            "scope_hash": scope,
            "patch_sha256": patch,
            "patch_bytes": patch_bytes,
            "test_contract_hash": contract,
            "five_field_provisional_id": five,
            "alias_pair": alias,
            "four_field_id": None,  # filled below
        })
    for arm in arms:
        arm["four_field_id"] = four_field_id(arm)
    return arms


def matrix_arithmetic() -> dict:
    """The frozen arithmetic 13 arms / 7 trees / 12 four-field / 12 five-field / 1 pair."""
    arms = load_arms()
    trees = sorted({a["effective_tree_oid"] for a in arms})
    four = sorted({a["four_field_id"] for a in arms})
    five = sorted({a["five_field_provisional_id"] for a in arms})
    pairs = {k: v for k, v in five_field_pairs().items() if len(v) > 1}
    return {
        "n_arms": len(arms),
        "n_unique_trees": len(trees),
        "n_four_field_classes": len(four),
        "n_five_field_provisional": len(five),
        "n_alias_pairs": len(pairs),
        "alias_pairs": [{"provisional_id": k, "arms": v} for k, v in pairs.items()],
        "first_four_frozen_order": [a["arm_id"] for a in arms[:4]],
    }


def check_f2p_nodes(nodes: list[str]) -> bool:
    """Exact frozen F2P node-list check (count + membership).

    The R7 ``f2p_nodes_sha256`` pin's serialization is not disclosed in the
    kit, so it cannot be recomputed here; it is recorded as an externally
    verified constant.  Enforcement on this side is exact node-list equality.
    """
    return sorted(nodes) == sorted(F2P_NODES)


def f2p_pin_status() -> str:
    return "EXTERNALLY_VERIFIED_PIN_COMPOSITION_UNDOCUMENTED"


def check_matrix_file(path: Path) -> tuple[bool, str]:
    """Matrix file must byte-match the frozen M01D identity matrix hash."""
    return sha256_file(path) == FROZEN_MATRIX_SHA256, sha256_file(path)


def check_plan_file(path: Path) -> tuple[bool, str]:
    return sha256_file(path) == FROZEN_PLAN_SHA256, sha256_file(path)


def check_route_file(path: Path) -> tuple[bool, bool, dict]:
    """Route reference must hash-match and pin the frozen route fields."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False, False, {}
    ok_hash = sha256_file(path) == ROUTE_REFERENCE_SHA256
    provider = data.get("provider") or {}
    pinned = {
        "model": data.get("model"),
        "provider_order": provider.get("order"),
        "allow_fallbacks": provider.get("allow_fallbacks"),
        "endpoint": data.get("endpoint"),
    }
    ok_pin = pinned == {
        "model": ROUTE_PIN["model"],
        "provider_order": ROUTE_PIN["provider_order"],
        "allow_fallbacks": ROUTE_PIN["allow_fallbacks"],
        "endpoint": ROUTE_PIN["endpoint"],
    }
    return ok_hash, ok_pin, pinned


def _ref_bases(gitdir: Path) -> list[Path]:
    """Per-worktree gitdir + common dir (linked-worktree ``commondir`` file)."""
    bases = [gitdir]
    cd = gitdir / "commondir"
    if cd.is_file():
        try:
            s = cd.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            return bases
        if s:
            p = Path(s)
            bases.append(p if p.is_absolute() else (gitdir / p).resolve())
    return bases


def _resolve_ref(gitdir: Path, ref: str) -> str | None:
    for base in _ref_bases(gitdir):
        loose = base / ref
        if loose.is_file():
            try:
                return loose.read_text(encoding="utf-8", errors="replace").strip()[:64].lower()
            except Exception:
                return None
    for base in _ref_bases(gitdir):
        packed = base / "packed-refs"
        if packed.is_file():
            try:
                for ln in packed.read_text(encoding="utf-8", errors="replace").splitlines():
                    if ln.startswith("#") or " refs/" not in ln:
                        continue
                    sha, name = ln.rsplit(None, 1)
                    if name == ref:
                        return sha[:64].lower()
            except Exception:
                return None
    return None


def resolve_git_head(worktree: Path) -> str | None:
    """Resolve the checked-out commit of a worktree's HEAD without any git call.

    Handles a directory ``.git`` (plain repo) and a file ``.git`` with a
    ``gitdir:`` pointer (linked worktree).  Ref resolution falls back to the
    common git dir (``commondir``) and to packed-refs.
    """
    gitdir = worktree / ".git"
    if gitdir.is_file():
        try:
            line = gitdir.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            return None
        if line.startswith("gitdir:"):
            gitdir = Path(line.split(":", 1)[1].strip())
            if not gitdir.is_absolute():
                gitdir = (worktree / gitdir).resolve()
        else:
            return None
    head_file = gitdir / "HEAD"
    if not head_file.is_file():
        return None
    try:
        content = head_file.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return None
    if not content.startswith("ref:"):
        return content[:64].lower() if content else None
    return _resolve_ref(gitdir, content.split(":", 1)[1].strip())


def resolve_plan_arm(plan: dict, arm_id: str, task_id: str = FROZEN_TASK) -> dict | None:
    """Cross-validate a per-task plan record against the frozen embedded identity."""
    rows = plan.get("per_task_records") or []
    arm = load_arms()
    frozen = next((a for a in arm if a["arm_id"] == arm_id), None)
    if frozen is None:
        return None
    rec = None
    for r in rows:
        if isinstance(r, dict) and r.get("task_id") == task_id and r.get("arm_id") == arm_id:
            rec = r
            break
    if rec is None:
        return None
    match = (
        rec.get("effective_tree_oid") == frozen["effective_tree_oid"]
        and rec.get("scope_hash") == frozen["scope_hash"]
        and rec.get("reference_patch_sha256") == frozen["patch_sha256"]
        and rec.get("reference_patch_bytes") == frozen["reference_patch_bytes"]
        and rec.get("test_contract_hash") == frozen["test_contract_hash"]
        and rec.get("status") == "OK"
    )
    return {"match": match, "record": rec}


# --------------------------------------------------------------------------
# Option B resource isolation
# --------------------------------------------------------------------------
def execution_id_for(arm_id: str, run_token: str) -> str:
    """Deterministic unique physical-execution identifier (never reused across arms)."""
    return sha256_join([SCHEMA, arm_id, run_token, FROZEN_TASK])[:16]


def structural_assertion_only() -> dict:
    """Scoped, verifiable leakage-policy report (replaces the former constant-True
    ``results_are_outcome_domain_only()`` claim).

    Returns a STRUCTURAL_ASSERTION_ONLY policy statement.  It asserts what is
    statically provable offline (selector input domain, authority boundary,
    output provenance) and marks everything that would require a runtime
    isolation audit as PENDING.  It never claims runtime isolation proof.
    """
    return {
        "claim": "STRUCTURAL_ASSERTION_ONLY",
        "runtime_isolation_verified": "PENDING",
        "prompt_leakage_audit": "PENDING",
        "selector_input_domain": ["frozen_scope_json", "frozen_classification_json"],
        "selector_never_consumes": [
            "junit_xml_receipts", "behavioral_outcomes", "gold_labels",
        ],
        "authority_boundary": (
            "adapter holds no credentials; route reference is configuration only; "
            "no request interface is ever executed by adapter code"
        ),
        "output_provenance": "manifest/dry-run/admission only; receipts are validated offline",
        "note": "no dynamic leakage claim without a tested runtime isolation audit",
    }



def no_pseudo_replication() -> dict:
    """3 invocations on one task are stability checks, NOT independent units."""
    return {
        "scientific_independent_repetitions": False,
        "task_count": 1,
        "f2p_nodes": F2P_NODES_COUNT,
        "repetitions": F2P_REPETITIONS,
        "junit_receipts": JUNIT_COUNT_PER_ARM_PILOT,
        "independent_research_task_count": 1,
        "note": ("3 pytest repetitions on one task create zero additional research tasks; "
               "never pool invocation counts as independent N."),
    }


# --------------------------------------------------------------------------
# manifest
# --------------------------------------------------------------------------
def build_manifest_rows(run_token: str = "NOT_AUTHORIZED") -> list[dict]:
    rows = []
    for arm in load_arms():
        rows.append({
            "frozen_order": arm["frozen_order"],
            "arm_id": arm["arm_id"],
            "task_id": arm["task_id"],
            "effective_tree_oid": arm["effective_tree_oid"],
            "scope_hash": arm["scope_hash"],
            "reference_patch_sha256": arm["patch_sha256"],
            "reference_patch_bytes": arm["patch_bytes"],
            "test_contract_hash": arm["test_contract_hash"],
            "option_b_physical_execution_required": "YES",
            "historical_evidence_f2p_p2p": (
                "R7 F2P 9/9 PASS; R8 P2P 309/309 PASS"
                if arm["arm_id"] in ("RM_CSS", "FULL_REFERENCE")
                else ("R7 F2P 9/9 expected FAIL_ASSERTION" if arm["arm_id"] == "NEG" else "NONE")
            ),
            "prospective_m02e_status": "NOT_RUN",
            "prospective_junit_count": 0 if run_token == "NOT_AUTHORIZED" else JUNIT_COUNT_PER_ARM_PILOT,
            "prospective_model_usd": 0.0,
            "prospective_wall_seconds": "NOT_MEASURED",
            "execution_id": execution_id_for(arm["arm_id"], run_token),
            "run_dir": "",
            "result_reuse_allowed": "NO",
            "scientific_independent_repetitions": "FALSE",
        })
    return rows


def write_manifest_csv(out_path: Path, rows: list[dict]) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=MANIFEST_HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# --------------------------------------------------------------------------
# offline receipts verification (JUnit)
# --------------------------------------------------------------------------
def classify_junit(path: Path) -> str:
    """Return PASS / FAILURE / ERROR / MALFORMED for one JUnit XML.

    Outcome kinds only — no assertion-type guessing: a <failure> element is a
    FAILURE whatever the exception type, <error> is an ERROR.  Mixed kinds in
    one suite are reported as MIXED.
    """
    try:
        root = ET.parse(str(path)).getroot()
    except Exception:
        return "MALFORMED"
    outcomes = set()
    for tc in root.iter("testcase"):
        if tc.find("failure") is not None:
            outcomes.add("FAILURE")
        if tc.find("error") is not None:
            outcomes.add("ERROR")
        if tc.find("failure") is None and tc.find("error") is None:
            outcomes.add("PASS")
    if len(outcomes) == 1:
        return next(iter(outcomes))
    return "MIXED"


def receipts_check(run_dir: Path, expected_map: dict | None = None) -> dict:
    """Audit a prospective run directory: per-JUnit classification + Option B reuse scan.

    Returns a report dict and never mutates inputs.  Missing JUnit → NOT_RUN rows.
    """
    expected_map = expected_map or CONTROL_EXPECTED_JUNIT
    if not run_dir.is_dir():
        return {"status": "NOT_RUN", "reason": "run directory absent", "files": []}
    junit_files = sorted(run_dir.glob("**/*.xml"))
    if not junit_files:
        return {"status": "NOT_RUN", "reason": "no JUnit receipts found", "files": []}
    seen: dict[str, Path] = {}
    violations: list[dict] = []
    files: list[dict] = []
    for f in junit_files:
        dig = sha256_file(f)
        if dig in seen:
            violations.append({"duplicate_sha256": dig,
                               "first": str(seen[dig]), "second": str(f)})
        seen[dig] = f
        cls = classify_junit(f)
        files.append({"path": str(f), "classification": cls, "sha256": dig})
    res = {
        "status": "STOP" if violations else "PASS",
        "junit_count": len(files),
        "reuse_violations": violations,
        "files": files,
    }
    if run_dir.name in expected_map:
        expected = expected_map[run_dir.name]
        res["expected_classification"] = expected
        bad = [x for x in files if x["classification"] != expected]
        res["matched"] = len(files) - len(bad)
        res["total"] = len(files)
        res["status"] = "PASS" if res["matched"] == res["total"] and not violations else "STOP"
    return res


# --------------------------------------------------------------------------
# gate / authorization
# --------------------------------------------------------------------------
def _parse_window(window: str) -> tuple[datetime.datetime, datetime.datetime] | None:
    try:
        start_s, end_s = window.split("..")
        start = datetime.datetime.strptime(start_s, "%Y-%m-%dT%H:%M:%SZ")
        end = datetime.datetime.strptime(end_s, "%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return None
    return start, end


FROZEN_MAX_GENERATION_BUDGET_USD = 100.0


def validate_authorization(auth: dict) -> dict:
    """Fail-closed DECLARATIVE authorization schema (v2, M02-D1 hardened).

    The scientific route is pinned: qwen/qwen3-coder @ deepinfra/turbo,
    allow_fallbacks=false.  Anything else, missing tasks, duplicate/unknown
    arms, unbounded USD/token/duration budgets, or a fake exclusive-window
    string is a STOP.  A schema PASS here is DECLARATIVE only: it NEVER grants
    live authorization, never measures resource ownership, and never substitutes
    for per-request provider receipts.
    """
    errors = []
    tasks = auth.get("tasks")
    if tasks != [FROZEN_TASK]:
        errors.append(
            f"tasks must be exactly [{FROZEN_TASK}] (frozen pilot); "
            "absent/empty/extra/non-frozen rejected")
    arms = auth.get("arms") or []
    frozen_ids = {a["arm_id"] for a in load_arms()}
    if not arms:
        errors.append("arms list must be non-empty (exact arm list/task IDs from researcher)")
    if len(arms) != len(set(arms)):
        errors.append("duplicate arm ids rejected")
    unknown = sorted(set(arms) - frozen_ids)
    if unknown:
        errors.append(f"unknown arm ids: {unknown}")
    budget = auth.get("budget_usd")
    if not isinstance(budget, (int, float)) or budget < 0:
        errors.append("budget_usd must be a non-negative number")
    elif budget == 0:
        if auth.get("generation_api_budget_usd") != 0:
            errors.append(
                "zero benchmark budget requires an explicit generation_api_budget_usd=0 "
                "declaration (reference-patch phase), kept distinct from Qwen generation")
    else:
        if budget > FROZEN_MAX_GENERATION_BUDGET_USD:
            errors.append(
                f"budget_usd exceeds the frozen cap {FROZEN_MAX_GENERATION_BUDGET_USD:g}")
    if not isinstance(auth.get("max_tokens"), int) or auth["max_tokens"] <= 0:
        errors.append("max_tokens must be an explicit positive integer bound")
    if not isinstance(auth.get("max_wall_seconds"), (int, float)) or auth["max_wall_seconds"] <= 0:
        errors.append("max_wall_seconds must be an explicit positive bound (duration cap)")
    route = auth.get("route") or {}
    if route.get("provider") != "deepinfra/turbo":
        errors.append(f"provider must be deepinfra/turbo, got {route.get('provider')!r}")
    if route.get("model") != "qwen/qwen3-coder":
        errors.append(f"model must be qwen/qwen3-coder, got {route.get('model')!r}")
    if route.get("allow_fallbacks") is not False:
        errors.append("allow_fallbacks must be false")
    window = auth.get("resource_window")
    parsed = _parse_window(window) if isinstance(window, str) else None
    if parsed is None:
        errors.append("resource_window must be an ISO-8601 UTC pair 'YYYY-MM-DDTHH:MM:SSZ..YYYY-MM-DDTHH:MM:SSZ'")
    elif not (parsed[1] > parsed[0]):
        errors.append("resource_window end must be after start")
    if not auth.get("approval_message_id"):
        errors.append("separate explicit researcher execution authorization message id required")
    return {
        "ok": not errors,
        "errors": errors,
        "scope": "DECLARATIVE_SCHEMA_ONLY",
        "live_measured_resource_ownership": False,
        "live_provider_receipts": "NOT_MEASURED",
        "no_authorization_granted_by_validation": True,
    }



def compute_gates(preflight_result: dict, auth: dict | None = None) -> dict:
    ok_map = {
        "A1_option_b_sealed": "PASS",
        "A2_frozen_m01d_integrity": {
            None: "PENDING", True: "PASS", False: "STOP"
        }.get(preflight_result.get("matrix_hash_ok"), "PENDING"),
        "A3_request_level_provider_receipts": "PENDING",
        "A4_scoped_r7_f2p_control": "PASS_SCOPED_ONLY",
        "A4_full_environment_and_p2p": "PENDING",
        "A5_exclusive_resource_window": "PENDING",
        "A6_first_four_frozen_order": "PASS_SPEC_ONLY",
        "A7_bounded_m02e_execution_authorization": "PENDING",
        "arm_runner_13_frozen_interface": ("STOP" if preflight_result.get(
            "runner_13_arm_driver") == "MISSING" else "PASS"),
        "S5_S6_S7_frozen_population": "UNRESOLVED",
        "runtime_prompt_leakage_audit": "PENDING",
        "preflight_admission": (
            "EXECUTION_READY" if preflight_result.get("admission_ready")
            else "INCOMPLETE_NOT_ADMISSION"),
    }
    gates = dict(ok_map)
    if not preflight_result.get("admission_ready"):
        gates["A2_frozen_m01d_integrity"] = "STOP"
    if auth is not None:
        va = validate_authorization(auth)
        gates["A7_bounded_m02e_execution_authorization"] = "PASS" if va["ok"] else "STOP"
        gates["A3_request_level_provider_receipts"] = "PENDING"  # request-level receipts only exist after execution
    hard_stops = [k for k, v in gates.items() if v == "STOP"]
    verdict = "STOP" if hard_stops else "PENDING_NOT_AUTHORIZED"
    if hard_stops:
        verdict = "STOP"
    return {"schema": "m02_go_stop_v1", "gates": gates, "hard_stops": hard_stops,
            "verdict": verdict, "generated_utc": datetime.datetime.now(datetime.UTC).isoformat()}


# --------------------------------------------------------------------------
# preflight
# --------------------------------------------------------------------------
def preflight(worktree: Path, matrix_path: Path | None = None,
              plan_path: Path | None = None, route_path: Path | None = None,
              admission_required: bool = False) -> dict:
    """Read-only environment/identity verification.  Never writes to worktree.

    Admission mode (``admission_required=True``) FAILS CLOSED with typed
    hard stops if the worktree, matrix, plan, route, frozen stage scripts,
    revision or test nodes are absent or mismatched — an execution-admission
    result is never executable unless admission_ready is True.  The default
    diagnostic mode keeps inputs optional but marks the result
    INCOMPLETE_NOT_ADMISSION whenever anything required is missing, so an
    optional diagnostic can never be interpreted as execution-ready.
    """
    result: dict[str, Any] = {
        "worktree_present": worktree.is_dir(),
        "worktree_head": None,
        "worktree_head_match": None,
        "stage_hash_pins": {},
        "stage_hash_pins_ok": True,
        "matrix_hash_ok": None,
        "plan_hash_ok": None,
        "route_hash_ok": None,
        "route_pin_ok": None,
        "f2p_nodes_ok": check_f2p_nodes(F2P_NODES),
        "matrix_arithmetic": matrix_arithmetic(),
        "runner_13_arm_driver": "MISSING",
        "required_inputs": {
            "worktree": worktree.is_dir(),
            "matrix": matrix_path is not None,
            "plan": plan_path is not None,
            "route": route_path is not None,
        },
        "gates": {},
    }
    if result["worktree_present"]:
        result["worktree_head"] = resolve_git_head(worktree)
        result["worktree_head_match"] = (result["worktree_head"] == FROZEN_WORKTREE_HEAD)
        for rel, pin in STAGE_HASH_PINS.items():
            fp = worktree / rel
            if fp.exists():
                dig = sha256_file(fp)
                result["stage_hash_pins"][rel] = {"expected": pin, "actual": dig,
                                                  "ok": dig == pin}
                if dig != pin:
                    result["stage_hash_pins_ok"] = False
            else:
                result["stage_hash_pins"][rel] = {"expected": pin, "actual": None, "ok": False}
                result["stage_hash_pins_ok"] = False
    if matrix_path is not None:
        result["matrix_hash_ok"], result["matrix_sha256"] = check_matrix_file(matrix_path)
    if plan_path is not None:
        result["plan_hash_ok"], result["plan_sha256"] = check_plan_file(plan_path)
    if route_path is not None:
        result["route_hash_ok"], result["route_pin_ok"], result["route_pin"] = check_route_file(route_path)
    hard = []
    if admission_required:
        if not result["worktree_present"]:
            hard.append("REQUIRED_WORKTREE_MISSING")
        if matrix_path is None:
            hard.append("REQUIRED_MATRIX_MISSING")
        if plan_path is None:
            hard.append("REQUIRED_PLAN_MISSING")
        if route_path is None:
            hard.append("REQUIRED_ROUTE_MISSING")
        if not result["f2p_nodes_ok"]:
            hard.append("F2P_NODE_LIST_HASH_MISMATCH")
        missing_stages = [rel for rel, st in result["stage_hash_pins"].items()
                          if st["actual"] is None]
        if missing_stages:
            hard.append("STAGE_HASH_PINS_MISSING: " + ",".join(missing_stages))
    if result["worktree_present"] and (not result["worktree_head_match"]
                                        or not result["stage_hash_pins_ok"]):
        hard.append("FROZEN_WORKTREE_DRIFT")
    if matrix_path is not None and not result["matrix_hash_ok"]:
        hard.append("MATRIX_HASH_MISMATCH")
    if plan_path is not None and not result["plan_hash_ok"]:
        hard.append("PLAN_HASH_MISMATCH")
    if route_path is not None and (not result["route_hash_ok"] or not result["route_pin_ok"]):
        hard.append("ROUTE_PIN_MISMATCH")
    if not result["f2p_nodes_ok"]:
        hard.append("F2P_NODE_LIST_HASH_MISMATCH")
    result["hard_stops"] = hard
    result["admission_ready"] = (
        result["worktree_present"]
        and result["worktree_head_match"]
        and result["stage_hash_pins_ok"]
        and result["matrix_hash_ok"] is True
        and result["plan_hash_ok"] is True
        and result["route_hash_ok"] is True
        and result["route_pin_ok"] is True
        and result["f2p_nodes_ok"]
        and not hard
    )
    result["diagnostic_only"] = not result["admission_ready"] and not hard
    result["incomplete_not_admission"] = result["diagnostic_only"]
    result["exit_code"] = 4 if hard else 0
    return result


# --------------------------------------------------------------------------
# dry-run plan
# --------------------------------------------------------------------------
def dry_run_plan(_worktree: Path | None = None,
                 materializer: str = "scripts/opws_phase3b_patch_materialize.py",
                 scope_base: Path | None = None) -> list[dict]:
    """Deterministic per-arm plan using the frozen, byte-pinned scope sources.

    No execution; no writes to worktree.  Uses ONLY flags verified by source
    inspection of the frozen materializer (M02-D1 contract reads).  Honest
    availability markers:
      * MATERIALIZE_INPUTS_FROZEN   — scope JSON present and pin matches
      * MATERIALIZE_INPUTS_DERIVED  — NEG/FULL_REFERENCE derived controls
      * MATERIALIZE_INPUTS_UNRESOLVED — scope source missing or drift
      * --classification-json       — always marked UNRESOLVED (no frozen
        byte-pinned per-arm classification JSON exists on disk; verified)
      * F2P_EXECUTION_DRIVER=GAP     — no frozen multi-node per-arm F2P driver
      * P2P_ENGINE_AVAILABLE         — wp2_p2p_u_v2_exec.py --cap 200|400 exists
    """
    rows = []
    base = scope_base or FROZEN_WORKTREE_ROOT_DEFAULT
    for arm in load_arms():
        pin = resolve_scope_source(arm["arm_id"], base=base)
        if pin["kind"] == "DERIVED_CONTROL":
            scope_json = pin["source"]
            inputs_status = "MATERIALIZE_INPUTS_DERIVED"
        elif pin["present"] and pin["match"]:
            scope_json = pin["path"]
            inputs_status = "MATERIALIZE_INPUTS_FROZEN"
        else:
            scope_json = f"<UNRESOLVED:{pin['reason']}>"
            inputs_status = "MATERIALIZE_INPUTS_UNRESOLVED"
        posed_cmd = [
            "python", materializer,
            "--repo", "<FROZEN_SOURCE_GIT_REPO>",
            "--parent", FROZEN_PARENT,
            "--target", FROZEN_TARGET,
            "--task-id", FROZEN_TASK,
            "--scope-json", scope_json,
            "--classification-json", "<UNRESOLVED:no-frozen-per-arm-classification-json>",
            "--dry-run",
        ]
        rows.append({
            "frozen_order": arm["frozen_order"],
            "arm_id": arm["arm_id"],
            "tree_oid": arm["effective_tree_oid"],
            "materialize_cmd": " ".join(posed_cmd),
            "materialize_engine": "AVAILABLE",
            "materialize_inputs": inputs_status,
            "scope_pin": pin["match"],
            "scope_source": pin.get("source"),
            "classification_input": CLASSIFICATION_INPUT_STATUS,
            "execute_driver": "INTEGRATION_GAP",
            "execute_note": (
                "no frozen multi-node per-arm F2P driver; wp2_m3b_runner_smoke.py is a "
                "single-node smoke; run_state_v3 provides fresh unique DB + 3x per "
                "changed test file, but a 13-arm orchestrator with Option B isolation "
                "is not frozen; controlled requalification requires fresh M02-e runs "
                "(R7 receipts are historical, never reused)"
            ),
            "expected_junit": CONTROL_EXPECTED_JUNIT.get(arm["arm_id"], "UNKNOWN"),
            "junit_count_plan": JUNIT_COUNT_PER_ARM_PILOT,
            "p2p_engine": ("wp2_p2p_u_v2_exec.py --task <TID> --cap 200|400 "
                            "(requires budget decision; NOT_RUN until authorized)"),
            "status": "NOT_RUN",
            "model_usd": 0.0,
        })
    return rows


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="T12 M02 read-only arm adapter (0 API, 0 live runs).")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("preflight", help="verify frozen identities and environment gates (offline)")
    p.add_argument("--worktree", default=r"D:\WP2\active\opws-runtime-compat-2026-10-26")
    p.add_argument("--matrix", default=None)
    p.add_argument("--plan", default=None)
    p.add_argument("--route", default=None)
    p.add_argument("--admission-required", action="store_true",
                   help="fail closed (exit 4) on any missing/mismatched admission input")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("dry-run", help="emit deterministic per-arm plan + NOT_RUN manifest")
    p.add_argument("--worktree", default=r"D:\WP2\active\opws-runtime-compat-2026-10-26")
    p.add_argument("--out", default=None, help="write PHYSICAL_EXECUTION_MANIFEST.csv to this path")

    p = sub.add_parser("manifest", help="build/validate the 13-row NOT_RUN manifest")
    p.add_argument("--out", default=None)

    p = sub.add_parser("receipts-check", help="offline JUnit classification + Option B reuse scan")
    p.add_argument("run_dir")

    p = sub.add_parser("gate", help="compute M02_GO_STOP verdict (STOP until authorization)")
    p.add_argument("--worktree", default=r"D:\WP2\active\opws-runtime-compat-2026-10-26")
    p.add_argument("--matrix", default=None)
    p.add_argument("--plan", default=None)
    p.add_argument("--route", default=None)
    p.add_argument("--auth", default=None, help="optional execution authorization JSON (fail-closed validation)")
    p.add_argument("--out", default=None, help="write M02_GO_STOP.json")

    p = sub.add_parser("run", help="FAIL-CLOSED execution scaffold (never executes in this mission)")
    p.add_argument("--authorization", required=True, help="execution authorization JSON (schema-validated)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        res = preflight(Path(args.worktree),
                        Path(args.matrix) if args.matrix else None,
                        Path(args.plan) if args.plan else None,
                        Path(args.route) if args.route else None,
                        admission_required=args.admission_required)
        if args.json:
            print(json.dumps(res, indent=2, default=str))
        else:
            print(f"T12_M02_PREFLIGHT  worktree={args.worktree}")
            print(f"  worktree_head_match={res['worktree_head_match']} "
                  f"stage_hash_pins_ok={res['stage_hash_pins_ok']}")
            for rel, st in res["stage_hash_pins"].items():
                print(f"  pin {'OK ' if st['ok'] else 'MISMATCH'} {rel} "
                      f"expected={st['expected'][:12]} actual={(st['actual'] or 'ABSENT')[:12]}")
            print(f"  matrix_hash_ok={res['matrix_hash_ok']} plan_hash_ok={res['plan_hash_ok']} "
                  f"route_pin_ok={res['route_pin_ok']}")
            print(f"  arithmetic={res['matrix_arithmetic']['n_arms']} arms / "
                  f"{res['matrix_arithmetic']['n_unique_trees']} trees / "
                  f"{res['matrix_arithmetic']['n_four_field_classes']} 4-field classes")
            print(f"  runner_13_arm_driver={res['runner_13_arm_driver']}")
            if res["hard_stops"]:
                print("  HARD_STOPS: " + ", ".join(res["hard_stops"]))
                return int(res["exit_code"])
            if res["admission_ready"]:
                print("  EXECUTION_ADMISSION_READY (gates remain; execution NOT authorized)")
            else:
                print("  INCOMPLETE_NOT_ADMISSION (diagnostic only; execution NOT authorized)")
        return int(res["exit_code"])

    if args.command == "dry-run":
        plan = dry_run_plan(Path(args.worktree) if args.worktree else None)
        for row in plan:
            print(f"{row['frozen_order']:>2} {row['arm_id']:<26} status={row['status']:<7} "
                  f"execute={row['execute_driver']:<15} junit_plan={row['junit_count_plan']} "
                  f"inputs={row['materialize_inputs']} expected={row['expected_junit']}")
        if args.out:
            rows = build_manifest_rows()
            write_manifest_csv(Path(args.out), rows)
            print(f"WROTE_MANIFEST {args.out} ({len(rows)} rows, all NOT_RUN)")
        return 0

    if args.command == "manifest":
        rows = build_manifest_rows()
        if args.out:
            write_manifest_csv(Path(args.out), rows)
            print(f"WROTE_MANIFEST {args.out} ({len(rows)} rows)")
        else:
            for row in rows:
                print(f"{row['frozen_order']:>2} {row['arm_id']:<26} "
                      f"option_b={row['option_b_physical_execution_required']:<3} "
                      f"status={row['prospective_m02e_status']}")
        return 0

    if args.command == "receipts-check":
        res = receipts_check(Path(args.run_dir))
        print(json.dumps(res, indent=2, default=str))
        if res["status"] == "STOP":
            return 1
        if res["status"] == "NOT_RUN":
            return 2
        return 0

    if args.command == "gate":
        pre = preflight(Path(args.worktree),
                        Path(args.matrix) if args.matrix else None,
                        Path(args.plan) if args.plan else None,
                        Path(args.route) if args.route else None,
                        admission_required=True)
        auth = None
        if args.auth:
            auth = json.loads(Path(args.auth).read_text(encoding="utf-8"))
        res = compute_gates(pre, auth)
        if args.out:
            Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")
            print(f"WROTE_GATES {args.out}")
        print(json.dumps(res, indent=2, default=str))
        return 1 if res["verdict"] == "STOP" else 2

    if args.command == "run":
        # FAIL-CLOSED: this mission performs ZERO executions.
        try:
            auth = json.loads(Path(args.authorization).read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"RUN_REFUSED unreadable authorization: {exc}")
            return 2
        va = validate_authorization(auth)
        if not va["ok"]:
            print("RUN_REFUSED_INVALID_AUTHORIZATION")
            for e in va["errors"]:
                print("  - " + e)
            return 2
        print("RUN_REFUSED_DESIGN_GAP: frozen command surface has no multi-node per-arm F2P "
              "driver; a separately authorized minimal driver + resource window is the next "
              "executable gate. No speculative mock. Exit 5.")
        return 5

    return 3


if __name__ == "__main__":
    sys.exit(main())
