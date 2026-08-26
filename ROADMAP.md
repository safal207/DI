# DI Roadmap

This roadmap keeps DI focused as a protocol and conformance repository rather than an execution platform.

## Guiding Principle

> Do not promise action until limits are understood.

## Current Architecture

The repository now validates an evidence chain that has grown beyond the original seed schemas:

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
→ Lease / Fencing Epoch
→ Dispatch Admission
→ Execution
→ Logical Operation Identity
→ Commit Outcome Resolution
→ State Effect
→ Fresh Review
→ Next State
```

Each layer remains an evidence/conformance boundary. DI does not execute the represented action.

## v0.1 — Seed Protocol Foundation

Status: complete.

Delivered:

- DI concept and RFC seed;
- separation from DIF and DRP;
- capability, limitation, and feasibility schemas;
- examples, fixtures, manifest, validator, and CI;
- contributor onboarding surfaces.

## v0.2 — End-to-End Decision Integrity

Status: complete.

Delivered:

- cross-stack `DIF → DI → DRP → TIP → Review` envelope;
- closed-loop state continuity;
- recovery decision matrix;
- strategy selection and path revalidation;
- use-time authority and single-use authority consumption;
- execution receipts, state-effect receipts, evidence freshness, and conformance CLI.

## v0.3 — Multi-Agent Dispatch Ownership

Status: complete.

Delivered:

- one consumed mutation right mapped to one stable dispatch;
- append-only ownership events;
- explicit takeover semantics;
- execution binding to the latest recorded owner;
- multi-agent dispatch conformance profile.

## v0.4 — Lease and Split-Brain Fencing

Status: complete and merged.

Delivered:

- bounded dispatch leases;
- monotonic fencing tokens;
- stale-worker rejection at the side-effect admission boundary;
- exactly one represented accepted dispatch attempt;
- execution binding to the accepted current lease and attempt;
- `lease-split-brain-v0.4` conformance profile.

## v0.5 — Ambiguous Commit Recovery

Status: active.

Goal:

```text
correct executor admitted
→ side effect may commit
→ acknowledgement lost
→ commit state resolved without creating a second effect
```

Planned / in progress:

- stable `logical_operation_id` and `effect_key`;
- ordered commit-outcome receipts;
- authoritative resolution of unknown commit state;
- one committed logical operation → one committed effect identity;
- safe next-action rules for committed / not committed / still unknown;
- state-effect evidence before success closure;
- `ambiguous-commit-v0.5` conformance profile and CI smoke test.

Central laws:

```text
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
```

## Stabilization After v0.5

Before adding another architecture layer:

- reconcile README, roadmap, manifest, and conformance docs;
- keep one canonical profile ladder;
- inspect stale pull requests and old contributor issues;
- publish a stable checkpoint only from a green `main` workflow;
- collect one external sandbox trace without overstating provider conformance.

## Adoption and Use Cases

Status: exploratory.

Priority use cases:

- payment and wallet recovery;
- agent tool mutations;
- distributed workers and takeover;
- QA evidence chains;
- incident response and rollback;
- human approval at authority boundaries.

External products are validation cases, not members of the DI/DIF/DRP/TIP stack.

## Boundaries

DI should remain:

- inspectable;
- provider-neutral;
- evidence-bound;
- fail-closed on broken identity chains;
- explicit about runtime assumptions;
- reusable as a conformance profile.

DI should not become:

- an execution engine;
- a distributed lock service;
- an idempotency store;
- a transaction coordinator;
- a general-purpose policy engine;
- a task manager;
- a SaaS platform.
