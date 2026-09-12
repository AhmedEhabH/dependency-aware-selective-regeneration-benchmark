#!/usr/bin/env python3
"""M1B — CAP-RELAXED CONTROLLED ENCODING ABLATION executor.

STUDY_ID: scientific-djangocms-controlled-encoding-ablation-16k-01
Classification: POST-HOC CONTROLLED CAP-RELAXED ENCODING ABLATION

Reuses EXACTLY the audited M1A scientific contract (common JSON schema,
candidate map, action vocabulary, reason codes, evidence fields, semantic
validator, scenario texts, repository evidence, prompt template,
serialization-policy blocks, scorer, model qwen/qwen3-coder @ DeepInfra,
temperature 0, Graph OFF) with the ONLY study-level change:

    completion cap: 4096 -> 16384  (for BOTH arms)

Within M1B the ONLY arm-level difference remains the SERIALIZATION_POLICY
block (Full-v2: explicit decision for every candidate incl. PRESERVE;
Sparse-v2: non-PRESERVE only, omitted ids deterministically reconstruct as
PRESERVE). A frozen parity artifact proves that nothing except the completion
cap changed from M1A at the study level and nothing except the serialization
policy differs between the M1B arms.

This module is a thin driver over the audited M1A executor
(scripts/controlled_encoding_ablation_execute.py), overriding only the
cap-related and study-identity module globals. It adds a `parity` subcommand
that compares the M1B frozen inputs against the frozen M1A inputs. All other
subcommands delegate to the audited M1A implementation.

Subcommands:
  prevalidate       pre-run validation
  parity            frozen M1A-vs-M1B study-level parity proof (only cap differs)
  prompt-control    prompt-control proof (M1.4)
  probe             two capability probes @16384 (Probe A Full-v2, Probe B Sparse-v2)
  gates             six deterministic gates + audit
  freeze-manifest   freeze the 60-cell manifest
  run               execute remaining manifest cells
  metrics           compute final metrics + aggregate tables (per arm)
  interpret         apply the frozen interpretation decision rule
  close             closure six gates + audit
  all               prevalidate -> parity -> prompt-control -> probe -> gates ->
                    freeze-manifest -> run -> metrics -> interpret -> close
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from scripts import controlled_encoding_ablation_execute as m1a  # noqa: E402

# ---------------------------------------------------------------------------
# M1B overrides — the ONLY study-level change from M1A is the completion cap.
# ---------------------------------------------------------------------------

STUDY_ID = "scientific-djangocms-controlled-encoding-ablation-16k-01"
STUDY_DIR = _PROJECT_DIR / "research" / "controlled-encoding-ablation-16k-01"
EXPECTED_BRANCH = "research/controlled-encoding-ablation-16k-01"
WIRING_TAG = "controlled-encoding-ablation-16k-wiring-verified-01"
STUDY_TAG = "controlled-encoding-ablation-16k-study-01-audited"
CAP = 16384  # the ONLY change from M1A (4096 -> 16384, both arms)
SCIENTIFIC_CEILING_USD = 0.75
RUNTIME_CEILING_SECONDS = 4 * 3600

# Apply overrides to the audited M1A executor module globals.
m1a.STUDY_ID = STUDY_ID
m1a.STUDY_DIR = STUDY_DIR
m1a.EXPECTED_BRANCH = EXPECTED_BRANCH
m1a.WIRING_TAG = WIRING_TAG
m1a.STUDY_TAG = STUDY_TAG
m1a.CAP = CAP
m1a.SCIENTIFIC_CEILING_USD = SCIENTIFIC_CEILING_USD
m1a.RUNTIME_CEILING_SECONDS = RUNTIME_CEILING_SECONDS

M1A_STUDY_DIR = _PROJECT_DIR / "research" / "controlled-encoding-ablation-01"
M1A_STUDY_ID = "scientific-djangocms-controlled-encoding-ablation-01"


def _parity_checks() -> tuple[list[dict[str, Any]], bool]:
    from benchmark.selection import encoding_ablation as ea

    checks: list[dict[str, Any]] = []
    m1a_freeze = json.loads((M1A_STUDY_DIR / "endpoint_freeze.json").read_text(encoding="utf-8"))

    def _cmp(label: str, ok: bool, a: Any = None, b: Any = None, extra: Any = None) -> None:
        checks.append({"check": label, "ok": bool(ok), "detail": {"m1a": a, "m1b": b, "note": extra}})
        print(f"{'PASS' if ok else 'FAIL'}  {label}")

    # Identity of every scientific input EXCEPT completion cap.
    _cmp("common_schema_sha256", ea.COMMON_SCHEMA_SHA256 == m1a.COMMON_SCHEMA_SHA,
         ea.COMMON_SCHEMA_SHA256, m1a.COMMON_SCHEMA_SHA)
    _cmp("common_template_sha256", ea.COMMON_TEMPLATE_SHA256 == m1a.COMMON_TEMPLATE_SHA,
         ea.COMMON_TEMPLATE_SHA256, m1a.COMMON_TEMPLATE_SHA)
    _cmp("full_policy_sha256", ea.FULL_POLICY_TEMPLATE_SHA256 == m1a.FULL_POLICY_SHA,
         ea.FULL_POLICY_TEMPLATE_SHA256, m1a.FULL_POLICY_SHA)
    _cmp("sparse_policy_sha256", ea.SPARSE_POLICY_TEMPLATE_SHA256 == m1a.SPARSE_POLICY_SHA,
         ea.SPARSE_POLICY_TEMPLATE_SHA256, m1a.SPARSE_POLICY_SHA)
    _cmp("reason_codes_sha256", ea.REASON_CODES_SHA256 == m1a.REASON_CODES_SHA,
         ea.REASON_CODES_SHA256, m1a.REASON_CODES_SHA)
    _cmp("candidate_map_sha256", m1a._derive_mapping().sha256 == m1a.V2_MAPPING_SHA,
         m1a._derive_mapping().sha256, m1a.V2_MAPPING_SHA)
    _cmp("universe_sha256", m1a.wiring.frozen_universe_canonical_hash() == m1a.UNIVERSE_SHA,
         m1a.wiring.frozen_universe_canonical_hash(), m1a.UNIVERSE_SHA)
    _cmp("model_slug", m1a.PRIMARY_MODEL == "qwen/qwen3-coder", m1a.PRIMARY_MODEL, "qwen/qwen3-coder")
    _cmp("provider_tag", m1a.PROVIDER_TAG == "deepinfra/turbo", m1a.PROVIDER_TAG, "deepinfra/turbo")
    _cmp("temperature", m1a.TEMPERATURE == 0.0, m1a.TEMPERATURE, 0.0)
    _cmp("graph_off", True, "OFF", "OFF", "graph not injected in M1A or M1B")
    _cmp("m1a_endpoint_model", m1a_freeze.get("model_id") == "qwen/qwen3-coder",
         m1a_freeze.get("model_id"), "qwen/qwen3-coder")
    _cmp("m1a_endpoint_provider", m1a_freeze.get("provider_tag") == "deepinfra/turbo",
         m1a_freeze.get("provider_tag"), "deepinfra/turbo")
    _cmp("m1a_endpoint_cap_was_4096", m1a_freeze.get("completion_cap") == 4096,
         m1a_freeze.get("completion_cap"), 4096)
    # The ONLY study-level change: completion cap 4096 -> 16384 (both arms).
    _cmp("completion_cap_changed_to_16384", m1a.CAP == 16384, m1a.CAP, 16384,
         "the ONLY study-level change from M1A")

    scenario_hashes = m1a._scenario_hashes()
    for sid, expected in m1a.SCENARIO_EXPECTED_HASHES.items():
        _cmp(f"scenario_sha256_{sid}", scenario_hashes.get(sid) == expected,
             scenario_hashes.get(sid), expected)

    # Within M1B, only the serialization policy differs between arms.
    mapping = m1a._derive_mapping()
    all_pp = True
    for sid in m1a.FINAL_SCENARIOS:
        scenario, _ = m1a.wiring.load_study_scenario(sid)
        full_p = m1a.ea.render_full_prompt(
            scenario_id=sid,
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
            architecture_constraints=[c.description for c in scenario.architecture_constraints],
            mapping=mapping,
        )
        sparse_p = m1a.ea.render_sparse_prompt(
            scenario_id=sid,
            before=scenario.requirement_before,
            after=scenario.requirement_after,
            acceptance_criteria=[c.description for c in scenario.acceptance_criteria],
            architecture_constraints=[c.description for c in scenario.architecture_constraints],
            mapping=mapping,
        )
        proof = m1a.ea.prompt_control_proof(full_p, sparse_p)
        all_pp = all_pp and proof["PROMPT_CONTROLLED_DIFF"] == "PASS"
    _cmp("m1b_prompt_control_only_policy_differs", all_pp,
         None, None, "all 6 scenarios: only SERIALIZATION_POLICY differs between M1B arms")

    passed = all(c["ok"] for c in checks)
    return checks, passed


def cmd_parity(_args: argparse.Namespace) -> int:
    print("=== M1A-vs-M1B STUDY-LEVEL PARITY ===")
    checks, passed = _parity_checks()
    result = {
        "study_id": STUDY_ID,
        "m1a_study_id": M1A_STUDY_ID,
        "only_study_level_change": "completion_cap 4096 -> 16384 (both arms)",
        "within_m1b_only_policy_differs": checks[-1]["ok"],
        "parity": "PASS" if passed else "FAIL",
        "checks": checks,
        "checked_at": m1a._now_iso(),
    }
    STUDY_DIR.mkdir(parents=True, exist_ok=True)
    (STUDY_DIR / "FROZEN_M1A_PARITY.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    print(f"FROZEN_M1A_PARITY={'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


def _parity_passed() -> bool:
    path = STUDY_DIR / "FROZEN_M1A_PARITY.json"
    if not path.is_file():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    return bool(data.get("parity") == "PASS")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prevalidate", help="pre-run validation")
    p.add_argument("--output-dir", type=str, default=str(STUDY_DIR))
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("parity", help="M1A-vs-M1B study-level parity proof")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("prompt-control", help="prompt-control proof (M1.4)")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("probe", help="two non-study capability probes @16384")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("gates", help="six deterministic gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("freeze-manifest", help="freeze the 60-cell manifest")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("run", help="execute remaining manifest cells")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("metrics", help="compute final metrics")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("interpret", help="apply frozen interpretation rule")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("close", help="closure six gates + audit")
    p.set_defaults(_set_study_dir=True)

    p = sub.add_parser("all", help="full pipeline")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--inter-cell-delay", type=float, default=0.0)
    p.add_argument("--skip-gate-check", action="store_true", default=False)
    p.set_defaults(_set_study_dir=True)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if getattr(args, "_set_study_dir", False) and getattr(args, "output_dir", None):
        global STUDY_DIR
        STUDY_DIR = Path(args.output_dir)
        m1a.STUDY_DIR = STUDY_DIR
    if args.command == "prevalidate":
        return m1a.cmd_prevalidate(args)
    if args.command == "parity":
        return cmd_parity(args)
    if args.command == "prompt-control":
        return m1a.cmd_prompt_control(args)
    if args.command == "probe":
        return m1a.cmd_probe(args)
    if args.command == "gates":
        return m1a.cmd_gates(args)
    if args.command == "freeze-manifest":
        return m1a.cmd_freeze_manifest(args)
    if args.command == "run":
        return m1a.cmd_run(args)
    if args.command == "metrics":
        return m1a.cmd_metrics(args)
    if args.command == "interpret":
        return m1a.cmd_interpret(args)
    if args.command == "close":
        return m1a.cmd_close(args)
    if args.command == "all":
        return cmd_all(args)
    print(f"unknown command: {args.command}")
    return 2


def cmd_all(args: argparse.Namespace) -> int:
    if m1a.cmd_prevalidate(args) != 0:
        print("PREVALIDATION FAILED — STOP")
        return 1
    if cmd_parity(args) != 0:
        print("PARITY FAILED — STOP")
        return 1
    if m1a.cmd_prompt_control(args) != 0:
        print("PROMPT CONTROL FAILED — STOP")
        return 1
    if m1a.cmd_probe(args) != 0:
        print("CAPABILITY PROBES FAILED — STOP")
        return 1
    if m1a.cmd_gates(args) != 0:
        print("GATES FAILED — STOP")
        return 1
    if m1a.cmd_freeze_manifest(args) != 0:
        print("MANIFEST FREEZE FAILED — STOP")
        return 1
    if m1a.cmd_run(args) != 0:
        return 1
    if m1a.cmd_metrics(args) != 0:
        return 1
    if m1a.cmd_interpret(args) != 0:
        return 1
    if m1a.cmd_close(args) != 0:
        return 1
    print("\nCONTROLLED_ENCODING_ABLATION_16K PIPELINE COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
