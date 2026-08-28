# Evidence-Led Outreach Templates

Status: **ready to adapt; do not mass-send unchanged**

These templates sell a bounded verification problem, not confidential information about other companies.

## Core rule

We may reuse:

- a generalized failure class;
- our own method;
- public contracts;
- sanitized evidence we are authorized to publish.

We do not reuse:

- another company's private findings;
- non-public architecture details;
- credentials;
- customer data;
- claims that a named company uses or endorses DI without evidence.

## Cold email — product / engineering lead

**Subject:** What happens if the mutation commits but your agent loses the answer?

Hi {{Name}},

What prevents {{Company}}'s agent from creating a second effect when a payment or other mutation commits but the acknowledgement is lost?

I built a small provider-neutral conformance case around that exact boundary:

```text
one logical operation
→ one stable effect identity
→ acknowledgement lost
→ authoritative state recovery
→ no second mutation
```

The reference sandbox produces one stored effect, zero duplicates, a machine-readable DI v0.5 PASS report, and six adversarial mutations that must fail.

I am selecting a small number of teams for a bounded verification pilot: one sandbox/test-mode mutation flow, one failure surface, reproducible evidence, and an explicit claim boundary. No production credentials and no transfer of private findings between companies.

Would it be useful to test one {{Company}} flow where timeout, retry, or worker takeover could create a duplicate or misreported outcome?

Best,
Aleksey Safonov

## Short version

**Subject:** Can a timeout create a second effect?

Hi {{Name}},

I am testing one narrow question across agent/payment systems:

> Can the system prove a timed-out mutation did not already commit before it acts again?

The open-source reference case records one commit, a lost acknowledgement, authoritative recovery, zero duplicates, and six rejected unsafe mutations.

I can apply the same bounded method to one {{Company}} sandbox/test-mode flow and return a reproducible PASS/FAIL evidence pack. No production secrets and no reuse of another company's private findings.

Is that failure surface relevant to your current architecture?

## Follow-up after no reply

**Subject:** Re: Can a timeout create a second effect?

Hi {{Name}},

One concrete version of the question:

```text
mutation accepted
→ response lost
→ local state unknown
→ retry begins
```

At that moment, what evidence binds the retry to the original effect rather than a new one?

I have a reproducible reference trace and mutation suite for this boundary. A small pilot would stay limited to one agreed flow and one sandbox/test-mode environment.

Should I close the loop, or is there an owner for payment/agent execution integrity who would recognize this risk?

## Hiring manager version

**Subject:** QA proof of work for timeout, retry, and duplicate-effect risk

Hi {{Name}},

I am applying for {{Role}} because the product's stateful backend/payment surface matches the work I have been building publicly.

DI v0.5 is a Python conformance toolkit that checks whether an operation preserves intent, authority, dispatch identity, commit recovery, and observed state. Its reference sandbox commits one payment effect, intentionally loses the response, recovers the authoritative state, and prevents another mutation. The valid trace passes; six unsafe mutations fail in CI.

My strongest background is manual/backend/API QA and system analysis. I use this project as proof of how I reason about idempotency, retries, timeouts, state transitions, and evidence boundaries—not as a claim of automation experience I do not have.

Would this approach be useful for the failure paths in {{Company}}'s product?

## Existing technical thread — new evidence

Hi {{Name}},

Since the earlier note, I turned the ambiguous-commit question into a reproducible provider-neutral case rather than another conceptual proposal.

Current evidence:

```text
stored effects: 1
duplicate effects: 0
lost acknowledgement: true
authoritative recovery: committed
DI v0.5: PASS
unsafe mutations rejected: 6 / 6
```

The next useful step would be one bounded comparison against a public or sandbox {{Company}} flow. I would keep provider guarantees, observed facts, my interpretation, and remaining assumptions separate.

Is there one mutation path where you would most want this boundary tested?

## Ethical competitive-scarcity wording

Use only when multiple real conversations or pilots exist:

> I am exploring this failure surface with a small number of teams in the category and selecting one or two flows for deeper implementation. Each team's evidence remains private; only the provider-neutral method and independently publishable material are reused.

Do not say:

> We leaked this to your competitors.

That destroys trust and makes every future client assume its own evidence will be disclosed.

## Reply to interest

Thanks, {{Name}}.

To keep this small and useful, I suggest we choose exactly one mutation flow and answer five questions first:

1. What is the stable operation/effect identity?
2. What can make local commit state ambiguous?
3. Which recovery actions are permitted for committed, not committed, and unknown states?
4. What evidence establishes the final business state?
5. What sandbox/test-mode access is available without sharing production secrets?

I will then return a one-page scope with stop conditions, deliverables, and a fixed pilot price.

## Reply when asked for a free audit

I can review the public contract enough to determine whether a bounded pilot is feasible, but I do not start an open-ended audit or production investigation for free.

The smallest paid calibration covers one selected failure surface, one reproducible trace, adversarial mutations, and a PASS/FAIL boundary. If the public contract is insufficient, the output is a precise `BLOCKED` result with the missing evidence rather than invented certainty.

## Reply when asked for production credentials

I do not need or accept production credentials in plaintext.

The safe options are:

- sandbox/test mode;
- a client-run capture script producing sanitized evidence;
- public API contracts and fixtures;
- a locally generated trace reviewed by the client before sharing.

If none of those can support the selected claim, the pilot should stop rather than weaken the evidence boundary.

## Closing question library

Use one question, not all at once:

- What proves a timeout did not already commit?
- What binds every retry to the same effect identity?
- Can two workers consume one mutation permission?
- What rejects the stale worker after takeover?
- Does a 200 response prove the intended business state?
- Which evidence permits the next irreversible action?
- Where does `unknown` become `not_committed`, and what authorizes that conclusion?

## Personalization checklist

Before sending, replace generic language with one verified public detail:

```text
company feature
+ public API / docs term
+ relevant failure surface
+ one bounded question
+ one proof link
+ one next step
```

Do not invent architecture or performance claims.
