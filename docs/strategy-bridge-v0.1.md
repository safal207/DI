# Strategy Bridge v0.1

Status: Draft cross-stack integration invariant

The Strategy Bridge makes the missing **HOW?** explicit between feasibility and commitment.

It is **not a fifth protocol**. It is an integration seam between DI and DRP.

## Updated decision line

```text
Intent
→ Feasibility
→ Strategy
→ Decision
→ Transition
→ Review
→ Next State
```

In plain language:

```text
ХОЧУ
↓
МОЖНО?
↓
КАКИМИ СПОСОБАМИ?
↓
КАКОЙ ПУТЬ ВЫБИРАЕМ?
↓
РЕШИЛИ
↓
КАК ПЕРЕЙТИ ПО ВЫБРАННОМУ ПУТИ?
```

## Two different HOW questions

There are two different questions that must not collapse into one.

### HOW #1 — strategy synthesis

Before commitment:

> What feasible ways can achieve the confirmed intent, and what are the trade-offs of each?

DI produces bounded feasible paths. Strategy compares those paths using dimensions such as:

- risk;
- cost;
- latency;
- reversibility;
- evidence strength;
- unknowns;
- authority requirements.

Strategy may recommend a path, but recommendation is not commitment.

### HOW #2 — transition realization

After commitment:

> Given the selected path and current state, what justified transition should happen next?

That is TIP's transition problem.

Therefore:

```text
strategic HOW ≠ transition HOW
```

## Responsibilities

```text
DIF
→ clarify what is wanted

DI
→ establish what is feasible
→ enumerate bounded feasible paths

Strategy Bridge
→ compare feasible paths
→ expose trade-offs
→ recommend without committing

DRP
→ select and preserve one committed path

TIP
→ continue exactly that selected path through a justified state transition
```

## Machine-readable path identity

Envelope v0.2 introduces stable path identities.

```text
DI.feasible_paths[].path_id
        ↓
Strategy.candidate_path_ids
        ↓
DRP.selected_path_id
        ↓
TIP.selected_path_id
```

Canonical schema:

```text
schemas/decision-transition-envelope-v0.2.schema.json
```

## Core invariants

A strategy candidate must originate from DI:

```text
Strategy.candidate_path_ids ⊆ DI.feasible_paths.path_id
```

The committed path must have been both feasible and evaluated:

```text
DRP.selected_path_id ∈ DI.feasible_paths.path_id
AND
DRP.selected_path_id ∈ Strategy.candidate_path_ids
```

The transition layer must preserve the committed path exactly:

```text
TIP.selected_path_id == DRP.selected_path_id
```

This is forbidden:

```text
DI offers: A / B / C
Strategy evaluates: A / B / C
DRP commits: B
TIP executes: C
```

The path change is not an implementation detail. It is a new decision and must return through the decision boundary instead of being silently substituted downstream.

## Recommendation is not authority

Strategy may contain:

```text
recommended_path_id = B
```

DRP may still commit A if the decision-maker has a justified reason and A is inside the evaluated feasible set.

The important boundary is:

```text
recommendation ≠ commitment
```

Once DRP commits a path, however, TIP must preserve it unless a later DRP record explicitly supersedes that decision.

## Non-collapse rule

```text
Feasibility ≠ Strategy ≠ Decision ≠ Transition
```

Meaning:

- possible does not mean we know the best way;
- a known way does not mean we selected it;
- a recommendation does not authorize execution;
- a committed path does not permit a different transition path;
- changing the path after commitment requires a new decision, not silent mutation.

## Example

```text
DI
A = read existing transaction
B = verified idempotent replay
C = wait for stronger evidence

Strategy
compare A/B/C
recommend B

DRP
selected_path_id = B

TIP
selected_path_id = B
```

A fixture where TIP silently changes to C is intentionally invalid.

## Updated end-to-end integrity line

```text
Confirmed Intent
→ Feasibility Boundary
→ Feasible Paths
→ Strategy Comparison
→ Committed Path
→ Transition Along That Path
→ Use-Time Authority
→ Observed Execution
→ Observed State Effect
→ Fresh Evidence Review
→ Next State
```

Every arrow is an inspectable handoff rather than an assumption.
