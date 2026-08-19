#!/usr/bin/env python3
"""Validate recovery decision -> execution -> observed state effect binding.

This validator is intentionally narrow. It checks that a recovery decision made
for a failed cycle is the same recovery mode the next cycle declares, the same
mode an Execution Receipt says was actually observed, and that the resulting
state effect is evidence-backed before recovery is called confirmed.

It does not redefine DIF, DI, DRP, or TIP semantics.
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
    ("fixtures/invalid-execution-receipt-mode-mismatch.json", False),
    ("fixtures/invalid-execution-receipt-without-evidence.json", False),
    ("fixtures/invalid-state-effect-target-mismatch.json", False),
    ("fixtures/invalid-state-effect-without-evidence.json", False),
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


def validate_execution_receipt(
    receipt: dict[str, Any],
    *,
    path: str,
    decision: dict[str, Any],
    cycle: dict[str, Any],
    recovery_of: Any,
    execution_mode: Any,
) -> list[str]:
    """Validate that observed execution is faithful to the selected recovery action."""

    errors: list[str] = []
    if receipt.get("receipt_version") != "0.1":
        errors.append(f"{path}.receipt_version: expected '0.1'")
    if not isinstance(receipt.get("receipt_id"), str) or not receipt.get("receipt_id"):
        errors.append(f"{path}.receipt_id: required")

    if receipt.get("recovery_decision_id") != decision.get("decision_id"):
        errors.append(f"{path}.recovery_decision_id: must exactly match recovery_decision.decision_id")
    if receipt.get("source_cycle_id") != recovery_of:
        errors.append(f"{path}.source_cycle_id: must exactly match recovery_of_cycle_id")
    if receipt.get("recovery_cycle_id") != cycle.get("cycle_id"):
        errors.append(f"{path}.recovery_cycle_id: must exactly match the current recovery cycle_id")

    declared = receipt.get("declared_execution_mode")
    observed = receipt.get("observed_execution_mode")
    status = receipt.get("execution_status")
    evidence = receipt.get("evidence_references")
    selected = decision.get("selected_action")

    if declared != execution_mode:
        errors.append(f"{path}.declared_execution_mode: must exactly match recovery cycle execution_mode")
    if declared != selected:
        errors.append(f"{path}.declared_execution_mode: must exactly match matrix selected_action")

    if status not in {"observed", "failed", "unknown"}:
        errors.append(f"{path}.execution_status: unsupported status {status!r}")

    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{path}.evidence_references: execution receipt requires at least one evidence reference")

    if status == "observed":
        if observed != declared:
            errors.append(
                f"{path}.observed_execution_mode: {observed!r} must exactly match declared execution mode {declared!r}"
            )
        if observed == "UNKNOWN":
            errors.append(f"{path}.observed_execution_mode: observed receipt cannot claim UNKNOWN execution mode")
    elif observed not in {declared, "UNKNOWN"}:
        errors.append(
            f"{path}.observed_execution_mode: failed/unknown receipt may only preserve the declared mode or UNKNOWN"
        )

    return errors


def validate_state_effect_receipt(
    effect: dict[str, Any],
    *,
    path: str,
    receipt: dict[str, Any],
    cycle: dict[str, Any],
) -> list[str]:
    """Validate that the observed execution produced the state effect claimed by review."""

    errors: list[str] = []

    if effect.get("effect_version") != "0.1":
        errors.append(f"{path}.effect_version: expected '0.1'")
    if not isinstance(effect.get("effect_id"), str) or not effect.get("effect_id"):
        errors.append(f"{path}.effect_id: required")
    if effect.get("execution_receipt_id") != receipt.get("receipt_id"):
        errors.append(f"{path}.execution_receipt_id: must exactly match execution_receipt.receipt_id")
    if effect.get("recovery_cycle_id") != cycle.get("cycle_id"):
        errors.append(f"{path}.recovery_cycle_id: must exactly match the current recovery cycle_id")

    status = effect.get("effect_status")
    observed_state = effect.get("observed_state")
    evidence = effect.get("evidence_references")

    if status not in {"observed", "failed", "unknown"}:
        errors.append(f"{path}.effect_status: unsupported status {status!r}")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{path}.evidence_references: state effect receipt requires at least one evidence reference")

    envelope = cycle.get("envelope")
    target_state = None
    review = None
    if isinstance(envelope, dict):
        tip = envelope.get("tip")
        if isinstance(tip, dict):
            target_state = tip.get("target_state")
        candidate_review = envelope.get("review")
        if isinstance(candidate_review, dict):
            review = candidate_review

    if effect.get("expected_target_state") != target_state:
        errors.append(f"{path}.expected_target_state: must exactly match envelope.tip.target_state")

    if status == "observed":
        if receipt.get("execution_status") != "observed":
            errors.append(f"{path}.effect_status: observed effect requires an observed Execution Receipt")
        if observed_state != target_state:
            errors.append(
                f"{path}.observed_state: {observed_state!r} must exactly match target state {target_state!r} when effect_status='observed'"
            )

    if isinstance(review, dict) and review.get("status") == "reviewed":
        if review.get("next_state") == "RECOVERY_CONFIRMED":
            if status != "observed":
                errors.append(f"{path}.effect_status: RECOVERY_CONFIRMED requires an observed state effect")
            if observed_state != target_state:
                errors.append(
                    f"{path}.observed_state: RECOVERY_CONFIRMED requires the target state to be actually observed"
                )

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
        receipt = cycle.get("execution_receipt")
        effect = cycle.get("state_effect_receipt")

        if recovery_of is None:
            if execution_mode is not None:
                errors.append(f"{path}.execution_mode: only recovery cycles may declare execution_mode")
            if decision is not None:
                errors.append(f"{path}.recovery_decision: only recovery cycles may carry a recovery decision")
            if receipt is not None:
                errors.append(f"{path}.execution_receipt: only recovery cycles may carry an execution receipt")
            if effect is not None:
                errors.append(f"{path}.state_effect_receipt: only recovery cycles may carry a state effect receipt")
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
            continue

        if not isinstance(receipt, dict):
            errors.append(
                f"{path}.execution_receipt: active recovery cycle requires an Execution Receipt proving observed execution"
            )
            continue

        errors.extend(
            validate_execution_receipt(
                receipt,
                path=f"{path}.execution_receipt",
                decision=decision,
                cycle=cycle,
                recovery_of=recovery_of,
                execution_mode=execution_mode,
            )
        )

        if not isinstance(effect, dict):
            errors.append(
                f"{path}.state_effect_receipt: active recovery cycle requires a State Effect Receipt proving the resulting state"
            )
            continue

        errors.extend(
            validate_state_effect_receipt(
                effect,
                path=f"{path}.state_effect_receipt",
                receipt=receipt,
                cycle=cycle,
            )
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
