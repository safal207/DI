# Doability Intelligence (DI)

[![Validate DI fixtures](https://github.com/safal207/DI/actions/workflows/validate-fixtures.yml/badge.svg)](https://github.com/safal207/DI/actions/workflows/validate-fixtures.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release: v0.5-draft](https://img.shields.io/badge/release-v0.5--draft-blue.svg)](https://github.com/safal207/DI/releases/tag/v0.5-draft)

**Current checkpoint:** [`v0.5-draft`](https://github.com/safal207/DI/releases/tag/v0.5-draft) is published from exact validated commit `a35a990c0c3d7715551b1cdaf933a58411f26c2b`. The v0.5 architecture is frozen while external evidence is collected.

DI maps what can and cannot be done before a decision becomes a commitment.

> **Do not promise action until limits are understood.**

По-русски:

> **Не обещай действие, пока не понятны возможности и границы.**

## 30-second proof

The current reference case models one dangerous recovery path:

```text
one logical payment operation
→ one effect commits
→ acknowledgement is lost
→ local commit state remains unknown
→ authoritative lookup recovers the committed effect
→ no second mutation is authorized
```

Reproducible result:

```text
stored effects:             1
duplicate effects:          0
acknowledgement lost:        true
authoritative state:        committed
selected next action:       ACCEPT_EXISTING_EFFECT
DI v0.5 conformance:        PASS
unsafe mutations rejected:  6 / 6
```

Start here:

- [Live interactive demo](https://di-ambiguous-payment-recovery.lovable.app) — public mobile-first presentation; this repository remains the source of truth.
- [Ambiguous-payment case study](docs/case-study-ambiguous-payment-recovery.md)
- [Evidence index](EVIDENCE.md)
- [Reproducible evidence pack](evidence/ambiguous-payment-sandbox/README.md)
- [Mutation report](evidence/ambiguous-payment-sandbox/mutation-report.json)

## What DI is

DI is a narrow pre-decision layer for clarifying:

- capabilities;
- permissions;
- limitations;
- constraints;
- risks and unknowns;
- reversible and blocked paths;
- whether a decision is ready to become a commitment.

DI does not execute the action and does not silently turn technical capability into permission.

```text
request
→ capability and limitation mapping
→ feasible / conditional / blocked / unknown
→ decision boundary
```

## Decision and transition integrity stack

DI cooperates with three independent projects:

```text
DIF → clarify human intent
DI  → clarify feasibility and limits
DRP → preserve the committed decision and rationale
TIP → reason about the transition and review the observed result
```

Canonical repositories:

- [DIF / DeepIntent Funnel](https://github.com/safal207/DIF)
- [DI / Doability Intelligence](https://github.com/safal207/DI)
- [DRP / Decision Record Protocol](https://github.com/safal207/DRP)
- [TIP / Transition Intelligence Protocol](https://github.com/safal207/transition-intelligence-protocol)

The projects remain separate:

```text
DIF != DI
DI  != DRP
DRP != TIP
TIP != execution engine
```

See [`docs/decision-transition-integrity-stack.md`](docs/decision-transition-integrity-stack.md).

## Current validated architecture

```text
Intent
→ Feasibility
→ Strategy
→ Decision
→ Path Revalidation
→ Transition
→ Use-Time Authority
→ Authority Consumption
→ Dispatch Ownership
→ Lease / Fencing Epoch
→ Dispatch Admission
→ Execution
→ Logical Operation Identity
→ Commit Outcome Resolution
→ State Effect
→ Fresh Review
→ Next State
```

This is evidence and conformance tooling. It is not a production transaction coordinator or distributed runtime.

## Profile ladder

| Profile | Protects against |
|---|---|
| `end-to-end-integrity-v0.2` | intent, path, authority, execution, state-effect, and review drift |
| `multi-agent-dispatch-v0.3` | a new worker silently receiving a new mutation permission |
| `lease-split-brain-v0.4` | a stale worker crossing the side-effect boundary after takeover |
| `ambiguous-commit-v0.5` | a lost acknowledgement being mistaken for a failed commit and creating a second effect |

The v0.5 central laws are:

```text
transport outcome != commit outcome
unknown commit != not committed
retry != new effect identity
one committed logical operation -> one committed effect identity
```

## Reproduce the sandbox evidence

The sandbox and validators use Python's standard library only.

```bash
python tools/ambiguous_payment_sandbox.py \
  --output-dir evidence/ambiguous-payment-sandbox \
  --check

python tools/test_ambiguous_payment_sandbox.py \
  --output evidence/ambiguous-payment-sandbox/mutation-report.json \
  --check

python scripts/di-conformance.py \
  evidence/ambiguous-payment-sandbox/trace.json \
  --profile ambiguous-commit-v0.5 \
  --pretty
```

CI performs the same generation, mutation checks, committed-artifact comparison, CLI validation, and credential-boundary scan.

## Test the test

The valid baseline must pass. These unsafe mutations must fail:

| Mutation | Required rejection |
|---|---|
| effect-key drift | retry cannot become a new effect identity |
| multiple committed effects | one operation cannot resolve to two effects |
| unknown claimed as not committed | missing evidence cannot authorize retry |
| retry after commit | known committed effect blocks another mutation |
| retry with a new key | original effect identity must be preserved |
| success without state effect | outcome claim requires matching observed state |

The current mutation report records `6 / 6` rejected as expected.

## Optional Stripe test-mode bridge

The deterministic sandbox is the credential-free baseline.

Optional tools are also included:

```text
tools/capture_stripe_testmode.py
tools/stripe_capture_to_di_trace.py
```

They require a caller-supplied Stripe `sk_test_...` key at runtime, refuse live keys, and never write the secret or raw idempotency key.

See [`docs/stripe-testmode-capture.md`](docs/stripe-testmode-capture.md).

No live Stripe capture, endorsement, or full Stripe conformance is claimed by this repository.

## What PASS means

A PASS means the supplied trace satisfies the selected profile's structural and semantic invariants.

For v0.5, that includes:

- one stable logical-operation identity;
- one stable effect key across ambiguous recovery;
- ordered commit observations;
- no silent conversion of `unknown` into `not_committed`;
- a next action compatible with the resolved commit state;
- matching state-effect evidence before success closure.

## What PASS does not mean

A PASS does not independently prove that:

- external evidence is truthful;
- a database or provider idempotency store was atomic;
- a lease service enforced fencing at runtime;
- a transaction was exactly-once;
- a distributed lock existed;
- network evidence was complete;
- an external company uses or endorses DI.

Those remain runtime, evidence, and provider boundaries.

## Architecture freeze and v0.6

The v0.5 profile ladder is frozen while external evidence is collected.

Allowed work includes fixtures, mutation tests, adapters, benchmarks, security fixes, stable error codes, provider-neutral sandbox tooling, and paid external validation.

A new v0.6 layer requires an external counterexample, a current-profile result, a mutation test, a precise claim boundary, and a project-boundary review.

Current decision:

```text
v0.6 = NO-GO / DEFERRED
```

Why: the deterministic evidence fits v0.5 and does not expose a missing architecture seam.

See:

- [`docs/architecture-freeze-v0.5.md`](docs/architecture-freeze-v0.5.md)
- [`docs/v0.6-decision.md`](docs/v0.6-decision.md)

## Commercial paths

The evidence is packaged for three bounded uses:

### Hiring proof of work

- [`docs/commercial/job-proof-of-work.md`](docs/commercial/job-proof-of-work.md)

### Paid verification pilot

- [`docs/commercial/paid-pilot-one-pager.md`](docs/commercial/paid-pilot-one-pager.md)
- [`docs/commercial/qualification-checklist.md`](docs/commercial/qualification-checklist.md)
- [`docs/commercial/outreach-templates.md`](docs/commercial/outreach-templates.md)

### Open-core product

- [`docs/commercial/conformance-product-brief.md`](docs/commercial/conformance-product-brief.md)
- [`docs/commercial/README.md`](docs/commercial/README.md)

The smallest offer remains:

```text
one mutation flow
→ one high-risk failure surface
→ one reproducible trace pack
→ one PASS / FAIL / BLOCKED boundary
```

## Key documentation

- [`docs/rfc-0001.md`](docs/rfc-0001.md) — original DI specification seed.
- [`docs/concept.md`](docs/concept.md) — DI concept and boundaries.
- [`docs/relation-to-dif-and-drp.md`](docs/relation-to-dif-and-drp.md) — DI's place between intent and commitment.
- [`docs/decision-transition-integrity-stack-v0.5.md`](docs/decision-transition-integrity-stack-v0.5.md) — current profile ladder.
- [`docs/conformance-test-kit.md`](docs/conformance-test-kit.md) — CLI profiles and report contract.
- [`docs/ambiguous-commit-integrity-v0.5.md`](docs/ambiguous-commit-integrity-v0.5.md) — lost-acknowledgement semantics.
- [`docs/case-study-ambiguous-payment-recovery.md`](docs/case-study-ambiguous-payment-recovery.md) — reproducible current case.
- [`docs/case-study-stripe-payment-recovery.md`](docs/case-study-stripe-payment-recovery.md) — public-documentation mapping, not a live Stripe integration.
- [`releases/v0.5-draft.md`](releases/v0.5-draft.md) — published prerelease scope and limitations.
- [`ROADMAP.md`](ROADMAP.md) — current maturity and next priorities.

## Machine-readable artifacts

Important schemas include:

- [`schemas/decision-transition-envelope.schema.json`](schemas/decision-transition-envelope.schema.json)
- [`schemas/recovery-decision-matrix.schema.json`](schemas/recovery-decision-matrix.schema.json)
- [`schemas/use-time-authority-receipt.schema.json`](schemas/use-time-authority-receipt.schema.json)
- [`schemas/authority-consumption-receipt.schema.json`](schemas/authority-consumption-receipt.schema.json)
- [`schemas/dispatch-ownership-event.schema.json`](schemas/dispatch-ownership-event.schema.json)
- [`schemas/dispatch-lease-receipt.schema.json`](schemas/dispatch-lease-receipt.schema.json)
- [`schemas/dispatch-attempt-receipt.schema.json`](schemas/dispatch-attempt-receipt.schema.json)
- [`schemas/logical-operation.schema.json`](schemas/logical-operation.schema.json)
- [`schemas/commit-outcome-receipt.schema.json`](schemas/commit-outcome-receipt.schema.json)
- [`schemas/commit-resolution.schema.json`](schemas/commit-resolution.schema.json)
- [`schemas/state-effect-receipt.schema.json`](schemas/state-effect-receipt.schema.json)
- [`schemas/conformance-report.schema.json`](schemas/conformance-report.schema.json)

See [`MANIFEST.md`](MANIFEST.md) for the fixture and validator map.

## Credential boundary

The repository runs a read-only credential-boundary scan through a reusable ContractGraph-QA workflow pinned to an immutable commit. The caller grants only:

```text
contents: read
```

The scan does not add, read, or rotate external credentials. Its purpose is to detect credential material accidentally crossing the tracked repository boundary.

## Project status

- v0.1 seed protocol: complete.
- v0.2 end-to-end integrity: complete.
- v0.3 multi-agent ownership: complete.
- v0.4 lease and split-brain fencing: complete.
- v0.5 ambiguous commit recovery: complete.
- public `v0.5-draft` prerelease: published.
- v0.5 architecture freeze: active.
- deterministic ambiguous-payment evidence: reproducible and CI-validated.
- public client demo: published at [`di-ambiguous-payment-recovery.lovable.app`](https://di-ambiguous-payment-recovery.lovable.app); repository artifacts remain authoritative.
- unsafe mutations rejected: 6 / 6.
- v0.6 decision: deferred pending an external counterexample.

DI remains intentionally provider-neutral, inspectable, and fail-closed on broken identity chains.

## Contributing

Focused contributions are welcome. Useful areas include:

- realistic positive and negative traces;
- clearer validator errors;
- external sandbox mappings with accurate attribution;
- stable error codes;
- protocol terminology and documentation consistency;
- adapters that never import provider secrets into the repository.

Start with [`CONTRIBUTING.md`](CONTRIBUTING.md) and the open `good first issue` / `help wanted` tasks.

## License

MIT — see [`LICENSE`](LICENSE).
