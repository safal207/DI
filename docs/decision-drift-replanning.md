# Decision Drift and Explicit Replanning

## Core rule

A committed path becoming invalid does **not** authorize the system to silently choose another path.

```text
committed path B
→ B becomes invalid or unknown
→ TIP is blocked
→ fresh DI feasibility assessment
→ fresh Strategy comparison
→ new DRP decision
→ new DRP explicitly supersedes old DRP
→ TIP follows the new selected path
```

Child-simple version:

> If the road you chose gets closed, do not secretly take another road. Stop, look at the map again, choose again, record the new choice, then continue.

## Why this matters

Without an explicit replan boundary, a system can preserve the appearance of decision continuity while changing the actual action underneath it:

```text
DRP selected B
B later becomes impossible
TIP executes C
```

That is decision drift.

The problem is not that C is necessarily bad. The problem is that C was never the committed path.

## Path revalidation seam

Decision & Transition Integrity Envelope v0.2 adds a `path_revalidation` seam between DRP and TIP.

```text
DRP
→ path_revalidation
→ TIP
```

Binding:

```text
path_revalidation.decision_record_id == drp.record_id
path_revalidation.selected_path_id == drp.selected_path_id
```

A revalidation must carry evidence.

### Valid

```text
status = valid
→ TIP may continue the exact DRP-selected path
```

### Invalid or unknown

```text
status = invalid | unknown
→ TIP.status = blocked
→ no path substitution
→ replan required
```

The old TIP path identity remains attached to the old decision even while blocked. This prevents a blocked transition from being rewritten into a different action.

## Replanning chain

The compact machine-checkable replan chain is defined by:

- `schemas/decision-replan-chain.schema.json`
- `scripts/validate-decision-replan.py`

Canonical continuity:

```text
old DRP(B)
→ path B invalidated
→ fresh DI assessment F2
→ fresh Strategy S2
→ new DRP(C)
→ new DRP.supersedes_record_id = old DRP.record_id
→ TIP(C)
```

The replacement path must be present in the fresh DI feasible set and in the Strategy candidate set.

The replacement TIP path must exactly equal the replacement DRP selected path.

## Supersession, not mutation

The old decision remains true as history:

```text
D1: selected B under conditions at t1
```

The new decision says:

```text
D2: selected C after B became invalid at t2
D2 supersedes D1
```

Never rewrite D1 to pretend it selected C.

This preserves causal memory:

```text
what was known
→ what was selected
→ what changed
→ why replanning happened
→ what replaced the old commitment
```

## Negative case: silent reroute

Invalid:

```text
D1 selected B
B revalidation = invalid
TIP selected C and status = committed
```

Expected result:

```text
FAIL
```

Because:

```text
invalid path ≠ permission to choose another path
```

## Negative case: missing supersession

Invalid:

```text
D1 invalidated
D2 selects C
D2.supersedes_record_id != D1.record_id
```

Expected result:

```text
FAIL
```

A replacement decision without the causal supersession link is an orphan decision.

## Principle

```text
Feasibility changed
≠
Decision changed automatically
```

Instead:

```text
Feasibility changed
→ stop
→ reassess
→ compare
→ recommit
→ transition
```

Or in one sentence:

> When reality invalidates a committed path, return to reasoning; never let execution silently rewrite the decision.
