# DI Roadmap

This roadmap keeps DI focused as a protocol and conformance repository rather than an execution platform.

## Guiding Principle

> Do not promise action until limits are understood.

## Current Architecture

The repository validates an evidence chain around decision and transition integrity:

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

Status: **complete**.

Delivered:

- DI concept and RFC seed;
- separation from DIF and DRP;
- capability, limitation, and feasibility schemas;
- examples, fixtures, manifest, validator, and CI;
- contributor onboarding surfaces.

## v0.2 — End-to-End Decision Integrity

Status: **complete**.

Delivered:

- cross-stack `DIF → DI → DRP → TIP → Review` envelope;
- closed-loop state continuity;
- recovery decision matrix;
- strategy selection and path revalidation;
- use-time authority and single-use authority consumption;
- execution receipts, state-effect receipts, evidence freshness, and conformance CLI.

## v0.3 — Multi-Agent Dispatch Ownership

Status: **complete**.

Delivered:

- one consumed mutation right mapped to one stable dispatch;
- append-only ownership events;
- explicit takeover semantics;
- execution binding to the latest recorded owner;
- `multi-agent-dispatch-v0.3` conformance profile.

## v0.4 — Lease and Split-Brain Fencing

Status: **complete**.

Delivered:

- bounded dispatch leases;
- monotonic fencing tokens;
- stale-worker rejection at the side-effect admission boundary;
- exactly one represented accepted dispatch attempt;
- execution binding to the accepted current lease and attempt;
- `lease-split-brain-v0.4` conformance profile.

## v0.5 — Ambiguous Commit Recovery

Status: **complete and validated**.

Delivered:

- stable `logical_operation_id` and `effect_key`;
- ordered commit-outcome receipts;
- authoritative resolution of unknown commit state;
- one committed logical operation → one committed effect identity;
- safe next-action rules for committed / not committed / still unknown;
- state-effect evidence before success closure;
- mutation checks for key drift, contradictory resolution, duplicate committed effects, unsafe retries, and unsupported success;
- `ambiguous-commit-v0.5` conformance profile and CI smoke test.

Central laws:

```text
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
one committed logical operation -> one committed effect identity
```

## v0.5 Stabilization

Status: **active**.

Goals:

- align README, roadmap, release notes, manifest, and conformance documentation;
- run the full profile ladder from one green `main` workflow;
- add a read-only credential-boundary workflow pinned to an immutable provider revision;
- resolve stale PRs without discarding useful contributor work;
- keep one canonical profile ladder;
- prepare a `v0.5-draft` release marker only from an exact green `main` commit.

Release gate:

```text
stabilization merged
AND
Validate DI fixtures = success on merge commit
AND
FCRP Credential Boundary = success on merge commit
AND
no known release-blocking regression
```

## Adoption and External Validation

Status: **exploratory**.

Priority use cases:

- payment and wallet recovery;
- agent tool mutations;
- distributed workers and takeover;
- QA evidence chains;
- incident response and rollback;
- human approval at authority boundaries.

Next evidence target:

- collect one provider sandbox or test-mode trace;
- translate only observable facts into a DI conformance fixture;
- preserve the distinction between provider guarantees, our inference, observed evidence, and runtime assumptions;
- avoid claiming provider endorsement or conformance.

External products are validation cases, not members of the DI/DIF/DRP/TIP stack.

## After the v0.5 checkpoint

Do not add another architecture layer automatically.

Candidate work should first answer one of these questions:

1. Does a real external trace reveal an unmodelled integrity seam?
2. Is a current invariant too weak or too hard to apply?
3. Can the conformance interface become easier to consume without becoming an execution platform?
4. Does the protocol need RFC clarification rather than another schema?

Possible next directions:

- packaged conformance artifacts for CI systems;
- clearer stable error codes;
- external trace adapters that do not import provider secrets;
- a compact benchmark across several recovery failure modes;
- RFC-0002 only after evidence justifies terminology or semantic changes.

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
