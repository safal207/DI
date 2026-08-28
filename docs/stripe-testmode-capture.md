# Optional Stripe Test-Mode Capture

Status: **adapter ready; no live Stripe capture committed**

This document explains how to collect one sanitized Stripe test-mode observation for the DI v0.5 post-admission seam.

It does not claim Stripe endorsement, integration, or conformance.

## Why this is optional

The deterministic sandbox is the reproducible baseline because it needs no account or secret.

A real Stripe test-mode call requires a private test secret. Secrets must not be committed, printed, requested in an issue, or copied into a trace.

The repository therefore provides tooling, but CI does not execute it.

## Safety rules

The capture tool:

- reads `STRIPE_SECRET_KEY` from the process environment only;
- requires the key prefix `sk_test_`;
- refuses live keys;
- never prints the key;
- never writes the key;
- never writes the raw idempotency key;
- does not request customer data;
- writes local captures under an ignored directory by default convention.

Use a restricted disposable test environment where possible. Rotate the test key if it is ever exposed outside the intended secret store.

## Capture sequence

```text
create and confirm one test PaymentIntent
with one idempotency key
↓
intentionally discard the first response body
↓
local observation = unknown
↓
replay the exact request with the exact same key
↓
recover the PaymentIntent id
↓
GET the PaymentIntent explicitly
↓
write a sanitized capture
```

The first request is not treated as failed merely because its response body is discarded.

## Run

From the repository root:

```bash
export STRIPE_SECRET_KEY='sk_test_...'

python tools/capture_stripe_testmode.py \
  --amount 2500 \
  --currency eur \
  --output evidence/stripe-testmode-local/capture.json
```

The `evidence/stripe-testmode-local/` directory is ignored by Git.

Translate the sanitized capture:

```bash
python tools/stripe_capture_to_di_trace.py \
  evidence/stripe-testmode-local/capture.json \
  --output-dir evidence/stripe-testmode-local/di-trace
```

Expected outputs:

```text
evidence/stripe-testmode-local/
├── capture.json
└── di-trace/
    ├── trace.json
    └── conformance-report.json
```

## What may be published

Before publishing any capture, inspect it manually.

A publishable sanitized subset may include:

- test-mode flag;
- PaymentIntent id;
- amount and currency;
- status;
- request ids;
- timestamps;
- hash of the idempotency key;
- DI trace and conformance report;
- exact claim boundary.

Do not publish:

- secret keys;
- raw Authorization headers;
- raw idempotency keys unless intentionally approved;
- customer email, name, address, card data, or metadata containing personal information;
- unrelated account configuration;
- production identifiers.

## Adapter boundary

The Stripe adapter validates only the provider-facing post-admission sequence:

```text
response ambiguity
→ same-key recovery
→ authoritative PaymentIntent lookup
→ observed state
```

The earlier DI records for:

```text
authority
ownership
lease
fencing
local dispatch admission
```

remain a provider-neutral scaffold unless the caller has separately collected real evidence for those layers.

Therefore a PASS from the adapted trace means:

> The sanitized supplied observations are internally consistent with the selected DI v0.5 post-admission interpretation.

It does not mean:

> Stripe's runtime has been independently proven exactly-once, or Stripe conforms to the entire DI stack.

## Failure handling

The capture must stop if:

- the key is missing or not a test key;
- the first request fails before a test mutation can be represented;
- same-key replay does not recover a PaymentIntent id;
- lookup is not test mode;
- the PaymentIntent is not in the expected succeeded state;
- the translated DI trace fails conformance.

Do not weaken DI invariants to force a provider observation to pass. Preserve the failed evidence and investigate the mismatch.
