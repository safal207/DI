# DI Roadmap

This roadmap keeps DI focused as a small, protocol-like repository.

## Current Status

DI currently has:

```text
concept
→ docs
→ RFC
→ schemas
→ examples
→ fixtures
→ manifest
→ validator
→ CI
```

## Guiding Principle

> Do not promise action until limits are understood.

## Phase 0 — Seed Protocol Foundation

Status: mostly complete.

Goals:

- define DI as Doability Intelligence,
- separate DI from DIF and DRP,
- add minimal schemas,
- add examples,
- add fixtures,
- add local validation,
- add CI validation,
- add RFC-0001.

## Phase 1 — Contributor Onboarding

Status: active.

Goals:

- add contributor guide,
- label good first issues,
- identify simple entry points,
- improve examples,
- make terminology clearer,
- add contributor-friendly documentation.

Suggested tasks:

- add new examples for real-world domains,
- improve schema comments and naming,
- add more invalid fixtures,
- clarify open questions in RFC-0001,
- improve README navigation.

## Phase 2 — Validation Depth

Status: planned.

Goals:

- expand fixture coverage,
- add more invalid cases,
- validate examples as structured objects if useful,
- improve validator error messages,
- consider a stricter JSON Schema validator only if dependency cost is justified.

Non-goal:

- do not build a production validation framework yet.

## Phase 3 — Protocol Maturity

Status: planned.

Goals:

- refine DI assessment model,
- stabilize terminology,
- define evidence anchors if needed,
- define relation to DRP records more precisely,
- prepare RFC-0002 if the concept matures.

## Phase 4 — Adoption and Use Cases

Status: exploratory.

Goals:

- collect feasibility examples from AI agents, QA, startup planning, fintech, support workflows, education, and governance,
- document where DI helps prevent premature commitment,
- invite feedback from AI safety, QA, compliance, and developer-tooling communities.

## Boundaries

DI should remain:

- narrow,
- pre-decision,
- reviewable,
- protocol-like,
- lightweight.

DI should not become:

- an execution engine,
- a policy engine,
- a task manager,
- a SaaS platform,
- a generic AI workflow product.
