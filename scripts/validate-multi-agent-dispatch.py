#!/usr/bin/env python3
"""Validate multi-agent dispatch ownership continuity (v0.3).

A worker may change after a dispatch has been consumed, but the dispatch identity
must not fork. Ownership changes are append-only events with monotonic generations.
Execution must bind to the latest ownership event for the same consumed dispatch.

This validator proves trace semantics; it does not itself implement a distributed
lock or consensus protocol.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/valid-multi-agent-dispatch-takeover-v0.3.json"
AUTOMATED_ACTIONS = {"SAFE_RETRY", "ROLLBACK"}
TRANSFER_BASES = {"explicit_handoff", "orchestrator_reassignment", "lease_expiry"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_evidence(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(nonempty_string(item) for item in value)


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


def require_object(instance: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any] | None:
    value = instance.get(key)
    if not isinstance(value, dict):
        errors.append(f"$.{key}: object is required")
        return None
    return value


def validate_multi_agent_dispatch(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: trace must be an object"]

    errors: list[str] = []
    if instance.get("profile_version") != "0.3":
        errors.append("$.profile_version: expected '0.3'")

    execution_mode = instance.get("execution_mode")
    if execution_mode not in AUTOMATED_ACTIONS:
        errors.append(f"$.execution_mode: expected automated mode, got {execution_mode!r}")

    decision = require_object(instance, "recovery_decision", errors)
    consumption = require_object(instance, "authority_consumption_receipt", errors)
    execution = require_object(instance, "execution_receipt", errors)
    ownership_events = instance.get("dispatch_ownership_events")
    if not isinstance(ownership_events, list) or not ownership_events:
        errors.append("$.dispatch_ownership_events: non-empty array is required")
        ownership_events = []

    if decision is None or consumption is None or execution is None:
        return errors

    decision_id = decision.get("decision_id")
    authority_id = decision.get("authority_id")
    authority_generation = decision.get("authority_generation")
    selected_action = decision.get("selected_action")

    if not nonempty_string(decision_id):
        errors.append("$.recovery_decision.decision_id: non-empty string is required")
    if selected_action != execution_mode:
        errors.append("$.recovery_decision.selected_action: must exactly match execution_mode")
    if not nonempty_string(authority_id):
        errors.append("$.recovery_decision.authority_id: non-empty string is required")
    if not isinstance(authority_generation, int) or isinstance(authority_generation, bool):
        errors.append("$.recovery_decision.authority_generation: integer is required")

    dispatch_id = consumption.get("dispatch_id")
    use_token = consumption.get("use_token")
    consumption_receipt_id = consumption.get("consumption_receipt_id")

    if consumption.get("consumption_version") != "0.1":
        errors.append("$.authority_consumption_receipt.consumption_version: expected '0.1'")
    if consumption.get("recovery_decision_id") != decision_id:
        errors.append("$.authority_consumption_receipt.recovery_decision_id: must match recovery_decision.decision_id")
    if consumption.get("authority_id") != authority_id:
        errors.append("$.authority_consumption_receipt.authority_id: must match recovery_decision.authority_id")
    if consumption.get("authority_generation") != authority_generation:
        errors.append("$.authority_consumption_receipt.authority_generation: must match recovery_decision.authority_generation")
    if consumption.get("bound_execution_mode") != execution_mode:
        errors.append("$.authority_consumption_receipt.bound_execution_mode: must match execution_mode")
    if consumption.get("consumption_status") != "consumed":
        errors.append("$.authority_consumption_receipt.consumption_status: automated dispatch requires 'consumed'")
    if not nonempty_string(dispatch_id):
        errors.append("$.authority_consumption_receipt.dispatch_id: non-empty string is required")
    if not nonempty_string(use_token):
        errors.append("$.authority_consumption_receipt.use_token: non-empty string is required")
    if not nonempty_string(consumption_receipt_id):
        errors.append("$.authority_consumption_receipt.consumption_receipt_id: non-empty string is required")
    if not nonempty_evidence(consumption.get("evidence_references")):
        errors.append("$.authority_consumption_receipt.evidence_references: durable evidence is required")

    consumed_at = parse_timestamp(
        consumption.get("consumed_at"),
        "$.authority_consumption_receipt.consumed_at",
        errors,
    )

    seen_event_ids: set[str] = set()
    previous_event: dict[str, Any] | None = None
    previous_time: datetime | None = None

    for index, event in enumerate(ownership_events):
        path = f"$.dispatch_ownership_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{path}: object is required")
            continue

        event_id = event.get("ownership_event_id")
        actor_id = event.get("actor_id")
        generation = event.get("ownership_generation")
        event_type = event.get("event_type")
        event_time = parse_timestamp(event.get("occurred_at"), f"{path}.occurred_at", errors)

        if event.get("ownership_event_version") != "0.1":
            errors.append(f"{path}.ownership_event_version: expected '0.1'")
        if not nonempty_string(event_id):
            errors.append(f"{path}.ownership_event_id: non-empty string is required")
        elif event_id in seen_event_ids:
            errors.append(f"{path}.ownership_event_id: duplicate event id {event_id!r}")
        else:
            seen_event_ids.add(event_id)
        if event.get("dispatch_id") != dispatch_id:
            errors.append(f"{path}.dispatch_id: ownership must stay on the consumed dispatch")
        if not nonempty_string(actor_id):
            errors.append(f"{path}.actor_id: non-empty string is required")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
            errors.append(f"{path}.ownership_generation: positive integer is required")
        if not nonempty_evidence(event.get("evidence_references")):
            errors.append(f"{path}.evidence_references: ownership event requires evidence")

        if index == 0:
            if event_type != "claim":
                errors.append(f"{path}.event_type: first ownership event must be 'claim'")
            if generation != 1:
                errors.append(f"{path}.ownership_generation: initial claim must start at generation 1")
            if event.get("previous_ownership_event_id") is not None:
                errors.append(f"{path}.previous_ownership_event_id: initial claim must not have a predecessor")
            if event.get("transfer_basis") is not None:
                errors.append(f"{path}.transfer_basis: initial claim must not declare a transfer basis")
            if consumed_at is not None and event_time is not None and event_time < consumed_at:
                errors.append(f"{path}.occurred_at: dispatch cannot be claimed before authority consumption")
        else:
            assert previous_event is not None
            if event_type != "transfer":
                errors.append(f"{path}.event_type: ownership changes after the initial claim must be 'transfer'")
            if event.get("previous_ownership_event_id") != previous_event.get("ownership_event_id"):
                errors.append(f"{path}.previous_ownership_event_id: must point to the immediately prior ownership event")
            previous_generation = previous_event.get("ownership_generation")
            if isinstance(previous_generation, int) and not isinstance(previous_generation, bool):
                if generation != previous_generation + 1:
                    errors.append(f"{path}.ownership_generation: must increment exactly by one")
            if actor_id == previous_event.get("actor_id"):
                errors.append(f"{path}.actor_id: transfer must change the owning actor")
            if event.get("transfer_basis") not in TRANSFER_BASES:
                errors.append(f"{path}.transfer_basis: recognized transfer basis is required")
            if previous_time is not None and event_time is not None and event_time <= previous_time:
                errors.append(f"{path}.occurred_at: ownership events must be strictly time-ordered")

        previous_event = event
        previous_time = event_time

    if ownership_events and isinstance(ownership_events[-1], dict):
        latest = ownership_events[-1]
        latest_time = previous_time

        if execution.get("recovery_decision_id") != decision_id:
            errors.append("$.execution_receipt.recovery_decision_id: must match recovery_decision.decision_id")
        if execution.get("declared_execution_mode") != execution_mode:
            errors.append("$.execution_receipt.declared_execution_mode: must match execution_mode")
        if execution.get("execution_status") == "observed" and execution.get("observed_execution_mode") != execution_mode:
            errors.append("$.execution_receipt.observed_execution_mode: observed mode must match execution_mode")
        if execution.get("authority_generation_at_execution") != authority_generation:
            errors.append("$.execution_receipt.authority_generation_at_execution: must match decision authority generation")
        if execution.get("authority_consumption_receipt_id") != consumption_receipt_id:
            errors.append("$.execution_receipt.authority_consumption_receipt_id: must bind to exact consumption receipt")
        if execution.get("use_token") != use_token:
            errors.append("$.execution_receipt.use_token: must bind to consumed use_token")
        if execution.get("dispatch_id") != dispatch_id:
            errors.append("$.execution_receipt.dispatch_id: worker takeover must preserve consumed dispatch_id")
        if execution.get("actor_id") != latest.get("actor_id"):
            errors.append("$.execution_receipt.actor_id: only the latest dispatch owner may execute")
        if execution.get("dispatch_ownership_event_id") != latest.get("ownership_event_id"):
            errors.append("$.execution_receipt.dispatch_ownership_event_id: must bind to latest ownership event")
        if execution.get("dispatch_ownership_generation") != latest.get("ownership_generation"):
            errors.append("$.execution_receipt.dispatch_ownership_generation: must bind to latest ownership generation")
        if not nonempty_evidence(execution.get("evidence_references")):
            errors.append("$.execution_receipt.evidence_references: observed execution requires evidence")

        executed_at = parse_timestamp(execution.get("executed_at"), "$.execution_receipt.executed_at", errors)
        if latest_time is not None and executed_at is not None and executed_at < latest_time:
            errors.append("$.execution_receipt.executed_at: execution cannot precede the ownership event it relies on")

    return errors


def set_nested(instance: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    cursor: Any = instance
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def append_parallel_transfer(instance: dict[str, Any]) -> None:
    sibling = copy.deepcopy(instance["dispatch_ownership_events"][1])
    sibling["ownership_event_id"] = "ownership.payment-recovery.parallel"
    sibling["actor_id"] = "worker.C"
    sibling["previous_ownership_event_id"] = "ownership.payment-recovery.001"
    sibling["ownership_generation"] = 2
    sibling["occurred_at"] = "2026-08-24T05:00:04.500000+00:00"
    sibling["evidence_references"] = ["evidence://orchestrator/parallel-transfer"]
    instance["dispatch_ownership_events"].append(sibling)


MUTATIONS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    (
        "transfer forks dispatch",
        lambda x: set_nested(x, ("dispatch_ownership_events", 1, "dispatch_id"), "dispatch.payment-recovery.NEW"),
    ),
    (
        "stale owner executes",
        lambda x: set_nested(x, ("execution_receipt", "actor_id"), "worker.A"),
    ),
    (
        "execution binds stale ownership generation",
        lambda x: set_nested(x, ("execution_receipt", "dispatch_ownership_generation"), 1),
    ),
    (
        "execution switches dispatch",
        lambda x: set_nested(x, ("execution_receipt", "dispatch_id"), "dispatch.payment-recovery.NEW"),
    ),
    (
        "broken transfer predecessor",
        lambda x: set_nested(x, ("dispatch_ownership_events", 1, "previous_ownership_event_id"), "ownership.missing"),
    ),
    (
        "ownership generation skips",
        lambda x: set_nested(x, ("dispatch_ownership_events", 1, "ownership_generation"), 3),
    ),
    (
        "execution happens before handoff",
        lambda x: set_nested(x, ("execution_receipt", "executed_at"), "2026-08-24T05:00:03+00:00"),
    ),
    (
        "consumption bound to different decision",
        lambda x: set_nested(x, ("authority_consumption_receipt", "recovery_decision_id"), "recovery.other"),
    ),
    (
        "ownership event loses evidence",
        lambda x: set_nested(x, ("dispatch_ownership_events", 1, "evidence_references"), []),
    ),
    (
        "parallel transfer fork",
        append_parallel_transfer,
    ),
]


def main() -> int:
    try:
        canonical = load_json(FIXTURE)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL canonical fixture load: {exc}")
        return 1

    canonical_errors = validate_multi_agent_dispatch(canonical)
    if canonical_errors:
        print("FAIL canonical multi-agent dispatch fixture")
        for error in canonical_errors:
            print(f"  - {error}")
        return 1
    print("PASS canonical multi-agent dispatch takeover")

    ok = True
    for name, mutate in MUTATIONS:
        case = copy.deepcopy(canonical)
        mutate(case)
        errors = validate_multi_agent_dispatch(case)
        if errors:
            print(f"PASS mutation rejected: {name}")
        else:
            print(f"FAIL mutation unexpectedly passed: {name}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
