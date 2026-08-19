#!/usr/bin/env python3
"""Validate use-time authority binding at the execution seam.

A fresh state observation is not sufficient authority to act. This validator
checks that the authority referenced by a recovery decision is revalidated at
use time, remains active in the same generation, and is still valid when the
bound execution occurs.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

CASES = [
    ("fixtures/valid-decision-transition-cycle-chain-recovery.json", True),
    ("fixtures/invalid-authority-revoked-before-execution.json", False),
    ("fixtures/invalid-authority-generation-mismatch.json", False),
    ("fixtures/invalid-authority-binding-window-expired.json", False),
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_timestamp(value: Any, path: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
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


def validate_authority_binding(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: chain must be an object"]

    cycles = instance.get("cycles")
    if not isinstance(cycles, list):
        return ["$.cycles: must be an array"]

    errors: list[str] = []

    for index, cycle in enumerate(cycles):
        path = f"$.cycles[{index}]"
        if not isinstance(cycle, dict):
            continue

        recovery_of = cycle.get("recovery_of_cycle_id")
        if recovery_of is None:
            continue

        decision = cycle.get("recovery_decision")
        authority = cycle.get("use_time_authority_receipt")
        execution = cycle.get("execution_receipt")
        execution_mode = cycle.get("execution_mode")

        if not isinstance(decision, dict):
            errors.append(f"{path}.recovery_decision: required for an active recovery cycle")
            continue

        if decision.get("selected_action") == "STOP":
            continue

        if not isinstance(authority, dict):
            errors.append(f"{path}.use_time_authority_receipt: required before active execution")
            continue
        if not isinstance(execution, dict):
            errors.append(f"{path}.execution_receipt: required for authority/use-time validation")
            continue

        decision_id = decision.get("decision_id")
        authority_id = decision.get("authority_id")
        authority_generation = decision.get("authority_generation")

        if not isinstance(authority_id, str) or not authority_id:
            errors.append(f"{path}.recovery_decision.authority_id: active execution requires an authority identity")
        if not isinstance(authority_generation, int) or isinstance(authority_generation, bool) or authority_generation < 0:
            errors.append(f"{path}.recovery_decision.authority_generation: non-negative integer is required")

        if authority.get("authority_receipt_version") != "0.1":
            errors.append(f"{path}.use_time_authority_receipt.authority_receipt_version: expected '0.1'")
        if authority.get("authority_id") != authority_id:
            errors.append(f"{path}.use_time_authority_receipt.authority_id: must exactly match recovery_decision.authority_id")
        if authority.get("recovery_decision_id") != decision_id:
            errors.append(f"{path}.use_time_authority_receipt.recovery_decision_id: must exactly match recovery_decision.decision_id")
        if authority.get("recovery_cycle_id") != cycle.get("cycle_id"):
            errors.append(f"{path}.use_time_authority_receipt.recovery_cycle_id: must exactly match cycle_id")
        if authority.get("bound_execution_mode") != execution_mode:
            errors.append(f"{path}.use_time_authority_receipt.bound_execution_mode: must exactly match execution_mode")
        if authority.get("authority_generation") != authority_generation:
            errors.append(
                f"{path}.use_time_authority_receipt.authority_generation: must exactly match recovery decision generation {authority_generation!r}"
            )

        status = authority.get("authority_status")
        if status != "active":
            errors.append(f"{path}.use_time_authority_receipt.authority_status: active execution requires status='active', got {status!r}")

        evidence = authority.get("evidence_references")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{path}.use_time_authority_receipt.evidence_references: use-time authority requires evidence")

        checked_at = parse_timestamp(authority.get("checked_at"), f"{path}.use_time_authority_receipt.checked_at", errors)
        executed_at = parse_timestamp(execution.get("executed_at"), f"{path}.execution_receipt.executed_at", errors)
        max_age = authority.get("max_binding_age_seconds")
        if not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 0:
            errors.append(f"{path}.use_time_authority_receipt.max_binding_age_seconds: non-negative integer is required")

        if checked_at is not None and executed_at is not None:
            if checked_at > executed_at:
                errors.append(f"{path}.use_time_authority_receipt.checked_at: authority cannot be checked after execution")
            elif isinstance(max_age, int) and not isinstance(max_age, bool) and max_age >= 0:
                age = (executed_at - checked_at).total_seconds()
                if age > max_age:
                    errors.append(
                        f"{path}.use_time_authority_receipt.checked_at: authority binding age {age:.0f}s exceeds allowed {max_age}s"
                    )

        revoked_at_raw = authority.get("revoked_at")
        if revoked_at_raw is not None:
            revoked_at = parse_timestamp(revoked_at_raw, f"{path}.use_time_authority_receipt.revoked_at", errors)
            if revoked_at is not None and executed_at is not None and revoked_at <= executed_at:
                errors.append(f"{path}.use_time_authority_receipt.revoked_at: authority was revoked before or at execution")

        receipt_id = authority.get("authority_receipt_id")
        if execution.get("authority_receipt_id") != receipt_id:
            errors.append(f"{path}.execution_receipt.authority_receipt_id: must bind to the exact use-time authority receipt")
        if execution.get("authority_generation_at_execution") != authority_generation:
            errors.append(
                f"{path}.execution_receipt.authority_generation_at_execution: must exactly match decision/use-time generation {authority_generation!r}"
            )
        if execution.get("authority_status_at_execution") != "active":
            errors.append(f"{path}.execution_receipt.authority_status_at_execution: execution requires active authority")

    return errors


def run_case(fixture_rel: str, expected_pass: bool) -> bool:
    try:
        instance = load_json(ROOT / fixture_rel)
        errors = validate_authority_binding(instance)
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
        print("  - fixture unexpectedly passed authority binding validation")
    return False


def main() -> int:
    ok = True
    for fixture_rel, expected_pass in CASES:
        ok = run_case(fixture_rel, expected_pass) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
