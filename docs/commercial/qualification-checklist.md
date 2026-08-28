# Verification Pilot Qualification Checklist

Status: **go / conditional / no-go gate**

Use this before spending deep technical time on a prospect.

## Fast score

Give one point for each `yes`:

1. Does the product perform a state-changing operation?
2. Can timeout, retry, concurrency, takeover, or delayed evidence make the result ambiguous?
3. Could a duplicate or incorrect state have material business impact?
4. Is there a sandbox, test mode, public contract, or local fixture?
5. Is there a named technical owner?
6. Can the team provide sanitized evidence without sharing production secrets?
7. Is the team willing to define one bounded flow?
8. Is there a budget or hiring need connected to the problem?

Interpretation:

```text
7–8 points → high-priority paid pilot / role
5–6 points → conditional; clarify missing boundary
3–4 points → research only, no deep unpaid work
0–2 points → no-go
```

## Problem fit

High-fit mutation types:

- payment authorization, capture, settlement, or refund;
- wallet transfer or agent spending;
- order or subscription creation;
- smart-contract relay or off-chain settlement;
- account state mutation;
- workflow/tool execution with irreversible side effects;
- job dispatch across multiple workers;
- incident rollback or compensating action.

Strong signals:

- documented idempotency keys;
- webhooks or asynchronous status;
- retries after timeouts;
- multiple workers or agents;
- leases, locks, or leader election;
- eventual consistency;
- provider/local state reconciliation;
- audit or evidence requirements.

## Evidence fit

At least one must exist:

- public API specification;
- sandbox or test mode;
- reproducible local environment;
- client-run sanitized capture;
- existing failing fixture;
- incident trace with permission to analyze;
- state-machine or business-rule documentation.

A verbal promise alone is not evidence.

## Authority and privacy fit

Required:

- explicit permission to test the selected environment;
- no request for unauthorized access;
- no production secret sent by email or chat;
- no customer data needed for the pilot;
- public attribution rules agreed before publication;
- private findings remain private.

Automatic no-go:

- request to bypass access controls;
- request to test production without authorization;
- request to use leaked credentials;
- request to disclose a competitor's private finding;
- request to guarantee security or exactly-once behavior without evidence.

## Commercial fit

Ask:

- Who owns the problem?
- What is the business consequence of a duplicate or unknown result?
- What decision will the pilot support?
- Is this a hiring evaluation, a fixed pilot, or a product purchase?
- What is the approved budget range?
- Who can approve scope and payment?
- What is the latest useful delivery date?

Weak signal:

> Interesting research—please audit everything first, then we will decide whether it has value.

Strong signal:

> Here is one flow, one sandbox, one owner, one decision, and an approved paid calibration.

## Scope lock

Before starting, write:

```text
Selected flow:
Starting state:
Intended effect:
Stable operation identity:
Primary failure surface:
Allowed evidence sources:
Blocked evidence sources:
Expected target state:
Stop conditions:
Deliverables:
Price:
Payment dates:
Private/public boundary:
```

No work starts until the other party confirms the scope.

## Pilot outcome states

### PASS

The supplied trace satisfies the selected profile and no tested mutation crosses the defined boundary.

### FAIL

A reproducible trace or mutation violates a named invariant.

### BLOCKED

The evidence is insufficient to resolve the selected claim safely.

### OUT OF SCOPE

The finding concerns a different flow or requires a new agreement.

`BLOCKED` is not failure to deliver. It is the correct result when evidence cannot support a stronger claim.

## Expansion gate

Expand only when the first pilot produces at least one of:

- a material reproducible finding;
- a useful release gate;
- a reusable adapter;
- a regression pack the team wants maintained;
- a clear reduction in investigation time;
- a hiring decision based on demonstrated fit.

Do not expand merely because more architecture is imaginable.

## Final go/no-go decision

```text
GO
→ bounded flow + safe evidence + owner + money/decision

CONDITIONAL
→ one missing item with a concrete resolution date

NO-GO
→ unsafe access, no evidence path, no owner, or indefinite unpaid scope
```
