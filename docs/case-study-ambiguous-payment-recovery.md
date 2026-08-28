# Recovering an Ambiguous Payment Without Creating a Duplicate Effect

Status: **reproducible provider-neutral case study**

## The burning question

> After a payment request times out, how can an autonomous agent prove that the first operation did not already commit before it acts again?

The dangerous shortcut is:

```text
no acknowledgement observed
→ assume failure
→ create another payment
```

That shortcut can turn one intended purchase into two financial effects.

DI v0.5 tests a stricter chain:

```text
one logical operation
→ one stable effect identity
→ transport ambiguity remains unknown
→ authoritative commit resolution
→ next action compatible with the resolved state
→ observed state effect
```

## Experiment

The repository contains a deterministic stateful payment sandbox. It accepts one logical operation and one stable effect key.

The test performs this sequence:

```text
1. submit one payment mutation
2. commit exactly one provider effect
3. intentionally lose the acknowledgement
4. preserve local commit state as unknown
5. query the authoritative provider state
6. recover the same committed effect
7. select ACCEPT_EXISTING_EFFECT
8. do not create another mutation
```

The sandbox is intentionally provider-neutral. It uses no account, network, credential, or external API.

## Direct observations

The raw event log contains three events:

```text
mutation_committed
acknowledgement_lost
authoritative_lookup → committed
```

Final provider state:

```text
stored_effect_count   = 1
duplicate_effect_count = 0
```

The recovery decision is:

```text
resolution_status    = committed
selected_next_action = ACCEPT_EXISTING_EFFECT
```

## DI mapping

The observed sandbox events are translated into the released `ambiguous-commit-v0.5` trace shape.

The post-admission section preserves:

```text
logical_operation_id
→ operation.sandbox-payment.001

effect_key
→ effect-key.sandbox-payment.001

initial transport observation
→ unknown

authoritative observation
→ committed / sandbox-effect.payment.001

resolution
→ ACCEPT_EXISTING_EFFECT

observed target state
→ PAYMENT_COMMITTED
```

The preceding authority, ownership, lease, fencing, and dispatch records are a provider-neutral DI conformance scaffold. They are not observations about an external payment provider.

## Result

The generated trace passes the canonical profile:

```text
profile: ambiguous-commit-v0.5
status:  PASS
errors:  []
```

Evidence pack:

```text
evidence/ambiguous-payment-sandbox/
├── README.md
├── raw-events.json
├── summary.json
├── trace.json
├── conformance-report.json
├── cli-conformance-report.json
├── mutation-report.json
└── provenance.json
```

## The test that checks the test

A validator that accepts its own happy-path fixture is not enough.

The sandbox trace is mutated in six unsafe ways:

| Mutation | Expected result | Why |
|---|---|---|
| effect-key drift | FAIL | a retry cannot silently become a new effect identity |
| multiple committed effects | FAIL | one logical operation cannot resolve to two committed effects |
| unknown claimed as not committed | FAIL | absence of authoritative evidence cannot authorize retry |
| retry after committed | FAIL | a known effect blocks a new mutation |
| retry with a new key | FAIL | retry must preserve the original effect identity |
| success without state effect | FAIL | commit/execution evidence is not proof of the intended observed outcome |

Result:

```text
baseline valid trace:       PASS
unsafe mutations rejected:  6 / 6
mutation suite:             PASS
```

## Reproduce

```bash
python tools/ambiguous_payment_sandbox.py \
  --output-dir evidence/ambiguous-payment-sandbox \
  --check

python tools/test_ambiguous_payment_sandbox.py \
  --output evidence/ambiguous-payment-sandbox/mutation-report.json \
  --check

python scripts/di-conformance.py \
  evidence/ambiguous-payment-sandbox/trace.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

CI runs the same generation, mutation suite, reproducibility checks, and CLI profile. It also uploads a workflow artifact for independent inspection.

## What this case demonstrates

Within the supplied deterministic system:

- a committed mutation can coexist with a lost response;
- transport ambiguity is preserved as `unknown` rather than guessed as failure;
- authoritative lookup recovers the existing effect;
- the agent's next action is bounded by evidence;
- one intended operation remains one stored effect;
- the validator rejects common duplicate-effect shortcuts.

## What this case does not demonstrate

This case does not independently prove:

- Stripe or another external provider behaves this way;
- an external idempotency store is atomic;
- a distributed transaction is exactly-once;
- all relevant network evidence is complete;
- DI is a certification or security audit;
- an external company uses or endorses DI, DIF, DRP, or TIP.

## Optional Stripe test-mode bridge

Two optional tools are included:

```text
tools/capture_stripe_testmode.py
tools/stripe_capture_to_di_trace.py
```

The capture tool:

- requires a caller-supplied `sk_test_...` key at runtime;
- refuses non-test keys;
- intentionally discards the first response body;
- replays the same request with the same idempotency key;
- performs an explicit PaymentIntent lookup;
- writes a sanitized capture without the secret or raw idempotency key.

The translation tool maps only the post-admission Stripe test-mode observations into DI. The earlier DI dispatch/fencing section remains a provider-neutral scaffold and must not be attributed to Stripe.

No live Stripe call is claimed by this case study.

## Product meaning

The case can be applied to more than payments:

```text
wallet transfer
order creation
refund
subscription mutation
agent tool call
smart-contract relay
job dispatch
account update
```

The common question is:

> When the caller loses the answer, can the system recover the prior effect identity and observed state before authorizing another irreversible action?

That is the practical wedge for DI conformance work.
