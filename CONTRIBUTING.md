# Contributing to Doability Intelligence (DI)

Thank you for considering a contribution to DI.

DI is a seed-stage protocol repository. The goal is to keep it narrow, clear, reviewable, and useful.

## Project Thesis

> DI maps what can and cannot be done before decisions become commitments.

## Core Principle

> Do not promise action until limits are understood.

## What Contributions Are Welcome

Good contributions include:

- clearer protocol language,
- better examples,
- additional fixtures,
- schema improvements,
- documentation cleanup,
- validation improvements,
- real-world feasibility scenarios,
- issue triage and review comments.

## What DI Should Not Become

Please avoid contributions that turn DI into:

- an execution engine,
- a task manager,
- a decision log,
- a policy engine,
- a productivity dashboard,
- a SaaS platform,
- a generic prompt collection.

DI should remain a pre-decision capability and limitation assessment layer.

## Contributor Entry Points

The easiest places to start are:

- examples,
- fixtures,
- terminology cleanup,
- documentation clarity,
- small validator improvements.

Look for issues labeled:

- `good first issue`,
- `help wanted`,
- `documentation`,
- `examples`,
- `fixtures`.

## Repository Map

```text
README.md                         project overview
MANIFEST.md                       fixture manifest
docs/rfc-0001.md                  DI v0.1 draft specification
docs/concept.md                   conceptual overview
docs/capability-boundaries.md     capability boundary model
docs/limitation-model.md          limitation model
docs/relation-to-dif-and-drp.md   relation to DIF and DRP
schemas/                          JSON Schemas
fixtures/                         valid and invalid schema fixtures
examples/                         applied DI examples
scripts/validate-fixtures.py      minimal fixture validator
tests/                            harness regression tests
.github/workflows/                CI validation workflow
```

## Development Setup

No package manager is required.

To validate fixtures locally, run:

```bash
python scripts/validate-fixtures.py
```

The script uses only Python standard library modules.

To run the harness regression tests, run:

```bash
python -m unittest discover -s tests -v
```

### Harness failure vs expected rejection

A fixture case declared as expected-to-fail passes only when the fixture is
readable and the rules under test reject it (a semantic rejection). Anything
that prevents the case from being evaluated - a missing file, invalid JSON,
invalid UTF-8, an unreadable path, a non-object schema root, or an exception
raised by the validation code - is a harness failure. It is printed as
`HARNESS-FAIL` and always fails the case, so a deleted or corrupted negative
fixture can never be silently scored as a passing integrity check.

## Pull Request Guidelines

A good PR should:

- be small and focused,
- explain the DI boundary it affects,
- avoid unrelated refactoring,
- keep language protocol-like rather than marketing-heavy,
- update examples or fixtures if schemas change,
- pass the fixture validator.

## Suggested PR Description

```md
## Summary

Explain what changed.

## DI Boundary

Explain whether this affects capabilities, limitations, constraints, examples, fixtures, or validation.

## Validation

- [ ] `python scripts/validate-fixtures.py` passes
- [ ] `python -m unittest discover -s tests` passes

## Notes

Mention any open questions or trade-offs.
```

## Writing Style

Prefer:

- precise language,
- explicit boundaries,
- concrete examples,
- small claims,
- reviewable definitions.

Avoid:

- vague intelligence claims,
- product marketing,
- overbroad architecture,
- promises of execution,
- claims that DI replaces human judgment.

## Relationship to DIF and DRP

Use this framing:

```text
DIF → clarify intent
DI  → clarify limits
DRP → commit decision
```

DI should not absorb DIF or DRP.

The separation is part of the protocol design.
