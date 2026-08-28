# Recovering an Ambiguous Payment Without Creating a Duplicate Effect

Status: **executable deterministic sandbox case**

This case demonstrates the DI `ambiguous-commit-v0.5` profile against a small
provider-neutral payment runtime.

It is not a live Stripe run, not a production-provider integration, and not a
claim that an external system conforms to DI. The purpose is narrower: make the
failure and the evidence chain reproducible without credentials, network access,
or hidden infrastructure.

## The question

A payment worker sends a mutation. The side effect commits, but the success
response is lost.

```text
payment mutation sent
→ effect commits
→ acknowledgement disappears
→ local state becomes UNKNOWN
```

What may the agent do next?

The unsafe shortcut is:

```text
"I did not receive success"
→ "the payment failed"
→ create a new payment identity
```

That can create a duplicate financial effect.

The v0.5 rule is:

```text
transport outcome != commit outcome
unknown commit != not committed
```

## Executable scenario

The sandbox in [`sandbox/ambiguous_payment_sandbox.py`](../sandbox/ambiguous_payment_sandbox.py)
models six observable steps:

```text
1. worker A presents fencing token 101
   → stale attempt rejected

2. worker B presents fencing token 102
   → current attempt admitted

3. worker B submits logical operation O with effect key K
   → exactly one payment effect commits

4. acknowledgement is deliberately lost after commit
   → caller sees UNKNOWN

5. authoritative lookup by K finds the committed effect
   → commit state becomes committed

6. same operation is replayed with the same K and identical parameters
   → the existing effect is returned
   → committed effect count remains 1
```

The sandbox also rejects reuse of the same effect key with different payment
parameters.

## Canonical evidence chain

The runtime is bound to the repository's anonymous public trace:

```text
fixtures/valid-ambiguous-commit-recovery-v0.5.json
```

The trace preserves:

```text
logical_operation_id
→ effect_key
→ accepted dispatch attempt
→ execution receipt
→ initial non-authoritative UNKNOWN observation
→ authoritative committed observation
→ one resolved effect identity
→ ACCEPT_EXISTING_EFFECT
→ matching observed state effect
```

The executable sandbox fails if its observed operation identity, effect key, or
committed effect identity drifts from that trace.

## Result

The committed machine-readable report is:

```text
artifacts/sandbox/conformance-report.json
```

Expected result:

```json
{
  "profile": "ambiguous-commit-v0.5",
  "status": "PASS",
  "error_count": 0,
  "sandbox": {
    "committed_effect_count": 1,
    "same_key_replay_reused_effect": true,
    "stale_attempt_rejected": true,
    "current_attempt_accepted": true
  }
}
```

The full report also records all mutation checks and the claim boundary.

## Testing the test

A positive trace is not enough. A validator that always says `PASS` is merely a
very supportive friend 😄

[`scripts/validate-sandbox-case.py`](../scripts/validate-sandbox-case.py) runs the
sandbox and then corrupts the resulting trace in six ways:

| Mutation | Required result |
|---|---|
| Change the effect key during recovery | `FAIL` |
| Resolve one logical operation to two committed effects | `FAIL` |
| Treat non-authoritative `UNKNOWN` as `not_committed` | `FAIL` |
| Retry after a committed effect is already known | `FAIL` |
| Retry with a new effect key | `FAIL` |
| Claim success without the matching state effect | `FAIL` |

The test passes only when:

```text
canonical sandbox trace → PASS
AND
every corrupted trace → FAIL for the expected reason
```

It also verifies that:

- a stale fencing epoch is rejected;
- the current epoch is admitted;
- one lost acknowledgement still produces only one committed effect;
- same-key replay returns that existing effect;
- same-key parameter drift is rejected;
- the committed JSON report matches the result observed during CI.

## Reproduce locally

Run the sandbox and print its trace:

```bash
python sandbox/ambiguous_payment_sandbox.py --pretty
```

Write the trace to a temporary file:

```bash
python sandbox/ambiguous_payment_sandbox.py \
  --output /tmp/ambiguous-payment-trace.json
```

Validate the executable case and all negative mutations:

```bash
python scripts/validate-sandbox-case.py
```

Run the public v0.5 conformance interface directly:

```bash
python scripts/di-conformance.py \
  fixtures/valid-ambiguous-commit-recovery-v0.5.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

CI executes the same checks on every pull request and push to `main`.

## Evidence classification

This case deliberately separates four kinds of statement:

| Class | What exists here |
|---|---|
| Sandbox runtime fact | one in-memory effect is committed and recovered by lookup |
| DI inference | committed state permits `ACCEPT_EXISTING_EFFECT`, not another mutation |
| Conformance evidence | the generated chain satisfies `ambiguous-commit-v0.5` |
| External-provider fact | none; no provider account or secret was used |

The evidence references inside the canonical trace are anonymous identifiers.
They make relationships inspectable; they are not cryptographic proof that a
third-party provider emitted those records.

## What this case proves

Within the deterministic runtime and supplied evidence model, it demonstrates:

```text
one intended operation
→ one stable effect key
→ one committed effect
→ lost acknowledgement
→ authoritative recovery
→ no duplicate effect
```

It also demonstrates that the validator rejects the six targeted integrity
breaks above.

## What this case does not prove

This case does not independently prove that:

- an external payment API implements idempotency atomically;
- an external lookup is truthful or complete;
- a database transaction is exactly-once;
- a distributed lease service enforces fencing at the real mutation boundary;
- a network trace contains every relevant event;
- Stripe, Crossmint, Valta, or another company uses or endorses DI;
- the same outcome automatically holds in production.

DI validates a supplied evidence chain. Runtime and provider guarantees must be
established separately.

## Relation to DIF, DI, DRP, and TIP

The scenario can be read through the full stack without collapsing the project
boundaries:

```text
DIF
→ confirmed intent: complete one intended purchase, not two

DI
→ blind new mutation is blocked while prior commit state is unknown

DRP
→ commit the recovery decision and its rationale

TIP
→ UNKNOWN → authoritative recovery → COMMITTED

Review
→ evidence supports ACCEPT_EXISTING_EFFECT
```

The external payment runtime remains a validation case, not a member of the
DIF/DI/DRP/TIP stack.

## Next external-evidence step

The same trace adapter can later be fed observable events from a provider
sandbox or test-mode account. That stronger test requires credentials supplied
through an approved secret boundary; credentials must never be committed to the
repository.

Until such a run is captured, the correct public claim is:

> DI v0.5 has a reproducible provider-neutral sandbox showing how an ambiguous
> committed payment can be recovered without authorizing a duplicate effect.
