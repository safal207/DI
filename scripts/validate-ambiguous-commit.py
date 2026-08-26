#!/usr/bin/env python3
"""Validate ambiguous commit recovery and stable effect identity semantics (v0.5).

v0.4 proves that only the current fenced lease may cross the side-effect
admission boundary. v0.5 adds the post-admission seam: a mutation may have
committed even when its response is lost. The trace must preserve one logical
operation identity, resolve unknown commit state from evidence, and prevent a
committed effect from becoming a new mutation.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/valid-ambiguous-commit-recovery-v0.5.json"
BASE_VALIDATOR_PATH = ROOT / "scripts/validate-lease-split-brain.py"

OBSERVATION_METHODS = {
    "mutation_response",
    "same_key_replay",
    "authoritative_lookup",
    "provider_event",
    "operator_confirmation",
}
COMMIT_STATUSES = {"committed", "not_committed", "unknown"}
RESOLUTION_STATUSES = {"committed", "not_committed", "still_unknown"}
NEXT_ACTIONS = {
    "ACCEPT_EXISTING_EFFECT",
    "RETRY_SAME_EFFECT_KEY",
    "STOP",
    "HUMAN_ESCALATION",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_v04_validator() -> Callable[[Any], list[str]]:
    spec = importlib.util.spec_from_file_location(
        "di_lease_split_brain_v04", BASE_VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.4 validator from {BASE_VALIDATOR_PATH}")
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    validator = getattr(module, "validate_lease_split_brain", None)
    if not callable(validator):
        raise RuntimeError("validate_lease_split_brain() is missing")
    return validator


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_evidence(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(nonempty_string(item) for item in value)
    )


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not nonempty_string(value):
        errors.append(f"{path}: timestamp is required")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid RFC3339/ISO-8601 timestamp {value!r}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"{path}: timestamp must include a timezone offset")
        return None
    return parsed.astimezone(timezone.utc)


def validate_ambiguous_commit(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: trace must be an object"]

    errors: list[str] = []
    if instance.get("profile_version") != "0.5":
        errors.append("$.profile_version: expected '0.5'")

    # Reuse every v0.4 ownership, lease, fencing, and admission invariant.
    try:
        base_validator = load_v04_validator()
        base_view = copy.deepcopy(instance)
        base_view["profile_version"] = "0.4"
        errors.extend(f"v0.4::{error}" for error in base_validator(base_view))
    except RuntimeError as exc:
        errors.append(f"$: cannot load v0.4 validator: {exc}")
        return errors

    operation = instance.get("logical_operation")
    observations = instance.get("commit_outcome_receipts")
    resolution = instance.get("commit_resolution")
    state_effect = instance.get("state_effect_receipt")
    execution = instance.get("execution_receipt")
    attempts = instance.get("dispatch_attempt_receipts")

    if not isinstance(operation, dict):
        errors.append("$.logical_operation: object is required")
        return errors
    if not isinstance(observations, list) or not observations:
        errors.append("$.commit_outcome_receipts: non-empty array is required")
        return errors
    if not isinstance(resolution, dict):
        errors.append("$.commit_resolution: object is required")
        return errors
    if not isinstance(state_effect, dict):
        errors.append("$.state_effect_receipt: object is required")
        return errors
    if not isinstance(execution, dict):
        errors.append("$.execution_receipt: object is required")
        return errors
    if not isinstance(attempts, list):
        errors.append("$.dispatch_attempt_receipts: array is required")
        return errors

    operation_id = operation.get("logical_operation_id")
    effect_key = operation.get("effect_key")
    if operation.get("operation_version") != "0.1":
        errors.append("$.logical_operation.operation_version: expected '0.1'")
    if not nonempty_string(operation_id):
        errors.append(
            "$.logical_operation.logical_operation_id: non-empty string is required"
        )
    if not nonempty_string(effect_key):
        errors.append("$.logical_operation.effect_key: non-empty string is required")
    if not nonempty_string(operation.get("intended_effect")):
        errors.append(
            "$.logical_operation.intended_effect: non-empty string is required"
        )
    if operation.get("identity_contract") not in {
        "same_key_same_effect",
        "authoritative_lookup_only",
    }:
        errors.append(
            "$.logical_operation.identity_contract: unsupported effect identity contract"
        )
    if not nonempty_evidence(operation.get("evidence_references")):
        errors.append(
            "$.logical_operation.evidence_references: operation identity requires evidence"
        )

    accepted_attempt_ids = [
        attempt.get("attempt_id")
        for attempt in attempts
        if isinstance(attempt, dict) and attempt.get("outcome") == "accepted"
    ]
    accepted_attempt_id = (
        accepted_attempt_ids[0] if len(accepted_attempt_ids) == 1 else None
    )

    execution_time = parse_timestamp(
        execution.get("executed_at"), "$.execution_receipt.executed_at", errors
    )

    seen_receipt_ids: set[str] = set()
    committed_effect_ids: set[str] = set()
    authoritative_receipts: list[dict[str, Any]] = []
    previous_observed_at: datetime | None = None
    committed_authoritatively = False

    for index, receipt in enumerate(observations):
        path = f"$.commit_outcome_receipts[{index}]"
        if not isinstance(receipt, dict):
            errors.append(f"{path}: object is required")
            continue

        receipt_id = receipt.get("receipt_id")
        method = receipt.get("observation_method")
        status = receipt.get("commit_status")
        authoritative = receipt.get("authoritative")
        observed_at = parse_timestamp(
            receipt.get("observed_at"), f"{path}.observed_at", errors
        )

        if receipt.get("receipt_version") != "0.1":
            errors.append(f"{path}.receipt_version: expected '0.1'")
        if not nonempty_string(receipt_id):
            errors.append(f"{path}.receipt_id: non-empty string is required")
        elif receipt_id in seen_receipt_ids:
            errors.append(f"{path}.receipt_id: duplicate receipt id {receipt_id!r}")
        else:
            seen_receipt_ids.add(receipt_id)

        if receipt.get("logical_operation_id") != operation_id:
            errors.append(
                f"{path}.logical_operation_id: must match the canonical logical operation"
            )
        if receipt.get("effect_key") != effect_key:
            errors.append(f"{path}.effect_key: must match the canonical effect key")
        if method not in OBSERVATION_METHODS:
            errors.append(f"{path}.observation_method: unsupported method {method!r}")
        if status not in COMMIT_STATUSES:
            errors.append(f"{path}.commit_status: unsupported status {status!r}")
        if not isinstance(authoritative, bool):
            errors.append(f"{path}.authoritative: boolean is required")
        if not nonempty_evidence(receipt.get("evidence_references")):
            errors.append(
                f"{path}.evidence_references: commit observation requires evidence"
            )

        if observed_at is not None:
            if previous_observed_at is not None and observed_at < previous_observed_at:
                errors.append(
                    f"{path}.observed_at: commit observations must be time-ordered"
                )
            if execution_time is not None and observed_at < execution_time:
                errors.append(
                    f"{path}.observed_at: commit observation cannot precede execution"
                )
            previous_observed_at = observed_at

        if method == "mutation_response":
            if receipt.get("dispatch_attempt_id") != accepted_attempt_id:
                errors.append(
                    f"{path}.dispatch_attempt_id: mutation response must bind to the single accepted dispatch attempt"
                )
        elif "dispatch_attempt_id" in receipt and not nonempty_string(
            receipt.get("dispatch_attempt_id")
        ):
            errors.append(
                f"{path}.dispatch_attempt_id: when present it must be a non-empty string"
            )

        committed_effect_id = receipt.get("committed_effect_id")
        if status == "committed":
            if not nonempty_string(committed_effect_id):
                errors.append(
                    f"{path}.committed_effect_id: committed observation requires a stable effect id"
                )
            else:
                committed_effect_ids.add(committed_effect_id)
        elif committed_effect_id is not None:
            errors.append(
                f"{path}.committed_effect_id: only committed observations may carry an effect id"
            )

        if authoritative is True:
            if status == "unknown":
                errors.append(
                    f"{path}: an authoritative observation cannot leave commit status unknown"
                )
            else:
                authoritative_receipts.append(receipt)
                if status == "committed":
                    committed_authoritatively = True
                elif status == "not_committed" and committed_authoritatively:
                    errors.append(
                        f"{path}.commit_status: authoritative history cannot regress from committed to not_committed"
                    )

    if len(committed_effect_ids) > 1:
        errors.append(
            "$.commit_outcome_receipts: one logical operation resolved to multiple committed effect identities"
        )

    if resolution.get("resolution_version") != "0.1":
        errors.append("$.commit_resolution.resolution_version: expected '0.1'")
    if not nonempty_string(resolution.get("resolution_id")):
        errors.append(
            "$.commit_resolution.resolution_id: non-empty string is required"
        )
    if resolution.get("logical_operation_id") != operation_id:
        errors.append(
            "$.commit_resolution.logical_operation_id: must match the canonical logical operation"
        )
    if resolution.get("effect_key") != effect_key:
        errors.append(
            "$.commit_resolution.effect_key: must match the canonical effect key"
        )
    if not nonempty_evidence(resolution.get("evidence_references")):
        errors.append(
            "$.commit_resolution.evidence_references: durable resolution evidence is required"
        )

    resolution_status = resolution.get("resolution_status")
    next_action = resolution.get("selected_next_action")
    if resolution_status not in RESOLUTION_STATUSES:
        errors.append(
            f"$.commit_resolution.resolution_status: unsupported status {resolution_status!r}"
        )
    if next_action not in NEXT_ACTIONS:
        errors.append(
            f"$.commit_resolution.selected_next_action: unsupported action {next_action!r}"
        )

    resolution_time = parse_timestamp(
        resolution.get("resolved_at"), "$.commit_resolution.resolved_at", errors
    )
    if (
        resolution_time is not None
        and previous_observed_at is not None
        and resolution_time < previous_observed_at
    ):
        errors.append(
            "$.commit_resolution.resolved_at: resolution cannot precede its latest observation"
        )

    if authoritative_receipts:
        final_authoritative_status = authoritative_receipts[-1].get(
            "commit_status"
        )
        expected_resolution_status = (
            final_authoritative_status
            if final_authoritative_status in {"committed", "not_committed"}
            else "still_unknown"
        )
        if resolution_status != expected_resolution_status:
            errors.append(
                "$.commit_resolution.resolution_status: must match the latest authoritative commit observation"
            )
    elif resolution_status != "still_unknown":
        errors.append(
            "$.commit_resolution.resolution_status: without authoritative commit evidence the result must remain still_unknown"
        )

    resolved_effect_id = resolution.get("resolved_effect_id")
    next_effect_key = resolution.get("next_effect_key")

    if resolution_status == "committed":
        if len(committed_effect_ids) != 1:
            errors.append(
                "$.commit_resolution.resolved_effect_id: committed resolution requires exactly one committed effect identity"
            )
        elif resolved_effect_id not in committed_effect_ids:
            errors.append(
                "$.commit_resolution.resolved_effect_id: must match the committed effect identity"
            )
        if next_action not in {"ACCEPT_EXISTING_EFFECT", "STOP"}:
            errors.append(
                "$.commit_resolution.selected_next_action: committed effect may not authorize another mutation"
            )
        if next_effect_key is not None:
            errors.append(
                "$.commit_resolution.next_effect_key: committed effect must not mint another mutation key"
            )

    elif resolution_status == "not_committed":
        if resolved_effect_id is not None:
            errors.append(
                "$.commit_resolution.resolved_effect_id: not_committed resolution cannot carry an effect id"
            )
        if next_action not in {"RETRY_SAME_EFFECT_KEY", "STOP"}:
            errors.append(
                "$.commit_resolution.selected_next_action: not_committed may only retry the same effect key or stop"
            )
        if next_action == "RETRY_SAME_EFFECT_KEY":
            if next_effect_key != effect_key:
                errors.append(
                    "$.commit_resolution.next_effect_key: retry must preserve the original effect key"
                )
        elif next_effect_key is not None:
            errors.append(
                "$.commit_resolution.next_effect_key: STOP must not carry a retry key"
            )

    elif resolution_status == "still_unknown":
        if resolved_effect_id is not None:
            errors.append(
                "$.commit_resolution.resolved_effect_id: still_unknown cannot claim an effect id"
            )
        if next_action not in {"STOP", "HUMAN_ESCALATION"}:
            errors.append(
                "$.commit_resolution.selected_next_action: unresolved commit must stop or escalate"
            )
        if next_effect_key is not None:
            errors.append(
                "$.commit_resolution.next_effect_key: unresolved commit must not authorize a retry key"
            )

    if state_effect.get("effect_version") != "0.1":
        errors.append("$.state_effect_receipt.effect_version: expected '0.1'")
    if state_effect.get("execution_receipt_id") != execution.get("receipt_id"):
        errors.append(
            "$.state_effect_receipt.execution_receipt_id: must bind to the v0.4 execution receipt"
        )
    if state_effect.get("recovery_cycle_id") != execution.get(
        "recovery_cycle_id"
    ):
        errors.append(
            "$.state_effect_receipt.recovery_cycle_id: must match the execution recovery cycle"
        )
    if not nonempty_evidence(state_effect.get("evidence_references")):
        errors.append(
            "$.state_effect_receipt.evidence_references: authoritative state evidence is required"
        )

    effect_observed_at = parse_timestamp(
        state_effect.get("observed_at"),
        "$.state_effect_receipt.observed_at",
        errors,
    )
    if (
        effect_observed_at is not None
        and resolution_time is not None
        and effect_observed_at < resolution_time
    ):
        errors.append(
            "$.state_effect_receipt.observed_at: state effect cannot precede commit resolution"
        )

    effect_status = state_effect.get("effect_status")
    expected_state = state_effect.get("expected_target_state")
    observed_state = state_effect.get("observed_state")

    if resolution_status == "committed":
        if effect_status != "observed":
            errors.append(
                "$.state_effect_receipt.effect_status: committed resolution requires an observed state effect"
            )
        if not nonempty_string(expected_state) or observed_state != expected_state:
            errors.append(
                "$.state_effect_receipt.observed_state: committed resolution must match the expected target state"
            )
    elif resolution_status == "still_unknown" and effect_status != "unknown":
        errors.append(
            "$.state_effect_receipt.effect_status: unresolved commit must preserve unknown state effect"
        )
    elif resolution_status == "not_committed":
        if effect_status == "observed" and observed_state == expected_state:
            errors.append(
                "$.state_effect_receipt: not_committed resolution cannot claim the intended state effect"
            )

    return errors


def mutation_cases() -> list[tuple[str, Callable[[dict[str, Any]], None], str]]:
    def effect_key_drift(case: dict[str, Any]) -> None:
        case["commit_outcome_receipts"][1]["effect_key"] = "effect-key.NEW"

    def multiple_committed_effects(case: dict[str, Any]) -> None:
        receipt = copy.deepcopy(case["commit_outcome_receipts"][1])
        receipt["receipt_id"] = "commit-outcome.payment-recovery.lookup.003"
        receipt["committed_effect_id"] = "provider-effect.payment.002"
        receipt["observed_at"] = "2026-08-24T14:42:06.150000+00:00"
        case["commit_outcome_receipts"].append(receipt)

    def unknown_claimed_not_committed(case: dict[str, Any]) -> None:
        receipt = case["commit_outcome_receipts"][1]
        receipt["commit_status"] = "unknown"
        receipt["authoritative"] = False
        receipt.pop("committed_effect_id", None)
        resolution = case["commit_resolution"]
        resolution["resolution_status"] = "not_committed"
        resolution["selected_next_action"] = "RETRY_SAME_EFFECT_KEY"
        resolution["next_effect_key"] = case["logical_operation"]["effect_key"]
        resolution.pop("resolved_effect_id", None)
        effect = case["state_effect_receipt"]
        effect["effect_status"] = "failed"
        effect["observed_state"] = "PAYMENT_NOT_COMMITTED"

    def retry_after_commit(case: dict[str, Any]) -> None:
        resolution = case["commit_resolution"]
        resolution["selected_next_action"] = "RETRY_SAME_EFFECT_KEY"
        resolution["next_effect_key"] = case["logical_operation"]["effect_key"]

    def retry_with_new_key(case: dict[str, Any]) -> None:
        receipt = case["commit_outcome_receipts"][1]
        receipt["commit_status"] = "not_committed"
        receipt.pop("committed_effect_id", None)
        resolution = case["commit_resolution"]
        resolution["resolution_status"] = "not_committed"
        resolution["selected_next_action"] = "RETRY_SAME_EFFECT_KEY"
        resolution["next_effect_key"] = "effect-key.NEW"
        resolution.pop("resolved_effect_id", None)
        effect = case["state_effect_receipt"]
        effect["effect_status"] = "failed"
        effect["observed_state"] = "PAYMENT_NOT_COMMITTED"

    def success_without_state_effect(case: dict[str, Any]) -> None:
        case["state_effect_receipt"]["observed_state"] = "PAYMENT_UNKNOWN"

    return [
        (
            "effect-key-drift",
            effect_key_drift,
            "must match the canonical effect key",
        ),
        (
            "multiple-committed-effects",
            multiple_committed_effects,
            "multiple committed effect identities",
        ),
        (
            "unknown-claimed-not-committed",
            unknown_claimed_not_committed,
            "without authoritative commit evidence",
        ),
        (
            "retry-after-commit",
            retry_after_commit,
            "committed effect may not authorize another mutation",
        ),
        (
            "retry-with-new-key",
            retry_with_new_key,
            "retry must preserve the original effect key",
        ),
        (
            "success-without-state-effect",
            success_without_state_effect,
            "must match the expected target state",
        ),
    ]


def main() -> int:
    try:
        canonical = load_json(FIXTURE)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL canonical fixture: {exc}")
        return 1

    canonical_errors = validate_ambiguous_commit(canonical)
    if canonical_errors:
        print("FAIL canonical v0.5 trace")
        for error in canonical_errors:
            print(f"  - {error}")
        return 1
    print("PASS canonical v0.5 trace")

    ok = True
    for name, mutate, expected_fragment in mutation_cases():
        case = copy.deepcopy(canonical)
        mutate(case)
        errors = validate_ambiguous_commit(case)
        matched = any(expected_fragment in error for error in errors)
        if errors and matched:
            print(f"PASS mutation {name} rejected")
        else:
            ok = False
            print(f"FAIL mutation {name}")
            if not errors:
                print("  - mutated trace unexpectedly passed")
            else:
                print(f"  - expected an error containing {expected_fragment!r}")
                for error in errors:
                    print(f"  - {error}")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
