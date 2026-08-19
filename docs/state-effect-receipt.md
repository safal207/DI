# State Effect Receipt v0.1

Status: Draft integration contract

A Recovery Execution Receipt proves **what recovery action was actually observed**.
A State Effect Receipt proves **what state that action actually produced**.

These are different claims.

```text
Recovery Decision Matrix
→ declared execution mode
→ Execution Receipt: action observed
→ State Effect Receipt: resulting state observed
→ Review / Next State
```

## Why this exists

A system can execute the authorized action correctly and still fail to produce the intended outcome.

Example:

```text
Decision: SAFE_RETRY
Execution Receipt: SAFE_RETRY really happened
Expected effect: RECEIPT_DELIVERED
Observed effect: RECEIPT_NOT_DELIVERED
```

The execution is faithful, but the intended transition did not succeed.

Therefore:

> action happened ≠ intended outcome happened

## Minimal record

Schema:

```text
schemas/state-effect-receipt.schema.json
```

Fields:

```text
effect_version
effect_id
execution_receipt_id
recovery_cycle_id
expected_target_state
observed_state
effect_status
evidence_references
```

## Binding invariants

The State Effect Receipt must bind to the exact observed execution and recovery cycle:

```text
state_effect_receipt.execution_receipt_id
== execution_receipt.receipt_id

state_effect_receipt.recovery_cycle_id
== recovery_cycle.cycle_id
```

The expected effect must come from the transition contract, not be invented after execution:

```text
state_effect_receipt.expected_target_state
== recovery_cycle.envelope.tip.target_state
```

For an observed successful effect:

```text
state_effect_receipt.effect_status == observed

state_effect_receipt.observed_state
== state_effect_receipt.expected_target_state
```

and evidence must be present.

## Recovery closure rule

A cycle must not claim:

```text
review.next_state = RECOVERY_CONFIRMED
```

merely because the recovery action executed.

`RECOVERY_CONFIRMED` requires both:

```text
Execution Receipt
→ execution_status = observed

State Effect Receipt
→ effect_status = observed
→ observed_state == TIP target_state
→ evidence_references is not empty
```

If execution occurs but the target state is not observed, the failed/partial outcome must remain visible. The system must not rewrite it into success.

## Example

```text
Failure state
EXECUTION_FAILED_CONFIRMED

↓ Recovery Decision Matrix
SAFE_RETRY

↓ Execution Receipt
SAFE_RETRY observed

↓ State Effect Receipt
expected: RECEIPT_DELIVERED
observed: RECEIPT_DELIVERED

↓ Review
RECOVERY_CONFIRMED
```

Invalid:

```text
SAFE_RETRY observed
↓
expected: RECEIPT_DELIVERED
observed: RECEIPT_NOT_DELIVERED
↓
RECOVERY_CONFIRMED   ❌
```

## Boundary

The State Effect Receipt does not prove causality beyond the observed action/effect relationship and does not redefine TIP semantics.

It records an evidence-backed state observation at the execution boundary.

```text
Execution Receipt ≠ State Effect Receipt
State Effect Receipt ≠ causal proof
Observed action ≠ successful outcome
```

The purpose is narrower:

> do not let a system claim that a recovery succeeded merely because the recovery action ran.
