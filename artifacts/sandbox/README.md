# Deterministic Ambiguous-Payment Sandbox Evidence

This directory contains the durable machine-readable result for the executable
provider-neutral payment-recovery case.

## Evidence package

- Canonical trace:
  [`../../fixtures/valid-ambiguous-commit-recovery-v0.5.json`](../../fixtures/valid-ambiguous-commit-recovery-v0.5.json)
- Conformance report:
  [`conformance-report.json`](conformance-report.json)
- Executable runtime:
  [`../../sandbox/ambiguous_payment_sandbox.py`](../../sandbox/ambiguous_payment_sandbox.py)
- Test-the-test validator:
  [`../../scripts/validate-sandbox-case.py`](../../scripts/validate-sandbox-case.py)
- Case study:
  [`../../docs/case-study-deterministic-ambiguous-payment-recovery.md`](../../docs/case-study-deterministic-ambiguous-payment-recovery.md)
- Commercial pilot scope:
  [`../../docs/verification-pilot-offer.md`](../../docs/verification-pilot-offer.md)

## Reproduce

```bash
python sandbox/ambiguous_payment_sandbox.py --pretty
python scripts/validate-sandbox-case.py
python scripts/di-conformance.py \
  fixtures/valid-ambiguous-commit-recovery-v0.5.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

## Claim boundary

This package proves behavior inside a deterministic local sandbox and validates
the supplied evidence chain. It does not prove that an external payment
provider, database, lease service, or exactly-once runtime behaves the same way.
