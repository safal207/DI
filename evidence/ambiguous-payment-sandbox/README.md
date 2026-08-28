# Ambiguous Payment Sandbox Evidence

Status: **reproducible provider-neutral evidence pack**

This directory records one deterministic post-admission failure scenario:

```text
one logical payment operation
→ one provider effect commits
→ acknowledgement is lost
→ local commit state becomes unknown
→ authoritative lookup recovers the committed effect
→ no second mutation is authorized
```

## Result

```text
stored effects:       1
duplicate effects:    0
local state after ACK loss: unknown
authoritative state:  committed
selected next action: ACCEPT_EXISTING_EFFECT
DI v0.5 conformance:  PASS
mutation suite:       PASS (6/6 unsafe mutations rejected)
```

## Files

- [`raw-events.json`](raw-events.json) — direct event log from the deterministic stateful sandbox.
- [`summary.json`](summary.json) — compact outcome and duplicate-effect counts.
- [`trace.json`](trace.json) — the generated DI `ambiguous-commit-v0.5` trace.
- [`conformance-report.json`](conformance-report.json) — direct validator result.
- [`cli-conformance-report.json`](cli-conformance-report.json) — portable `di-conformance.py` report.
- [`mutation-report.json`](mutation-report.json) — test-the-test result.
- [`provenance.json`](provenance.json) — workflow run, artifact digest, and claim boundary.

## Reproduce

From the repository root:

```bash
python tools/ambiguous_payment_sandbox.py \
  --output-dir evidence/ambiguous-payment-sandbox \
  --check

python tools/test_ambiguous_payment_sandbox.py \
  --output evidence/ambiguous-payment-sandbox/mutation-report.json \
  --check
```

To generate a fresh temporary pack:

```bash
rm -rf generated/ambiguous-payment-sandbox
python tools/ambiguous_payment_sandbox.py \
  --output-dir generated/ambiguous-payment-sandbox
python tools/test_ambiguous_payment_sandbox.py \
  --output generated/ambiguous-payment-sandbox/mutation-report.json
```

## Test-the-test matrix

The baseline valid trace must pass. The following mutations must fail:

| Mutation | Safety property checked |
|---|---|
| effect-key drift | one logical operation keeps one stable effect identity |
| multiple committed effects | one operation cannot resolve to two committed effects |
| unknown claimed as not committed | missing evidence cannot authorize a retry |
| retry after commit | a known committed effect blocks another mutation |
| retry with a new key | retry cannot silently become a new operation |
| success without state effect | execution/commit evidence is not enough without the expected observed state |

## What this evidence proves

Within the supplied deterministic sandbox and trace:

- the mutation committed exactly one stored effect;
- the acknowledgement was intentionally lost;
- local uncertainty was preserved as `unknown`;
- authoritative lookup recovered the same effect;
- DI selected `ACCEPT_EXISTING_EFFECT`, not another mutation;
- the released v0.5 validator accepted the valid trace;
- the validator rejected every listed adversarial mutation.

## What this evidence does not prove

This pack does **not** independently prove:

- behavior of Stripe or any other external provider;
- atomicity of an external idempotency store;
- exactly-once behavior of a real distributed runtime;
- complete network evidence;
- provider endorsement or conformance.

The earlier ownership/lease/fencing section of the DI trace is a provider-neutral conformance scaffold. The direct sandbox observations in this pack focus on the post-admission seam:

```text
mutation commit
→ acknowledgement ambiguity
→ authoritative resolution
→ state effect
```

## Optional live test-mode bridge

The repository also includes:

```text
tools/capture_stripe_testmode.py
tools/stripe_capture_to_di_trace.py
```

Those tools require a caller-supplied Stripe **test** secret at runtime, refuse live keys, and never write the secret or raw idempotency key. They are not executed in CI.
