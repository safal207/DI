# DI Fixture Manifest

This manifest lists the seed fixtures used to review the DI schemas.

The fixtures are intentionally small. They are not a full validation suite yet. They provide concrete examples for schema validation, CLI checks, and CI integration.

| Fixture | Schema | Expected Result | Purpose |
|---|---|---|---|
| `fixtures/valid-capability.json` | `schemas/capability.schema.json` | pass | Demonstrates a constrained but available DI capability record for support-note drafting. |
| `fixtures/valid-limitation.json` | `schemas/limitation.schema.json` | pass | Demonstrates a blocking limitation caused by missing permission / unverified identity. |
| `fixtures/valid-feasibility-check.json` | `schemas/feasibility-check.schema.json` | pass | Demonstrates a full feasibility check for AI agent support with feasible and blocked actions. |
| `fixtures/invalid-feasibility-missing-request.json` | `schemas/feasibility-check.schema.json` | fail | Demonstrates rejection when the required `request` field is missing. |

## Validation

Run locally:

```bash
python scripts/validate-fixtures.py
```

CI runs the same validator on every push to `main` and on every pull request via:

```text
.github/workflows/validate-fixtures.yml
```

The validator is intentionally minimal and dependency-free.

It checks:

- file existence,
- JSON syntax,
- required fields,
- unknown fields when `additionalProperties: false`,
- enum constraints,
- simple object, array, and string type constraints used by the current seed schemas.

It does not implement full JSON Schema 2020-12.

## Current Scope

This repository currently defines:

- conceptual documentation,
- JSON Schemas,
- practical examples,
- validation fixtures,
- a minimal fixture validation script,
- minimal CI validation for fixtures.

It does not yet define:

- a production validator,
- release automation,
- an execution engine,
- a policy engine,
- a decision log.

## Principle

> Fixtures make DI reviewable before DI becomes executable.
