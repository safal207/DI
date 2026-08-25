# Decision & Transition Integrity Stack v0.4

Status: Draft architecture evolution

v0.4 preserves the v0.3 multi-agent ownership chain and adds one more execution-integrity seam: **Lease & Fencing Admission**.

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
→ State Effect
→ Fresh Review
→ Next State
```

v0.3 established:

```text
one dispatch
→ one linear ownership chain
→ execution by latest recorded owner
```

v0.4 adds:

```text
latest owner
→ bounded lease
→ monotonic fencing token
→ side-effect admission
```

## Why v0.3 was not enough

A trace can correctly record that ownership transferred from A to B while worker A remains partitioned from the coordinator and still believes it owns the work.

```text
A thinks: I still own X
B thinks: I now own X
```

Both local beliefs can coexist.

So the system needs an execution-time discriminator that does not depend on worker belief.

v0.4 uses a fencing epoch:

```text
A lease → token 101
B lease → token 102
```

Once B's newer epoch exists, A's token is stale.

## New seam

```text
Dispatch Ownership
→ Lease Receipt
→ Dispatch Attempt Receipt
→ Execution Receipt
```

A lease receipt binds one ownership epoch to:

```text
actor
ownership generation
lease window
fencing token
```

A dispatch attempt receipt records whether that epoch was actually admitted by the side-effect boundary.

## Central laws

```text
ownership != active lease
```

```text
active lease != eternal execution right
```

```text
newer fencing token > older fencing token
```

```text
stale worker may attempt
but stale epoch must not be accepted
```

```text
exactly one represented attempt may be accepted for the canonical mutation dispatch
```

## Lease-expiry takeover

If ownership transfer says:

```text
transfer_basis = lease_expiry
```

then:

```text
transfer_time >= predecessor lease expiry
```

The new owner receives a newer fencing token.

The old worker can remain alive and confused without becoming admissible again.

## Split-brain example

```text
Authority Consumption
→ dispatch X
→ A generation 1 / token 101
→ A lease expires
→ B generation 2 / token 102

A → X + 101 → REJECT
B → X + 102 → ACCEPT

Execution Receipt
→ B
→ dispatch X
→ token 102
→ accepted attempt B
```

The key point is that the losing split-brain attempt remains observable in the trace.

## What v0.4 catches

```text
takeover before lease expiry
stale worker accepted
both workers accepted
fencing token regression or reuse
execution bound to stale lease
execution bound to stale fencing token
accepted attempt outside lease window
lease bound to wrong ownership epoch
execution bound to rejected admission attempt
```

## Runtime boundary

v0.4 is still evidence semantics, not a runtime lock implementation.

The strongest production pattern is:

```text
side-effect owner receives dispatch_id + fencing_token
↓
atomically compare with highest admitted token
↓
stale token → reject
current/new token → record and admit
```

This check belongs at the mutation boundary.

A worker-local lease check is not enough because a partitioned worker can have stale local state.

## Machine-readable pieces

```text
schemas/dispatch-lease-receipt.schema.json
schemas/dispatch-attempt-receipt.schema.json
schemas/execution-receipt.schema.json
fixtures/valid-lease-split-brain-recovery-v0.4.json
scripts/validate-lease-split-brain.py
scripts/di-conformance.py --profile lease-split-brain-v0.4
```

## Layer progression

```text
v0.2
Decision / path / authority / execution / effect integrity

v0.3
+ multi-agent ownership continuity

v0.4
+ lease expiry and fencing against stale executors
```

## Summary

v0.4 closes the stale-owner execution gap:

> The latest recorded owner is not safe merely because the trace says so. Execution must also bind to a live lease epoch, and a newer fencing token must make older epochs rejectable at the side-effect boundary.
