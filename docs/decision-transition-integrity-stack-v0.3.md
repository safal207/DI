# Decision & Transition Integrity Stack v0.3

Status: Draft architecture evolution

v0.3 preserves the v0.2 decision/transition chain and adds one execution-integrity seam for multi-agent systems: **Dispatch Ownership Continuity**.

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
→ Execution
→ State Effect
→ Fresh Review
→ Next State
```

v0.2 established:

```text
one committed path
→ one revalidated transition
→ one consumed mutation right
→ one dispatch
→ one observed effect
```

v0.3 adds:

```text
one dispatch
→ one current owner generation
→ explicit linear ownership transfer
→ execution by the latest owner
```

## Why this exists

Single-use authority prevents two independent mutation rights from being created from one decision.

But a distributed worker system has another failure mode:

```text
worker A owns dispatch X
↓
A becomes unavailable
↓
worker B starts recovery
```

Without an ownership invariant, B may accidentally create a new dispatch or execute while A is still eligible to execute X.

So:

```text
single-use authority
!=
single current executor
```

Both matter.

## New seam

```text
Authority Consumption
→ Dispatch Ownership Event(s)
→ Execution Receipt
```

Ownership events are append-only.

The initial event is generation 1.

Every transfer points to the immediately prior event and increments the generation exactly once.

The execution receipt binds to the latest:

```text
actor_id
ownership_event_id
ownership_generation
dispatch_id
```

## Central laws

```text
new worker != new permission
```

```text
worker identity may change
but
consumed dispatch identity must remain stable
```

```text
latest ownership generation
=
only actor represented as eligible to execute
```

## What v0.3 catches

```text
silent dispatch fork
stale-owner execution
parallel ownership branches
generation rollback or skip
broken ownership predecessor
execution before handoff
ownership without evidence
```

## What v0.3 does not claim

The trace does not itself implement consensus, locking, or transactional isolation.

A conforming runtime still needs a coordination primitive capable of making ownership transfer real.

The protocol makes the coordination claim inspectable and falsifiable.

## Machine-readable pieces

```text
schemas/dispatch-ownership-event.schema.json
fixtures/valid-multi-agent-dispatch-takeover-v0.3.json
scripts/validate-multi-agent-dispatch.py
scripts/di-conformance.py --profile multi-agent-dispatch-v0.3
```

## Relationship to protocol boundaries

Dispatch Ownership Continuity is not a new fifth protocol.

It is an integration boundary after TIP has selected a transition and after automated authority has been consumed.

The protocol responsibilities remain separate:

```text
DIF → what is actually intended?
DI → what is feasible?
Strategy → what paths exist and how do they compare?
DRP → what path was committed?
TIP → how do we transition along that committed path?
Execution integrity → who may carry the already-committed dispatch now, and what actually happened?
```

## Summary

v0.3 closes the multi-agent takeover gap:

> An executor may be replaced without replacing the decision, authority consumption, or dispatch identity. The replacement must be represented as an explicit ownership transfer, and only the latest owner may be represented as the executor.
