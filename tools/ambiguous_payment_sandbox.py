#!/usr/bin/env python3
"""Deterministic provider-neutral ambiguous-payment sandbox.

The sandbox commits one logical payment effect, intentionally loses the
acknowledgement, then resolves the authoritative state without creating a
second effect. It maps the observed events into the existing DI v0.5 trace
shape and validates the result with the repository's canonical validator.

No network access, credentials, external provider, or third-party dependency
is required.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "fixtures/valid-ambiguous-commit-recovery-v0.5.json"
VALIDATOR_PATH = ROOT / "scripts/validate-ambiguous-commit.py"
DEFAULT_OUTPUT = ROOT / "evidence/ambiguous-payment-sandbox"


class LostAcknowledgement(RuntimeError):
    """Raised after a mutation commits but before its response is accepted locally."""


@dataclass(frozen=True)
class SandboxEffect:
    effect_id: str
    logical_operation_id: str
    effect_key: str
    amount_minor: int
    currency: str
    state: str


class DeterministicClock:
    def __init__(self) -> None:
        self._current = datetime(2026, 8, 28, 12, 0, 0, tzinfo=timezone.utc)

    def tick(self, milliseconds: int = 100) -> str:
        self._current += timedelta(milliseconds=milliseconds)
        return self._current.isoformat(timespec="milliseconds")


class InMemoryPaymentProvider:
    """Tiny stateful provider with same-key/same-effect semantics."""

    def __init__(self, clock: DeterministicClock) -> None:
        self.clock = clock
        self.effects_by_key: dict[str, SandboxEffect] = {}
        self.events: list[dict[str, Any]] = []
        self._next_effect_number = 1

    def _record(self, event_type: str, **details: Any) -> dict[str, Any]:
        event = {
            "event_index": len(self.events) + 1,
            "event_type": event_type,
            "observed_at": self.clock.tick(),
            **details,
        }
        self.events.append(event)
        return event

    def submit(
        self,
        *,
        logical_operation_id: str,
        effect_key: str,
        amount_minor: int,
        currency: str,
        lose_acknowledgement: bool,
    ) -> SandboxEffect:
        existing = self.effects_by_key.get(effect_key)
        if existing is not None:
            if (
                existing.logical_operation_id != logical_operation_id
                or existing.amount_minor != amount_minor
                or existing.currency != currency
            ):
                self._record(
                    "same_key_parameter_mismatch_rejected",
                    logical_operation_id=logical_operation_id,
                    effect_key=effect_key,
                )
                raise ValueError("same effect key was reused with different parameters")
            self._record(
                "same_key_existing_effect_returned",
                logical_operation_id=logical_operation_id,
                effect_key=effect_key,
                effect_id=existing.effect_id,
                state=existing.state,
            )
            return existing

        effect = SandboxEffect(
            effect_id=f"sandbox-effect.payment.{self._next_effect_number:03d}",
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            amount_minor=amount_minor,
            currency=currency,
            state="PAYMENT_COMMITTED",
        )
        self._next_effect_number += 1
        self.effects_by_key[effect_key] = effect
        self._record(
            "mutation_committed",
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            effect_id=effect.effect_id,
            amount_minor=amount_minor,
            currency=currency,
            state=effect.state,
        )

        if lose_acknowledgement:
            self._record(
                "acknowledgement_lost",
                logical_operation_id=logical_operation_id,
                effect_key=effect_key,
                local_commit_state="unknown",
            )
            raise LostAcknowledgement(
                "the provider committed the effect but the local acknowledgement was lost"
            )

        self._record(
            "mutation_acknowledged",
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            effect_id=effect.effect_id,
            state=effect.state,
        )
        return effect

    def authoritative_lookup(self, *, effect_key: str) -> SandboxEffect | None:
        effect = self.effects_by_key.get(effect_key)
        self._record(
            "authoritative_lookup",
            effect_key=effect_key,
            commit_status="committed" if effect else "not_committed",
            effect_id=effect.effect_id if effect else None,
            state=effect.state if effect else "PAYMENT_NOT_COMMITTED",
        )
        return effect


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_validator_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "di_validate_ambiguous_commit", VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_strings(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        result = value
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [replace_strings(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: replace_strings(item, replacements)
            for key, item in value.items()
        }
    return value


def _event(events: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
    matches = [item for item in events if item.get("event_type") == event_type]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {event_type!r} event, got {len(matches)}")
    return matches[0]


def materialize_trace(
    *,
    events: list[dict[str, Any]],
    logical_operation_id: str,
    effect_key: str,
    committed_effect_id: str,
    trace_id: str,
    evidence_namespace: str,
    template_path: Path = TEMPLATE,
) -> dict[str, Any]:
    """Map observed sandbox/provider events into the released v0.5 trace shape."""

    template = load_json(template_path)
    trace = replace_strings(
        copy.deepcopy(template),
        {
            "payment-recovery": "sandbox-payment-recovery",
            "provider-effect.payment.001": committed_effect_id,
            "operation.sandbox-payment-recovery.001": logical_operation_id,
            "effect-key.sandbox-payment-recovery.001": effect_key,
        },
    )
    trace["trace_id"] = trace_id

    committed = _event(events, "mutation_committed")
    lost = _event(events, "acknowledgement_lost")
    lookup = _event(events, "authoritative_lookup")

    # Rebase the represented execution timeline to the deterministic sandbox run.
    trace["authority_consumption_receipt"]["consumed_at"] = (
        "2026-08-28T11:59:56.000+00:00"
    )
    trace["dispatch_ownership_events"][0]["occurred_at"] = (
        "2026-08-28T11:59:56.100+00:00"
    )
    trace["dispatch_leases"][0]["issued_at"] = "2026-08-28T11:59:56.200+00:00"
    trace["dispatch_leases"][0]["expires_at"] = "2026-08-28T11:59:59.000+00:00"
    trace["dispatch_ownership_events"][1]["occurred_at"] = (
        "2026-08-28T11:59:59.100+00:00"
    )
    trace["dispatch_leases"][1]["issued_at"] = "2026-08-28T11:59:59.200+00:00"
    trace["dispatch_leases"][1]["expires_at"] = "2026-08-28T12:00:10.000+00:00"
    trace["dispatch_attempt_receipts"][0]["attempted_at"] = (
        "2026-08-28T11:59:59.300+00:00"
    )
    trace["dispatch_attempt_receipts"][1]["attempted_at"] = (
        "2026-08-28T11:59:59.400+00:00"
    )
    trace["execution_receipt"]["executed_at"] = "2026-08-28T11:59:59.500+00:00"

    operation = trace["logical_operation"]
    operation["logical_operation_id"] = logical_operation_id
    operation["effect_key"] = effect_key
    operation["intended_effect"] = (
        "Commit exactly one provider-neutral sandbox payment effect."
    )
    operation["evidence_references"] = [
        f"evidence://{evidence_namespace}/logical-operation/{logical_operation_id}",
        f"evidence://{evidence_namespace}/identity-contract/same-key-same-effect",
    ]

    unknown_receipt = trace["commit_outcome_receipts"][0]
    unknown_receipt["logical_operation_id"] = logical_operation_id
    unknown_receipt["effect_key"] = effect_key
    unknown_receipt["observed_at"] = lost["observed_at"]
    unknown_receipt["evidence_references"] = [
        f"evidence://{evidence_namespace}/event/{lost['event_index']}/acknowledgement-lost"
    ]

    committed_receipt = trace["commit_outcome_receipts"][1]
    committed_receipt["logical_operation_id"] = logical_operation_id
    committed_receipt["effect_key"] = effect_key
    committed_receipt["committed_effect_id"] = committed_effect_id
    committed_receipt["observed_at"] = lookup["observed_at"]
    committed_receipt["evidence_references"] = [
        f"evidence://{evidence_namespace}/event/{lookup['event_index']}/authoritative-lookup"
    ]

    resolution = trace["commit_resolution"]
    resolution["logical_operation_id"] = logical_operation_id
    resolution["effect_key"] = effect_key
    resolution["resolved_effect_id"] = committed_effect_id
    resolution["resolution_status"] = "committed"
    resolution["selected_next_action"] = "ACCEPT_EXISTING_EFFECT"
    resolution.pop("next_effect_key", None)
    resolution["resolved_at"] = (
        datetime.fromisoformat(lookup["observed_at"])
        + timedelta(milliseconds=100)
    ).isoformat(timespec="milliseconds")
    resolution["evidence_references"] = [
        f"evidence://{evidence_namespace}/event/{lookup['event_index']}/authoritative-lookup",
        f"evidence://{evidence_namespace}/decision/no-second-mutation-authorized",
    ]

    state_effect = trace["state_effect_receipt"]
    state_effect["expected_target_state"] = "PAYMENT_COMMITTED"
    state_effect["observed_state"] = committed["state"]
    state_effect["effect_status"] = "observed"
    state_effect["observed_at"] = (
        datetime.fromisoformat(resolution["resolved_at"])
        + timedelta(milliseconds=100)
    ).isoformat(timespec="milliseconds")
    state_effect["evidence_references"] = [
        f"evidence://{evidence_namespace}/event/{committed['event_index']}/mutation-committed",
        f"evidence://{evidence_namespace}/effect/{committed_effect_id}",
    ]
    return trace


def run_sandbox() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    clock = DeterministicClock()
    provider = InMemoryPaymentProvider(clock)
    logical_operation_id = "operation.sandbox-payment.001"
    effect_key = "effect-key.sandbox-payment.001"

    acknowledgement_lost = False
    try:
        provider.submit(
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            amount_minor=2500,
            currency="EUR",
            lose_acknowledgement=True,
        )
    except LostAcknowledgement:
        acknowledgement_lost = True

    if not acknowledgement_lost:
        raise RuntimeError("sandbox did not exercise the lost-acknowledgement path")

    recovered = provider.authoritative_lookup(effect_key=effect_key)
    if recovered is None:
        raise RuntimeError("authoritative lookup did not recover the committed effect")

    trace = materialize_trace(
        events=provider.events,
        logical_operation_id=logical_operation_id,
        effect_key=effect_key,
        committed_effect_id=recovered.effect_id,
        trace_id="sandbox.ambiguous-payment-recovery.001",
        evidence_namespace="di-sandbox/ambiguous-payment/001",
    )

    validator_module = load_validator_module()
    validator: Callable[[Any], list[str]] = getattr(
        validator_module, "validate_ambiguous_commit"
    )
    errors = validator(trace)
    report = {
        "report_version": "0.1",
        "profile": "ambiguous-commit-v0.5",
        "input_file": "evidence/ambiguous-payment-sandbox/trace.json",
        "status": "FAIL" if errors else "PASS",
        "error_count": len(errors),
        "errors": errors,
    }
    summary = {
        "sandbox_version": "0.1",
        "scenario": "commit_then_lose_ack_then_authoritative_lookup",
        "logical_operation_id": logical_operation_id,
        "effect_key_sha256": hashlib.sha256(effect_key.encode("utf-8")).hexdigest(),
        "acknowledgement_lost": acknowledgement_lost,
        "authoritative_commit_status": "committed",
        "committed_effect_id": recovered.effect_id,
        "stored_effect_count": len(provider.effects_by_key),
        "duplicate_effect_count": max(0, len(provider.effects_by_key) - 1),
        "selected_next_action": "ACCEPT_EXISTING_EFFECT",
        "conformance_status": report["status"],
        "external_provider_used": False,
    }
    raw = {
        "event_log_version": "0.1",
        "provider": "deterministic-in-memory-sandbox",
        "provider_state": {
            "stored_effect_count": len(provider.effects_by_key),
            "effects": [effect.__dict__ for effect in provider.effects_by_key.values()],
        },
        "events": provider.events,
    }
    return raw, trace, {"report": report, "summary": summary}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compare_json(path: Path, expected: Any) -> list[str]:
    if not path.exists():
        return [f"missing expected artifact: {path}"]
    actual = load_json(path)
    return [] if actual == expected else [f"artifact differs from deterministic output: {path}"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Directory for raw events, DI trace, report, and summary",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare deterministic output with already committed artifacts",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw, trace, result = run_sandbox()
    artifacts = {
        "raw-events.json": raw,
        "trace.json": trace,
        "conformance-report.json": result["report"],
        "summary.json": result["summary"],
    }

    if args.check:
        errors: list[str] = []
        for filename, value in artifacts.items():
            errors.extend(compare_json(args.output_dir / filename, value))
        if errors:
            print("FAIL deterministic sandbox artifact check")
            for error in errors:
                print(f"  - {error}")
            return 1
        print("PASS deterministic sandbox artifacts are reproducible")
    else:
        for filename, value in artifacts.items():
            write_json(args.output_dir / filename, value)
        print(f"WROTE deterministic sandbox evidence to {args.output_dir}")

    if result["report"]["status"] != "PASS":
        print("FAIL generated sandbox trace did not conform")
        for error in result["report"]["errors"]:
            print(f"  - {error}")
        return 1

    print("PASS ambiguous-payment sandbox: one effect, lost acknowledgement, authoritative recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
