# Recovery Decision Matrix v0.1

Status: Draft integration guard

The Recovery Decision Matrix is **not a new protocol**. It is a narrow recovery guard used after a failure has already been observed and preserved by the existing decision-and-transition integrity stack.

It answers one bounded question:

> Given this confirmed failure state and the evidence we currently have, which recovery path is admissible now?

Allowed outcomes:

```text
SAFE_RETRY
ROLLBACK
STOP
HUMAN_ESCALATION
```

## Child-friendly model

Imagine a toy car hits a wall.

You do not immediately press the accelerator again.

First ask:

```text
Can I safely try again?
Can I undo the last move?
Should I stop?
Do I need an adult?
```

The matrix is the checklist that prevents choosing an answer without the conditions that make it safe.

## Decision rules

### SAFE_RETRY

Use only when a retry safety primitive is established.

In v0.1 the validator requires at least one of:

```text
idempotency_verified == true
OR
operation_reversible == true
```

It also rejects SAFE_RETRY while consequence or uncertainty is `high`.

This means a retry is not safe merely because the previous attempt failed.

### ROLLBACK

Use only when both are true:

```text
rollback_available == true
operation_reversible == true
```

A desired rollback is not the same thing as an available rollback contract.

### STOP

STOP is the conservative terminal choice when no justified mutation should be attempted.

It does not require pretending that recovery succeeded. The failure remains preserved as evidence-backed history.

### HUMAN_ESCALATION

Use only with an explicit trigger:

```text
HIGH_CONSEQUENCE
CRITICAL_UNKNOWN
AUTHORITY_BOUNDARY
POLICY_REQUIRES_HUMAN
```

The trigger must match the recorded conditions. `HUMAN_ESCALATION` with `NONE` is invalid.

## Relationship to the stack

```text
DIF → clarify intent
DI  → clarify limits
DRP → preserve committed decision
TIP → reason about transition
Review → observe failure
Recovery Decision Matrix → gate the next recovery path
Next cycle → execute only the admitted path through the normal stack
```

The matrix does not bypass DI, DRP, or TIP. It does not execute anything. It only says whether a proposed recovery class is justified by the recorded recovery conditions.

## Core invariant

```text
failure evidence
→ recovery conditions
→ one selected recovery class
→ semantic validation
→ normal next decision/transition cycle
```

A recovery label without its prerequisites is invalid.

## Machine-readable files

Schema:

```text
schemas/recovery-decision-matrix.schema.json
```

Positive fixtures cover all four allowed outcomes:

```text
fixtures/valid-recovery-decision-safe-retry.json
fixtures/valid-recovery-decision-rollback.json
fixtures/valid-recovery-decision-stop.json
fixtures/valid-recovery-decision-human-escalation.json
```

Negative fixtures prove the guard rejects:

```text
SAFE_RETRY without idempotency/reversibility
ROLLBACK without an available rollback path
HUMAN_ESCALATION without an explicit matching trigger
```

## Boundary

This matrix must remain weaker than the canonical project contracts.

It must not become:

- a replacement for DIF intent confirmation;
- a replacement for DI feasibility analysis;
- a replacement for DRP commitment history;
- a replacement for TIP transition reasoning;
- an execution engine;
- a generic policy engine.

Its job is deliberately small:

> After failure, do not choose a recovery action whose safety conditions have not been established.
