# Multi-Agent Dispatch Integrity v0.3

Status: Draft execution-integrity extension

v0.3 addresses a failure mode that appears when more than one worker can participate in the same automated recovery action.

The central distinction is:

```text
worker identity may change
!=
dispatch identity may change
```

A worker crash, handoff, reschedule, or orchestrator reassignment does not create a second mutation right.

## Problem

After authority has been consumed, worker A may claim the dispatch and then become unavailable before execution finishes.

Naive recovery can accidentally do this:

```text
Recovery Decision D
→ consume authority once
→ dispatch X claimed by worker A
→ worker A disappears
→ worker B creates dispatch Y
→ both X and Y may eventually execute
```

This violates the single-use intent even if worker B uses a fresh token or believes it is merely retrying work.

## v0.3 rule

The safe continuation is:

```text
Recovery Decision D
→ Authority Consumption
→ dispatch X
→ ownership generation 1: worker A
→ explicit ownership transfer
→ ownership generation 2: worker B
→ worker B executes dispatch X
```

The actor changes. The consumed dispatch does not.

## Ownership events

v0.3 introduces an append-only ownership event:

```text
schemas/dispatch-ownership-event.schema.json
```

An event records:

- `ownership_event_id`
- `dispatch_id`
- `event_type` (`claim` or `transfer`)
- `actor_id`
- `ownership_generation`
- optional predecessor and transfer basis
- timestamp
- evidence references

The initial ownership event is:

```text
claim
ownership_generation = 1
no predecessor
```

Every later change is:

```text
transfer
previous_ownership_event_id = immediately prior event
ownership_generation = prior generation + 1
actor_id != prior actor_id
```

## Execution binding

For the v0.3 profile, execution binds to the latest ownership event:

```text
execution.dispatch_id
== authority_consumption.dispatch_id
== latest_ownership.dispatch_id
```

and:

```text
execution.actor_id
== latest_ownership.actor_id

execution.dispatch_ownership_event_id
== latest_ownership.ownership_event_id

execution.dispatch_ownership_generation
== latest_ownership.ownership_generation
```

This makes stale-worker execution observable.

## Invalid examples

### Silent new dispatch after takeover

```text
worker A owns X
↓
handoff to worker B
↓
worker B creates Y
→ FAIL
```

### Stale worker executes after transfer

```text
ownership generation 1 = A
ownership generation 2 = B
A executes X after generation 2 exists
→ FAIL
```

### Parallel ownership fork

```text
ownership generation 1 = A
↓
transfer generation 2 = B
transfer generation 2 = C
→ FAIL
```

The ownership chain must be linear and generation-monotonic.

## Conformance profile

Validate a trace with:

```bash
python scripts/di-conformance.py \
  fixtures/valid-multi-agent-dispatch-takeover-v0.3.json \
  --profile multi-agent-dispatch-v0.3 \
  --pretty
```

Canonical semantic validator:

```text
scripts/validate-multi-agent-dispatch.py
```

The validator also creates deliberately broken mutations and requires all of them to be rejected.

## Relationship to v0.2

v0.3 does not replace the v0.2 end-to-end profile.

v0.2 answers questions such as:

```text
Was the intent confirmed?
Was the path feasible and selected?
Was it revalidated?
Was authority valid and consumed?
What executed?
What state changed?
Is the evidence fresh?
```

v0.3 adds another question at the execution boundary:

```text
Which actor currently owns the already-consumed dispatch?
```

So:

```text
v0.2 execution integrity
+
v0.3 multi-agent ownership continuity
```

## Runtime atomicity boundary

Ownership events are evidence and conformance artifacts. They do not by themselves implement mutual exclusion.

A production system still needs a real coordination primitive appropriate to its architecture, for example a transactional row update, compare-and-swap generation, lease/lock service, or another linearizable ownership mechanism.

The protocol-level requirement is that the emitted evidence makes ownership continuity and any transfer inspectable.

The strongest implementation shape is approximately:

```text
read current ownership generation
→ compare-and-swap to next generation + new owner
→ preserve dispatch_id
→ execute only while bound to that generation
```

If the runtime cannot guarantee that, the trace must not overclaim single-owner execution.

## Summary

v0.3 adds one law:

> A new worker is not a new permission. Multi-agent takeover may transfer ownership of an existing dispatch, but it must not silently create a second dispatch for the already-consumed recovery decision.
