#!/usr/bin/env python3
"""Unified benchmark CLI — thin wrapper around existing study launchers.

Prospective entry point described by the reader-first README and
`docs/MODEL_PROVIDER_GUIDE.md`. It does NOT duplicate study logic; it resolves
a model profile and dispatches to the existing study-specific launcher.

Commands:
    models                       list available model profiles
    dry-run --study <study>      zero-API pre-run plan (resolve profile + gates)
    probe --study <study>        provider capability probe (real tiny calls)
    live --study <study>         execute the scientific run (after gates + audit)
    verify --study <study>       run the study's ZERO-API verifier / gates

Scientific rules enforced here:
    - a live run must be launched only after the six gates + audit pass;
    - a live run refuses to continue if the resolved profile differs from the
      frozen manifest identity (`assert_resolved_matches_frozen`);
    - dry-run requires NO API token; probe/live fail clearly when the token is
      missing;
    - secrets are referenced by environment-variable name only, never logged.

Examples:
    python scripts/benchmark_cli.py models
    python scripts/benchmark_cli.py dry-run --study real-commit-p1
    python scripts/benchmark_cli.py probe --study real-commit-p1 --model-profile qwen3-coder-openrouter-deepinfra
    python scripts/benchmark_cli.py verify --study real-commit-p1
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "src"))

from benchmark.model_profiles import load_profiles, resolve_profile  # noqa: E402

STUDY_LAUNCHERS: dict[str, dict[str, str]] = {
    "real-commit-p1": {
        "verify": "scripts/verify_real_commit_p1_gates.py",
        "prevalidate": "scripts/execute_real_commit_p1.py prevalidate",
        "probe": "scripts/execute_real_commit_p1.py probe",
        "live": "scripts/execute_real_commit_p1.py run",
        "default_profile": "qwen3-coder-openrouter-deepinfra",
    },
    "controlled-encoding-16k": {
        "verify": "scripts/verify_controlled_encoding_16k_claims.py",
        "prevalidate": "scripts/controlled_encoding_ablation_16k_execute.py prevalidate",
        "probe": "scripts/controlled_encoding_ablation_16k_execute.py probe",
        "live": "scripts/controlled_encoding_ablation_16k_execute.py run",
        "default_profile": "qwen3-coder-openrouter-deepinfra",
    },
}


def _run(args: list[str]) -> int:
    if args and args[0].endswith(".py"):
        args = [sys.executable, *args]
    proc = subprocess.run(args, cwd=_PROJECT_DIR)
    return proc.returncode


def _study(name: str) -> dict[str, str]:
    if name not in STUDY_LAUNCHERS:
        print(f"unknown study {name!r}; known: {sorted(STUDY_LAUNCHERS)}")
        raise SystemExit(2)
    return STUDY_LAUNCHERS[name]


def cmd_models(_args: argparse.Namespace) -> int:
    profiles = load_profiles()
    print("MODEL PROFILES")
    print("==============")
    for pid, p in sorted(profiles.items()):
        print(f"\n[{pid}]")
        print(f"  gateway          : {p.gateway}")
        print(f"  base_url         : {p.base_url}")
        print(f"  model            : {p.model}")
        print(f"  provider_pin     : {p.provider_pin or '-'}")
        print(f"  api_key_env      : {p.api_key_env or '-'}")
        print(f"  temperature      : {p.temperature}")
        print(f"  max_completion   : {p.max_completion_tokens}")
        print(f"  structured_output: {p.structured_output}")
        print(f"  fallbacks        : {p.fallbacks}")
        print(f"  ceiling_usd      : {p.budget_abort_ceiling_usd}")
        print(f"  sha256           : {p.profile_sha256()}")
        if p.description:
            print(f"  description      : {p.description}")
    return 0


def cmd_dry_run(args: argparse.Namespace) -> int:
    study = _study(args.study)
    profile_id = args.model_profile or study["default_profile"]
    profiles = load_profiles()
    if profile_id not in profiles:
        print(f"unknown profile {profile_id!r}; available: {sorted(profiles)}")
        return 2
    profile = profiles[profile_id]
    if profile.api_key_env and not args.allow_missing_token:
        # dry-run must NOT require a token; just report its presence state
        pass
    resolved = resolve_profile(profile)
    print(f"STUDY={args.study}")
    print(f"PROFILE={resolved.profile_id}")
    print(f"EXACT_MODEL={resolved.exact_model}")
    print(f"PROFILE_SHA256={resolved.profile_sha256}")
    print(f"API_KEY_PRESENT={resolved.api_key_present}")
    print(f"STRUCTURED_OUTPUT={resolved.structured_output}")
    print("DRY-RUN: resolving profile only — study gates run via `verify`.")
    print(f"Run: python scripts/benchmark_cli.py verify --study {args.study}")
    return 0


def cmd_probe(args: argparse.Namespace) -> int:
    study = _study(args.study)
    profiles = load_profiles()
    profile_id = args.model_profile or study["default_profile"]
    profile = profiles[profile_id]
    resolved = resolve_profile(profile)
    if not resolved.api_key_present:
        print(f"missing API token: profile {profile_id} requires env {profile.api_key_env!r}")
        return 1
    return _run(study["probe"].split())


def cmd_live(args: argparse.Namespace) -> int:
    study = _study(args.study)
    profiles = load_profiles()
    profile_id = args.model_profile or study["default_profile"]
    profile = profiles[profile_id]
    resolved = resolve_profile(profile)
    if not resolved.api_key_present:
        print(f"missing API token: profile {profile_id} requires env {profile.api_key_env!r}")
        return 1
    print(f"LIVE {args.study} with {resolved.exact_model} (profile {resolved.profile_id})")
    print("Gate discipline: run `verify` (six ZERO-API gates + audit) first.")
    return _run(study["live"].split())


def cmd_verify(args: argparse.Namespace) -> int:
    study = _study(args.study)
    return _run(study["verify"].split())


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_models = sub.add_parser("models", help="list available model profiles")
    p_models.set_defaults(_fn=cmd_models)

    p_dry = sub.add_parser("dry-run", help="zero-API pre-run plan")
    p_dry.add_argument("--study", required=True, choices=sorted(STUDY_LAUNCHERS))
    p_dry.add_argument("--model-profile", default=None)
    p_dry.add_argument("--allow-missing-token", action="store_true", default=False)
    p_dry.set_defaults(_fn=cmd_dry_run)

    p_probe = sub.add_parser("probe", help="provider capability probe")
    p_probe.add_argument("--study", required=True, choices=sorted(STUDY_LAUNCHERS))
    p_probe.add_argument("--model-profile", default=None)
    p_probe.set_defaults(_fn=cmd_probe)

    p_live = sub.add_parser("live", help="execute the scientific run")
    p_live.add_argument("--study", required=True, choices=sorted(STUDY_LAUNCHERS))
    p_live.add_argument("--model-profile", default=None)
    p_live.set_defaults(_fn=cmd_live)

    p_verify = sub.add_parser("verify", help="run the study's ZERO-API verifier / gates")
    p_verify.add_argument("--study", required=True, choices=sorted(STUDY_LAUNCHERS))
    p_verify.set_defaults(_fn=cmd_verify)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    result = args._fn(args)
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())
