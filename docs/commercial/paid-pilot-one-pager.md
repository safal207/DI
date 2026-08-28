# Ambiguous Mutation Recovery Verification Pilot

Status: **commercial hypothesis for validation**

## The burning question

> Can your agent prove that a timed-out mutation did not already commit before it tries again?

This matters anywhere one request can create money movement, an order, a refund, a wallet transfer, a subscription change, a smart-contract relay, or another irreversible side effect.

## What we verify

One selected mutation flow is traced across:

```text
intent / requested operation
→ allowed path
→ authority at use time
→ dispatch identity
→ worker ownership / takeover
→ side-effect admission
→ lost or ambiguous acknowledgement
→ commit-state recovery
→ observed final effect
→ permitted next action
```

The pilot tests whether retries, worker takeovers, or timeout recovery can silently create a second effect or drift to a new operation identity.

## Smallest paid scope

One pilot covers:

- one mutation endpoint or workflow;
- one sandbox, test-mode, public contract, or local reproduction environment;
- one primary failure surface;
- one positive trace;
- at least three adversarial mutations;
- one machine-readable PASS/FAIL report;
- one concise remediation and claim-boundary memo.

Examples of primary failure surfaces:

- response lost after commit;
- idempotency-key drift;
- retry after confirmed commit;
- concurrent workers acting on one permission;
- stale worker after lease takeover;
- success claimed without observed state effect.

## Deliverables

```text
1. Flow and trust-boundary map
2. Observable trace adapter or capture recipe
3. Canonical positive fixture
4. Negative / mutation fixtures
5. DI conformance report
6. Reproduction commands
7. Findings and remediation boundary
8. Explicit statement of what was not proven
```

The client retains its private raw evidence. Public reuse, if any, requires separate written approval and sanitization.

## Entry criteria

The pilot starts only when:

- a named technical owner exists;
- the selected flow is agreed in writing;
- a sandbox, test mode, public API contract, or local fixture is available;
- no production secret needs to be shared with us in plaintext;
- expected state transitions and stop conditions are clear;
- the commercial terms are confirmed.

## Stop conditions

Work stops and returns a bounded `BLOCKED` result when:

- authorization is missing;
- production credentials are requested or exposed;
- the observable contract is insufficient to distinguish outcomes;
- the system cannot provide a safe test environment;
- scope expands beyond the selected mutation flow;
- evidence would require misrepresenting an external provider guarantee.

A blocked result still includes the exact missing evidence and smallest safe next step.

## Suggested commercial ladder

These are pricing hypotheses, not market guarantees.

### Calibration — one failure surface

```text
Duration: 1–2 working days
Suggested price: USD 1,500–3,000 fixed
```

Use when the company wants to test whether the method finds a real integrity gap on one flow.

### Verification sprint — one complete mutation flow

```text
Duration: up to 5 working days
Suggested price: USD 5,000–12,000 fixed
```

Adds a broader mutation matrix, adapter hardening, and remediation review.

### Ongoing evidence retainer

```text
Suggested price: USD 8,000–20,000 per month
```

Only after a paid pilot proves recurring value. Possible scope: new flows, release gates, incident traces, and regression packs.

## Payment terms

Recommended default:

```text
50% to start
50% on delivery of the agreed evidence pack
```

For a very small calibration, 100% upfront can be simpler.

No production implementation, unlimited support, or security certification is included unless separately scoped.

## Why the pilot is different from a generic QA review

A generic review may report:

> The API returned 200.

This pilot asks a stronger sequence of questions:

```text
Was this the authorized operation?
Was the same identity preserved through retry?
Which worker was admitted?
Did the side effect commit?
What evidence establishes the final state?
Is another mutation still permitted?
```

## Proof of work

Reference case:

```text
docs/case-study-ambiguous-payment-recovery.md
```

Reproducible evidence:

```text
evidence/ambiguous-payment-sandbox/
```

Published checkpoint:

```text
DI v0.5-draft
```

## Claim boundary

A pilot PASS means the supplied and observed evidence satisfies the selected DI conformance profile.

It does not independently certify:

- external evidence truthfulness;
- exactly-once runtime behavior;
- provider atomicity;
- complete network history;
- regulatory compliance;
- absence of every possible defect.

## One-sentence offer

> We verify one high-risk agent or payment mutation from authorization through ambiguous recovery and observed outcome, then deliver a reproducible trace, adversarial tests, and an explicit PASS/FAIL boundary.
