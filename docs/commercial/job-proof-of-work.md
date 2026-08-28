# DI v0.5 as Hiring Proof of Work

Status: **application and interview asset**

## Positioning

DI is not evidence of years of commercial automation experience that do not exist.

It is evidence of a specific engineering capability:

> Reasoning about stateful, high-risk backend mutations where retries, timeouts, worker takeovers, authority, and observed outcomes must stay connected.

The strongest target roles are:

- manual / backend / API QA in payments or FinTech;
- system analyst roles around integrations and stateful workflows;
- Web3 / wallet / smart-contract QA;
- agentic systems QA and safety evaluation;
- product-quality roles where evidence and failure boundaries matter.

## Thirty-second explanation

> I built an open-source conformance toolkit for checking whether a high-risk operation preserves its intent, authority, identity, execution path, and observed result. The v0.5 case focuses on a common payments problem: a mutation commits, its response is lost, and the system must recover the existing effect instead of creating a duplicate. The repository includes a deterministic stateful sandbox, a machine-readable trace, a PASS report, six adversarial mutations, and CI reproducibility checks.

## CV bullet

> Built DI v0.5, a Python-based provider-neutral conformance toolkit for stateful mutation integrity across idempotency, timeout recovery, multi-worker ownership, lease fencing, commit-state resolution, and evidence-backed outcomes; added deterministic sandbox evidence, mutation tests, CLI reports, and CI gates.

## Short application paragraph

> My strongest area is backend/API QA for stateful and financially sensitive flows. I recently published DI v0.5-draft, an open-source conformance toolkit that tests the chain from intended operation and use-time authority through worker ownership, execution, ambiguous commit recovery, and observed state. Its reference sandbox commits one payment effect, intentionally loses the acknowledgement, recovers the authoritative state, and proves that no duplicate effect is created; six unsafe mutations are rejected in CI.

## Payments-role version

> I test a payment as a state machine rather than a single request. A timeout is not proof of failure, a retry is not automatically a new permission, and an API response is not proof of the intended ledger state. DI v0.5 makes those boundaries executable through stable operation identity, commit-outcome receipts, authoritative recovery, state-effect evidence, and adversarial mutation tests.

## Agentic-systems version

> Agent safety becomes concrete at the mutation boundary: what was the agent authorized to do, which worker consumed that authority, what effect identity crossed the boundary, and what evidence permits the next action? DI provides a provider-neutral trace and conformance report for that chain without pretending to be the runtime itself.

## System-analyst version

> DI turns implicit integration assumptions into inspectable contracts: request intent, feasible paths, committed decision, operation identity, state transition, recovery behavior, and observed outcome. This helps expose missing idempotency semantics, ambiguous status models, unsafe retry rules, and gaps between API state and business state.

## Interview story — STAR structure

### Situation

A client or agent sends a financial mutation. The operation may commit, but the response is lost. Retrying blindly can create a duplicate effect.

### Task

Create a provider-neutral, reproducible method that distinguishes transport failure from commit outcome and makes unsafe recovery detectable.

### Action

- modelled one stable logical operation and effect key;
- preserved local uncertainty as `unknown`;
- added authoritative commit observations and resolution rules;
- connected resolution to observed state effect;
- built a deterministic stateful sandbox;
- generated a DI v0.5 trace and CLI report;
- mutated the valid trace in six unsafe ways;
- added CI reproducibility and credential-boundary checks;
- published the `v0.5-draft` checkpoint.

### Result

```text
valid sandbox trace: PASS
stored effects: 1
duplicate effects: 0
unsafe mutations rejected: 6 / 6
```

The honest limitation is that the deterministic case proves the supplied sandbox/trace behavior, not an external provider's exactly-once runtime.

## Technical questions this project helps answer

- What is the difference between transport outcome and commit outcome?
- Why is idempotency key stability important?
- When is a retry safe?
- How should a system handle `unknown` state?
- Why is execution evidence different from outcome evidence?
- How do stale workers create split-brain risk?
- What does a fencing token protect?
- Why must authority be checked at use time?
- How can a test suite prove its negative detection capability?
- What belongs in a provider contract versus a local runtime invariant?

## Portfolio links to lead with

```text
1. README — project and profile ladder
2. Published v0.5-draft release
3. Ambiguous-payment case study
4. Evidence pack
5. Mutation report
6. Conformance CLI
```

## What not to claim

Do not say:

- Stripe uses or endorses DI;
- DI proves exactly-once behavior of external systems;
- the deterministic sandbox is a production integration;
- the project replaces payment-provider idempotency;
- the project proves commercial Playwright/Cypress experience;
- a PASS means the whole product is secure or correct.

## Best closing line in an interview

> The project is intentionally narrower than a runtime. It proves that I can define a stateful risk boundary, build positive and negative evidence, make the result reproducible, and say precisely what the test still does not prove.
