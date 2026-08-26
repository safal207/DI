# Ambiguous Commit Integrity v0.5

Status: Draft cross-stack integrity layer

## Problem

v0.4 can prove that only the current fenced execution epoch was admitted.

That still does not answer the next question:

> Did the admitted mutation actually commit?

A dangerous sequence is:

```text
current worker admitted
→ mutation sent
→ side effect commits
→ response is lost
→ local state says UNKNOWN
→ another worker retries as if the first mutation failed
```

A transport failure is not proof of a failed commit.

## Core laws

```text
transport outcome != commit outcome
```

```text
unknown commit != not committed
```

```text
same logical operation
→ same logical_operation_id
→ same effect_key
```

```text
committed logical operation
→ one stable committed effect identity
→ no new mutation identity
```

## Canonical flow

```text
v0.4 accepted dispatch attempt
↓
logical operation + effect key
↓
mutation response is lost
↓
commit_status = unknown
↓
authoritative lookup / same-key replay / provider event
↓
commit state resolved
↓
committed      → accept existing effect or stop
not committed  → retry only with the same effect key or stop
still unknown  → stop or human escalation
↓
state-effect evidence
```

## Stable logical operation identity

Machine-readable schema:

```text
schemas/logical-operation.schema.json
```

The identity record binds:

```text
logical_operation_id
effect_key
intended_effect
identity_contract
evidence_references
```

`logical_operation_id` represents the user's or system's intended mutation.

`effect_key` is the stable identity carried to the side-effect boundary. It may correspond to a provider idempotency key, a database uniqueness key, a command id, or another documented same-operation primitive.

Changing the key after an ambiguous result is not a retry. It is a new mutation identity.

## Commit outcome receipts

Machine-readable schema:

```text
schemas/commit-outcome-receipt.schema.json
```

A receipt records one observation of commit state:

```text
logical_operation_id
effect_key
observation_method
commit_status
authoritative
committed_effect_id
evidence_references
```

Supported observation methods include:

```text
mutation_response
same_key_replay
authoritative_lookup
provider_event
operator_confirmation
```

A non-authoritative transport observation may honestly say `unknown`.

An authoritative observation may say `committed` or `not_committed`, but not `unknown`.

A committed observation must name a stable `committed_effect_id`.

## Commit resolution

Machine-readable schema:

```text
schemas/commit-resolution.schema.json
```

The final resolution maps evidence to the next admissible action.

| Resolved state | Allowed next action |
|---|---|
| `committed` | `ACCEPT_EXISTING_EFFECT` or `STOP` |
| `not_committed` | `RETRY_SAME_EFFECT_KEY` or `STOP` |
| `still_unknown` | `STOP` or `HUMAN_ESCALATION` |

For `RETRY_SAME_EFFECT_KEY`:

```text
next_effect_key == original effect_key
```

A committed result cannot mint another mutation key.

## Canonical example

```text
worker A / token 101 → stale → rejected
worker B / token 102 → accepted
worker B sends mutation
response lost
commit state unknown
provider lookup finds effect payment-001 committed
resolution = ACCEPT_EXISTING_EFFECT
state effect = PAYMENT_COMMITTED
```

Reference trace:

```text
fixtures/valid-ambiguous-commit-recovery-v0.5.json
```

Validator:

```text
scripts/validate-ambiguous-commit.py
```

Conformance profile:

```text
ambiguous-commit-v0.5
```

## What v0.5 catches

```text
effect-key drift after timeout
unknown treated as not_committed without authoritative evidence
one logical operation resolving to multiple committed effect ids
retry authorized after a committed effect is already known
retry using a new effect key
success claimed without matching state-effect evidence
commit observations recorded before execution
commit-resolution history regressing from committed to not_committed
```

## Runtime boundary

v0.5 validates evidence semantics. It is not an exactly-once runtime implementation.

A production system still needs a mutation boundary that can durably enforce the chosen identity contract, for example:

```text
receive logical_operation_id + effect_key
↓
atomically find-or-create the effect
↓
same key + same parameters → return the existing effect
same key + different parameters → reject
new key → new operation only when separately authorized
```

An authoritative lookup must itself come from a trustworthy system of record.

The validator cannot prove that an external provider, database, queue, or ledger implemented these guarantees truthfully or atomically.

## Relation to earlier layers

```text
v0.2
Decision / path / authority / execution / effect integrity

v0.3
+ multi-agent ownership continuity

v0.4
+ lease expiry and fencing against stale executors

v0.5
+ ambiguous commit resolution and stable effect identity
```

## Summary

v0.5 closes the lost-acknowledgement gap:

> Not seeing a successful response does not authorize a new mutation. The system must preserve one logical operation identity, resolve commit state from evidence, and treat a known committed effect as the existing outcome rather than permission to act again.
