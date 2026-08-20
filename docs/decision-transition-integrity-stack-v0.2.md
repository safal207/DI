# Decision & Transition Integrity Stack v0.2

Status: Draft architecture evolution

v0.2 preserves the existing DIF / DI / DRP / TIP protocol boundaries and makes one previously implicit integration step explicit: **Strategy** between feasibility and commitment.

Strategy is not a fifth protocol. It is the cross-stack reasoning seam that answers the first HOW question without silently making the final decision.

## Canonical line

```text
Signal
→ Intent
→ Feasibility
→ Strategy
→ Decision
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
DIF      → confirmed human intent
DI       → feasibility boundary + feasible paths
Strategy → path comparison, trade-offs, non-binding recommendation
DRP      → committed path and decision history
TIP      → justified transition along the committed path
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
Committed path
→ how does the system safely move from current state to target state along this path?
```

This happens after commitment.

They must not collapse:

```text
strategic HOW ≠ transition HOW
```

## New handoff

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
→ TIP.selected_path_id
```

The central invariant is:

```text
TIP.selected_path_id == DRP.selected_path_id
```

If the path must change after commitment, the system returns to a new decision boundary. It does not silently substitute another path inside TIP or execution.

## Non-collapse rules

```text
Intent ≠ Feasibility
Feasibility ≠ Strategy
Strategy ≠ Decision
Decision ≠ Transition
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
```

Examples:

```text
fixtures/valid-decision-transition-envelope-v0.2-strategy.json
fixtures/invalid-decision-transition-envelope-v0.2-tip-path-mismatch.json
```

## Compatibility

The existing v0.1 envelope remains valid for historical fixtures and existing integration examples.

v0.2 is an additive architecture evolution for flows where path synthesis and path identity must be explicit.

Protocol repositories remain authoritative for their own semantics. This cross-stack note does not redefine DIF, DI, DRP, or TIP internally.

## Summary

The missing joint is now explicit:

```text
МОЖНО?
↓
КАК?
↓
РЕШИЛИ
```

with the stronger invariant:

> Feasibility tells us what can be done. Strategy tells us the available ways. DRP tells us which way was actually chosen. TIP must then preserve that choice through the transition.
