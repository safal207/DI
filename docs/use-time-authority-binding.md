# Use-Time Authority Binding v0.1

Status: Draft integration invariant

Fresh evidence does not imply current authority.

A recovery action may be well-justified and the state evidence may be fresh, but execution is still invalid if the permission or authority to act was revoked before use.

This document adds one narrow execution-boundary rule:

```text
Recovery Decision
→ Use-Time Authority Receipt
→ Execution Receipt
```

It is not a new protocol and does not redefine DIF, DI, DRP, or TIP.

## Core problem

```text
12:29:58 authority = active
12:29:59 authority = revoked
12:30:00 execution happens
```

The earlier authority observation was true when produced, but it no longer authorizes execution.

Therefore:

> fresh evidence ≠ current authority

and:

> authorization at decision time ≠ authorization at use time

## Canonical record

Schema:

```text
schemas/use-time-authority-receipt.schema.json
```

The receipt records:

```text
authority_id
authority_generation
authority_status
checked_at
max_binding_age_seconds
recovery_decision_id
recovery_cycle_id
bound_execution_mode
evidence_references
```

## Binding invariants

The decision and use-time receipt must refer to the same authority generation:

```text
recovery_decision.authority_id
== use_time_authority_receipt.authority_id

recovery_decision.authority_generation
== use_time_authority_receipt.authority_generation
```

The receipt must bind to the exact recovery decision, cycle, and execution mode:

```text
use_time_authority_receipt.recovery_decision_id
== recovery_decision.decision_id

use_time_authority_receipt.recovery_cycle_id
== recovery_cycle.cycle_id

use_time_authority_receipt.bound_execution_mode
== recovery_cycle.execution_mode
```

The Execution Receipt must then bind back to that authority receipt and generation:

```text
execution_receipt.authority_receipt_id
== use_time_authority_receipt.authority_receipt_id

execution_receipt.authority_generation_at_execution
== recovery_decision.authority_generation

execution_receipt.authority_status_at_execution
== active
```

## Revocation rule

If authority is `revoked` or `unknown`, active automated execution is invalid.

If a revocation timestamp is known:

```text
revoked_at <= executed_at
→ execution invalid
```

This holds even if the authority was active when it was checked earlier.

## Use-time freshness rule

The authority check is consumed at the execution seam, not treated as indefinitely reusable proof.

```text
checked_at <= executed_at

executed_at - checked_at
<= max_binding_age_seconds
```

A generation change also invalidates the older authority receipt, even if its timestamp is recent.

## Negative cases

The validator rejects:

```text
active at check
→ revoked before execution
→ execution attempted
```

```text
decision generation = 7
use-time generation = 8
→ execution attempted under changed authority
```

```text
authority checked 20 seconds ago
max binding age = 5 seconds
→ stale authority at dispatch
```

## End-to-end line

```text
Intent
→ Feasibility
→ Decision
→ Transition
→ Recovery Decision
→ Use-Time Authority
→ Execution
→ State Effect
→ Fresh Review
→ Next State
```

The key invariant is:

> Revalidate authority at the point of use; never let an old grant silently authorize a new execution.
