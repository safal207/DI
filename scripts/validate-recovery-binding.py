#!/usr/bin/env python3
"""Validate Recovery Decision Matrix -> recovery-cycle execution binding.

This validator is intentionally narrow. It checks that a recovery decision made
for a failed cycle is the same recovery mode that the next cycle actually
executes. It does not redefine DIF, DI, DRP, or TIP semantics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("fixtures/valid-decision-transition-cycle-chain-recovery.json", True),
    ("fixtures/invalid-recovery-execution-binding-action-mismatch.json", False),
    ("fixtures/invalid-recovery-execution-binding-stop-continued.json", False),
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_matrix(decision: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    action = decision.get("selected_action")
    evidence = decision.get("evidence_references")
    trigger = decision.get("escalation_trigger")

    if decision.get("matrix_version") != "0.1":
        errors.append(f"{path}.matrix_version: expected '0.1'")
    if not isinstance(decision.get("decision_id"), str) or not decision.get("decision_id"):
        errors.append(f"{path}.decision_id: required")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{path}.evidence_references: at least one evidence reference is required")
    if not isinstance(decision.get("rationale"), str) or not decision.get("rationale", "").strip():
        errors.append(f"{path}.rationale: non-empty rationale is required")

    if action == "SAFE_RETRY":
        safe = decision.get("idempotency_verified") is True or decision.get("operation_reversible") is True
        if not safe:
            errors.append(f"{path}.selected_action: SAFE_RETRY requires verified idempotency or reversibility")
        if decision.get("uncertainty_level") == "high":
            errors.append(f"{path}.selected_action: SAFE_RETRY cannot run under high uncertainty")
        if decision.get("consequence_level") == "high":
            errors.append(f"{path}.selected_action: SAFE_RETRY cannot run for high consequence without escalation")
    elif action == "ROLLBACK":
        if decision.get("rollback_available") is not True:
            errors.append(f"{path}.selected_action: ROLLBACK requires rollback_available=true")
        if decision.get("operation_reversible") is not True:
            errors.append(f"{path}.selected_action: ROLLBACK requires operation_reversible=true")
    elif action == "HUMAN_ESCALATION":
        if trigger == "NONE":
            errors.append(f"{path}.escalation_trigger: HUMAN_ESCALATION requires an explicit trigger")
    elif action == "STOP":
        pass
    else:
        errors.append(f"{path}.selected_action: unsupported action {action!r}")

    if action != "HUMAN_ESCALATION" and trigger != "NONE":
        errors.append(f"{path}.escalation_trigger: non-escalation actions must use 'NONE'")

    return errors


def validate_binding(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: chain must be an object"]

    cycles = instance.get("cycles")
    if not isinstance(cycles, list):
        return ["$.cycles: must be an array"]

    errors: list[str] = []
    for index, cycle in enumerate(cycles):
        path = f"$.cycles[{index}]"
        if not isinstance(cycle, dict):
            errors.append(f"{path}: must be an object")
            continue

        recovery_of = cycle.get("recovery_of_cycle_id")
        execution_mode = cycle.get("execution_mode")
        decision = cycle.get("recovery_decision")

        if recovery_of is None:
            if execution_mode is not None:
                errors.append(f"{path}.execution_mode: only recovery cycles may declare execution_mode")
            if decision is not None:
                errors.append(f"{path}.recovery_decision: only recovery cycles may carry a recovery decision")
            continue

        if index == 0:
            errors.append(f"{path}: first cycle cannot be a recovery cycle")
            continue

        previous = cycles[index - 1]
        if not isinstance(previous, dict):
            errors.append(f"{path}: previous cycle is not inspectable")
            continue

        previous_id = previous.get("cycle_id")
        if recovery_of != previous_id:
            errors.append(f"{path}.recovery_of_cycle_id: must equal immediately preceding cycle_id {previous_id!r}")
        if cycle.get("previous_cycle_id") != previous_id:
            errors.append(f"{path}.previous_cycle_id: must equal immediately preceding cycle_id {previous_id!r}")

        previous_envelope = previous.get("envelope")
        previous_next_state = None
        if isinstance(previous_envelope, dict):
            previous_review = previous_envelope.get("review")
            if isinstance(previous_review, dict):
                previous_next_state = previous_review.get("next_state")

        if cycle.get("input_state") != previous_next_state:
            errors.append(
                f"{path}.input_state: must equal the failed cycle's observed next_state {previous_next_state!r}"
            )

        if not isinstance(decision, dict):
            errors.append(f"{path}.recovery_decision: recovery cycle requires an embedded Recovery Decision Matrix record")
            continue

        errors.extend(validate_matrix(decision, f"{path}.recovery_decision"))

        if decision.get("source_cycle_id") != recovery_of:
            errors.append(f"{path}.recovery_decision.source_cycle_id: must equal recovery_of_cycle_id")
        if decision.get("failure_state") != cycle.get("input_state"):
            errors.append(f"{path}.recovery_decision.failure_state: must equal the recovery cycle input_state")

        selected_action = decision.get("selected_action")
        if execution_mode != selected_action:
            errors.append(
                f"{path}.execution_mode: {execution_mode!r} must exactly match matrix selected_action {selected_action!r}"
            )

        if selected_action == "STOP":
            errors.append(
                f"{path}: STOP forbids creation of an active automated recovery cycle; preserve the failed state instead"
            )

    return errors


def run_case(fixture_rel: str, expected_pass: bool) -> bool:
    try:
        instance = load_json(ROOT / fixture_rel)
        errors = validate_binding(instance)
    except (OSError, json.JSONDecodeError) as exc:
        errors = [str(exc)]

    actual_pass = not errors
    expected_label = "pass" if expected_pass else "fail"
    if actual_pass == expected_pass:
        print(f"PASS {fixture_rel} expected={expected_label}")
        return True

    print(f"FAIL {fixture_rel} expected={expected_label}")
    for error in errors:
        print(f"  - {error}")
    if actual_pass and not expected_pass:
        print("  - fixture unexpectedly passed binding validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
