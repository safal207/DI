# Recovery Execution Receipt v0.1

Status: Draft integration evidence contract

The Execution Receipt closes the final gap between a recovery decision and what was actually observed at execution time.

It is **not a new protocol** and does not replace DIF, DI, DRP, TIP, or the Recovery Decision Matrix.

## Core invariant

```text
Recovery Decision Matrix
selected_action
        ↓
Recovery Cycle
execution_mode
        ↓
Execution Receipt
observed_execution_mode
```

For an observed automated recovery action:

```text
selected_action
== execution_mode
== declared_execution_mode
== observed_execution_mode
```

A system must not claim execution fidelity merely because the planned action and the declared execution mode match.

The receipt requires evidence of what was actually observed.

## Why this exists

Without a receipt, this invalid path can look internally consistent:

```text
Matrix: ROLLBACK
Cycle:  ROLLBACK
Actual executor operation: SAFE_RETRY
```

The first two records agree, but the side effect does not.

The Execution Receipt exposes that difference.

## Minimal receipt

```json
{
  "receipt_version": "0.1",
  "receipt_id": "receipt.recovery.004",
  "recovery_decision_id": "recovery.safe-retry.004",
  "source_cycle_id": "dti.failed.cycle.003",
  "recovery_cycle_id": "dti.recovery.cycle.004",
  "declared_execution_mode": "SAFE_RETRY",
  "observed_execution_mode": "SAFE_RETRY",
  "execution_status": "observed",
  "evidence_references": [
    "evidence://executor/attempt-id",
    "evidence://transport/http-200"
  ]
}
```

## Binding rules

The validator requires:

```text
receipt.recovery_decision_id
== recovery_decision.decision_id

receipt.source_cycle_id
== recovery_of_cycle_id

receipt.recovery_cycle_id
== cycle_id

receipt.declared_execution_mode
== cycle.execution_mode
== recovery_decision.selected_action
```

When `execution_status = observed`:

```text
receipt.observed_execution_mode
== receipt.declared_execution_mode
```

and at least one evidence reference is required.

A recovery cycle that reaches `RECOVERY_CONFIRMED` must carry an observed Execution Receipt.

## Unknown or failed execution

The receipt may preserve uncertainty instead of inventing success:

```text
execution_status = failed | unknown
observed_execution_mode = declared mode | UNKNOWN
```

This is preferable to claiming a successful recovery when the real side effect cannot be established.

## STOP

`STOP` remains terminal for automated recovery.

No active recovery cycle should be created after a Matrix decision of `STOP`, so there is no automated execution receipt for a forbidden continuation.

## Evidence boundary

An evidence reference is a pointer to inspectable execution evidence, such as:

- executor operation id;
- transport response;
- provider operation id;
- ledger/state diff;
- rollback transaction id;
- human escalation record.

The v0.1 receipt does not define a universal evidence storage format. It only requires that the claim of observed execution is grounded by references.

## Files

Schema:

```text
schemas/execution-receipt.schema.json
```

Validation:

```bash
python scripts/validate-recovery-binding.py
```

Negative fixtures include:

- declared `SAFE_RETRY` but observed `ROLLBACK`;
- `execution_status = observed` without evidence.

## Principle

> A recovery plan is not proof of a recovery action. A declared action is not proof of a side effect. Preserve evidence of what actually happened.
