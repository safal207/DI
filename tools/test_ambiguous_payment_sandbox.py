#!/usr/bin/env python3
"""Mutation-test the deterministic ambiguous-payment sandbox trace.

The baseline trace must PASS. Every canonical v0.5 adversarial mutation must be
rejected for the expected reason. This is the test that checks the test.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Callable

import ambiguous_payment_sandbox as sandbox

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evidence/ambiguous-payment-sandbox/mutation-report.json"


def run_mutations() -> dict[str, Any]:
    _, trace, result = sandbox.run_sandbox()
    module = sandbox.load_validator_module()
    validator: Callable[[Any], list[str]] = getattr(
        module, "validate_ambiguous_commit"
    )
    mutation_cases = getattr(module, "mutation_cases")

    baseline_errors = validator(trace)
    cases: list[dict[str, Any]] = []
    overall_ok = not baseline_errors and result["report"]["status"] == "PASS"

    for name, mutate, expected_fragment in mutation_cases():
        mutated = copy.deepcopy(trace)
        mutate(mutated)
        errors = validator(mutated)
        matching_errors = [error for error in errors if expected_fragment in error]
        rejected_as_expected = bool(errors) and bool(matching_errors)
        overall_ok = overall_ok and rejected_as_expected
        cases.append(
            {
                "mutation": name,
                "expected_error_fragment": expected_fragment,
                "validator_status": "FAIL" if errors else "PASS",
                "rejected_as_expected": rejected_as_expected,
                "matching_errors": matching_errors,
                "all_errors": errors,
            }
        )

    return {
        "report_version": "0.1",
        "suite": "ambiguous-payment-sandbox-mutation-test",
        "baseline": {
            "expected": "PASS",
            "actual": "FAIL" if baseline_errors else "PASS",
            "errors": baseline_errors,
        },
        "mutation_count": len(cases),
        "mutations_rejected_as_expected": sum(
            1 for case in cases if case["rejected_as_expected"]
        ),
        "status": "PASS" if overall_ok else "FAIL",
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the generated report with the committed report",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_mutations()

    if args.check:
        if not args.output.exists():
            print(f"FAIL missing committed mutation report: {args.output}")
            return 1
        actual = json.loads(args.output.read_text(encoding="utf-8"))
        if actual != report:
            print(f"FAIL committed mutation report is not reproducible: {args.output}")
            return 1
        print("PASS committed mutation report is reproducible")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"WROTE mutation report to {args.output}")

    if report["status"] != "PASS":
        print("FAIL mutation suite")
        for case in report["cases"]:
            if not case["rejected_as_expected"]:
                print(f"  - {case['mutation']} was not rejected as expected")
        return 1

    print(
        "PASS test-the-test: baseline accepted and "
        f"{report['mutation_count']} unsafe mutations rejected"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
