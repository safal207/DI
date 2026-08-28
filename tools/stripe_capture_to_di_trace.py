#!/usr/bin/env python3
"""Translate a sanitized Stripe test-mode capture into a DI v0.5 trace.

The adapter covers the post-admission provider seam. The earlier ownership,
lease, fencing, and dispatch records remain the provider-neutral DI scaffold;
they are not claims about Stripe internals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import ambiguous_payment_sandbox as sandbox


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    capture = load_json(args.capture)
    if capture.get("provider") != "stripe" or capture.get("provider_mode") != "test":
        print("FAIL capture must be a Stripe test-mode capture")
        return 2

    lookup = capture.get("authoritative_lookup")
    first = capture.get("first_mutation")
    if not isinstance(lookup, dict) or not isinstance(first, dict):
        print("FAIL capture is missing first_mutation or authoritative_lookup")
        return 2
    if lookup.get("livemode") is not False:
        print("FAIL refusing to adapt a non-test-mode Stripe observation")
        return 2
    if lookup.get("status") != "succeeded":
        print(f"FAIL expected succeeded PaymentIntent, got {lookup.get('status')!r}")
        return 1

    effect_id = f"stripe-payment-intent:{lookup['payment_intent_id']}"
    effect_key = f"stripe-idempotency-sha256:{capture['effect_key_sha256']}"
    committed_at = lookup["observed_at"]
    ack_at = first["observed_at"]
    events = [
        {
            "event_index": 1,
            "event_type": "acknowledgement_lost",
            "observed_at": ack_at,
            "logical_operation_id": capture["logical_operation_id"],
            "effect_key": effect_key,
            "local_commit_state": "unknown",
        },
        {
            "event_index": 2,
            "event_type": "authoritative_lookup",
            "observed_at": committed_at,
            "effect_key": effect_key,
            "commit_status": "committed",
            "effect_id": effect_id,
            "state": "PAYMENT_COMMITTED",
        },
        {
            "event_index": 3,
            "event_type": "mutation_committed",
            "observed_at": committed_at,
            "logical_operation_id": capture["logical_operation_id"],
            "effect_key": effect_key,
            "effect_id": effect_id,
            "amount_minor": lookup.get("amount"),
            "currency": str(lookup.get("currency", "")).upper(),
            "state": "PAYMENT_COMMITTED",
        },
    ]

    trace = sandbox.materialize_trace(
        events=events,
        logical_operation_id=capture["logical_operation_id"],
        effect_key=effect_key,
        committed_effect_id=effect_id,
        trace_id=f"stripe-testmode.ambiguous-payment.{lookup['payment_intent_id']}",
        evidence_namespace=f"stripe-testmode/payment-intent/{lookup['payment_intent_id']}",
    )
    module = sandbox.load_validator_module()
    errors = module.validate_ambiguous_commit(trace)
    report = {
        "report_version": "0.1",
        "profile": "ambiguous-commit-v0.5",
        "input_file": str(args.capture),
        "status": "FAIL" if errors else "PASS",
        "error_count": len(errors),
        "errors": errors,
        "scope": (
            "post-admission Stripe test-mode evidence mapped onto a "
            "provider-neutral DI scaffold"
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "trace.json").write_text(
        json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output_dir / "conformance-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"WROTE DI trace and report to {args.output_dir}")
    if errors:
        for error in errors:
            print(f"  - {error}")
        return 1
    print("PASS sanitized Stripe test-mode post-admission trace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
