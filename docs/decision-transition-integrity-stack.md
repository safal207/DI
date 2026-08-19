# Decision & Transition Integrity Stack v0.1

Status: Architecture note

This document describes how four independent projects can cooperate without collapsing their boundaries:

- **DIF — DeepIntent Funnel**
- **DI — Doability Intelligence**
- **DRP — Decision Record Protocol**
- **TIP — Transition Intelligence Protocol**

The stack is an integration architecture, **not a fifth protocol**. Each repository remains authoritative for its own semantics, schemas, validators, and lifecycle rules.

## One-line model

```text
Signal
→ Intent
→ Feasibility
→ Decision
→ Transition
→ Review
→ Next State
```

The corresponding project responsibilities are:

```text
Raw Signal
   ↓
DIF — clarify human intent
   ↓
Confirmed Intent
   ↓
DI — clarify capabilities, limitations, constraints, and feasible paths
   ↓
Decision Boundary
   ↓
DRP — preserve the committed decision, rationale, dependencies, and supersession
   ↓
Committed Action Context
   ↓
TIP — reason about the justified state transition and review what happened
   ↓
Observed Next State
```

## Why the stack exists

Many systems compress several different questions into one step:

> “The user asked for X, so execute X.”

That hides four independent failure surfaces:

1. the system may misunderstand what the human meant;
2. the requested action may be impossible, unsafe, forbidden, or underspecified;
3. the final decision may lose its rationale and causal history;
4. the action may create a transition that is unsafe, ambiguous, or different from the intended one.

The stack separates those questions before they become one opaque action.

## Protocol boundaries

### DIF — intention boundary

DIF asks:

> What does the human actually mean, and has the human confirmed that interpretation?

DIF turns raw expression into a human-confirmed intent. It must not claim final authority over a person's intention.

Typical output:

```text
confirmed_intent
+ relevant context
+ unresolved ambiguity
```

DIF does **not** decide whether the intent is feasible.

### DI — feasibility boundary

DI asks:

> What can and cannot be done under the current capabilities, permissions, constraints, risks, and unknowns?

DI maps:

- capabilities;
- limitations;
- permissions;
- safety constraints;
- reversibility;
- unknowns;
- feasible paths;
- blocked actions.

Typical output:

```text
feasible
blocked
conditionally feasible
unknown
```

DI does **not** make or preserve the final committed decision.

### DRP — commitment boundary

DRP asks:

> What was decided, why, what did it depend on, and what later superseded it?

DRP begins when a decision becomes a commitment worth preserving beyond the immediate conversation or tool run.

It records:

- stable decision identity;
- rationale;
- causal links;
- dependencies;
- responsibility;
- supersession.

DRP does **not** execute the decision and does not determine whether the resulting transition was safe or successful.

### TIP — transition boundary

TIP asks:

> Given a trusted starting state and a decision/action context, what transition is justified next, and what was actually observed after the action?

TIP reasons over:

```text
State
→ Tension
→ Cause
→ Transition
→ Cooperation
→ Action
→ Review
→ Next State
```

TIP is adjacent to the decision stack. It does not replace DIF, DI, or DRP.

TIP may consume a trusted starting state produced elsewhere. When TIP uses its own IFP readiness flow, the canonical TIP/IFP handoff rules remain authoritative inside the TIP repository.

## Canonical architecture

```text
                        ┌──────────────────────────────┐
                        │              TIP             │
                        │                              │
                        │ State → Transition → Action  │
                        │          → Review → Next     │
                        └──────────────▲───────────────┘
                                       │
Raw Signal → DIF → Confirmed Intent → DI → Decision Boundary → DRP
                 intent clarified      limits clarified    decision preserved
                                       │
                                       └── blocked / conditional / feasible
```

A more operational view:

```text
1. DIF
   “What is being asked?”

2. DI
   “Can it be done, under what constraints, and what must not be attempted?”

3. DRP
   “What did we commit to and why?”

4. TIP
   “What transition does that commitment justify now, and what happened after action?”
```

## Handoff contracts

The stack should not rely on vague prose such as “the next system knows what the previous one meant.”

Each boundary should preserve a minimal inspectable handoff.

### DIF → DI

Minimum handoff:

```text
confirmed_intent_id
intent_summary
human_confirmation
relevant_context
known_ambiguities
```

Invariant:

> DI must evaluate the confirmed intent, not silently reinterpret the original raw signal.

### DI → DRP

Minimum handoff:

```text
feasibility_assessment_id
allowed_paths
blocked_paths
constraints
critical_unknowns
decision_readiness
```

Invariant:

> A committed decision must not silently exceed the feasibility boundary that justified it.

### DRP → TIP

Minimum handoff:

```text
record_id
committed_decision
rationale_reference
constraints_carried_forward
starting_state_reference
```

Invariant:

> TIP must reason about the transition authorized by the committed decision, not a mutated or broader action.

