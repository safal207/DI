#!/usr/bin/env python3
"""Run DI conformance validation against an external trace file.

The CLI exposes stable machine-readable reports for supported semantic profiles
and exits non-zero on conformance failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PROFILE = "end-to-end-integrity-v0.2"
PROFILE_VALIDATORS: dict[str, tuple[Path, str]] = {
    "end-to-end-integrity-v0.2": (
        SCRIPT_DIR / "validate-end-to-end-integrity.py",
        "validate_end_to_end",
    ),
    "multi-agent-dispatch-v0.3": (
        SCRIPT_DIR / "validate-multi-agent-dispatch.py",
        "validate_multi_agent_dispatch",
    ),
    "lease-split-brain-v0.4": (
        SCRIPT_DIR / "validate-lease-split-brain.py",
        "validate_lease_split_brain",
    ),
}


def load_validator(profile: str) -> Callable[[Any], list[str]]:
    validator_path, function_name = PROFILE_VALIDATORS[profile]
    module_name = "di_conformance_" + profile.replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, validator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {validator_path}")

    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    validator = getattr(module, function_name, None)
    if not callable(validator):
        raise RuntimeError(f"{function_name}() is missing from {validator_path.name}")
    return validator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a trace against a DI conformance profile."
    )
    parser.add_argument("trace", type=Path, help="Path to a JSON trace file")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILE_VALIDATORS),
        default=DEFAULT_PROFILE,
        help="Conformance profile to apply",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON report",
    )
    return parser.parse_args()


def make_report(profile: str, input_file: str, errors: list[str]) -> dict[str, Any]:
    return {
        "report_version": "0.1",
        "profile": profile,
        "input_file": input_file,
        "status": "FAIL" if errors else "PASS",
        "error_count": len(errors),
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    trace_path = args.trace
    errors: list[str]

    try:
        with trace_path.open("r", encoding="utf-8") as handle:
            instance = json.load(handle)
        validator = load_validator(args.profile)
        errors = validator(instance)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        errors = [f"input/validator error: {exc}"]

    report = make_report(args.profile, str(trace_path), errors)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
