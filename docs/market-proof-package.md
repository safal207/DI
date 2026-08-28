# DI v0.5 Market Proof Package

Status: reusable positioning based on the executable sandbox case

This document turns one technical result into three honest market paths:

```text
proof of work for a role
+
bounded paid verification pilot
+
reusable conformance tooling
```

The technical source is:

- [`Recovering an Ambiguous Payment Without Creating a Duplicate Effect`](case-study-deterministic-ambiguous-payment-recovery.md)
- [`artifacts/sandbox/conformance-report.json`](../artifacts/sandbox/conformance-report.json)
- [`scripts/validate-sandbox-case.py`](../scripts/validate-sandbox-case.py)

## One-sentence value

> DI makes the chain from intended action to observed effect inspectable, so a
> timeout, retry, takeover, or missing acknowledgement cannot silently become a
> second mutation permission.

## Proof-of-work positioning for jobs

Use this version for payments, FinTech, wallet, backend, Web3, or agent-safety
roles:

> I built a provider-neutral conformance case for ambiguous payment recovery. It
> simulates a committed effect whose acknowledgement is lost, recovers the
> authoritative state, proves that same-key replay preserves one effect, and
> rejects six corrupted traces such as effect-key drift, retry after commit, and
> success without state evidence. The project is intentionally honest about its
> boundary: it validates evidence semantics rather than claiming an external
> exactly-once runtime.

### Evidence to show

```text
case study
→ executable sandbox
→ canonical trace
→ PASS report
→ negative mutations
→ green CI
```

### What not to claim

Do not say:

- “I formally proved Stripe is exactly once.”
- “This prevents every duplicate payment.”
- “Crossmint, Valta, or another provider uses DI.”
- “The deterministic sandbox is production evidence.”

Say instead:

> The sandbox proves that the method and validator distinguish the intended
> recovery chain from targeted integrity breaks. A provider sandbox trace is the
> next evidence level.

## Paid-pilot positioning

Opening question:

> When your agent loses a response after a financial mutation, what evidence
> stops it from creating a second effect under a new request identity?

Concise offer:

> I can run a bounded 1–2 day verification on one mutation flow. The output is a
> reproducible trace, machine-readable PASS/FAIL report, findings separated from
> inference, and the smallest safe remediation direction. No production action
> or sensitive architecture disclosure is required.

Use the full scope in [`verification-pilot-offer.md`](verification-pilot-offer.md).

## Product positioning

The reusable product direction is not an execution engine. It is a conformance
boundary:

```text
system emits trace
→ DI profile validates identity and evidence continuity
→ JSON PASS / FAIL report
→ CI stores or gates on the result
```

### First practical wedge

```text
Ambiguous Mutation Recovery Check
```

Input:

- one trace representing operation identity, dispatch, execution, commit
  observations, state effect, and review.

Output:

- `PASS` when the chain preserves the selected profile;
- `FAIL` with precise semantic errors when identity, authority, effect, or
  evidence continuity breaks.

### Buyers who may care

- agent-payment platforms;
- wallet infrastructure;
- payment orchestration teams;
- AI-agent frameworks with mutating tools;
- QA and reliability teams;
- compliance or audit teams that need replayable evidence;
- distributed workflow systems where ownership can transfer.

## Competitive-market wording

It is legitimate to create scarcity around our limited verification capacity.
It is not legitimate to trade one company's private findings to another.

Safe wording:

> We are validating this failure surface across a small number of architectures
> in the category and selecting one or two flows for deeper implementation. The
> reusable method is shared; private findings remain isolated to each team.

Unsafe wording:

> We found your competitor's weakness and will tell you what it is.

The first creates honest market competition for a bounded capability. The
second destroys trust and future deal value.

## Three calls to action

### Employment

> Would this evidence-first approach be useful for the payment, wallet, or
> backend flows your QA team considers highest risk?

### Verification pilot

> Which single timeout/retry/takeover flow would be most expensive if it created
> a duplicate effect?

### Tool integration

> Can your system emit enough operation, execution, commit, and state evidence
> to run one DI conformance profile in CI?

## Decision rule

Do not customize twenty generic pitches.

For each target company:

```text
read its public contract
→ identify one relevant mutation failure surface
→ choose one proof artifact
→ ask one burning question
→ propose one bounded next step
```

The sandbox is a proof that the method runs. The next commercial value comes
from testing the client's own bounded flow and preserving a trustworthy claim
boundary.
