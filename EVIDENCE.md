# DI Evidence Index

## Published checkpoint

```text
Git tag / prerelease: v0.5-draft
Validated release target: a35a990c0c3d7715551b1cdaf933a58411f26c2b
Architecture freeze: active
```

## Reproducible ambiguous-payment case

Case study:

- [`docs/case-study-ambiguous-payment-recovery.md`](docs/case-study-ambiguous-payment-recovery.md)

Evidence pack:

- [`evidence/ambiguous-payment-sandbox/README.md`](evidence/ambiguous-payment-sandbox/README.md)
- [`evidence/ambiguous-payment-sandbox/raw-events.json`](evidence/ambiguous-payment-sandbox/raw-events.json)
- [`evidence/ambiguous-payment-sandbox/summary.json`](evidence/ambiguous-payment-sandbox/summary.json)
- [`evidence/ambiguous-payment-sandbox/trace.json`](evidence/ambiguous-payment-sandbox/trace.json)
- [`evidence/ambiguous-payment-sandbox/conformance-report.json`](evidence/ambiguous-payment-sandbox/conformance-report.json)
- [`evidence/ambiguous-payment-sandbox/mutation-report.json`](evidence/ambiguous-payment-sandbox/mutation-report.json)
- [`evidence/ambiguous-payment-sandbox/provenance.json`](evidence/ambiguous-payment-sandbox/provenance.json)

Result:

```text
stored effects: 1
duplicate effects: 0
lost acknowledgement: true
authoritative recovery: committed
selected next action: ACCEPT_EXISTING_EFFECT
DI conformance: PASS
unsafe mutations rejected: 6 / 6
```

## Reproduction tools

- [`tools/ambiguous_payment_sandbox.py`](tools/ambiguous_payment_sandbox.py)
- [`tools/test_ambiguous_payment_sandbox.py`](tools/test_ambiguous_payment_sandbox.py)
- [`scripts/di-conformance.py`](scripts/di-conformance.py)

## Optional external bridge

- [`docs/stripe-testmode-capture.md`](docs/stripe-testmode-capture.md)
- [`tools/capture_stripe_testmode.py`](tools/capture_stripe_testmode.py)
- [`tools/stripe_capture_to_di_trace.py`](tools/stripe_capture_to_di_trace.py)

No live Stripe capture is claimed or committed. The adapter requires a caller-supplied test secret at runtime and writes only sanitized output.

## Architecture decision

- [`docs/architecture-freeze-v0.5.md`](docs/architecture-freeze-v0.5.md)
- [`docs/v0.6-decision.md`](docs/v0.6-decision.md)

Current decision:

```text
NO-GO / DEFERRED for v0.6
```

The sandbox evidence fits v0.5 and does not expose a missing architecture seam.

## Claim boundary

DI evidence validates supplied trace semantics and named invariants. It does not independently prove external provider truthfulness, runtime atomicity, exactly-once execution, complete network evidence, or external endorsement.
