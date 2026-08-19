# DI Fixture Manifest

This manifest lists the seed fixtures used to review the DI schemas, the cross-stack integration envelope, the closed-loop cycle chain, the Recovery Decision Matrix, recovery decision → execution binding, execution receipts, observed state effects, and evidence freshness.

The fixtures are intentionally small. They are not a full validation suite yet. They provide concrete examples for schema validation, semantic handoff checks, cycle continuity checks, recovery provenance checks, recovery-path admissibility checks, decision-to-execution binding checks, observed-execution receipt checks, state-effect checks, freshness/generation checks, CLI checks, and CI integration.

| Fixture | Schema / Validator | Expected Result | Purpose |
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
| `fixtures/valid-decision-transition-cycle-chain-recovery.json` | cycle-chain + binding validators | pass | Demonstrates preserved failure followed by a recovery cycle whose Matrix action, declared execution mode, observed Execution Receipt, observed State Effect Receipt, generation, and freshness window all agree. |
| `fixtures/invalid-decision-transition-cycle-chain-recovery-without-evidence.json` | cycle-chain validator | fail | Demonstrates rejection when a recovery cycle claims reviewed closure without recovery evidence. |
| `fixtures/valid-recovery-decision-safe-retry.json` | `schemas/recovery-decision-matrix.schema.json` | pass | Demonstrates SAFE_RETRY backed by a verified idempotency contract. |
| `fixtures/valid-recovery-decision-rollback.json` | `schemas/recovery-decision-matrix.schema.json` | pass | Demonstrates ROLLBACK with an available, reversible rollback path. |
| `fixtures/valid-recovery-decision-stop.json` | `schemas/recovery-decision-matrix.schema.json` | pass | Demonstrates conservative STOP when no additional mutation is justified. |
| `fixtures/valid-recovery-decision-human-escalation.json` | `schemas/recovery-decision-matrix.schema.json` | pass | Demonstrates HUMAN_ESCALATION triggered by an observed authority boundary. |
| `fixtures/invalid-recovery-decision-unsafe-retry.json` | `schemas/recovery-decision-matrix.schema.json` | fail | Rejects SAFE_RETRY when neither idempotency nor reversibility is established. |
| `fixtures/invalid-recovery-decision-rollback-unavailable.json` | `schemas/recovery-decision-matrix.schema.json` | fail | Rejects ROLLBACK when no rollback path is available. |
| `fixtures/invalid-recovery-decision-human-escalation-without-trigger.json` | `schemas/recovery-decision-matrix.schema.json` | fail | Rejects HUMAN_ESCALATION when no explicit matching trigger exists. |
| `fixtures/invalid-recovery-execution-binding-action-mismatch.json` | `scripts/validate-recovery-binding.py` | fail | Matrix selects `SAFE_RETRY` while the recovery cycle declares `ROLLBACK`; execution substitution must be rejected. |
| `fixtures/invalid-recovery-execution-binding-stop-continued.json` | `scripts/validate-recovery-binding.py` | fail | Matrix selects `STOP` but an active recovery cycle is still created; automated continuation must be rejected. |
| `fixtures/invalid-execution-receipt-mode-mismatch.json` | `scripts/validate-recovery-binding.py` | fail | Matrix and cycle declare `SAFE_RETRY`, but the Execution Receipt observes `ROLLBACK`; observed execution substitution must be rejected. |
| `fixtures/invalid-execution-receipt-without-evidence.json` | `scripts/validate-recovery-binding.py` | fail | Execution Receipt claims an observed action without any evidence reference. |
| `fixtures/invalid-state-effect-target-mismatch.json` | `scripts/validate-recovery-binding.py` | fail | Execution is observed, but the State Effect Receipt does not observe TIP's target state while Review claims `RECOVERY_CONFIRMED`. |
| `fixtures/invalid-state-effect-without-evidence.json` | `scripts/validate-recovery-binding.py` | fail | State Effect Receipt claims the target state was observed without any evidence reference. |
| `fixtures/invalid-state-effect-stale-generation.json` | `scripts/validate-recovery-binding.py` | fail | State effect is recent but belongs to generation 3 while Review accepts generation 4. |
| `fixtures/invalid-state-effect-stale-time.json` | `scripts/validate-recovery-binding.py` | fail | State effect belongs to the accepted generation but is older than Review's maximum evidence age. |