### TIP → Review / next cycle

Minimum review output:

```text
observed_action
observed_consequence
evidence_references
next_state
remaining_uncertainty
```

The observed next state may become new input for another decision cycle.

## Non-collapse rules

The following distinctions are intentional:

```text
DIF ≠ DI
DI  ≠ DRP
DRP ≠ TIP
TIP ≠ execution engine
```

More specifically:

- intent confirmation is not feasibility;
- feasibility is not authorization;
- authorization is not execution;
- execution is not proof of intended outcome;
- observed outcome is not automatic proof of causality;
- a new state does not silently rewrite the decision that produced it.

## End-to-end invariant

A healthy end-to-end chain should make this inspectable:

```text
human-confirmed intent
→ bounded feasible path
→ explicit committed decision
→ action faithful to that decision
→ observed transition
→ evidence-backed review
→ explicit next state
```

The stack fails integrity if any link silently changes meaning, scope, authority, or observed outcome.

## Anonymous financial walkthrough

This example is intentionally provider-neutral. It is not a claim about any specific company or product.

### Scenario

An autonomous agent submits a financial transaction. The client times out before it can determine whether the transaction was accepted.

A naive system may immediately retry.

A decision-and-transition-integrity flow handles the ambiguity in stages.

### 1. DIF — clarify intent

Raw signal:

```text
“The payment timed out. Try again.”
```

Possible meanings include:

- create a second payment;
- recover the status of the first payment;
- ensure the intended purchase completes exactly once.

Human-confirmed intent:

```text
Ensure the intended payment reaches one correct terminal outcome without creating an unintended duplicate financial action.
```

DIF prevents the phrase “try again” from being treated as automatic permission to duplicate execution.

### 2. DI — clarify limits

DI evaluates the environment:

Known capabilities:

- transaction creation exists;
- transaction lookup exists;
- an idempotency primitive may or may not exist;
- settlement evidence may arrive later.

Critical constraints:

- another financial commit may be irreversible;
- commit state is currently unknown;
- retry semantics must be known before another create request is safe.

Feasible paths:

```text
A. recover/read existing transaction state;
B. replay only if the contract provides safe idempotent semantics;
C. wait for stronger evidence if terminality is not yet established.
```

Blocked path:

```text
blindly issue a new non-idempotent payment while prior commit state is unknown
```

### 3. DRP — preserve the decision

Example committed decision:

```text
Do not issue a new financial commit while the original operation remains ambiguous.
Recover the prior operation using the strongest available public contract before authorizing another payment action.
```

The DRP record preserves why:

- duplicate financial execution is a material risk;
- the first operation may already have committed;
- recovery evidence exists or must be obtained first.

If a later policy changes this rule, the new decision supersedes rather than silently overwrites the old record.

### 4. TIP — reason about the transition

Starting state:

```text
payment_requested
+ client_timeout
+ commit_state_unknown
```

Tension:

```text
The desired purchase may be incomplete, but a second financial action may duplicate an already committed operation.
```

Cause:

```text
transport ambiguity prevents the client from knowing the authoritative payment state.
```

Candidate transition:

```text
unknown → established transaction state
```

Smallest justified action:

```text
perform the contract-defined recovery/read operation before any new financial commit
```

Review:

```text
observe terminal/non-terminal state;
record evidence;
only then choose the next action.
```

Next state examples:

```text
SUCCESS_CONFIRMED
FAILED_CONFIRMED
STILL_PENDING
RECOVERY_BLOCKED
```

### What this walkthrough demonstrates

No single protocol owns the entire problem.

```text
DIF protects meaning.
DI protects feasibility boundaries.
DRP protects decision memory and rationale.
TIP protects transition reasoning and review.
```

The value comes from preserving the handoffs between them.

## External validation rule

External companies, products, incidents, and public API contracts are **validation cases**, not members of this stack.

A provider should only be named in a published case study when the evidence and attribution rules for that case are clear.

Safer default:

```text
external scenario
→ anonymous protocol walkthrough
→ validate model usefulness
→ optionally request provider review
→ publish named case only with accurate attribution
```

A project's public behavior may be used as evidence for a protocol example without implying that the external project uses, endorses, integrates, or conforms to DIF, DI, DRP, or TIP.

## Versioning rule

This architecture note may evolve independently from the four protocol repositories.

Changes to this document must not silently redefine normative semantics in DIF, DI, DRP, or TIP.

When a cross-stack rule conflicts with a protocol's canonical specification, the protocol's own repository wins for that protocol.

## Summary

```text
DIF — protect intent.
DI  — protect feasibility.
DRP — protect committed decision history.
TIP — protect transition reasoning and review.
```

Together they form a decision-and-transition integrity architecture:

```text
Signal
→ Intent
→ Feasibility
→ Decision
→ Transition
→ Review
→ Next State
```
