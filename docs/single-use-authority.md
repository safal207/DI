# Single-Use Authority Consumption

Status: Draft integrity law

## Problem

A use-time authority check answers:

```text
Is this authority still valid now?
```

It does **not** answer:

```text
Has another worker already used this authority?
```

Without a consumption boundary, two workers can both observe the same active authority and both dispatch the same automated mutation.

```text
authority active
→ worker A checks active
→ worker B checks active
→ worker A executes
→ worker B executes
→ duplicate side effect
```

## Core law

```text
grant valid != grant unconsumed
```

For automated `SAFE_RETRY` and `ROLLBACK`, execution requires a successful single-use consumption step.

Canonical sequence:

```text
Recovery Decision
→ Use-Time Authority Receipt
→ Authority Consumption Receipt
→ Execution Receipt
→ State Effect Receipt
→ Review
```

## Binding invariant

For an automated mutation:

```text
authority_consumption_receipt.authority_receipt_id
  == use_time_authority_receipt.authority_receipt_id

authority_consumption_receipt.recovery_decision_id
  == recovery_decision.decision_id

authority_consumption_receipt.recovery_cycle_id
  == cycle.cycle_id

authority_consumption_receipt.bound_execution_mode
  == cycle.execution_mode

authority_consumption_receipt.authority_generation
  == recovery_decision.authority_generation

authority_consumption_receipt.consumption_status
  == consumed

execution_receipt.authority_consumption_receipt_id
  == authority_consumption_receipt.consumption_receipt_id
execution_receipt.use_token
  == authority_consumption_receipt.use_token
execution_receipt.dispatch_id
  == authority_consumption_receipt.dispatch_id
```

Ordering:

```text
authority.checked_at <= consumed_at <= executed_at
```

The same consumed `authority_receipt_id` or `use_token` must not be accepted twice in one evidence chain.

## Failure semantics

These are invalid:

```text
execute without consume
consume after execute
consume one dispatch but execute another
replay an already consumed authority receipt/use token
```

If consumption reports `already_consumed`, `failed`, or `unknown`, automated mutation must not proceed as if authority had been consumed successfully.

## Atomicity boundary

The receipt is evidence of consumption. A JSON document cannot itself make consumption atomic.

The strongest implementation is:

```text
atomically claim/consume use_token
+
create or claim dispatch_id
+
commit that state durably
```

inside the same consistency boundary as the side-effect dispatcher or its durable outbox.

If that is impossible, the minimum safe pattern is:

```text
durable unique consumption record
→ stable dispatch_id
→ retries recover the same dispatch
```

rather than creating a fresh dispatch from the same authority.

## Machine-readable artifacts

Schema:

```text
schemas/authority-consumption-receipt.schema.json
```

Semantic validator:

```text
scripts/validate-authority-consumption.py
```

Fixtures:

```text
fixtures/valid-authority-consumption.json
fixtures/invalid-authority-execution-without-consumption.json
fixtures/invalid-authority-consume-after-execution.json
fixtures/invalid-authority-dispatch-mismatch.json
fixtures/invalid-authority-replayed-use-token.json
```

## Child-simple version

```text
Ticket is valid
!=
ticket has not already been used
```

So before the machine acts:

```text
check ticket
→ punch ticket once
→ bind that punch to one ride
→ ride
```

A second worker holding the same already-punched ticket must not get a second ride.
