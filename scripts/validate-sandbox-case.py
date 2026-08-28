#!/usr/bin/env python3
"""Validate the executable ambiguous-payment sandbox and its public evidence.

This is intentionally a test of the test:

- the deterministic runtime must produce exactly the canonical v0.5 trace;
- that trace must pass the v0.5 semantic validator;
- a same-key replay must reuse one effect;
- parameter drift under the same key must be rejected;
- every canonical negative mutation must fail for the expected reason;
- the committed machine-readable PASS report must match the observed result.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SANDBOX_PATH = ROOT / "sandbox/ambiguous_payment_sandbox.py"
VALIDATOR_PATH = ROOT / "scripts/validate-ambiguous-commit.py"
TRACE_PATH = ROOT / "fixtures/valid-ambiguous-commit-recovery-v0.5.json"
REPORT_PATH = ROOT / "artifacts/sandbox/conformance-report.json"


def load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    try:
        sandbox_module = load_module(SANDBOX_PATH, "di_deterministic_payment_sandbox")
        validator_module = load_module(VALIDATOR_PATH, "di_ambiguous_commit_validator")
        result = sandbox_module.run_demo()
        committed_trace = load_json(TRACE_PATH)
        committed_report = load_json(REPORT_PATH)
    except (OSError, json.JSONDecodeError, RuntimeError, AssertionError, ValueError) as exc:
        print(f"FAIL sandbox setup: {exc}")
        return 1

    ok = True

    if result.trace == committed_trace:
        print("PASS sandbox output is byte-model equivalent to the canonical public trace")
    else:
        ok = False
        print("FAIL sandbox output drifted from the canonical public trace")

    errors = validator_module.validate_ambiguous_commit(result.trace)
    if errors:
        ok = False
        print("FAIL sandbox trace did not satisfy ambiguous-commit-v0.5")
        for error in errors:
            print(f"  - {error}")
    else:
        print("PASS sandbox trace satisfies ambiguous-commit-v0.5")

    if (
        result.committed_effect_count == 1
        and result.first_effect_id == result.replay_effect_id
    ):
        print("PASS lost acknowledgement plus same-key replay preserved exactly one effect")
    else:
        ok = False
        print("FAIL sandbox created or selected a duplicate effect")

    if result.stale_attempt_rejected and result.current_attempt_accepted:
        print("PASS fencing rejected the stale epoch and admitted the current epoch")
    else:
        ok = False
        print("FAIL sandbox fencing admission was inconsistent")

    parameter_guard = sandbox_module.PaymentSandbox(current_fencing_token=102)
    parameter_guard.submit(
        logical_operation_id="operation.parameter-guard.001",
        effect_key="effect-key.parameter-guard.001",
        amount_minor=500,
        currency="usd",
        fencing_token=102,
    )
    try:
        parameter_guard.submit(
            logical_operation_id="operation.parameter-guard.001",
            effect_key="effect-key.parameter-guard.001",
            amount_minor=600,
            currency="usd",
            fencing_token=102,
        )
    except ValueError:
        print("PASS same effect key with changed parameters was rejected")
    else:
        ok = False
        print("FAIL same effect key accepted changed payment parameters")

    mutation_results: list[dict[str, Any]] = []
    for name, mutate, expected_fragment in validator_module.mutation_cases():
        mutated = copy.deepcopy(result.trace)
        mutate(mutated)
        mutation_errors = validator_module.validate_ambiguous_commit(mutated)
        matched = any(expected_fragment in error for error in mutation_errors)
        mutation_results.append(
            {
                "mutation": name,
                "status": "REJECTED" if mutation_errors else "ACCEPTED",
                "expected_error_observed": matched,
            }
        )
        if mutation_errors and matched:
            print(f"PASS mutation {name} rejected for the expected reason")
        else:
            ok = False
            print(f"FAIL mutation {name} did not fail for {expected_fragment!r}")
            for error in mutation_errors:
                print(f"  - {error}")

    expected_report = {
        "report_version": "0.1",
        "profile": "ambiguous-commit-v0.5",
        "input_file": "fixtures/valid-ambiguous-commit-recovery-v0.5.json",
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
        "sandbox": {
            "runtime": "deterministic-provider-neutral",
            "committed_effect_count": result.committed_effect_count,
            "same_key_replay_reused_effect": result.first_effect_id
            == result.replay_effect_id,
            "stale_attempt_rejected": result.stale_attempt_rejected,
            "current_attempt_accepted": result.current_attempt_accepted,
        },
        "mutation_checks": mutation_results,
        "claim_boundary": (
            "Validates the supplied deterministic evidence chain; does not prove "
            "an external provider, database, lease service, or exactly-once runtime."
        ),
    }

    if committed_report == expected_report:
        print("PASS committed conformance report matches observed sandbox results")
    else:
        ok = False
        print("FAIL committed conformance report does not match observed sandbox results")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
