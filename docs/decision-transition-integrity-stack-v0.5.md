# Decision & Transition Integrity Stack v0.5

Status: Draft architecture evolution

v0.5 preserves the v0.4 lease/fencing admission chain and adds the post-execution seam: **Commit Outcome Resolution**.

## Canonical line

```text
Intent
→ Feasibility
→ Strategy
→ Decision
→ Path Revalidation
→ Transition
→ Use-Time Authority
→ Authority Consumption
→ Dispatch Ownership
→ Dispatch Lease / Fencing Epoch
→ Dispatch Admission Attempt
→ Execution
→ Logical Operation Identity
→ Commit Outcome Observation
→ Commit Resolution
→ State Effect
→ Fresh Review
→ Next State
```

## What v0.4 established

```text
stale worker may still attempt
but only the current fencing epoch may be admitted
```

## Why v0.4 was not enough

The current worker may be admitted correctly and the mutation may still end in an ambiguous local state:

```text
side effect commits
+
response is lost
=
local commit state unknown
```

If the system equates `unknown` with `failed`, it may create a second effect even though ownership and fencing were correct.

## New seam

```text
Execution
→ Logical Operation Identity
→ Commit Outcome Receipts
→ Commit Resolution
→ State Effect
```

The new seam preserves two identities:

```text
logical_operation_id
→ what mutation was intended

effect_key
→ which stable mutation identity crossed the side-effect boundary
```

## Central laws

```text
transport outcome != commit outcome
```

```text
unknown commit != not committed
```

```text
retry != new effect identity
```

```text
one committed logical operation
→ one committed effect identity
```

## Resolution rules

```text
committed
→ ACCEPT_EXISTING_EFFECT / STOP

not_committed
→ RETRY_SAME_EFFECT_KEY / STOP

still_unknown
→ STOP / HUMAN_ESCALATION
```

## Canonical trace

```text
worker A token 101 → stale → rejected
worker B token 102 → current → accepted
worker B mutation → response lost
commit observation → unknown
provider lookup → committed effect payment-001
resolution → ACCEPT_EXISTING_EFFECT
state effect → PAYMENT_COMMITTED
```

## Machine-readable pieces

```text
schemas/logical-operation.schema.json
schemas/commit-outcome-receipt.schema.json
schemas/commit-resolution.schema.json
fixtures/valid-ambiguous-commit-recovery-v0.5.json
scripts/validate-ambiguous-commit.py
scripts/di-conformance.py --profile ambiguous-commit-v0.5
```

## What a v0.5 PASS means

According to the supplied trace:

```text
v0.4 lease/fencing admission still holds
AND
one stable logical operation identity is represented
AND
all commit observations preserve the same effect key
AND
unknown state is not silently treated as failure
AND
authoritative commit observations do not contradict each other
AND
one committed logical operation resolves to one effect identity
AND
the selected next action is compatible with the resolved commit state
AND
committed success is backed by matching state-effect evidence
```

## What a v0.5 PASS does not mean

PASS does not independently prove:

```text
the provider idempotency store was atomic
an external lookup was truthful
a database transaction was exactly-once
network evidence was complete
the side-effect system cannot be corrupted
```

The profile validates the supplied evidence chain, not the external runtime itself.

## Layer progression

```text
v0.2 → decision-to-evidence integrity
v0.3 → multi-agent ownership continuity
v0.4 → lease expiry and fencing
v0.5 → ambiguous commit resolution and stable effect identity
```

## Summary

v0.5 protects the moment after a correct executor has acted but before the system knows whether the effect committed:

> A missing acknowledgement cannot become permission for a new effect. Preserve the logical operation, resolve the commit state, and only then authorize the next transition.
