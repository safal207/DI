# Decision & Transition Integrity Stack v0.2

Status: Draft architecture evolution

v0.2 preserves the existing DIF / DI / DRP / TIP protocol boundaries and makes two previously implicit decision/transition seams explicit:

1. **Strategy** between feasibility and commitment;
2. **Path Revalidation** between commitment and transition.

The execution-integrity line is also strengthened with **Single-Use Authority Consumption** between use-time authority and automated execution.

None of these seams is a fifth protocol. They are cross-stack integrity boundaries.

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
→ Authority Consumption
→ Execution Receipt
→ State Effect Receipt
→ Fresh Review
→ Next State
```

The new distinction is:

```text
authority valid now
≠
authority still available for another use
```

For automated `SAFE_RETRY` and `ROLLBACK`, use-time validity must therefore be followed by durable single-use consumption before execution.

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

## Single-use authority rule

A valid use-time authority check can still be unsafe if two workers race to use the same recovery decision.

Invalid:

```text
Recovery Decision D
↓
authority active
↓
worker A → token A → dispatch A
worker B → token B → dispatch B
```

Different tokens do not create two permissions.

For automated mutation the single-use scope is:

```text
(
  authority_id,
  authority_generation,
  recovery_decision_id,
  bound_execution_mode
)
```

At most one successful consumption is allowed for that scope.

Execution must then bind to the exact consumption receipt, `use_token`, and `dispatch_id`.

See:

```text
docs/authority-consumption-binding.md
schemas/authority-consumption-receipt.schema.json
scripts/validate-authority-consumption.py
```

## Non-collapse rules

```text
Intent ≠ Feasibility
Feasibility ≠ Strategy
Strategy ≠ Decision
Decision ≠ Path Revalidation
Path Revalidation ≠ Transition
Transition ≠ Execution
Use-Time Authority ≠ Authority Consumption
Authority Consumption ≠ Execution
Execution ≠ Outcome
Outcome evidence ≠ current authority
Fresh evidence ≠ proof of causality
```

## Machine-readable contract

Strategy-bearing envelopes use:

```text
schemas/decision-transition-envelope-v0.2.schema.json
```

Execution-integrity artifacts include:

```text
schemas/use-time-authority-receipt.schema.json
schemas/authority-consumption-receipt.schema.json
schemas/execution-receipt.schema.json
```

Semantic validation uses:

```text
scripts/validate-strategy-binding.py
scripts/validate-decision-replan.py
scripts/validate-authority-binding.py
scripts/validate-authority-consumption.py
```

Examples:

```text
fixtures/valid-decision-transition-envelope-v0.2-strategy.json
fixtures/invalid-decision-transition-envelope-v0.2-tip-path-mismatch.json
fixtures/invalid-decision-drift-silent-reroute.json
fixtures/valid-decision-replan-chain.json
fixtures/invalid-decision-replan-without-supersession.json
fixtures/valid-authority-consumption.json
fixtures/invalid-authority-replayed-use-token.json
fixtures/invalid-authority-double-consume-same-decision.json
```

## Atomicity boundary

The consumption receipt is evidence, not a runtime lock by itself.

A production implementation should atomically claim the single-use scope and create/claim the dispatch record at the side-effect boundary whenever possible.

If that cannot be one transaction, the safer order is:

```text
durable consume
→ persist unique dispatch_id
→ dispatch
→ retry by recovering the same dispatch_id
```

Writing a consumption receipt only after dispatch does not close the concurrency race.

## Compatibility

The existing v0.1 envelope remains valid for historical fixtures and existing integration examples.

v0.2 is an additive architecture evolution for flows where path synthesis, path identity, post-commit path validity, and safe automated mutation must be explicit.

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
↓
РАЗРЕШЕНИЕ ЕЩЁ ДЕЙСТВУЕТ?
↓
ЕГО ЕЩЁ НЕ ИСПОЛЬЗОВАЛИ?
↓
ИСПОЛНЕНИЕ
```

with the stronger invariants:

> Feasibility tells us what can be done. Strategy tells us the available ways. DRP tells us which way was chosen. Path Revalidation proves that choice is still usable now. If it is not, the system must replan and supersede the old decision rather than silently changing the path.

> Use-time authority proves permission is valid now. Authority Consumption proves that one automated mutation right has been claimed exactly once before dispatch.
