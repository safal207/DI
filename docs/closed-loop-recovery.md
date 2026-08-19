# Closed-Loop Failure Recovery

Status: Draft integration note

This note extends the Decision & Transition Integrity cycle chain with an explicit failure-and-recovery pattern.

The core rule is simple:

> Failure is a real observed state. Recovery must start from that state; it must not rewrite the failed cycle as if it had succeeded.

## Child-simple model

```text
Cycle 1: unknown payment
→ evidence
→ SUCCESS_CONFIRMED

Cycle 2: SUCCESS_CONFIRMED
→ read fulfillment
→ FULFILLMENT_CONFIRMED

Cycle 3: FULFILLMENT_CONFIRMED
→ downstream action attempt
→ evidence of failure
→ EXECUTION_FAILED_CONFIRMED

Cycle 4: EXECUTION_FAILED_CONFIRMED
→ bounded recovery action
→ recovery evidence
→ RECOVERY_CONFIRMED
```

The important part is the boundary between cycles 3 and 4:

```text
cycle 3 review.next_state
==
cycle 4 input_state
```

Recovery also carries:

```text
recovery_of_cycle_id
```

so the recovery cycle names the exact failed cycle it is trying to recover.

## Recovery invariants

For a recovery cycle:

1. `previous_cycle_id` identifies the immediately preceding cycle.
2. `recovery_of_cycle_id` must point to that same failed cycle in v0.1.
3. The previous cycle must already be reviewed.
4. The recovery `input_state` must exactly equal the previous `review.next_state`.
5. A recovery cannot be called `reviewed` without evidence.
6. Recovery must not silently rewrite prior confirmed states.

## Why this matters

A weak system may behave like this:

```text
attempt failed
→ retry happened
→ mark whole story successful
```

That destroys evidence that a failure ever occurred.

The integrity-preserving form is:

```text
attempt failed
→ failure observed and preserved
→ new recovery decision
→ recovery attempt
→ recovery observed separately
```

This gives an auditable history:

```text
success
→ later failure
→ bounded recovery
→ recovered state
```

instead of pretending the path was always successful.

## Fixtures

Valid failure + recovery chain:

```text
fixtures/valid-decision-transition-cycle-chain-recovery.json
```

Invalid recovery that claims closure without evidence:

```text
fixtures/invalid-decision-transition-cycle-chain-recovery-without-evidence.json
```

## Boundary

This is a cross-stack integration rule. It does not redefine canonical DIF, DI, DRP, or TIP semantics. Each protocol repository remains authoritative for its own records and lifecycle rules.
