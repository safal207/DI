# Recovery Decision → Execution Binding v0.1

Status: Integration guard

This note defines one narrow invariant across the existing closed-loop recovery artifacts:

```text
observed failure
→ Recovery Decision Matrix
→ selected_action
→ next recovery cycle execution_mode
→ reviewed result
```

It is **not a new protocol**. DIF, DI, DRP, and TIP remain authoritative for their own semantics. The Recovery Decision Matrix remains a bounded recovery-choice guard. This binding only prevents the chosen recovery action from being silently changed at execution time.

## Core invariant

```text
recovery_decision.selected_action
==
recovery_cycle.execution_mode
```

Example:

```text
Matrix: SAFE_RETRY
Cycle:  SAFE_RETRY
→ valid binding
```

Invalid:

```text
Matrix: SAFE_RETRY
Cycle:  ROLLBACK
→ reject
```

The system must not authorize one recovery path and execute another.

## Provenance invariant

A recovery cycle must identify the exact failed cycle it is recovering:

```text
recovery_cycle.recovery_of_cycle_id
== recovery_decision.source_cycle_id
== previous_cycle.cycle_id
```

The failed state must also carry forward exactly:

```text
previous_cycle.review.next_state
== recovery_cycle.input_state
== recovery_decision.failure_state
```

This prevents recovery from being attached to a different failure or from starting from an invented state.

## STOP semantics

`STOP` is intentionally different from the active recovery modes.

```text
selected_action = STOP
→ preserve failed state
→ do not create an automated recovery execution cycle
```

Therefore an active recovery cycle whose embedded matrix selected `STOP` is invalid.

## Active recovery modes

The current matrix vocabulary is:

```text
SAFE_RETRY
ROLLBACK
STOP
HUMAN_ESCALATION
```

For active recovery cycles, `execution_mode` records what is actually being executed or initiated.

The binding does not prove that the action succeeded. Success or failure still belongs to TIP review and evidence-backed next-state observation.

## Example flow

```text
Cycle 3
EXECUTION_FAILED_CONFIRMED
        ↓
Recovery Decision Matrix
selected_action = SAFE_RETRY
        ↓ exact binding
Cycle 4
execution_mode = SAFE_RETRY
recovery_of_cycle_id = Cycle 3
        ↓
TIP Review + evidence
        ↓
RECOVERY_CONFIRMED
```

## Negative cases

The repository includes two explicit binding failures:

1. matrix selects `SAFE_RETRY`, but the cycle declares `ROLLBACK`;
2. matrix selects `STOP`, but an automated recovery cycle is created anyway.

Both must fail binding validation.

## Validation

Run:

```bash
python scripts/validate-fixtures.py
python scripts/validate-recovery-binding.py
```

CI executes both validators.

The binding validator checks:

```text
source failure identity
→ observed failure state continuity
→ matrix recovery decision
→ exact execution_mode match
→ STOP non-execution rule
```

## Principle

> A recovery decision is not trustworthy if execution may silently substitute a different recovery action.
