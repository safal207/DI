# Single-Use Authority Consumption Binding

Status: Draft integration contract

## Problem

Use-time authority answers:

```text
Is this authority valid now?
```

It does **not** answer:

```text
Has another worker already used this mutation right?
```

Without a consumption boundary, two workers can race:

```text
authority = active
        ↓
worker A checks active ─┐
worker B checks active ─┤
                       ↓
                 both dispatch
```

Every local check can be truthful while the global outcome is still a duplicate side effect.

The missing distinction is:

```text
grant valid
≠
grant unconsumed
```

## Canonical automated mutation line

For `SAFE_RETRY` and `ROLLBACK`:

```text
Recovery Decision
→ Use-Time Authority Receipt
→ Authority Consumption Receipt
→ Execution Receipt
→ State Effect Receipt
→ Review
```

`HUMAN_ESCALATION` is intentionally outside this automated mutation consumption gate.

## Single-use scope

A successful automated mutation consumes this logical scope once:

```text
(
  authority_id,
  authority_generation,
  recovery_decision_id,
  bound_execution_mode
)
```

The scope is stronger than `use_token` alone.

Why?

```text
worker A → token A
worker B → token B
```

Different tokens must not manufacture two permissions from one recovery decision.

Therefore:

```text
one recovery decision authority scope
→ at most one consumption_status = consumed
```

The validator also requires each successfully consumed `use_token` and authority receipt to be single-use in the inspected chain.

## Binding invariants

For automated mutation:

```text
authority_consumption_receipt.authority_receipt_id
== use_time_authority_receipt.authority_receipt_id
```

```text
authority_consumption_receipt.authority_id
== recovery_decision.authority_id
== use_time_authority_receipt.authority_id
```

```text
authority_consumption_receipt.authority_generation
== recovery_decision.authority_generation
== use_time_authority_receipt.authority_generation
== execution_receipt.authority_generation_at_execution
```

```text
authority_consumption_receipt.recovery_decision_id
== recovery_decision.decision_id
== execution_receipt.recovery_decision_id
```

```text
authority_consumption_receipt.recovery_cycle_id
== cycle.cycle_id
== execution_receipt.recovery_cycle_id
```

```text
authority_consumption_receipt.bound_execution_mode
== cycle.execution_mode
== execution_receipt.declared_execution_mode
```

And execution must bind to the exact consumed dispatch claim:

```text
execution_receipt.authority_consumption_receipt_id
== authority_consumption_receipt.consumption_receipt_id
```

```text
execution_receipt.use_token
== authority_consumption_receipt.use_token
```

```text
execution_receipt.dispatch_id
== authority_consumption_receipt.dispatch_id
```

## Ordering

The temporal order is:

```text
authority.checked_at
<= consumption.consumed_at
<= execution.executed_at
```

Consumption and execution must also remain inside the use-time authority binding window.

## Replay behavior

If consumption reports that the single-use scope was already consumed, the correct behavior is **not** to create another dispatch.

Conceptually:

```text
already consumed
↓
NO new mutation
↓
recover / inspect the existing dispatch
```

This keeps retry semantics separate from duplicate side effects.

## Atomicity requirement

A JSON receipt is evidence of a claim. It is **not** atomicity itself.

A production implementation should enforce the single-use scope at the side-effect boundary, preferably with one transactional operation:

```text
claim single-use scope
+
create or claim dispatch_id
```

If one transaction is impossible, the safer fallback is:

```text
1. durably consume the scope first
2. persist a unique dispatch_id
3. dispatch
4. retries recover the same dispatch_id instead of creating another one
```

A runtime that merely writes a consumption receipt after dispatch has not solved the race.

## Machine-readable artifacts

Schema:

```text
schemas/authority-consumption-receipt.schema.json
```

Semantic validator:

```text
scripts/validate-authority-consumption.py
```

Valid fixture:

```text
fixtures/valid-authority-consumption.json
```

Negative fixtures:

```text
fixtures/invalid-authority-execution-without-consumption.json
fixtures/invalid-authority-consume-after-execution.json
fixtures/invalid-authority-dispatch-mismatch.json
fixtures/invalid-authority-replayed-use-token.json
fixtures/invalid-authority-double-consume-same-decision.json
```

## Core law

```text
permission valid now
≠
permission available for another use
```

For automated mutation, validity must be followed by durable single-use consumption before execution.
