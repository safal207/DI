#!/usr/bin/env python3
"""Validate one full DI decision-to-evidence integrity trace.

The goal is not only to validate each artifact in isolation, but to prove that
identity, authority, execution, outcome, freshness, and next-state claims stay
bound across the complete chain.

The script validates one canonical fixture and then deep-copies it into a set
of deliberately broken mutation cases. Every mutation must be rejected.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/valid-end-to-end-integrity-v0.2.json"
AUTOMATED_ACTIONS = {"SAFE_RETRY", "ROLLBACK"}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
        errors.append(f"{path}: RFC3339/ISO-8601 timestamp is required")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{path}: invalid timestamp {value!r}")
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


def validate_end_to_end(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: trace must be an object"]

    errors: list[str] = []

    if instance.get("trace_version") != "0.1":
        errors.append("$.trace_version: expected '0.1'")

    cycle_id = instance.get("cycle_id")
    input_state = instance.get("input_state")
    recovery_of_cycle_id = instance.get("recovery_of_cycle_id")
    execution_mode = instance.get("execution_mode")

    for path, value in (
        ("$.trace_id", instance.get("trace_id")),
        ("$.cycle_id", cycle_id),
        ("$.input_state", input_state),
        ("$.recovery_of_cycle_id", recovery_of_cycle_id),
    ):
        if not nonempty_string(value):
            errors.append(f"{path}: non-empty string is required")

    envelope = require_object(instance, "envelope", errors)
    recovery = require_object(instance, "recovery_decision", errors)
    authority = require_object(instance, "use_time_authority_receipt", errors)
    consumption = require_object(instance, "authority_consumption_receipt", errors)
    execution = require_object(instance, "execution_receipt", errors)
    effect = require_object(instance, "state_effect_receipt", errors)

    if any(part is None for part in (envelope, recovery, authority, consumption, execution, effect)):
        return errors

    assert envelope is not None
    assert recovery is not None
    assert authority is not None
    assert consumption is not None
    assert execution is not None
    assert effect is not None

    if envelope.get("envelope_version") != "0.2":
        errors.append("$.envelope.envelope_version: expected '0.2'")

    dif = envelope.get("dif")
    di = envelope.get("di")
    strategy = envelope.get("strategy")
    drp = envelope.get("drp")
    revalidation = envelope.get("path_revalidation")
    tip = envelope.get("tip")
    review = envelope.get("review")

    if not all(isinstance(part, dict) for part in (dif, di, strategy, drp, revalidation, tip, review)):
        errors.append("$.envelope: DIF, DI, Strategy, DRP, Path Revalidation, TIP, and Review objects are required")
        return errors

    assert isinstance(dif, dict)
    assert isinstance(di, dict)
    assert isinstance(strategy, dict)
    assert isinstance(drp, dict)
    assert isinstance(revalidation, dict)
    assert isinstance(tip, dict)
    assert isinstance(review, dict)

    # Intent -> feasibility.
    if dif.get("human_confirmed") is not True:
        errors.append("$.envelope.dif.human_confirmed: intent must be human-confirmed")
    if dif.get("status") != "confirmed":
        errors.append("$.envelope.dif.status: expected 'confirmed'")
    if di.get("intent_id") != dif.get("intent_id"):
        errors.append("$.envelope.di.intent_id: must exactly match DIF intent_id")

    feasibility_id = di.get("feasibility_id")
    feasible_paths = di.get("feasible_paths")
    if not nonempty_string(feasibility_id):
        errors.append("$.envelope.di.feasibility_id: required")
    if not isinstance(feasible_paths, list) or not feasible_paths:
        errors.append("$.envelope.di.feasible_paths: at least one feasible path is required")
        feasible_paths = []

    feasible_ids: list[str] = []
    for index, path in enumerate(feasible_paths):
        pp = f"$.envelope.di.feasible_paths[{index}]"
        if not isinstance(path, dict):
            errors.append(f"{pp}: object is required")
            continue
        path_id = path.get("path_id")
        if not nonempty_string(path_id):
            errors.append(f"{pp}.path_id: required")
            continue
        if path_id in feasible_ids:
            errors.append(f"{pp}.path_id: duplicate path id {path_id!r}")
        feasible_ids.append(path_id)

    # Feasibility -> Strategy -> DRP.
    if strategy.get("feasibility_id") != feasibility_id:
        errors.append("$.envelope.strategy.feasibility_id: must exactly match DI feasibility_id")

    candidate_ids = strategy.get("candidate_path_ids")
    if not isinstance(candidate_ids, list) or not candidate_ids:
        errors.append("$.envelope.strategy.candidate_path_ids: at least one candidate is required")
        candidate_ids = []
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append("$.envelope.strategy.candidate_path_ids: duplicates are forbidden")
    for path_id in candidate_ids:
        if path_id not in feasible_ids:
            errors.append(f"$.envelope.strategy.candidate_path_ids: {path_id!r} was not produced by DI")

    recommended = strategy.get("recommended_path_id")
    if recommended not in candidate_ids:
        errors.append("$.envelope.strategy.recommended_path_id: must be a candidate path")

    selected_path = drp.get("selected_path_id")
    if drp.get("feasibility_id") != feasibility_id:
        errors.append("$.envelope.drp.feasibility_id: must exactly match DI feasibility_id")
    if drp.get("strategy_id") != strategy.get("strategy_id"):
        errors.append("$.envelope.drp.strategy_id: must exactly match Strategy strategy_id")
    if selected_path not in feasible_ids:
        errors.append("$.envelope.drp.selected_path_id: committed path must be feasible")
    if selected_path not in candidate_ids:
        errors.append("$.envelope.drp.selected_path_id: committed path must have been evaluated by Strategy")

    # DRP -> Path Revalidation -> TIP.
    if revalidation.get("decision_record_id") != drp.get("record_id"):
        errors.append("$.envelope.path_revalidation.decision_record_id: must exactly match DRP record_id")
    if revalidation.get("selected_path_id") != selected_path:
        errors.append("$.envelope.path_revalidation.selected_path_id: must exactly match DRP selected_path_id")
    if not nonempty_evidence(revalidation.get("evidence_references")):
        errors.append("$.envelope.path_revalidation.evidence_references: non-empty evidence is required")

    revalidation_status = revalidation.get("status")
    if tip.get("decision_record_id") != drp.get("record_id"):
        errors.append("$.envelope.tip.decision_record_id: must exactly match DRP record_id")
    if tip.get("selected_path_id") != selected_path:
        errors.append("$.envelope.tip.selected_path_id: path substitution after commitment is forbidden")
    if tip.get("selected_path_id") != revalidation.get("selected_path_id"):
        errors.append("$.envelope.tip.selected_path_id: must exactly match revalidated path")
    if tip.get("starting_state") != input_state:
        errors.append("$.envelope.tip.starting_state: must exactly match trace input_state")

    if revalidation_status != "valid" and tip.get("status") != "blocked":
        errors.append("$.envelope.tip.status: invalid/unknown path revalidation must block TIP")
    if revalidation_status == "valid" and tip.get("status") == "blocked":
        errors.append("$.envelope.tip.status: valid path revalidation cannot be represented as blocked in the canonical success trace")

    # Recovery decision binds the failed state and automated action.
    if recovery.get("source_cycle_id") != recovery_of_cycle_id:
        errors.append("$.recovery_decision.source_cycle_id: must exactly match recovery_of_cycle_id")
    if recovery.get("failure_state") != input_state:
        errors.append("$.recovery_decision.failure_state: must exactly match input_state")
    if recovery.get("selected_action") != execution_mode:
        errors.append("$.execution_mode: must exactly match recovery_decision.selected_action")

    if execution_mode in AUTOMATED_ACTIONS:
        if recovery.get("selected_action") == "SAFE_RETRY":
            idempotent = recovery.get("idempotency_verified") is True
            reversible = recovery.get("operation_reversible") is True
            if not (idempotent or reversible):
                errors.append("$.recovery_decision: SAFE_RETRY requires verified idempotency or reversibility")
        if recovery.get("selected_action") == "ROLLBACK":
            if recovery.get("rollback_available") is not True or recovery.get("operation_reversible") is not True:
                errors.append("$.recovery_decision: ROLLBACK requires available reversible rollback")

    recovery_decision_id = recovery.get("decision_id")
    recovery_authority_id = recovery.get("authority_id")
    recovery_authority_generation = recovery.get("authority_generation")

    # Recovery Decision -> Use-Time Authority.
    if authority.get("recovery_decision_id") != recovery_decision_id:
        errors.append("$.use_time_authority_receipt.recovery_decision_id: must exactly match recovery decision")
    if authority.get("recovery_cycle_id") != cycle_id:
        errors.append("$.use_time_authority_receipt.recovery_cycle_id: must exactly match cycle_id")
    if authority.get("bound_execution_mode") != execution_mode:
        errors.append("$.use_time_authority_receipt.bound_execution_mode: must exactly match execution_mode")
    if authority.get("authority_id") != recovery_authority_id:
        errors.append("$.use_time_authority_receipt.authority_id: must exactly match recovery decision authority_id")
    if authority.get("authority_generation") != recovery_authority_generation:
        errors.append("$.use_time_authority_receipt.authority_generation: must exactly match recovery decision generation")
    if authority.get("authority_status") != "active":
        errors.append("$.use_time_authority_receipt.authority_status: automated mutation requires active authority")
    if not nonempty_evidence(authority.get("evidence_references")):
        errors.append("$.use_time_authority_receipt.evidence_references: non-empty evidence is required")

    authority_receipt_id = authority.get("authority_receipt_id")

    # Use-Time Authority -> Single-Use Consumption.
    if consumption.get("authority_receipt_id") != authority_receipt_id:
        errors.append("$.authority_consumption_receipt.authority_receipt_id: must bind to exact authority receipt")
    if consumption.get("authority_id") != recovery_authority_id:
        errors.append("$.authority_consumption_receipt.authority_id: must exactly match recovery authority_id")
    if consumption.get("authority_generation") != recovery_authority_generation:
        errors.append("$.authority_consumption_receipt.authority_generation: must exactly match recovery authority generation")
    if consumption.get("recovery_decision_id") != recovery_decision_id:
        errors.append("$.authority_consumption_receipt.recovery_decision_id: must exactly match recovery decision")
    if consumption.get("recovery_cycle_id") != cycle_id:
        errors.append("$.authority_consumption_receipt.recovery_cycle_id: must exactly match cycle_id")
    if consumption.get("bound_execution_mode") != execution_mode:
        errors.append("$.authority_consumption_receipt.bound_execution_mode: must exactly match execution_mode")
    if consumption.get("consumption_status") != "consumed":
        errors.append("$.authority_consumption_receipt.consumption_status: automated execution requires 'consumed'")
    if not nonempty_evidence(consumption.get("evidence_references")):
        errors.append("$.authority_consumption_receipt.evidence_references: non-empty evidence is required")

    consumption_receipt_id = consumption.get("consumption_receipt_id")
    use_token = consumption.get("use_token")
    dispatch_id = consumption.get("dispatch_id")
    for path, value in (
        ("$.authority_consumption_receipt.consumption_receipt_id", consumption_receipt_id),
        ("$.authority_consumption_receipt.use_token", use_token),
        ("$.authority_consumption_receipt.dispatch_id", dispatch_id),
    ):
        if not nonempty_string(value):
            errors.append(f"{path}: non-empty string is required")

    # Consumption -> Execution.
    if execution.get("recovery_decision_id") != recovery_decision_id:
        errors.append("$.execution_receipt.recovery_decision_id: must exactly match recovery decision")
    if execution.get("source_cycle_id") != recovery_of_cycle_id:
        errors.append("$.execution_receipt.source_cycle_id: must exactly match recovery source cycle")
    if execution.get("recovery_cycle_id") != cycle_id:
        errors.append("$.execution_receipt.recovery_cycle_id: must exactly match cycle_id")
    if execution.get("declared_execution_mode") != execution_mode:
        errors.append("$.execution_receipt.declared_execution_mode: must exactly match execution_mode")
    if execution.get("execution_status") == "observed" and execution.get("observed_execution_mode") != execution_mode:
        errors.append("$.execution_receipt.observed_execution_mode: observed mode must exactly match execution_mode")
    if execution.get("authority_receipt_id") != authority_receipt_id:
        errors.append("$.execution_receipt.authority_receipt_id: must exactly match consumed authority receipt")
    if execution.get("authority_generation_at_execution") != recovery_authority_generation:
        errors.append("$.execution_receipt.authority_generation_at_execution: must exactly match authority generation")
    if execution.get("authority_status_at_execution") != "active":
        errors.append("$.execution_receipt.authority_status_at_execution: automated observed execution requires active authority")
    if execution.get("authority_consumption_receipt_id") != consumption_receipt_id:
        errors.append("$.execution_receipt.authority_consumption_receipt_id: must exactly match consumption receipt")
    if execution.get("use_token") != use_token:
        errors.append("$.execution_receipt.use_token: must exactly match consumed use_token")
    if execution.get("dispatch_id") != dispatch_id:
        errors.append("$.execution_receipt.dispatch_id: must exactly match consumed dispatch_id")
    if not nonempty_evidence(execution.get("evidence_references")):
        errors.append("$.execution_receipt.evidence_references: non-empty evidence is required")

    # Execution -> State Effect.
    if effect.get("execution_receipt_id") != execution.get("receipt_id"):
        errors.append("$.state_effect_receipt.execution_receipt_id: must exactly match execution receipt_id")
    if effect.get("recovery_cycle_id") != cycle_id:
        errors.append("$.state_effect_receipt.recovery_cycle_id: must exactly match cycle_id")
    if effect.get("expected_target_state") != tip.get("target_state"):
        errors.append("$.state_effect_receipt.expected_target_state: must exactly match TIP target_state")
    if effect.get("effect_status") == "observed" and effect.get("observed_state") != tip.get("target_state"):
        errors.append("$.state_effect_receipt.observed_state: observed effect must equal TIP target_state")
    if effect.get("effect_status") == "observed" and not nonempty_evidence(effect.get("evidence_references")):
        errors.append("$.state_effect_receipt.evidence_references: observed effect requires evidence")

    # State Effect -> Fresh Review -> Next State.
    if review.get("transition_id") != tip.get("transition_id"):
        errors.append("$.envelope.review.transition_id: must exactly match TIP transition_id")

    reviewed = review.get("status") == "reviewed"
    if reviewed and tip.get("status") != "reviewed":
        errors.append("$.envelope.tip.status: reviewed final outcome requires reviewed TIP")
    if reviewed and not nonempty_evidence(review.get("evidence_references")):
        errors.append("$.envelope.review.evidence_references: reviewed outcome requires evidence")

    state_generation = effect.get("state_generation")
    if reviewed and review.get("accepted_state_generation") != state_generation:
        errors.append("$.envelope.review.accepted_state_generation: must exactly match state effect generation")

    # Temporal ordering and freshness.
    revalidated_at = parse_timestamp(revalidation.get("checked_at"), "$.envelope.path_revalidation.checked_at", errors)
    checked_at = parse_timestamp(authority.get("checked_at"), "$.use_time_authority_receipt.checked_at", errors)
    consumed_at = parse_timestamp(consumption.get("consumed_at"), "$.authority_consumption_receipt.consumed_at", errors)
    executed_at = parse_timestamp(execution.get("executed_at"), "$.execution_receipt.executed_at", errors)
    observed_at = parse_timestamp(effect.get("observed_at"), "$.state_effect_receipt.observed_at", errors)
    reviewed_at = parse_timestamp(review.get("reviewed_at"), "$.envelope.review.reviewed_at", errors) if reviewed else None

    ordered = [
        ("path revalidation", revalidated_at),
        ("authority check", checked_at),
        ("authority consumption", consumed_at),
        ("execution", executed_at),
        ("state observation", observed_at),
        ("review", reviewed_at),
    ]
    previous_name: str | None = None
    previous_time: datetime | None = None
    for name, timestamp in ordered:
        if timestamp is None:
            continue
        if previous_time is not None and timestamp < previous_time:
            errors.append(f"$: temporal order violation: {name} occurred before {previous_name}")
        previous_name = name
        previous_time = timestamp

    max_binding_age = authority.get("max_binding_age_seconds")
    if not isinstance(max_binding_age, int) or isinstance(max_binding_age, bool) or max_binding_age < 0:
        errors.append("$.use_time_authority_receipt.max_binding_age_seconds: non-negative integer is required")
    elif checked_at is not None:
        if consumed_at is not None and (consumed_at - checked_at).total_seconds() > max_binding_age:
            errors.append("$.authority_consumption_receipt.consumed_at: authority binding expired before consumption")
        if executed_at is not None and (executed_at - checked_at).total_seconds() > max_binding_age:
            errors.append("$.execution_receipt.executed_at: authority binding expired before execution")

    max_evidence_age = review.get("max_evidence_age_seconds")
    if reviewed:
        if not isinstance(max_evidence_age, int) or isinstance(max_evidence_age, bool) or max_evidence_age < 0:
            errors.append("$.envelope.review.max_evidence_age_seconds: reviewed outcome requires non-negative max evidence age")
        elif observed_at is not None and reviewed_at is not None:
            if observed_at > reviewed_at:
                errors.append("$.state_effect_receipt.observed_at: state evidence cannot be observed after review")
            elif (reviewed_at - observed_at).total_seconds() > max_evidence_age:
                errors.append("$.envelope.review.reviewed_at: state evidence is stale at review time")

    recovery_confirmed = review.get("next_state") == "RECOVERY_CONFIRMED"
    if recovery_confirmed:
        if execution.get("execution_status") != "observed":
            errors.append("$.envelope.review.next_state: RECOVERY_CONFIRMED requires observed execution")
        if effect.get("effect_status") != "observed":
            errors.append("$.envelope.review.next_state: RECOVERY_CONFIRMED requires observed state effect")
        if effect.get("observed_state") != tip.get("target_state"):
            errors.append("$.envelope.review.next_state: RECOVERY_CONFIRMED requires observed target state")
        if revalidation_status != "valid":
            errors.append("$.envelope.review.next_state: RECOVERY_CONFIRMED requires a valid committed path")
        if consumption.get("consumption_status") != "consumed":
            errors.append("$.envelope.review.next_state: RECOVERY_CONFIRMED requires consumed single-use authority")

    return errors


def mutate_di_intent(instance: dict[str, Any]) -> None:
    instance["envelope"]["di"]["intent_id"] = "dif.intent.WRONG"


def mutate_drp_path(instance: dict[str, Any]) -> None:
    instance["envelope"]["drp"]["selected_path_id"] = "path.X.not-evaluated"


def mutate_invalid_revalidation(instance: dict[str, Any]) -> None:
    instance["envelope"]["path_revalidation"]["status"] = "invalid"


def mutate_tip_path(instance: dict[str, Any]) -> None:
    instance["envelope"]["tip"]["selected_path_id"] = "path.C.wait-for-evidence"


def mutate_recovery_action(instance: dict[str, Any]) -> None:
    instance["recovery_decision"]["selected_action"] = "ROLLBACK"


def mutate_authority_generation(instance: dict[str, Any]) -> None:
    instance["use_time_authority_receipt"]["authority_generation"] = 99


def mutate_dispatch_binding(instance: dict[str, Any]) -> None:
    instance["execution_receipt"]["dispatch_id"] = "dispatch.WRONG"


def mutate_execution_before_consumption(instance: dict[str, Any]) -> None:
    instance["execution_receipt"]["executed_at"] = "2026-08-21T15:00:01.500000+00:00"


def mutate_effect_target(instance: dict[str, Any]) -> None:
    instance["state_effect_receipt"]["observed_state"] = "TRANSACTION_STATE_UNKNOWN"


def mutate_state_generation(instance: dict[str, Any]) -> None:
    instance["envelope"]["review"]["accepted_state_generation"] = 20


def mutate_stale_review(instance: dict[str, Any]) -> None:
    instance["envelope"]["review"]["reviewed_at"] = "2026-08-21T15:01:00+00:00"


MUTATIONS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("intent link broken", mutate_di_intent),
    ("DRP chose unevaluated path", mutate_drp_path),
    ("path invalidated without blocking TIP", mutate_invalid_revalidation),
    ("TIP silently changed committed path", mutate_tip_path),
    ("recovery action drifted from execution mode", mutate_recovery_action),
    ("authority generation changed before use", mutate_authority_generation),
    ("execution dispatch differs from consumed dispatch", mutate_dispatch_binding),
    ("execution happened before authority consumption", mutate_execution_before_consumption),
    ("observed state differs from TIP target", mutate_effect_target),
    ("review accepted stale state generation", mutate_state_generation),
    ("review used stale state evidence", mutate_stale_review),
]


def main() -> int:
    try:
        canonical = load_json(FIXTURE)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL {FIXTURE.relative_to(ROOT)}: {exc}")
        return 1

    canonical_errors = validate_end_to_end(canonical)
    if canonical_errors:
        print(f"FAIL {FIXTURE.relative_to(ROOT)} expected=pass")
        for error in canonical_errors:
            print(f"  - {error}")
        return 1

    print(f"PASS {FIXTURE.relative_to(ROOT)} expected=pass")

    ok = True
    for name, mutation in MUTATIONS:
        candidate = copy.deepcopy(canonical)
        mutation(candidate)
        errors = validate_end_to_end(candidate)
        if errors:
            print(f"PASS mutation rejected: {name}")
        else:
            print(f"FAIL mutation unexpectedly passed: {name}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
