# DI Fixture Manifest

This manifest lists the seed fixtures used to review the DI schemas, the cross-stack integration envelope, and the closed-loop cycle chain.

The fixtures are intentionally small. They are not a full validation suite yet. They provide concrete examples for schema validation, semantic handoff checks, cycle continuity checks, recovery provenance checks, CLI checks, and CI integration.

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
| `fixtures/valid-decision-transition-cycle-chain-two-cycles.json` | `schemas/decision-transition-cycle-chain.schema.json` | pass | Demonstrates two reviewed cycles where cycle 1 `next_state` becomes the exact cycle 2 `input_state`. |
| `fixtures/invalid-decision-transition-cycle-chain-state-mismatch.json` | `schemas/decision-transition-cycle-chain.schema.json` | fail | Demonstrates rejection when cycle 2 silently starts from a state different from the previous reviewed `next_state`. |
| `fixtures/valid-decision-transition-cycle-chain-recovery.json` | `schemas/decision-transition-cycle-chain.schema.json` | pass | Demonstrates preserved failure followed by a separate evidence-backed recovery cycle linked with `recovery_of_cycle_id`. |
| `fixtures/invalid-decision-transition-cycle-chain-recovery-without-evidence.json` | `schemas/decision-transition-cycle-chain.schema.json` | fail | Demonstrates rejection when a recovery cycle claims reviewed closure without recovery evidence. |

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

For `schemas/decision-transition-cycle-chain.schema.json`, the validator also checks:

```text
cycle.cycle_id == cycle.envelope.envelope_id
cycle.input_state == cycle.envelope.tip.starting_state
cycle[n].previous_cycle_id == cycle[n-1].cycle_id
cycle[n].input_state == cycle[n-1].envelope.review.next_state
```

For an explicit recovery cycle, it additionally requires:

```text
recovery_of_cycle_id == previous_cycle_id
```

and the referenced failed cycle must already exist earlier in the chain. The failed observation remains preserved; recovery is a new reviewed cycle rather than a rewrite of the failed one.

It validates every nested envelope with the envelope schema and semantic rules, and requires chained cycles to be reviewed before their observed state can seed another cycle.

See [`docs/closed-loop-recovery.md`](docs/closed-loop-recovery.md) for the failure → recovery walkthrough.

The validator does not implement full JSON Schema 2020-12.

## Current Scope

This repository currently defines:

- conceptual documentation,
- JSON Schemas,
- practical examples,
- validation fixtures,
- a minimal fixture validation script,
- semantic handoff checks for the cross-stack envelope,
- semantic continuity checks across sequential cycles,
- explicit recovery provenance across failed and recovered cycles,
- minimal CI validation for fixtures.

It does not yet define:

- a production validator,
- release automation,
- an execution engine,
- a policy engine,
- a decision log.

## Principle

> Fixtures make DI and its integration boundaries reviewable before they become executable infrastructure.
