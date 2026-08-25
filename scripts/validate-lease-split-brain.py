#!/usr/bin/env python3
"""Validate lease expiry, fencing, and split-brain recovery semantics (v0.4).

v0.3 proves that dispatch ownership is append-only and execution binds to the
latest owner. v0.4 adds bounded leases and monotonic fencing tokens so a stale
worker can be rejected even if it still believes it owns the dispatch.

This validator proves recorded trace semantics. Runtime safety still requires
the side-effect owner to enforce the fencing token atomically at admission.
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
FIXTURE = ROOT / "fixtures/valid-lease-split-brain-recovery-v0.4.json"
BASE_VALIDATOR_PATH = ROOT / "scripts/validate-multi-agent-dispatch.py"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_v03_validator() -> Callable[[Any], list[str]]:
    spec = importlib.util.spec_from_file_location("di_multi_agent_v03", BASE_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load v0.3 validator from {BASE_VALIDATOR_PATH}")
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    validator = getattr(module, "validate_multi_agent_dispatch", None)
    if not callable(validator):
        raise RuntimeError("validate_multi_agent_dispatch() is missing")
    return validator


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


def validate_lease_split_brain(instance: Any) -> list[str]:
    if not isinstance(instance, dict):
        return ["$: trace must be an object"]

    errors: list[str] = []
    if instance.get("profile_version") != "0.4":
        errors.append("$.profile_version: expected '0.4'")

    # Reuse every v0.3 ownership/dispatch invariant rather than forking it.
    try:
        base_validator = load_v03_validator()
        base_view = copy.deepcopy(instance)
        base_view["profile_version"] = "0.3"
        errors.extend(f"v0.3::{error}" for error in base_validator(base_view))
    except RuntimeError as exc:
        errors.append(f"$: cannot load v0.3 validator: {exc}")
        return errors

    consumption = instance.get("authority_consumption_receipt")
    ownership_events = instance.get("dispatch_ownership_events")
    leases = instance.get("dispatch_leases")
    attempts = instance.get("dispatch_attempt_receipts")
    execution = instance.get("execution_receipt")

    if not isinstance(consumption, dict):
        errors.append("$.authority_consumption_receipt: object is required")
        return errors
    if not isinstance(ownership_events, list) or not ownership_events:
        errors.append("$.dispatch_ownership_events: non-empty array is required")
        return errors
    if not isinstance(leases, list) or not leases:
        errors.append("$.dispatch_leases: non-empty array is required")
        return errors
    if not isinstance(attempts, list) or not attempts:
        errors.append("$.dispatch_attempt_receipts: non-empty array is required")
        return errors
    if not isinstance(execution, dict):
        errors.append("$.execution_receipt: object is required")
        return errors

    dispatch_id = consumption.get("dispatch_id")

    event_map: dict[str, dict[str, Any]] = {}
    event_times: dict[str, datetime] = {}
    for index, event in enumerate(ownership_events):
        path = f"$.dispatch_ownership_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{path}: object is required")
            continue
        event_id = event.get("ownership_event_id")
        if nonempty_string(event_id):
            event_map[event_id] = event
            parsed = parse_timestamp(event.get("occurred_at"), f"{path}.occurred_at", errors)
            if parsed is not None:
                event_times[event_id] = parsed

    if not event_map:
        return errors

    latest_event = ownership_events[-1] if isinstance(ownership_events[-1], dict) else None
    if latest_event is None:
        errors.append("$.dispatch_ownership_events[-1]: latest ownership event must be an object")
        return errors
    latest_event_id = latest_event.get("ownership_event_id")
    latest_actor = latest_event.get("actor_id")
    latest_generation = latest_event.get("ownership_generation")

    lease_map: dict[str, dict[str, Any]] = {}
    lease_times: dict[str, tuple[datetime, datetime]] = {}
    lease_tokens: set[int] = set()
    leases_by_event: dict[str, list[dict[str, Any]]] = {}
    previous_issued_at: datetime | None = None
    previous_token: int | None = None

    for index, lease in enumerate(leases):
        path = f"$.dispatch_leases[{index}]"
        if not isinstance(lease, dict):
            errors.append(f"{path}: object is required")
            continue

        lease_id = lease.get("lease_id")
        event_id = lease.get("ownership_event_id")
        token = lease.get("fencing_token")
        issued_at = parse_timestamp(lease.get("issued_at"), f"{path}.issued_at", errors)
        expires_at = parse_timestamp(lease.get("expires_at"), f"{path}.expires_at", errors)

        if lease.get("lease_version") != "0.1":
            errors.append(f"{path}.lease_version: expected '0.1'")
        if not nonempty_string(lease_id):
            errors.append(f"{path}.lease_id: non-empty string is required")
        elif lease_id in lease_map:
            errors.append(f"{path}.lease_id: duplicate lease id {lease_id!r}")
        else:
            lease_map[lease_id] = lease
        if lease.get("dispatch_id") != dispatch_id:
            errors.append(f"{path}.dispatch_id: lease must stay on consumed dispatch")
        if not isinstance(token, int) or isinstance(token, bool) or token < 1:
            errors.append(f"{path}.fencing_token: positive integer is required")
        elif token in lease_tokens:
            errors.append(f"{path}.fencing_token: duplicate fencing token {token}")
        else:
            lease_tokens.add(token)
        if not nonempty_evidence(lease.get("evidence_references")):
            errors.append(f"{path}.evidence_references: durable lease evidence is required")

        event = event_map.get(event_id) if nonempty_string(event_id) else None
        if event is None:
            errors.append(f"{path}.ownership_event_id: must reference a known ownership event")
        else:
            if lease.get("actor_id") != event.get("actor_id"):
                errors.append(f"{path}.actor_id: must match bound ownership event actor")
            if lease.get("ownership_generation") != event.get("ownership_generation"):
                errors.append(f"{path}.ownership_generation: must match bound ownership generation")
            leases_by_event.setdefault(event_id, []).append(lease)
            event_time = event_times.get(event_id)
            if event_time is not None and issued_at is not None and issued_at < event_time:
                errors.append(f"{path}.issued_at: lease cannot be issued before ownership event")

        if issued_at is not None and expires_at is not None:
            if expires_at <= issued_at:
                errors.append(f"{path}.expires_at: lease must expire after it is issued")
            if nonempty_string(lease_id):
                lease_times[lease_id] = (issued_at, expires_at)

        # Lease array is an append-only issuance trace. Tokens must fence older epochs.
        if issued_at is not None and previous_issued_at is not None and issued_at < previous_issued_at:
            errors.append(f"{path}.issued_at: lease receipts must be issuance-ordered")
        if isinstance(token, int) and not isinstance(token, bool) and previous_token is not None:
            if token <= previous_token:
                errors.append(f"{path}.fencing_token: must strictly increase across lease epochs")
        if issued_at is not None:
            previous_issued_at = issued_at
        if isinstance(token, int) and not isinstance(token, bool):
            previous_token = token

    for index, event in enumerate(ownership_events):
        if not isinstance(event, dict):
            continue
        event_id = event.get("ownership_event_id")
        if nonempty_string(event_id) and not leases_by_event.get(event_id):
            errors.append(f"$.dispatch_ownership_events[{index}]: ownership epoch requires at least one lease receipt")

        if index > 0 and event.get("transfer_basis") == "lease_expiry":
            prior = ownership_events[index - 1]
            if not isinstance(prior, dict):
                continue
            prior_id = prior.get("ownership_event_id")
            prior_leases = leases_by_event.get(prior_id, []) if nonempty_string(prior_id) else []
            transfer_time = event_times.get(event_id) if nonempty_string(event_id) else None
            expiries: list[datetime] = []
            for prior_lease in prior_leases:
                lease_id = prior_lease.get("lease_id")
                if nonempty_string(lease_id) and lease_id in lease_times:
                    expiries.append(lease_times[lease_id][1])
            if not expiries:
                errors.append(f"$.dispatch_ownership_events[{index}]: lease_expiry transfer requires predecessor lease expiry evidence")
            elif transfer_time is not None and transfer_time < max(expiries):
                errors.append(f"$.dispatch_ownership_events[{index}].occurred_at: lease-expiry takeover cannot happen before predecessor lease expires")

    current_leases = leases_by_event.get(latest_event_id, []) if nonempty_string(latest_event_id) else []
    if not current_leases:
        errors.append("$.dispatch_leases: latest ownership event requires a current lease")
        return errors

    def token_value(lease: dict[str, Any]) -> int:
        value = lease.get("fencing_token")
        return value if isinstance(value, int) and not isinstance(value, bool) else -1

    current_lease = max(current_leases, key=token_value)
    current_lease_id = current_lease.get("lease_id")
    current_token = current_lease.get("fencing_token")
    current_times = lease_times.get(current_lease_id) if nonempty_string(current_lease_id) else None

    attempt_map: dict[str, dict[str, Any]] = {}
    accepted_attempts: list[dict[str, Any]] = []

    for index, attempt in enumerate(attempts):
        path = f"$.dispatch_attempt_receipts[{index}]"
        if not isinstance(attempt, dict):
            errors.append(f"{path}: object is required")
            continue

        attempt_id = attempt.get("attempt_id")
        lease_id = attempt.get("lease_id")
        event_id = attempt.get("ownership_event_id")
        attempt_time = parse_timestamp(attempt.get("attempted_at"), f"{path}.attempted_at", errors)

        if attempt.get("attempt_version") != "0.1":
            errors.append(f"{path}.attempt_version: expected '0.1'")
        if not nonempty_string(attempt_id):
            errors.append(f"{path}.attempt_id: non-empty string is required")
        elif attempt_id in attempt_map:
            errors.append(f"{path}.attempt_id: duplicate attempt id {attempt_id!r}")
        else:
            attempt_map[attempt_id] = attempt
        if attempt.get("dispatch_id") != dispatch_id:
            errors.append(f"{path}.dispatch_id: attempt must stay on consumed dispatch")
        if not nonempty_evidence(attempt.get("evidence_references")):
            errors.append(f"{path}.evidence_references: admission outcome requires evidence")

        lease = lease_map.get(lease_id) if nonempty_string(lease_id) else None
        if lease is None:
            errors.append(f"{path}.lease_id: must reference a known lease")
            continue
        event = event_map.get(event_id) if nonempty_string(event_id) else None
        if event is None:
            errors.append(f"{path}.ownership_event_id: must reference a known ownership event")
            continue

        if attempt.get("actor_id") != lease.get("actor_id") or attempt.get("actor_id") != event.get("actor_id"):
            errors.append(f"{path}.actor_id: must match lease and ownership actor")
        if attempt.get("ownership_generation") != lease.get("ownership_generation") or attempt.get("ownership_generation") != event.get("ownership_generation"):
            errors.append(f"{path}.ownership_generation: must match lease and ownership generation")
        if attempt.get("fencing_token") != lease.get("fencing_token"):
            errors.append(f"{path}.fencing_token: must match referenced lease")

        lease_window = lease_times.get(lease_id)
        lease_active = False
        if attempt_time is not None and lease_window is not None:
            issued_at, expires_at = lease_window
            if attempt_time < issued_at:
                errors.append(f"{path}.attempted_at: attempt cannot precede lease issuance")
            lease_active = issued_at <= attempt_time < expires_at

        is_current = (
            event_id == latest_event_id
            and attempt.get("actor_id") == latest_actor
            and attempt.get("ownership_generation") == latest_generation
            and lease_id == current_lease_id
            and attempt.get("fencing_token") == current_token
        )

        outcome = attempt.get("outcome")
        reason = attempt.get("reason")
        if outcome == "accepted":
            accepted_attempts.append(attempt)
            if reason != "accepted_current_lease":
                errors.append(f"{path}.reason: accepted attempt must use 'accepted_current_lease'")
            if not is_current:
                errors.append(f"{path}: only the current ownership lease with highest fencing token may be accepted")
            if not lease_active:
                errors.append(f"{path}: accepted attempt requires an unexpired lease")
        elif outcome == "rejected":
            if reason == "accepted_current_lease":
                errors.append(f"{path}.reason: rejected attempt cannot claim current-lease acceptance")
            if is_current and lease_active:
                errors.append(f"{path}: current live lease was rejected by the lease gate without a supported lease/fencing reason")
            if reason == "stale_fencing_token" and isinstance(current_token, int):
                token = attempt.get("fencing_token")
                if not isinstance(token, int) or isinstance(token, bool) or token >= current_token:
                    errors.append(f"{path}.reason: stale_fencing_token requires a token lower than current token")
            if reason == "lease_expired" and lease_active:
                errors.append(f"{path}.reason: lease_expired contradicts an active lease window")
            if reason in {"not_current_owner", "ownership_superseded"} and is_current:
                errors.append(f"{path}.reason: current owner cannot be marked superseded")
        else:
            errors.append(f"{path}.outcome: expected 'accepted' or 'rejected'")

    if len(accepted_attempts) != 1:
        errors.append(f"$.dispatch_attempt_receipts: exactly one attempt may be accepted, got {len(accepted_attempts)}")
        return errors

    accepted = accepted_attempts[0]
    accepted_id = accepted.get("attempt_id")
    accepted_time = parse_timestamp(accepted.get("attempted_at"), "$.dispatch_attempt_receipts[accepted].attempted_at", errors)

    if execution.get("dispatch_attempt_id") != accepted_id:
        errors.append("$.execution_receipt.dispatch_attempt_id: must bind to the single accepted dispatch attempt")
    if execution.get("dispatch_lease_id") != accepted.get("lease_id"):
        errors.append("$.execution_receipt.dispatch_lease_id: must bind to accepted attempt lease")
    if execution.get("dispatch_fencing_token") != accepted.get("fencing_token"):
        errors.append("$.execution_receipt.dispatch_fencing_token: must bind to accepted attempt fencing token")
    if execution.get("actor_id") != accepted.get("actor_id"):
        errors.append("$.execution_receipt.actor_id: must match accepted attempt actor")
    if execution.get("dispatch_ownership_event_id") != accepted.get("ownership_event_id"):
        errors.append("$.execution_receipt.dispatch_ownership_event_id: must match accepted attempt ownership event")
    if execution.get("dispatch_ownership_generation") != accepted.get("ownership_generation"):
        errors.append("$.execution_receipt.dispatch_ownership_generation: must match accepted attempt ownership generation")

    executed_at = parse_timestamp(execution.get("executed_at"), "$.execution_receipt.executed_at", errors)
    if accepted_time is not None and executed_at is not None and executed_at < accepted_time:
        errors.append("$.execution_receipt.executed_at: execution cannot precede accepted admission attempt")
    if current_times is not None and executed_at is not None:
        issued_at, expires_at = current_times
        if not (issued_at <= executed_at < expires_at):
            errors.append("$.execution_receipt.executed_at: execution must occur inside current lease window")

    return errors


def set_nested(instance: dict[str, Any], path: tuple[Any, ...], value: Any) -> None:
    cursor: Any = instance
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value


def accept_stale_worker(instance: dict[str, Any]) -> None:
    attempt = instance["dispatch_attempt_receipts"][0]
    attempt["outcome"] = "accepted"
    attempt["reason"] = "accepted_current_lease"


def accept_both_workers(instance: dict[str, Any]) -> None:
    accept_stale_worker(instance)
    instance["dispatch_attempt_receipts"][1]["outcome"] = "accepted"


def extend_predecessor_lease(instance: dict[str, Any]) -> None:
    instance["dispatch_leases"][0]["expires_at"] = "2026-08-24T14:42:06+00:00"


def duplicate_fencing_token(instance: dict[str, Any]) -> None:
    instance["dispatch_leases"][1]["fencing_token"] = 101
    instance["dispatch_attempt_receipts"][1]["fencing_token"] = 101
    instance["execution_receipt"]["dispatch_fencing_token"] = 101


MUTATIONS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    (
        "lease-expiry takeover occurs before predecessor expiry",
        lambda x: set_nested(x, ("dispatch_ownership_events", 1, "occurred_at"), "2026-08-24T14:42:04.900000+00:00"),
    ),
    ("stale worker is accepted", accept_stale_worker),
    ("both workers are accepted", accept_both_workers),
    ("fencing token does not advance", duplicate_fencing_token),
    (
        "execution uses stale fencing token",
        lambda x: set_nested(x, ("execution_receipt", "dispatch_fencing_token"), 101),
    ),
    (
        "execution uses stale lease",
        lambda x: set_nested(x, ("execution_receipt", "dispatch_lease_id"), "lease.payment-recovery.A.001"),
    ),
    (
        "current attempt happens after lease expiry",
        lambda x: set_nested(x, ("dispatch_attempt_receipts", 1, "attempted_at"), "2026-08-24T14:42:10.100000+00:00"),
    ),
    ("predecessor lease remains live during takeover", extend_predecessor_lease),
    (
        "current lease actor mismatches owner",
        lambda x: set_nested(x, ("dispatch_leases", 1, "actor_id"), "worker.C"),
    ),
    (
        "attempt references unknown lease",
        lambda x: set_nested(x, ("dispatch_attempt_receipts", 1, "lease_id"), "lease.unknown"),
    ),
    (
        "execution binds rejected stale attempt",
        lambda x: set_nested(x, ("execution_receipt", "dispatch_attempt_id"), "attempt.payment-recovery.A.stale.001"),
    ),
    (
        "rejected stale worker claims accepted-current reason",
        lambda x: set_nested(x, ("dispatch_attempt_receipts", 0, "reason"), "accepted_current_lease"),
    ),
]


def main() -> int:
    try:
        canonical = load_json(FIXTURE)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL canonical fixture load: {exc}")
        return 1

    canonical_errors = validate_lease_split_brain(canonical)
    if canonical_errors:
        print("FAIL canonical v0.4 lease/split-brain fixture")
        for error in canonical_errors:
            print(f"  - {error}")
        return 1
    print("PASS canonical v0.4 lease/split-brain recovery")

    ok = True
    for name, mutate in MUTATIONS:
        case = copy.deepcopy(canonical)
        mutate(case)
        errors = validate_lease_split_brain(case)
        if errors:
            print(f"PASS mutation rejected: {name}")
        else:
            print(f"FAIL mutation unexpectedly passed: {name}")
            ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
