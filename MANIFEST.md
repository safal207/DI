# DI Fixture Manifest

This manifest lists the seed fixtures used to review the DI schemas and the cross-stack integration envelope.

The fixtures are intentionally small. They are not a full validation suite yet. They provide concrete examples for schema validation, semantic handoff checks, CLI checks, and CI integration.

| Fixture | Schema | Expected Result | Purpose |
|---|---|---|---|
| `fixtures/valid-capability.json` | `schemas/capability.schema.json` | pass | Demonstrates a constrained but available DI capability record for support-note drafting. |
| `fixtures/valid-limitation.json` | `schemas/limitation.schema.json` | pass | Demonstrates a blocking limitation caused by missing permission / unverified identity. |
| `fixtures/valid-feasibility-check.json` | `schemas/feasibility-check.schema.json` | pass | Demonstrates a full feasibility check for AI agent support with feasible and blocked actions. |
| `fixtures/invalid-feasibility-missing-request.json` | `schemas/feasibility-check.schema.json` | fail | Demonstrates rejection when the required `request` field is missing. |
| `fixtures/valid-decision-transition-envelope.json` | `schemas/decision-transition-envelope.schema.json` | pass | Demonstrates a machine-readable `DIF → DI → DRP → TIP → pending Review` chain for an anonymous ambiguous-payment recovery scenario. |
| `fixtures/valid-decision-transition-envelope-reviewed.json` | `schemas/decision-transition-envelope.schema.json` | pass | Demonstrates a closed reviewed chain with evidence references and an explicit observed next state. |
| `fixtures/invalid-decision-transition-envelope-broken-reference.json` | `schemas/decision-transition-envelope.schema.json` | fail | Schema-valid shape with a deliberately broken `DRP → TIP` identity handoff; semantic validation must reject it. |
| `fixtures/invalid-decision-transition-envelope-reviewed-without-evidence.json` | `schemas/decision-transition-envelope.schema.json` | fail | Demonstrates that a reviewed transition cannot claim closure without evidence references. |

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

It checks the seed JSON Schema subset used by this repository:

- file existence,
- JSON syntax,
- required fields,
- unknown fields when `additionalProperties: false`,
- enum constraints,
- simple object, array, string, boolean, and numeric type constraints used by the current seed schemas.

For `schemas/decision-transition-envelope.schema.json`, it also checks cross-stack semantic invariants that JSON Schema cannot express directly:

```text
di.intent_id == dif.intent_id

drp.feasibility_id == di.feasibility_id

tip.decision_record_id == drp.record_id

review.transition_id == tip.transition_id
```

It additionally requires:

- the cross-stack DIF intent to be human-confirmed;
- a reviewed envelope to carry at least one evidence reference;
- a reviewed envelope to name a concrete observed next state;
- TIP lifecycle state to agree with pending/reviewed review state.

The validator does not implement full JSON Schema 2020-12.

## Current Scope

This repository currently defines:

- conceptual documentation,
- JSON Schemas,
- practical examples,
- validation fixtures,
- a minimal fixture validation script,
- semantic handoff checks for the cross-stack envelope,
- minimal CI validation for fixtures.

It does not yet define:

- a production validator,
- release automation,
- an execution engine,
- a policy engine,
- a decision log.

## Principle

> Fixtures make DI and its integration boundaries reviewable before they become executable infrastructure.
