# Doability Intelligence (DI)

DI maps what can and cannot be done before decisions become commitments.

По-русски:

> DI описывает, что возможно и невозможно, прежде чем решение станет обязательством.

## Core Thesis

Intelligent systems should not promise, plan, execute, or commit to an action before understanding the limits around that action.

DI is a narrow pre-decision layer for clarifying capabilities, limitations, constraints, risks, unknowns, and feasible action paths.

## One-Line Principle

> Do not promise action until limits are understood.

## Why DI Exists

Many systems fail not because they make the wrong decision, but because they act before understanding their own boundaries.

A request may look simple:

> Do this.

But before action, a system must ask:

- Is this technically possible?
- Is this permitted?
- Is this safe?
- Is this reversible?
- Is the required context available?
- Are there hidden constraints?
- Should this be escalated to a human?
- Is the system allowed to even attempt this?

DI is the layer that maps these questions before a decision becomes a commitment.

## What DI Is

DI is:

- a pre-decision layer,
- a capability boundary model,
- a limitation mapping protocol,
- a feasibility reasoning layer,
- a constraint clarification mechanism.

## What DI Is Not

DI is not:

- a task manager,
- an execution engine,
- a decision log,
- a policy engine,
- a productivity system,
- a SaaS platform,
- a replacement for human judgment.

DI does not decide.

DI clarifies whether action is possible, constrained, blocked, unknown, or conditionally feasible.

## Relation to DIF and DRP

DIF and DRP define two sides of a responsible decision system:

```text
DIF — do not act until intent is understood.
DRP — do not forget why a decision was made.
```

DI adds the third side:

```text
DI — do not promise action until limits are understood.
```

Together:

```text
DIF → clarify intent
DI  → clarify limits
DRP → commit decision
```

## Related Projects

DI is part of a small decision-integrity stack:

```text
DIF → clarify intent
DI  → clarify limits
DRP → commit decision
```

- [DIF / DeepIntent Funnel](https://github.com/safal207/DIF) — clarifies raw human signals into structured intent.
- [DI / Doability Intelligence](https://github.com/safal207/DI) — maps capabilities, limitations, constraints, and feasible action paths before commitment.
- [DRP / Decision Record Protocol](https://github.com/safal207/DRP) — records committed decisions with rationale, responsibility, and causal links.

Adjacent protocol:

- [TIP / Transition Intelligence Protocol](https://github.com/safal207/transition-intelligence-protocol) — studies transitions between states, including readiness, ambiguity, and safe movement from one state to another.

Cross-repo architecture note:

- [`docs/decision-transition-integrity-stack.md`](docs/decision-transition-integrity-stack.md) — defines how DIF, DI, DRP, and TIP cooperate while keeping their protocol boundaries separate, including handoff invariants and an anonymous financial walkthrough.

Each repository should stay narrow. DIF should not become DI. DI should not become DRP. DRP should not become an execution engine. TIP should not replace the decision stack; it should describe transition dynamics around it.

## Minimal Flow

```text
Raw signal / request
→ DIF: clarify intent
→ DI: clarify capabilities, limitations, constraints, and feasible paths
→ DRP: record the committed decision
```

## Repository Structure

```text
DI/
├── README.md
├── CONTRIBUTING.md
├── ROADMAP.md
├── docs/
│   ├── rfc-0001.md
│   ├── concept.md
│   ├── capability-boundaries.md
│   ├── limitation-model.md
│   ├── relation-to-dif-and-drp.md
│   └── decision-transition-integrity-stack.md
├── schemas/
│   ├── capability.schema.json
│   ├── limitation.schema.json
│   └── feasibility-check.schema.json
├── fixtures/
│   ├── valid-capability.json
│   ├── valid-limitation.json
│   ├── valid-feasibility-check.json
│   └── invalid-feasibility-missing-request.json
├── scripts/
│   └── validate-fixtures.py
├── .github/
│   └── workflows/
│       └── validate-fixtures.yml
└── examples/
    ├── ai-agent-support.md
    ├── startup-plan.md
    └── qa-automation.md
```

## Documentation

- [`docs/rfc-0001.md`](docs/rfc-0001.md) — draft RFC-style specification for DI v0.1.
- [`docs/concept.md`](docs/concept.md) — defines DI as the discipline of understanding what can and cannot be done before commitment.
- [`docs/capability-boundaries.md`](docs/capability-boundaries.md) — explains why technical capability is not permission.
- [`docs/limitation-model.md`](docs/limitation-model.md) — defines explicit limitation categories and severity levels.
- [`docs/relation-to-dif-and-drp.md`](docs/relation-to-dif-and-drp.md) — positions DI between DIF and DRP.
- [`docs/decision-transition-integrity-stack.md`](docs/decision-transition-integrity-stack.md) — cross-repo architecture for `DIF → DI → DRP` with TIP as the adjacent transition/review protocol.

## Schemas

- [`schemas/capability.schema.json`](schemas/capability.schema.json) — minimal capability record schema.
- [`schemas/limitation.schema.json`](schemas/limitation.schema.json) — minimal limitation record schema.
- [`schemas/feasibility-check.schema.json`](schemas/feasibility-check.schema.json) — minimal feasibility-check schema.

## Fixtures

- [`fixtures/valid-capability.json`](fixtures/valid-capability.json) — expected to pass capability schema validation.
- [`fixtures/valid-limitation.json`](fixtures/valid-limitation.json) — expected to pass limitation schema validation.
- [`fixtures/valid-feasibility-check.json`](fixtures/valid-feasibility-check.schema.json) — expected to pass feasibility-check schema validation.
- [`fixtures/invalid-feasibility-missing-request.json`](fixtures/invalid-feasibility-missing-request.json) — expected to fail feasibility-check schema validation.

See [`MANIFEST.md`](MANIFEST.md) for the fixture map.

## Validation

Run locally:

```bash
python scripts/validate-fixtures.py
```

CI runs the same validator on every push to `main` and on every pull request.

The validator is intentionally minimal and dependency-free. It checks the current seed fixtures against the current seed schemas. It is not a full JSON Schema 2020-12 implementation.

## Examples

DI is demonstrated through practical feasibility checks:

- [`examples/ai-agent-support.md`](examples/ai-agent-support.md) — maps support-agent capabilities, account-permission boundaries, blocked actions, and DRP readiness.
- [`examples/startup-plan.md`](examples/startup-plan.md) — maps startup revenue ambition into market, capital, founder-capacity, and validation constraints.
- [`examples/qa-automation.md`](examples/qa-automation.md) — maps QA automation feasibility across technical, operational, knowledge, and risk boundaries.

Each example follows the same pattern:

```text
Request
→ DIF Analysis / inferred intent
→ DI Feasibility Assessment
→ Boundary Assessment
→ Limitations
→ Feasible Paths
→ Blocked Actions
→ Critical Unknowns
→ Recommendation
→ DRP Readiness
```

## Contributing

DI is open to focused contributions that keep the repository narrow, protocol-like, and reviewable.

Good first contribution areas:

- improve examples,
- add realistic fixtures,
- clarify terminology,
- improve validator messages,
- review RFC-0001 open questions.

Start with:

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution guide and PR expectations.
- [`ROADMAP.md`](ROADMAP.md) — current development phases and entry points.
- issues labeled `good first issue` or `help wanted`.

## Status

Draft / seed repository.

This repository preserves DI as a narrow, clean concept: a layer for understanding capabilities, limitations, constraints, and feasibility before decisions become commitments.
