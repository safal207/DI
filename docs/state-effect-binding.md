# Execution → State Effect Binding v0.1

Status: Draft integration invariant

An action being observed is not the same as its intended outcome being observed.

This document adds one narrow post-execution check to the existing recovery chain:

```text
Recovery Decision
→ declared execution mode
→ Execution Receipt
→ State Effect Receipt
→ Review / Next State
```

It is not a new protocol and does not redefine DIF, DI, DRP, or TIP.

## Problem

A system may faithfully execute the selected recovery action and still fail to produce the intended state transition.

Example:

```text
selected action: SAFE_RETRY
execution observed: SAFE_RETRY
expected target: RECEIPT_DELIVERED
observed state: RECEIPT_NOT_DELIVERED
```

The execution is real, but the recovery outcome is not successful.

Therefore:

> action happened ≠ intended effect happened

## State Effect Receipt

A State Effect Receipt binds an observed execution to its observed state result.

Minimum fields:

```text
effect_id
execution_receipt_id
recovery_cycle_id
expected_target_state
observed_state
effect_status
observed_at
state_generation
evidence_references
```

Canonical schema:

```text
schemas/state-effect-receipt.schema.json
```

## Binding invariants

```text
state_effect_receipt.execution_receipt_id
== execution_receipt.receipt_id

state_effect_receipt.recovery_cycle_id
== recovery_cycle.cycle_id

state_effect_receipt.expected_target_state
== recovery_cycle.envelope.tip.target_state
```

When `effect_status = observed`:

```text
state_effect_receipt.observed_state
== recovery_cycle.envelope.tip.target_state
```

An observed state effect also requires an observed Execution Receipt and evidence references.

## Evidence freshness

Correct evidence can still be stale.

A Review that closes recovery declares which state generation it is accepting and how old evidence is allowed to be:

```text
review.accepted_state_generation
review.reviewed_at
review.max_evidence_age_seconds
```

The State Effect Receipt records:

```text
state_effect_receipt.state_generation
state_effect_receipt.observed_at
```

For `RECOVERY_CONFIRMED`:

```text
state_effect_receipt.state_generation
== review.accepted_state_generation

state_effect_receipt.observed_at
<= review.reviewed_at

review.reviewed_at - state_effect_receipt.observed_at
<= review.max_evidence_age_seconds
```

This rejects two different stale-evidence failures:

```text
old generation, recent timestamp
→ reject

correct generation, expired timestamp
→ reject
```

The freshness window is chosen by the consuming Review. The evidence producer cannot declare its own evidence fresh.

## Recovery confirmation rule

`RECOVERY_CONFIRMED` is only valid when execution, state effect, and freshness are all established:

```text
Execution Receipt.execution_status == observed
AND
State Effect Receipt.effect_status == observed
AND
State Effect Receipt.observed_state == TIP.target_state
AND
State Effect Receipt.state_generation == Review.accepted_state_generation
AND
State Effect Receipt is inside Review.max_evidence_age_seconds
```

So this is invalid:

```text
execution: observed
state effect: target matched once
but evidence belongs to an older generation or expired freshness window
review.next_state: RECOVERY_CONFIRMED
```

## Why this matters

This closes two distinct failure surfaces:

```text
Decision was correct
→ execution matched the decision
→ action really happened
→ BUT expected effect did not happen
```

and:

```text
Expected effect was observed earlier
→ world changed
→ old evidence reused
→ false claim about current state
```

The system must preserve those differences instead of collapsing them into success.

## End-to-end integrity line

```text
Intent
→ Feasibility
→ Decision
→ Transition
→ Recovery Decision
→ Declared Execution
→ Observed Execution
→ Observed State Effect
→ Freshness / Generation Check
→ Review
→ Next State
```

Each arrow is an inspectable handoff, not an assumption.
