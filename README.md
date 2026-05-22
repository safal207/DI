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

## Minimal Flow

```text
Raw signal / request
→ DIF: clarify intent
→ DI: clarify capabilities, limitations, constraints, and feasible paths
→ DRP: record the committed decision
```

## Status

Draft / seed repository.

This repository preserves DI as a narrow, clean concept: a layer for understanding capabilities, limitations, constraints, and feasibility before decisions become commitments.
