#!/usr/bin/env python3
"""Capture a sanitized Stripe test-mode lost-acknowledgement recovery trace.

This optional adapter performs real Stripe test-mode API calls only when the
caller supplies STRIPE_SECRET_KEY at runtime. The key must start with sk_test_,
is never printed, and is never written to the capture. The first response body
is deliberately discarded after Stripe returns response headers; the same
request is then replayed with the same idempotency key and resolved by an
explicit PaymentIntent lookup.

This script is not executed in repository CI and does not imply Stripe
endorsement or DI conformance of Stripe itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_BASE = "https://api.stripe.com/v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def require_test_secret() -> str:
    secret = os.environ.get("STRIPE_SECRET_KEY", "")
    if not secret:
        raise RuntimeError("STRIPE_SECRET_KEY is required for live test-mode capture")
    if not secret.startswith("sk_test_"):
        raise RuntimeError(
            "refusing to run: STRIPE_SECRET_KEY must be a Stripe test secret (sk_test_...)"
        )
    return secret


def stripe_request(
    *,
    secret: str,
    method: str,
    path: str,
    form: list[tuple[str, str]] | None = None,
    idempotency_key: str | None = None,
    discard_body: bool = False,
) -> dict[str, Any]:
    body = urllib.parse.urlencode(form).encode("utf-8") if form is not None else None
    request = urllib.request.Request(
        API_BASE + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "DI-v0.5-testmode-capture/0.1",
            **({"Idempotency-Key": idempotency_key} if idempotency_key else {}),
        },
    )
    observed_at = now()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = {
                "observed_at": observed_at,
                "http_status": response.status,
                "request_id": response.headers.get("Request-Id"),
            }
            if discard_body:
                result["response_body"] = "discarded"
                return result
            raw = response.read().decode("utf-8")
            result["body"] = json.loads(raw)
            return result
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw[:500]}}
        message = parsed.get("error", {}).get("message", "Stripe API request failed")
        raise RuntimeError(f"Stripe test-mode API error {exc.code}: {message}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Stripe test-mode network error: {exc.reason}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--amount", type=int, default=2500, help="Minor currency units")
    parser.add_argument("--currency", default="eur")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.amount <= 0:
        print("amount must be positive", file=sys.stderr)
        return 2

    try:
        secret = require_test_secret()
        logical_operation_id = f"stripe-testmode-operation-{uuid.uuid4()}"
        raw_idempotency_key = f"di-v05-{uuid.uuid4()}"
        key_digest = hashlib.sha256(raw_idempotency_key.encode("utf-8")).hexdigest()
        form = [
            ("amount", str(args.amount)),
            ("currency", args.currency.lower()),
            ("payment_method", "pm_card_visa"),
            ("payment_method_types[]", "card"),
            ("confirm", "true"),
            ("description", "DI v0.5 ambiguous commit test-mode capture"),
            ("metadata[di_logical_operation_id]", logical_operation_id),
        ]

        first = stripe_request(
            secret=secret,
            method="POST",
            path="/payment_intents",
            form=form,
            idempotency_key=raw_idempotency_key,
            discard_body=True,
        )
        replay = stripe_request(
            secret=secret,
            method="POST",
            path="/payment_intents",
            form=form,
            idempotency_key=raw_idempotency_key,
        )
        payment_intent = replay.get("body")
        if not isinstance(payment_intent, dict) or not payment_intent.get("id"):
            raise RuntimeError("same-key replay did not return a PaymentIntent id")
        payment_intent_id = payment_intent["id"]

        lookup = stripe_request(
            secret=secret,
            method="GET",
            path=f"/payment_intents/{urllib.parse.quote(payment_intent_id)}",
        )
        lookup_body = lookup.get("body")
        if not isinstance(lookup_body, dict):
            raise RuntimeError("PaymentIntent lookup did not return a JSON object")

        capture = {
            "capture_version": "0.1",
            "provider": "stripe",
            "provider_mode": "test",
            "captured_at": now(),
            "logical_operation_id": logical_operation_id,
            "effect_key_sha256": key_digest,
            "amount_minor": args.amount,
            "currency": args.currency.lower(),
            "first_mutation": {
                "observed_at": first["observed_at"],
                "http_status": first["http_status"],
                "request_id": first.get("request_id"),
                "local_observation": "acknowledgement_body_discarded",
                "commit_state_after_transport": "unknown",
            },
            "same_key_replay": {
                "observed_at": replay["observed_at"],
                "http_status": replay["http_status"],
                "request_id": replay.get("request_id"),
                "payment_intent_id": payment_intent_id,
                "status": payment_intent.get("status"),
            },
            "authoritative_lookup": {
                "observed_at": lookup["observed_at"],
                "http_status": lookup["http_status"],
                "request_id": lookup.get("request_id"),
                "payment_intent_id": lookup_body.get("id"),
                "status": lookup_body.get("status"),
                "amount": lookup_body.get("amount"),
                "currency": lookup_body.get("currency"),
                "livemode": lookup_body.get("livemode"),
            },
            "sanitization": {
                "secret_key_written": False,
                "raw_idempotency_key_written": False,
                "customer_data_requested": False,
            },
            "claim_boundary": (
                "This is a sanitized Stripe test-mode observation. It does not prove "
                "Stripe endorsement, exactly-once runtime behavior, or complete network evidence."
            ),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(capture, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"WROTE sanitized Stripe test-mode capture to {args.output}")
        print("No secret key or raw idempotency key was written.")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
