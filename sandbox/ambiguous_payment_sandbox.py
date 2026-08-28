#!/usr/bin/env python3
"""Deterministic provider-neutral sandbox for ambiguous payment recovery.

The sandbox models the failure DI v0.5 is designed to inspect:

1. a stale worker is rejected by a fencing boundary;
2. the current worker is admitted;
3. one payment effect commits;
4. the transport acknowledgement is lost;
5. an authoritative lookup recovers the committed effect;
6. a same-key replay returns the existing effect instead of creating another one.

No network access, provider account, credential, or external dependency is used.
The resulting trace is deliberately bound to the repository's canonical v0.5
fixture so CI can detect drift between the executable scenario and the public
conformance artifact.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_TRACE = ROOT / "fixtures/valid-ambiguous-commit-recovery-v0.5.json"


class LostAcknowledgement(RuntimeError):
    """Raised after an effect commits but before the caller receives success."""


@dataclass(frozen=True)
class PaymentEffect:
    effect_id: str
    logical_operation_id: str
    effect_key: str
    amount_minor: int
    currency: str


@dataclass(frozen=True)
class SandboxResult:
    trace: dict[str, Any]
    committed_effect_count: int
    first_effect_id: str
    replay_effect_id: str
    stale_attempt_rejected: bool
    current_attempt_accepted: bool


class PaymentSandbox:
    """Small in-memory side-effect boundary with fencing and stable effect keys."""

    def __init__(self, current_fencing_token: int = 102) -> None:
        self.current_fencing_token = current_fencing_token
        self._effects_by_key: dict[str, PaymentEffect] = {}
        self._fingerprints_by_key: dict[str, tuple[str, int, str]] = {}

    @property
    def committed_effect_count(self) -> int:
        return len(self._effects_by_key)

    def admit(self, fencing_token: int) -> bool:
        """Only the current fencing epoch may cross the mutation boundary."""

        return fencing_token == self.current_fencing_token

    def submit(
        self,
        *,
        logical_operation_id: str,
        effect_key: str,
        amount_minor: int,
        currency: str,
        fencing_token: int,
        lose_acknowledgement: bool = False,
    ) -> PaymentEffect:
        """Find or create exactly one effect for one stable effect key.

        Same key + same parameters returns the existing effect. Same key +
        different parameters is rejected because it would blur operation identity.
        """

        if not self.admit(fencing_token):
            raise PermissionError("stale fencing token rejected at side-effect boundary")

        fingerprint = (logical_operation_id, amount_minor, currency)
        existing = self._effects_by_key.get(effect_key)
        if existing is not None:
            if self._fingerprints_by_key[effect_key] != fingerprint:
                raise ValueError("same effect key cannot be reused with different parameters")
            return existing

        effect = PaymentEffect(
            effect_id=f"provider-effect.payment.{len(self._effects_by_key) + 1:03d}",
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            amount_minor=amount_minor,
            currency=currency,
        )
        self._effects_by_key[effect_key] = effect
        self._fingerprints_by_key[effect_key] = fingerprint

        if lose_acknowledgement:
            raise LostAcknowledgement(effect.effect_id)
        return effect

    def authoritative_lookup(self, effect_key: str) -> PaymentEffect | None:
        """Read the authoritative committed state for the stable effect key."""

        return self._effects_by_key.get(effect_key)


def load_canonical_trace() -> dict[str, Any]:
    with CANONICAL_TRACE.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("canonical v0.5 trace must be a JSON object")
    return value


def run_demo() -> SandboxResult:
    """Execute the deterministic lost-acknowledgement recovery scenario."""

    logical_operation_id = "operation.payment-recovery.001"
    effect_key = "effect-key.payment-recovery.001"
    sandbox = PaymentSandbox(current_fencing_token=102)

    stale_attempt_rejected = not sandbox.admit(101)
    current_attempt_accepted = sandbox.admit(102)
    if not stale_attempt_rejected or not current_attempt_accepted:
        raise AssertionError("fencing admission did not preserve the current epoch")

    acknowledgement_lost = False
    try:
        sandbox.submit(
            logical_operation_id=logical_operation_id,
            effect_key=effect_key,
            amount_minor=500,
            currency="usd",
            fencing_token=102,
            lose_acknowledgement=True,
        )
    except LostAcknowledgement:
        acknowledgement_lost = True

    if not acknowledgement_lost:
        raise AssertionError("scenario must lose the acknowledgement after commit")

    recovered = sandbox.authoritative_lookup(effect_key)
    if recovered is None:
        raise AssertionError("authoritative lookup failed to recover the committed effect")

    replay = sandbox.submit(
        logical_operation_id=logical_operation_id,
        effect_key=effect_key,
        amount_minor=500,
        currency="usd",
        fencing_token=102,
    )

    if replay.effect_id != recovered.effect_id:
        raise AssertionError("same-key replay created or selected a different effect")
    if sandbox.committed_effect_count != 1:
        raise AssertionError("ambiguous recovery created more than one committed effect")

    trace = load_canonical_trace()
    operation = trace.get("logical_operation", {})
    resolution = trace.get("commit_resolution", {})
    observations = trace.get("commit_outcome_receipts", [])

    if operation.get("logical_operation_id") != logical_operation_id:
        raise AssertionError("canonical trace logical_operation_id drifted from sandbox")
    if operation.get("effect_key") != effect_key:
        raise AssertionError("canonical trace effect_key drifted from sandbox")
    if not isinstance(observations, list) or len(observations) < 2:
        raise AssertionError("canonical trace must contain ambiguous and resolved observations")
    if observations[-1].get("committed_effect_id") != recovered.effect_id:
        raise AssertionError("canonical trace committed effect drifted from sandbox")
    if resolution.get("resolved_effect_id") != recovered.effect_id:
        raise AssertionError("canonical resolution drifted from sandbox result")
    if resolution.get("selected_next_action") != "ACCEPT_EXISTING_EFFECT":
        raise AssertionError("committed recovery must accept the existing effect")

    return SandboxResult(
        trace=trace,
        committed_effect_count=sandbox.committed_effect_count,
        first_effect_id=recovered.effect_id,
        replay_effect_id=replay.effect_id,
        stale_attempt_rejected=stale_attempt_rejected,
        current_attempt_accepted=current_attempt_accepted,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic DI v0.5 ambiguous-payment sandbox."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the generated JSON trace; stdout is used otherwise.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = run_demo()
    except (AssertionError, OSError, ValueError) as exc:
        print(f"FAIL deterministic payment sandbox: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(
        result.trace,
        indent=2 if args.pretty or args.output else None,
        sort_keys=args.output is None,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"WROTE {args.output}", file=sys.stderr)
    else:
        print(rendered)

    print(
        "PASS deterministic sandbox: stale rejected, current admitted, "
        "ack lost after commit, lookup recovered, same-key replay reused one effect",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
