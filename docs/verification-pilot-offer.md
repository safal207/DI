# Bounded Verification Pilot: Ambiguous Financial Effects

Status: reusable commercial scope

## The burning question

> After a timeout, retry, worker takeover, or lost acknowledgement, can an AI
> agent create a second financial effect while believing it is only recovering
> the first one?

This pilot answers that question against one bounded workflow.

## Who it is for

The scope fits systems that let software agents or distributed workers perform
mutating actions such as:

- payments;
- wallet transfers;
- swaps;
- refunds;
- subscription changes;
- purchasing;
- credit or allowance consumption;
- other stateful API mutations where duplicate effects matter.

## Pilot shape

Typical duration: **1–2 focused working days**, depending on environment access
and the quality of the public or sandbox contract.

The pilot is intentionally narrow:

```text
one mutation flow
→ one ambiguity or retry surface
→ one evidence chain
→ one reproducible verdict
```

It is not an open-ended security audit and does not require production access.

## Inputs

The client provides the smallest approved set of inputs:

- public API documentation or a sandbox/test contract;
- one selected mutation flow;
- expected idempotency, lookup, retry, timeout, and terminal-state behavior;
- test-only credentials when required, delivered through an approved secret
  channel rather than committed files or email quotations;
- explicit boundaries for actions that must not be attempted.

Public-contract-only work is possible when credentials are unavailable, but the
claim is then limited to contract analysis and local/simulated evidence.

## What is tested

### 1. Operation identity

```text
Does one intended action retain one stable logical identity across retries,
timeouts, and worker changes?
```

### 2. Effect identity

```text
Can recovery silently mint a new idempotency key, command ID, transaction ID,
or equivalent mutation identity?
```

### 3. Ambiguous commit handling

```text
Is UNKNOWN incorrectly treated as failure, or is commit state recovered from an
authoritative source before another mutation is allowed?
```

### 4. Concurrency and ownership

```text
Can two workers independently believe they may perform the same recovery action?
Are stale workers rejected at the real side-effect boundary?
```

### 5. Execution versus outcome

```text
Does a dispatched request get mistaken for proof that the intended state change
occurred?
```

### 6. Evidence and review

```text
Can the system show which operation was intended, what was admitted, what
committed, which state was observed, and why the next action is allowed?
```

## Deliverables

The pilot produces a compact review package:

1. **Scenario boundary** — exact flow, assumptions, stop conditions, and
   exclusions.
2. **Reproduction steps** — commands or requests needed to replay the case.
3. **Evidence trace** — operation, authority, dispatch, commit, state-effect,
   and review references where available.
4. **Conformance report** — machine-readable `PASS` or `FAIL` against the
   selected DI profile.
5. **Findings** — each issue separated into observed fact, inference, impact,
   and confidence.
6. **Smallest safe remediation direction** — no architecture rewrite unless the
   evidence justifies one.
7. **Residual-risk statement** — what the pilot did not and could not prove.

## Example verdicts

```text
PASS
The represented recovery preserved one logical operation and one stable effect
identity; authoritative evidence resolved the prior commit before another
mutation was considered.
```

```text
FAIL — effect identity drift
A retry after an ambiguous result used a new mutation identity, so the provider
could treat it as a second financial action.
```

```text
BLOCKED — evidence boundary
The API contract does not expose enough authoritative state to distinguish
committed, not committed, and still unknown without privileged evidence.
```

## Safety and confidentiality boundary

- Private findings stay inside the client engagement.
- Reusable knowledge is limited to the generalized failure class and our own
  verification method.
- A competitor is never told which private weakness, architecture, credential,
  customer, or operational detail another company disclosed.
- Test credentials are not committed, quoted into public threads, or included
  in evidence bundles.
- No production mutation is attempted without explicit written authorization.

## What a PASS means

A PASS means the supplied and observed evidence satisfies the selected
conformance profile for the bounded scenario.

## What a PASS does not mean

A PASS does not automatically prove:

- global absence of duplicate effects;
- exactly-once behavior for every code path;
- atomicity of a provider database;
- completeness or truthfulness of every external log;
- production safety outside the tested boundary;
- formal verification of the whole system.

## Why DI is useful here

The pilot does not ask only whether an endpoint returned `200`.

It preserves the entire decision-to-effect chain:

```text
human or system intent
→ feasible and blocked paths
→ committed recovery decision
→ use-time authority
→ single-use dispatch
→ current execution epoch
→ stable logical/effect identity
→ commit resolution
→ observed state effect
→ evidence-backed next action
```

## Engagement options after the pilot

The bounded pilot can end cleanly after delivery. When the result justifies more
work, the next step may be:

- remediation verification;
- a second critical mutation flow;
- CI integration of the conformance profile;
- a reusable trace adapter;
- ongoing QA or engineering work;
- a broader independent verification engagement.

The pilot is useful even when no larger engagement follows because the client
keeps the reproduction, evidence, report, and claim boundary.