## Validation

Run locally:

```bash
python scripts/validate-fixtures.py
python scripts/validate-recovery-binding.py
```

CI runs both validators on every push to `main` and on every pull request via:

```text
.github/workflows/validate-fixtures.yml
```

The validators are intentionally minimal and dependency-free.

The main fixture validator checks the seed JSON Schema subset used by this repository:

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

For `schemas/recovery-decision-matrix.schema.json`, semantic validation enforces:

```text
SAFE_RETRY
→ verified idempotency OR reversibility
→ not high uncertainty
→ not high consequence

ROLLBACK
→ rollback_available == true
→ operation_reversible == true

HUMAN_ESCALATION
→ explicit trigger != NONE
→ trigger matches the recorded condition

STOP
→ may conservatively terminate further mutation
```

Every recovery decision also requires a non-empty rationale and at least one evidence reference. Non-escalation actions must not carry an escalation trigger.

The recovery binding validator adds the use-time invariants:

```text
recovery_decision.source_cycle_id
== recovery_cycle.recovery_of_cycle_id

recovery_decision.failure_state
== recovery_cycle.input_state
== failed_cycle.review.next_state

recovery_decision.selected_action
== recovery_cycle.execution_mode
== execution_receipt.declared_execution_mode
```

For `execution_status = observed`:

```text
execution_receipt.observed_execution_mode
== execution_receipt.declared_execution_mode
```

Execution alone is not enough. The State Effect Receipt must also bind to the exact execution receipt and TIP target:

```text
state_effect_receipt.execution_receipt_id
== execution_receipt.receipt_id

state_effect_receipt.recovery_cycle_id
== recovery_cycle.cycle_id

state_effect_receipt.expected_target_state
== recovery_cycle.envelope.tip.target_state
```

For `effect_status = observed`:

```text
state_effect_receipt.observed_state
== recovery_cycle.envelope.tip.target_state
```

For `RECOVERY_CONFIRMED`, state evidence must also be fresh for the Review that consumes it:

```text
state_effect_receipt.state_generation
== review.accepted_state_generation

state_effect_receipt.observed_at
<= review.reviewed_at

review.reviewed_at - state_effect_receipt.observed_at
<= review.max_evidence_age_seconds
```

This separately rejects stale generations and expired timestamps. The freshness window is declared by the consuming Review, not by the evidence producer.

`RECOVERY_CONFIRMED` therefore requires an observed Execution Receipt, an evidence-backed observed State Effect Receipt matching TIP's target state, the accepted state generation, and the configured freshness window.

`STOP` is terminal for automated recovery: selecting `STOP` and then creating an active recovery cycle is invalid.

See:

- [`docs/closed-loop-recovery.md`](docs/closed-loop-recovery.md) for the failure → recovery walkthrough;
- [`docs/recovery-decision-matrix.md`](docs/recovery-decision-matrix.md) for the recovery-path gate;
- [`docs/recovery-execution-binding.md`](docs/recovery-execution-binding.md) for decision → execution fidelity;
- [`docs/execution-receipt.md`](docs/execution-receipt.md) for observed execution evidence;
- [`docs/state-effect-binding.md`](docs/state-effect-binding.md) for execution → observed state-effect and evidence-freshness fidelity.

The validators do not implement full JSON Schema 2020-12.

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
- recovery-action admissibility checks for SAFE_RETRY / ROLLBACK / STOP / HUMAN_ESCALATION,
- recovery decision → execution binding checks,
- execution receipt checks for observed recovery actions,
- state-effect receipt checks before recovery confirmation,
- generation and time freshness checks for state-effect evidence,
- minimal CI validation for fixtures.

It does not yet define:

- a production validator,
- release automation,
- an execution engine,
- a general-purpose policy engine,
- a decision log.

## Principle

> Fixtures make DI and its integration boundaries reviewable before they become executable infrastructure.
