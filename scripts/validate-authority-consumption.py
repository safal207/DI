#!/usr/bin/env python3
"""Validate single-use authority consumption at the automated dispatch seam.

Use-time authority proves that a grant is still valid. It does not prove that
another worker has not already used the same mutation right. Automated
SAFE_RETRY and ROLLBACK therefore require a durable consumption receipt that
binds one authority check and one recovery decision to one dispatch before
execution.

This validator checks evidence semantics only. Real atomicity must be enforced
by the system that owns the side effect, ideally by atomically consuming the
single-use scope and creating/claiming the dispatch record in the same
consistency boundary.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("fixtures/valid-authority-consumption.json", True),
    ("fixtures/invalid-authority-execution-without-consumption.json", False),
    ("fixtures/invalid-authority-consume-after-execution.json", False),
    ("fixtures/invalid-authority-dispatch-mismatch.json", False),
    ("fixtures/invalid-authority-replayed-use-token.json", False),
    ("fixtures/invalid-authority-double-consume-same-decision.json", False),
]

AUTOMATED_ACTIONS = {"SAFE_RETRY", "ROLLBACK"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not nonempty_string(value):
        errors.append(f"{path}: RFC3339 timestamp is required")
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


def validate_authority_consumption(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: chain must be an object"]

    cycles = instance.get("cycles")
    if not isinstance(cycles, list):
        return ["$.cycles: must be an array"]

    errors: list[str] = []
    consumed_tokens: dict[str, str] = {}
    consumed_authority_receipts: dict[str, str] = {}
    consumed_scopes: dict[tuple[str, int, str, str], str] = {}

    for index, cycle in enumerate(cycles):
        path = f"$.cycles[{index}]"
        if not isinstance(cycle, dict) or cycle.get("recovery_of_cycle_id") is None:
            continue

        decision = cycle.get("recovery_decision")
        if not isinstance(decision, dict):
            continue

        selected_action = decision.get("selected_action")
        if selected_action not in AUTOMATED_ACTIONS:
            continue

        authority = cycle.get("use_time_authority_receipt")
        consumption = cycle.get("authority_consumption_receipt")
        execution = cycle.get("execution_receipt")
        execution_mode = cycle.get("execution_mode")

        if not isinstance(authority, dict):
            errors.append(f"{path}.use_time_authority_receipt: required before automated authority consumption")
            continue
        if not isinstance(consumption, dict):
            errors.append(f"{path}.authority_consumption_receipt: required before automated execution")
            continue
        if not isinstance(execution, dict):
            errors.append(f"{path}.execution_receipt: required after authority consumption")
            continue

        decision_id = decision.get("decision_id")
        authority_id = decision.get("authority_id")
        authority_generation = decision.get("authority_generation")
        authority_receipt_id = authority.get("authority_receipt_id")

        if execution_mode != selected_action:
            errors.append(f"{path}.execution_mode: must exactly match recovery_decision.selected_action")

        if authority.get("authority_status") != "active":
            errors.append(f"{path}.use_time_authority_receipt.authority_status: automated mutation requires active authority")
        if authority.get("recovery_decision_id") != decision_id:
            errors.append(f"{path}.use_time_authority_receipt.recovery_decision_id: must exactly match recovery_decision.decision_id")
        if authority.get("recovery_cycle_id") != cycle.get("cycle_id"):
            errors.append(f"{path}.use_time_authority_receipt.recovery_cycle_id: must exactly match cycle_id")
        if authority.get("bound_execution_mode") != execution_mode:
            errors.append(f"{path}.use_time_authority_receipt.bound_execution_mode: must exactly match execution_mode")
        if authority.get("authority_id") != authority_id:
            errors.append(f"{path}.use_time_authority_receipt.authority_id: must exactly match recovery_decision.authority_id")
        if authority.get("authority_generation") != authority_generation:
            errors.append(f"{path}.use_time_authority_receipt.authority_generation: must exactly match recovery_decision.authority_generation")

        if consumption.get("consumption_version") != "0.1":
            errors.append(f"{path}.authority_consumption_receipt.consumption_version: expected '0.1'")
        if consumption.get("authority_receipt_id") != authority_receipt_id:
            errors.append(f"{path}.authority_consumption_receipt.authority_receipt_id: must bind to the exact use-time authority receipt")
        if consumption.get("authority_id") != authority_id:
            errors.append(f"{path}.authority_consumption_receipt.authority_id: must exactly match recovery_decision.authority_id")
        if consumption.get("authority_generation") != authority_generation:
            errors.append(f"{path}.authority_consumption_receipt.authority_generation: must exactly match the decision/use-time authority generation")
        if consumption.get("recovery_decision_id") != decision_id:
            errors.append(f"{path}.authority_consumption_receipt.recovery_decision_id: must exactly match recovery_decision.decision_id")
        if consumption.get("recovery_cycle_id") != cycle.get("cycle_id"):
            errors.append(f"{path}.authority_consumption_receipt.recovery_cycle_id: must exactly match cycle_id")
        if consumption.get("bound_execution_mode") != execution_mode:
            errors.append(f"{path}.authority_consumption_receipt.bound_execution_mode: must exactly match execution_mode")

        status = consumption.get("consumption_status")
        if status != "consumed":
            errors.append(f"{path}.authority_consumption_receipt.consumption_status: automated execution requires 'consumed', got {status!r}")

        consumption_receipt_id = consumption.get("consumption_receipt_id")
        use_token = consumption.get("use_token")
        dispatch_id = consumption.get("dispatch_id")
        for field_name, value in (
            ("consumption_receipt_id", consumption_receipt_id),
            ("use_token", use_token),
            ("dispatch_id", dispatch_id),
        ):
            if not nonempty_string(value):
                errors.append(f"{path}.authority_consumption_receipt.{field_name}: non-empty string is required")

        evidence = consumption.get("evidence_references")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{path}.authority_consumption_receipt.evidence_references: consumption requires durable evidence")

        checked_at = parse_timestamp(authority.get("checked_at"), f"{path}.use_time_authority_receipt.checked_at", errors)
        consumed_at = parse_timestamp(consumption.get("consumed_at"), f"{path}.authority_consumption_receipt.consumed_at", errors)
        executed_at = parse_timestamp(execution.get("executed_at"), f"{path}.execution_receipt.executed_at", errors)

        max_binding_age_seconds = authority.get("max_binding_age_seconds")
        if not isinstance(max_binding_age_seconds, int) or isinstance(max_binding_age_seconds, bool) or max_binding_age_seconds < 0:
            errors.append(f"{path}.use_time_authority_receipt.max_binding_age_seconds: non-negative integer is required")
            max_binding_age_seconds = None

        if checked_at is not None and consumed_at is not None:
            if checked_at > consumed_at:
                errors.append(f"{path}.authority_consumption_receipt.consumed_at: authority cannot be consumed before its use-time check")
            elif max_binding_age_seconds is not None and (consumed_at - checked_at).total_seconds() > max_binding_age_seconds:
                errors.append(f"{path}.authority_consumption_receipt.consumed_at: authority binding expired before consumption")

        if consumed_at is not None and executed_at is not None and consumed_at > executed_at:
            errors.append(f"{path}.authority_consumption_receipt.consumed_at: authority must be consumed before or at execution")

        if checked_at is not None and executed_at is not None and max_binding_age_seconds is not None:
            if (executed_at - checked_at).total_seconds() > max_binding_age_seconds:
                errors.append(f"{path}.execution_receipt.executed_at: use-time authority binding expired before execution")

        if execution.get("recovery_decision_id") != decision_id:
            errors.append(f"{path}.execution_receipt.recovery_decision_id: must exactly match recovery_decision.decision_id")
        if execution.get("recovery_cycle_id") != cycle.get("cycle_id"):
            errors.append(f"{path}.execution_receipt.recovery_cycle_id: must exactly match cycle_id")
        if execution.get("declared_execution_mode") != execution_mode:
            errors.append(f"{path}.execution_receipt.declared_execution_mode: must exactly match execution_mode")
        if execution.get("execution_status") == "observed" and execution.get("observed_execution_mode") != execution_mode:
            errors.append(f"{path}.execution_receipt.observed_execution_mode: observed automated mode must exactly match execution_mode")
        if execution.get("authority_status_at_execution") != "active":
            errors.append(f"{path}.execution_receipt.authority_status_at_execution: automated mutation requires active authority at execution")
        if execution.get("authority_generation_at_execution") != authority_generation:
            errors.append(f"{path}.execution_receipt.authority_generation_at_execution: must exactly match consumed authority generation")
        if execution.get("authority_consumption_receipt_id") != consumption_receipt_id:
            errors.append(f"{path}.execution_receipt.authority_consumption_receipt_id: must bind to the exact consumption receipt")
        if execution.get("use_token") != use_token:
            errors.append(f"{path}.execution_receipt.use_token: must exactly match consumed use_token")
        if execution.get("dispatch_id") != dispatch_id:
            errors.append(f"{path}.execution_receipt.dispatch_id: must exactly match the dispatch claimed during consumption")
        if execution.get("authority_receipt_id") != authority_receipt_id:
            errors.append(f"{path}.execution_receipt.authority_receipt_id: must bind to the same authority receipt that was consumed")

        if status == "consumed" and nonempty_string(use_token):
            previous_path = consumed_tokens.get(use_token)
            if previous_path is not None:
                errors.append(f"{path}.authority_consumption_receipt.use_token: {use_token!r} was already consumed at {previous_path}")
            else:
                consumed_tokens[use_token] = path

        if status == "consumed" and nonempty_string(authority_receipt_id):
            previous_path = consumed_authority_receipts.get(authority_receipt_id)
            if previous_path is not None:
                errors.append(
                    f"{path}.authority_consumption_receipt.authority_receipt_id: authority receipt {authority_receipt_id!r} was already consumed at {previous_path}"
                )
            else:
                consumed_authority_receipts[authority_receipt_id] = path

        if (
            status == "consumed"
            and nonempty_string(authority_id)
            and isinstance(authority_generation, int)
            and not isinstance(authority_generation, bool)
            and nonempty_string(decision_id)
            and execution_mode in AUTOMATED_ACTIONS
        ):
            single_use_scope = (
                authority_id,
                authority_generation,
                decision_id,
                execution_mode,
            )
            previous_path = consumed_scopes.get(single_use_scope)
            if previous_path is not None:
                errors.append(
                    f"{path}.authority_consumption_receipt: single-use recovery decision authority was already consumed at {previous_path}; a different token does not create a second permission"
                )
            else:
                consumed_scopes[single_use_scope] = path

    return errors


def run_case(fixture_rel: str, expected_pass: bool) -> bool:
    try:
        instance = load_json(ROOT / fixture_rel)
        errors = validate_authority_consumption(instance)
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
        print("  - fixture unexpectedly passed authority consumption validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
