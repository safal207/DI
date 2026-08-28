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

Status: **complete, validated, and published as `v0.5-draft`**.

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

## v0.5 Stabilization and Publication

Status: **complete**.

Delivered:

- README, roadmap, release notes, and conformance documentation aligned with the actual v0.2–v0.5 profile ladder;
- full profile ladder executed successfully on stabilized `main`;
- read-only credential-boundary workflow pinned to an immutable ContractGraph-QA revision and executed successfully;
- useful contributor content from PR #9 preserved at the correct path with attribution;
- obsolete PR branches replaced by current-main validation rather than merged with stale history;
- explicit release scope and runtime limitations documented;
- real Git tag and GitHub prerelease `v0.5-draft` published from exact validated commit `a35a990c0c3d7715551b1cdaf933a58411f26c2b`.

Release gate status:

```text
stabilization merged                         PASS
Validate DI fixtures                         PASS
FCRP Credential Boundary                     PASS
known release-blocking regression             NONE OBSERVED
Git tag v0.5-draft                            PUBLISHED
GitHub prerelease DI v0.5-draft               PUBLISHED
```

## v0.5 Architecture Freeze

Status: **active**.

Purpose:

```text
published internal model
→ external sandbox evidence
→ mutation pressure
→ architecture change only if evidence exposes a real gap
```

Allowed during the freeze:

- bug fixes and security fixes;
- fixtures and mutation tests for existing profiles;
- external trace adapters without provider secrets;
- provider-neutral sandbox tooling;
- stable error codes and easier conformance consumption;
- benchmark packs based on existing invariants;
- documentation corrections and realistic examples.

Blocked without the v0.6 admission gate:

- a new conformance profile version;
- a new normative architecture layer;
- weakening existing invariants to make an external trace pass;
- broadening DI into an execution engine, transaction coordinator, lock service, idempotency store, or policy engine.

The full admission gate is defined in [`docs/architecture-freeze-v0.5.md`](docs/architecture-freeze-v0.5.md).

## Adoption and External Validation

Status: **active evidence phase**.

Priority use cases:

- payment and wallet recovery;
- agent tool mutations;
- distributed workers and takeover;
- QA evidence chains;
- incident response and rollback;
- human approval at authority boundaries.

Current evidence target:

- build a deterministic provider-neutral ambiguous-payment sandbox;
- capture a reproducible request → lost acknowledgement → authoritative lookup trace;
- translate observable facts into the existing v0.5 shape;
- run both the valid trace and adversarial mutations through conformance;
- provide an optional live Stripe test-mode capture adapter that requires a user-supplied secret only at runtime and never commits it;
- publish a case study that separates documented provider guarantees, observations, DI interpretation, and remaining runtime assumptions.

External products are validation cases, not members of the DI/DIF/DRP/TIP stack.

## v0.6 Admission Gate

v0.6 is not planned by default.

A proposal is admitted only with:

1. an external reproducible trace;
2. a minimal counterexample to v0.2–v0.5;
3. evidence that the current model either allows an unsafe trace or cannot represent a needed integrity property;
4. a mutation test for the proposed invariant;
5. a precise claim boundary;
6. a project-boundary review showing the change belongs in DI.

Until all six exist, the architectural decision is:

```text
NO v0.6
→ improve evidence, adapters, usability, and market validation instead
```

## Product and Market Validation

The same evidence pack should support three entry paths:

- **employment proof-of-work** for payments, backend, Web3, and agent QA roles;
- **paid verification pilot** for timeout, retry, takeover, and duplicate-effect risks;
- **conformance toolkit** for teams that can emit trace JSON and need a portable PASS/FAIL report.

The first commercial offer should remain bounded:

```text
one selected mutation flow
→ one failure surface
→ one trace pack
→ conformance report
→ remediation boundary
```

No broad platform promise before paid pilot evidence.

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
