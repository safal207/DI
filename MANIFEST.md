# DI Fixture Manifest

This manifest lists the seed fixtures used to review the DI schemas.

The fixtures are intentionally small. They are not a full validation suite yet. They provide concrete examples for future schema validation, CLI checks, or CI integration.

| Fixture | Schema | Expected Result | Purpose |
|---|---|---|---|
| `fixtures/valid-capability.json` | `schemas/capability.schema.json` | pass | Demonstrates a constrained but available DI capability record for support-note drafting. |
| `fixtures/valid-limitation.json` | `schemas/limitation.schema.json` | pass | Demonstrates a blocking limitation caused by missing permission / unverified identity. |
| `fixtures/valid-feasibility-check.json` | `schemas/feasibility-check.schema.json` | pass | Demonstrates a full feasibility check for AI agent support with feasible and blocked actions. |
| `fixtures/invalid-feasibility-missing-request.json` | `schemas/feasibility-check.schema.json` | fail | Demonstrates rejection when the required `request` field is missing. |

## Current Scope

This repository currently defines:

- conceptual documentation,
- JSON Schemas,
- practical examples,
- validation fixtures.

It does not yet define:

- a CLI validator,
- CI validation,
- an execution engine,
- a policy engine,
- a decision log.

## Principle

> Fixtures make DI reviewable before DI becomes executable.
