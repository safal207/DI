#!/usr/bin/env python3
"""Run DI conformance validation against an external trace file.

This is the product-facing wrapper around the canonical semantic validator.
It emits a stable machine-readable report and exits non-zero on conformance
failure.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate-end-to-end-integrity.py"
PROFILE = "end-to-end-integrity-v0.2"


def load_validator() -> Callable[[Any], list[str]]:
    spec = importlib.util.spec_from_file_location("di_end_to_end_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {VALIDATOR_PATH}")

    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    validator = getattr(module, "validate_end_to_end", None)
    if not callable(validator):
        raise RuntimeError("validate_end_to_end() is missing from the canonical validator")
    return validator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a trace against a DI conformance profile."
    )
    parser.add_argument("trace", type=Path, help="Path to a JSON trace file")
    parser.add_argument(
        "--profile",
        choices=[PROFILE],
        default=PROFILE,
        help="Conformance profile to apply",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON report",
    )
    return parser.parse_args()


def make_report(input_file: str, errors: list[str]) -> dict[str, Any]:
    return {
        "report_version": "0.1",
        "profile": PROFILE,
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
        validator = load_validator()
        errors = validator(instance)
    except (OSError, json.JSONDecodeError, RuntimeError) as exc:
        errors = [f"input/validator error: {exc}"]

    report = make_report(str(trace_path), errors)
    print(json.dumps(report, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
