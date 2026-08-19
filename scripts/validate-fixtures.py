#!/usr/bin/env python3
"""Minimal DI fixture validator.

This script intentionally implements only the small JSON Schema subset needed by
this repository's seed schemas. It uses Python standard library only.

For the cross-stack Decision & Transition Integrity Envelope, the script also
checks reference-continuity invariants that JSON Schema alone cannot express.
For cycle chains, it additionally checks that an observed next state from one
review becomes the exact starting state of the next cycle. Recovery cycles may
also name the exact failed cycle they recover from.

For the Recovery Decision Matrix, the script validates that a selected recovery
action is justified by the evidence and safety conditions carried by the record.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE_SCHEMA = "schemas/decision-transition-envelope.schema.json"
CHAIN_SCHEMA = "schemas/decision-transition-cycle-chain.schema.json"
MATRIX_SCHEMA = "schemas/recovery-decision-matrix.schema.json"

CASES = [
    (
        "fixtures/valid-capability.json",
        "schemas/capability.schema.json",
        True,
    ),
    (
        "fixtures/valid-limitation.json",
        "schemas/limitation.schema.json",
        True,
    ),
    (
        "fixtures/valid-feasibility-check.json",
        "schemas/feasibility-check.schema.json",
        True,
    ),
    (
        "fixtures/invalid-feasibility-missing-request.json",
        "schemas/feasibility-check.schema.json",
        False,
    ),
    (
        "fixtures/valid-decision-transition-envelope.json",
        ENVELOPE_SCHEMA,
        True,
    ),
    (
        "fixtures/valid-decision-transition-envelope-reviewed.json",
        ENVELOPE_SCHEMA,
        True,
    ),
    (
        "fixtures/invalid-decision-transition-envelope-broken-reference.json",
        ENVELOPE_SCHEMA,
        False,
    ),
    (
        "fixtures/invalid-decision-transition-envelope-reviewed-without-evidence.json",
        ENVELOPE_SCHEMA,
        False,
    ),
    (
        "fixtures/valid-decision-transition-cycle-chain-two-cycles.json",
        CHAIN_SCHEMA,
        True,
    ),
    (
        "fixtures/invalid-decision-transition-cycle-chain-state-mismatch.json",
        CHAIN_SCHEMA,
        False,
    ),
    (
        "fixtures/valid-decision-transition-cycle-chain-recovery.json",
        CHAIN_SCHEMA,
        True,
    ),
    (
        "fixtures/invalid-decision-transition-cycle-chain-recovery-without-evidence.json",
        CHAIN_SCHEMA,
        False,
    ),
    (
        "fixtures/valid-recovery-decision-safe-retry.json",
        MATRIX_SCHEMA,
        True,
    ),
    (
        "fixtures/valid-recovery-decision-rollback.json",
        MATRIX_SCHEMA,
        True,
    ),
    (
        "fixtures/valid-recovery-decision-stop.json",
        MATRIX_SCHEMA,
        True,
    ),
    (
        "fixtures/valid-recovery-decision-human-escalation.json",
        MATRIX_SCHEMA,
        True,
    ),
    (
        "fixtures/invalid-recovery-decision-unsafe-retry.json",
        MATRIX_SCHEMA,
        False,
    ),
    (
        "fixtures/invalid-recovery-decision-rollback-unavailable.json",
        MATRIX_SCHEMA,
        False,
    ),
    (
        "fixtures/invalid-recovery-decision-human-escalation-without-trigger.json",
        MATRIX_SCHEMA,
        False,
    ),
]


def load_json(path: Path) -> Any:
    if not path.exists():
        raise ValueError(f"file does not exist: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc


def type_matches(value: Any, expected_type: str) -> bool:
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def validate(instance: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []

    expected_type = schema.get("type")
    if isinstance(expected_type, str) and not type_matches(instance, expected_type):
        return [f"{path}: expected {expected_type}, got {type(instance).__name__}"]

    enum_values = schema.get("enum")
    if enum_values is not None and instance not in enum_values:
        errors.append(f"{path}: value {instance!r} not in enum {enum_values!r}")

    if expected_type == "object" and isinstance(instance, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in instance:
                errors.append(f"{path}: missing required field {field!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties.keys())
            for field in instance.keys():
                if field not in allowed:
                    errors.append(f"{path}: unexpected field {field!r}")

        for field, value in instance.items():
            child_schema = properties.get(field)
            if isinstance(child_schema, dict):
                errors.extend(validate(value, child_schema, f"{path}.{field}"))

    if expected_type == "array" and isinstance(instance, list):
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(instance):
                errors.extend(validate(item, item_schema, f"{path}[{index}]"))

    return errors


def validate_envelope_semantics(instance: Any, path: str = "$") -> list[str]:
    """Validate cross-stack handoff continuity beyond JSON shape."""

    if not isinstance(instance, dict):
        return [f"{path}: envelope must be an object"]

    errors: list[str] = []

    dif = instance.get("dif")
    di = instance.get("di")
    drp = instance.get("drp")
    tip = instance.get("tip")
    review = instance.get("review")

    if not all(isinstance(part, dict) for part in (dif, di, drp, tip, review)):
        return errors

    if dif.get("human_confirmed") is not True:
        errors.append(f"{path}.dif.human_confirmed: cross-stack intent must be human-confirmed")

    if di.get("intent_id") != dif.get("intent_id"):
        errors.append(
            f"{path}.di.intent_id: must exactly match {path}.dif.intent_id to preserve DIF → DI identity"
        )

    if drp.get("feasibility_id") != di.get("feasibility_id"):
        errors.append(
            f"{path}.drp.feasibility_id: must exactly match {path}.di.feasibility_id to preserve DI → DRP identity"
        )

    if tip.get("decision_record_id") != drp.get("record_id"):
        errors.append(
            f"{path}.tip.decision_record_id: must exactly match {path}.drp.record_id to preserve DRP → TIP identity"
        )

    if review.get("transition_id") != tip.get("transition_id"):
        errors.append(
            f"{path}.review.transition_id: must exactly match {path}.tip.transition_id to preserve TIP → Review identity"
        )

    review_status = review.get("status")
    tip_status = tip.get("status")

    if review_status == "reviewed":
        evidence = review.get("evidence_references")
        next_state = review.get("next_state")

        if tip_status != "reviewed":
            errors.append(
                f"{path}.tip.status: must be 'reviewed' when {path}.review.status is 'reviewed'"
            )
        if not isinstance(evidence, list) or not evidence:
            errors.append(
                f"{path}.review.evidence_references: reviewed envelope requires at least one evidence reference"
            )
        if not isinstance(next_state, str) or not next_state or next_state == "UNOBSERVED":
            errors.append(
                f"{path}.review.next_state: reviewed envelope requires a concrete observed next state"
            )

    if review_status == "pending" and tip_status != "committed":
        errors.append(
            f"{path}.tip.status: pending review requires the transition to remain 'committed'"
        )

    return errors


def validate_cycle_chain_semantics(instance: Any) -> list[str]:
    """Validate end-to-end continuity across two or more reviewed cycles."""

    if not isinstance(instance, dict):
        return ["$: cycle chain must be an object"]

    cycles = instance.get("cycles")
    if not isinstance(cycles, list):
        return []

    errors: list[str] = []
    if len(cycles) < 2:
        errors.append("$.cycles: cycle-chain fixture requires at least two cycles")
        return errors

    envelope_schema = load_json(ROOT / ENVELOPE_SCHEMA)

    previous_cycle: dict[str, Any] | None = None
    seen_cycle_ids: set[str] = set()

    for index, cycle in enumerate(cycles):
        path = f"$.cycles[{index}]"
        if not isinstance(cycle, dict):
            continue

        envelope = cycle.get("envelope")
        if not isinstance(envelope, dict):
            continue

        errors.extend(validate(envelope, envelope_schema, f"{path}.envelope"))
        errors.extend(validate_envelope_semantics(envelope, f"{path}.envelope"))

        cycle_id = cycle.get("cycle_id")
        input_state = cycle.get("input_state")
        previous_cycle_id = cycle.get("previous_cycle_id")
        recovery_of_cycle_id = cycle.get("recovery_of_cycle_id")
        tip = envelope.get("tip")
        review = envelope.get("review")

        if cycle_id != envelope.get("envelope_id"):
            errors.append(
                f"{path}.cycle_id: must exactly match {path}.envelope.envelope_id"
            )

        if isinstance(cycle_id, str):
            if cycle_id in seen_cycle_ids:
                errors.append(f"{path}.cycle_id: duplicate cycle_id {cycle_id!r}")
            seen_cycle_ids.add(cycle_id)

        if isinstance(tip, dict) and input_state != tip.get("starting_state"):
            errors.append(
                f"{path}.input_state: must exactly match {path}.envelope.tip.starting_state"
            )

        if index == 0:
            if previous_cycle_id != "NONE":
                errors.append(f"{path}.previous_cycle_id: first cycle must use 'NONE'")
            if recovery_of_cycle_id is not None:
                errors.append(f"{path}.recovery_of_cycle_id: first cycle cannot be a recovery cycle")
        elif previous_cycle is not None:
            expected_previous_id = previous_cycle.get("cycle_id")
            if previous_cycle_id != expected_previous_id:
                errors.append(
                    f"{path}.previous_cycle_id: must exactly match previous cycle_id {expected_previous_id!r}"
                )

            previous_envelope = previous_cycle.get("envelope")
            if isinstance(previous_envelope, dict):
                previous_review = previous_envelope.get("review")
                if isinstance(previous_review, dict):
                    previous_next_state = previous_review.get("next_state")
                    if previous_review.get("status") != "reviewed":
                        errors.append(
                            f"{path}: previous cycle must be reviewed before its next state can seed a new cycle"
                        )
                    if input_state != previous_next_state:
                        errors.append(
                            f"{path}.input_state: must exactly equal previous review.next_state {previous_next_state!r}"
                        )

            if recovery_of_cycle_id is not None:
                if recovery_of_cycle_id != previous_cycle_id:
                    errors.append(
                        f"{path}.recovery_of_cycle_id: recovery must point to the immediately preceding failed cycle {previous_cycle_id!r}"
                    )
                if recovery_of_cycle_id not in seen_cycle_ids:
                    errors.append(
                        f"{path}.recovery_of_cycle_id: referenced recovery source {recovery_of_cycle_id!r} was not observed earlier in the chain"
                    )

        if isinstance(review, dict) and review.get("status") != "reviewed":
            errors.append(
                f"{path}.envelope.review.status: chained cycle must be reviewed before the chain is considered closed"
            )

        previous_cycle = cycle

    return errors


def validate_recovery_matrix_semantics(instance: Any) -> list[str]:
    """Validate that the selected recovery action is justified by known conditions."""

    if not isinstance(instance, dict):
        return ["$: recovery decision matrix must be an object"]

    errors: list[str] = []
    action = instance.get("selected_action")
    evidence = instance.get("evidence_references")
    trigger = instance.get("escalation_trigger")

    if not isinstance(instance.get("rationale"), str) or not instance.get("rationale", "").strip():
        errors.append("$.rationale: recovery decision requires a non-empty rationale")

    if not isinstance(evidence, list) or not evidence:
        errors.append("$.evidence_references: recovery decision requires at least one evidence reference")

    if action == "SAFE_RETRY":
        has_retry_safety = (
            instance.get("idempotency_verified") is True
            or instance.get("operation_reversible") is True
        )
        if not has_retry_safety:
            errors.append(
                "$.selected_action: SAFE_RETRY requires verified idempotency or a reversible operation"
            )
        if instance.get("uncertainty_level") == "high":
            errors.append(
                "$.selected_action: SAFE_RETRY is not allowed while uncertainty remains high"
            )
        if instance.get("consequence_level") == "high":
            errors.append(
                "$.selected_action: SAFE_RETRY is not allowed for high-consequence recovery without escalation"
            )

    elif action == "ROLLBACK":
        if instance.get("rollback_available") is not True:
            errors.append(
                "$.selected_action: ROLLBACK requires an available rollback path"
            )
        if instance.get("operation_reversible") is not True:
            errors.append(
                "$.selected_action: ROLLBACK requires the operation to be classified as reversible"
            )

    elif action == "HUMAN_ESCALATION":
        if trigger == "NONE":
            errors.append(
                "$.escalation_trigger: HUMAN_ESCALATION requires an explicit escalation trigger"
            )

        trigger_matches = {
            "HIGH_CONSEQUENCE": instance.get("consequence_level") == "high",
            "CRITICAL_UNKNOWN": instance.get("uncertainty_level") == "high",
            "AUTHORITY_BOUNDARY": instance.get("authority_boundary") is True,
            "POLICY_REQUIRES_HUMAN": instance.get("policy_requires_human") is True,
        }
        if trigger in trigger_matches and not trigger_matches[trigger]:
            errors.append(
                f"$.escalation_trigger: {trigger} does not match the recorded recovery conditions"
            )

    if action != "HUMAN_ESCALATION" and trigger != "NONE":
        errors.append(
            "$.escalation_trigger: non-escalation recovery actions must use escalation_trigger='NONE'"
        )

    return errors


def run_case(fixture_rel: str, schema_rel: str, expected_pass: bool) -> bool:
    fixture_path = ROOT / fixture_rel
    schema_path = ROOT / schema_rel

    try:
        fixture = load_json(fixture_path)
        schema = load_json(schema_path)
        errors = validate(fixture, schema)
        if schema_rel == ENVELOPE_SCHEMA:
            errors.extend(validate_envelope_semantics(fixture))
        elif schema_rel == CHAIN_SCHEMA:
            errors.extend(validate_cycle_chain_semantics(fixture))
        elif schema_rel == MATRIX_SCHEMA:
            errors.extend(validate_recovery_matrix_semantics(fixture))
    except ValueError as exc:
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
        print("  - fixture unexpectedly passed validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, schema_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, schema_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
