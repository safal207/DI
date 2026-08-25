# Lease & Split-Brain Integrity v0.4

Status: Draft cross-stack integrity layer

## Problem

v0.3 proves that ownership transfers are explicit and that execution binds to the latest recorded owner.

That is not enough in a distributed runtime.

A stale worker can miss the transfer and continue believing it still owns the dispatch:

```text
worker A owns dispatch X
↓
A becomes slow / partitioned / paused
↓
A lease expires
↓
worker B receives takeover
↓
A wakes up and still tries X
B also tries X
```

This is a split-brain execution attempt.

The safety question is not:

> Which worker believes it is the owner?

It is:

> Which execution epoch is currently admissible at the side-effect boundary?

## Core law

```text
ownership belief != execution authority
```

and:

```text
newer fencing token supersedes older fencing token
```

A stale worker may still attempt execution. That attempt must be rejected.

## Canonical flow

```text
authority consumed once
↓
dispatch X
↓
worker A ownership generation 1
↓
lease A / fencing token 101
↓
lease A expires
↓
ownership transfers to worker B generation 2
↓
lease B / fencing token 102
↓
A attempts X with token 101 → REJECTED
B attempts X with token 102 → ACCEPTED
↓
execution receipt binds to B / lease B / token 102
```

The dispatch identity never changes.

## Lease receipt

Machine-readable schema:

```text
schemas/dispatch-lease-receipt.schema.json
```

A lease receipt binds:

```text
dispatch_id
actor_id
ownership_event_id
ownership_generation
fencing_token
issued_at
expires_at
```

A lease is an execution epoch, not a new mutation permission.

The original authority consumption still owns the one mutation right.

## Fencing token

A fencing token is a monotonic epoch number issued by the coordination boundary.

Example:

```text
A → token 101
B → token 102
```

Once `102` exists, `101` is stale even if worker A did not observe the takeover.

The side-effect owner should enforce:

```text
incoming_token < highest_accepted_token
→ reject
```

This is stronger than asking a worker whether its local lease still looks valid.

## Lease expiry transfer

If an ownership transfer declares:

```text
transfer_basis = lease_expiry
```

then the transfer must not occur before the predecessor lease expires.

```text
transfer.occurred_at >= predecessor_lease.expires_at
```

If the predecessor ownership epoch has multiple lease receipts, takeover must occur after the latest predecessor expiry represented by the trace.

## Dispatch attempt receipt

Machine-readable schema:

```text
schemas/dispatch-attempt-receipt.schema.json
```

Each admission attempt records:

```text
actor
ownership epoch
lease
fencing token
attempt time
accepted | rejected
reason
evidence
```

This makes split-brain observable rather than hiding the losing attempt.

A valid trace can therefore contain both:

```text
A tried and was rejected
B tried and was accepted
```

That is safer evidence than pretending A never existed.

## Accepted attempt invariant

For the v0.4 conformance profile:

```text
exactly one attempt is accepted
```

The accepted attempt must bind to:

```text
latest ownership event
latest owner
current lease
highest represented fencing token
unexpired lease window
```

Execution then binds to that exact accepted attempt.

## Execution binding

`execution-receipt.schema.json` gains optional v0.4 fields:

```text
dispatch_lease_id
dispatch_fencing_token
dispatch_attempt_id
```

For v0.4:

```text
execution.dispatch_attempt_id
== accepted_attempt.attempt_id

execution.dispatch_lease_id
== accepted_attempt.lease_id

execution.dispatch_fencing_token
== accepted_attempt.fencing_token
```

This preserves compatibility with earlier profiles while making lease fencing explicit when needed.

## What v0.4 rejects

Examples:

```text
takeover before predecessor lease expiry
stale worker accepted after takeover
both workers accepted
fencing token regression or duplication
execution using stale lease
execution using stale fencing token
accepted attempt after lease expiry
lease bound to wrong owner
attempt bound to unknown lease
execution bound to rejected attempt
```

## Runtime boundary

The validator proves trace semantics only.

It does **not** itself create a distributed lock, lease service, consensus system, or atomic compare-and-set.

For real split-brain safety, the side-effect owner should enforce fencing tokens in the same consistency boundary that admits the mutation.

Strong pattern:

```text
receive dispatch X + token N
↓
atomically compare N with highest accepted token for X/scope
↓
N stale → reject
N current/new → record token and admit
```

A log written after an unsafe side effect cannot retroactively provide fencing.

## Clock boundary

Lease expiry uses timestamps in the trace, but production correctness should not depend only on unsynchronized worker clocks.

Prefer an authoritative lease/coordination service for:

```text
lease issuance
expiry decisions
fencing token generation
```

Fencing tokens provide a monotonic ordering signal even when workers disagree about wall-clock time.

## Conformance

Reference fixture:

```text
fixtures/valid-lease-split-brain-recovery-v0.4.json
```

Validator:

```text
scripts/validate-lease-split-brain.py
```

CLI:

```bash
python scripts/di-conformance.py \
  fixtures/valid-lease-split-brain-recovery-v0.4.json \
  --profile lease-split-brain-v0.4 \
  --pretty
```

## Summary

```text
v0.3: who owns the dispatch?

v0.4: which ownership epoch is still admissible to execute?
```

The central invariant is:

> A worker can be stale without knowing it. Safety therefore belongs at the side-effect boundary, where a newer fencing token must make older execution epochs rejectable.
