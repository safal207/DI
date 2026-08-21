# Decision & Transition Integrity Stack v0.2

Status: Draft architecture evolution

v0.2 preserves the existing DIF / DI / DRP / TIP protocol boundaries and makes two previously implicit integration seams explicit:

1. **Strategy** between feasibility and commitment;
2. **Path Revalidation** between commitment and transition.

Neither seam is a fifth protocol. They are cross-stack integrity boundaries.

## Canonical line

```text
Signal
→ Intent
→ Feasibility
→ Strategy
→ Decision
→ Path Revalidation
→ Transition
→ Review
→ Next State
```

Operationally:

```text
Хочу
↓
Можно?
↓
КАКИМИ СПОСОБАМИ?
↓
Какой путь выбираем?
↓
Решили
↓
Выбранный путь всё ещё возможен?
↓
Как перейти по выбранному пути?
↓
Что реально выполнили?
↓
Что реально изменилось?
↓
Можно ли доверять доказательству сейчас?
↓
Новое доказанное состояние
↓
Следующий цикл
```

## Responsibility map

```text
DIF               → confirmed human intent
DI                → feasibility boundary + feasible paths
Strategy          → path comparison, trade-offs, non-binding recommendation
DRP               → committed path and decision history
Path Revalidation → proof that the committed path remains usable now
TIP               → justified transition along the still-valid committed path
```

The later recovery and execution-integrity layers remain orthogonal:

```text
Recovery Decision Matrix
→ Use-Time Authority
→ Execution Receipt
→ State Effect Receipt
→ Fresh Review
→ Next State
```

## Two HOWs

### Strategic HOW

```text
Feasibility
→ what feasible methods exist?
→ what are their trade-offs?
```

This happens before commitment.

### Transition HOW

```text
Committed + revalidated path
→ how does the system safely move from current state to target state along this path?
```

This happens after commitment.

They must not collapse:

```text
strategic HOW ≠ transition HOW
```

## Path identity handoff

v0.1 effectively had:

```text
DI.feasibility_id
→ DRP.feasibility_id
```

v0.2 makes path identity inspectable:

```text
DI.feasible_paths[].path_id
→ Strategy.candidate_path_ids
→ DRP.selected_path_id
→ Path Revalidation.selected_path_id
→ TIP.selected_path_id
```

The central identity invariant is:

```text
TIP.selected_path_id
== Path Revalidation.selected_path_id
== DRP.selected_path_id
```

## Decision drift rule

A committed path may stop being feasible after the decision was recorded.

Example:

```text
DRP selected B
↓
reality changes
↓
B becomes invalid
```

This does **not** authorize TIP to choose C.

Invalid:

```text
DRP = B
Path Revalidation(B) = invalid
TIP = C
```

Correct behavior:

```text
DRP = B
↓
Path Revalidation(B) = invalid | unknown
↓
TIP = blocked
↓
fresh DI assessment
↓
fresh Strategy comparison
↓
new DRP
↓
new DRP supersedes old DRP
↓
new Path Revalidation
↓
new TIP
```

This preserves the distinction:

```text
feasibility changed
≠
decision changed automatically
```

The old decision remains part of history. The replacement decision explicitly carries:

```text
new_drp.supersedes_record_id == old_drp.record_id
```

See:

```text
docs/decision-drift-replanning.md
schemas/decision-replan-chain.schema.json
scripts/validate-decision-replan.py
```

## Non-collapse rules

```text
Intent ≠ Feasibility
Feasibility ≠ Strategy
Strategy ≠ Decision
Decision ≠ Path Revalidation
Path Revalidation ≠ Transition
Transition ≠ Execution
Execution ≠ Outcome
Outcome evidence ≠ current authority
Fresh evidence ≠ proof of causality
```

## Machine-readable contract

Strategy-bearing envelopes use:

```text
schemas/decision-transition-envelope-v0.2.schema.json
```

Semantic validation uses:

```text
scripts/validate-strategy-binding.py
scripts/validate-decision-replan.py
```

Examples:

```text
fixtures/valid-decision-transition-envelope-v0.2-strategy.json
fixtures/invalid-decision-transition-envelope-v0.2-tip-path-mismatch.json
fixtures/invalid-decision-drift-silent-reroute.json
fixtures/valid-decision-replan-chain.json
fixtures/invalid-decision-replan-without-supersession.json
```

## Compatibility

The existing v0.1 envelope remains valid for historical fixtures and existing integration examples.

v0.2 is an additive architecture evolution for flows where path synthesis, path identity, and post-commit path validity must be explicit.

Protocol repositories remain authoritative for their own semantics. This cross-stack note does not redefine DIF, DI, DRP, or TIP internally.

## Summary

The missing joints are now explicit:

```text
МОЖНО?
↓
КАК?
↓
РЕШИЛИ
↓
ЭТОТ ПУТЬ ВСЁ ЕЩЁ МОЖНО?
↓
ПЕРЕХОД
```

with the stronger invariant:

> Feasibility tells us what can be done. Strategy tells us the available ways. DRP tells us which way was chosen. Path Revalidation proves that choice is still usable now. If it is not, the system must replan and supersede the old decision rather than silently changing the path.
