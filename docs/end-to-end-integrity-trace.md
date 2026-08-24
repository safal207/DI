# End-to-End Integrity Trace v0.2

Status: Draft conformance contract

## Purpose

Individual schemas can be correct while the complete system is still wrong.

Example:

```text
DI valid ✅
DRP valid ✅
TIP valid ✅
Authority valid ✅
Execution receipt valid ✅
```

but if those artifacts refer to different path IDs, generations, dispatches, or states, the overall claim is false.

This contract therefore validates the **joins between layers**, not only each object in isolation.

## Canonical trace

```text
Confirmed Intent
↓
DI Feasible Paths
↓
Strategy Comparison
↓
DRP Selected Path
↓
Path Revalidation
↓
TIP Transition
↓
Recovery Decision
↓
Use-Time Authority
↓
Single-Use Authority Consumption
↓
Execution Receipt
↓
State Effect Receipt
↓
Fresh Review
↓
Proven Next State
```

The canonical fixture is:

```text
fixtures/valid-end-to-end-integrity-v0.2.json
```

The semantic validator is:

```text
scripts/validate-end-to-end-integrity.py
```

## Identity spine

The selected path must preserve identity across the decision/transition seam:

```text
DI.feasible_paths[].path_id
→ Strategy.candidate_path_ids
→ DRP.selected_path_id
= PathRevalidation.selected_path_id
= TIP.selected_path_id
```

The failed state must also preserve identity:

```text
trace.input_state
= recovery_decision.failure_state
= TIP.starting_state
```

And the recovery source must remain exact:

```text
trace.recovery_of_cycle_id
= recovery_decision.source_cycle_id
= execution_receipt.source_cycle_id
```

## Automated mutation spine

For `SAFE_RETRY` and `ROLLBACK`:

```text
recovery_decision.selected_action
= trace.execution_mode
= authority.bound_execution_mode
= consumption.bound_execution_mode
= execution.declared_execution_mode
```

For observed execution:

```text
execution.observed_execution_mode
= trace.execution_mode
```

Authority generation cannot drift:

```text
recovery_decision.authority_generation
= authority.authority_generation
= consumption.authority_generation
= execution.authority_generation_at_execution
```

## Single-use dispatch spine

Execution must be the exact dispatch claimed during authority consumption:

```text
consumption.consumption_receipt_id
= execution.authority_consumption_receipt_id
```

```text
consumption.use_token
= execution.use_token
```

```text
consumption.dispatch_id
= execution.dispatch_id
```

A valid permission is not enough. The permission must be durably consumed before the mutation occurs.

## Outcome spine

Observed execution is not proof of the intended state change.

Therefore:

```text
execution.receipt_id
= state_effect.execution_receipt_id
```

```text
TIP.target_state
= state_effect.expected_target_state
= state_effect.observed_state
```

when the effect status is `observed`.

## Freshness spine

For a reviewed recovery outcome:

```text
state_effect.state_generation
= review.accepted_state_generation
```

and:

```text
state_effect.observed_at
<= review.reviewed_at
```

with:

```text
review.reviewed_at - state_effect.observed_at
<= review.max_evidence_age_seconds
```

`RECOVERY_CONFIRMED` is valid only when execution was observed, the intended target state was observed, the state generation matches, evidence is fresh, the committed path was still valid, and single-use authority was consumed.

## Temporal spine

The canonical success trace is monotonic:

```text
Path Revalidation
<= Use-Time Authority Check
<= Authority Consumption
<= Execution
<= State Observation
<= Review
```

Authority consumption and execution must also remain inside the use-time authority binding window.

## Mutation tests

The validator does not only accept the known-good fixture. It deep-copies that trace and deliberately corrupts one seam at a time.

It must reject at least these cases:

```text
DIF / DI intent mismatch
DRP chooses a path Strategy did not evaluate
path becomes invalid but TIP continues
TIP silently substitutes another path
recovery action differs from execution mode
authority generation changes before use
execution dispatch differs from consumed dispatch
execution occurs before authority consumption
observed state differs from TIP target
review accepts a different state generation
review relies on stale state evidence
```

If any mutation passes, the validator exits non-zero.

## What this proves

The trace can demonstrate that the recorded artifacts form one coherent causal chain.

It does **not** prove that a runtime database transaction was actually atomic, that external evidence sources are truthful, or that an external provider behaved correctly beyond the supplied evidence.

Those remain implementation/evidence boundary assumptions.

## Core law

```text
valid pieces
≠
valid whole
```

The whole is valid only when the joins are also valid.
